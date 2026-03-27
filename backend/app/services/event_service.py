"""Event 业务服务层。

负责事件创建、快照提交、裁判触发、状态流转的编排。
状态机：draft -> waiting_b -> judged
所有状态变更写 event_state_logs，AI 场景写 ai_call_logs。
"""

import logging
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants.enums import EventStatus, SnapshotSide
from app.constants.error_codes import FORBIDDEN, INVALID_PARAMS, INVALID_STATE, NOT_FOUND, PREREQ_NOT_MET
from app.core.errors import AppError

logger = logging.getLogger(__name__)
from app.models.event import Event
from app.models.judge import JudgeResult
from app.models.relationship import Relationship
from app.models.snapshot import EventSnapshot
from app.repos import audit_repo, event_repo, judge_repo, snapshot_repo
from app.services import judge_service, review_service
from app.utils.ids import generate_public_id
from app.utils.permissions import (
    assert_relationship_member,
    get_event_with_permission,
    get_relationship_by_public_id,
)


def create_event(
    db: Session,
    user_id: int,
    title: str,
    relationship_public_id: str,
) -> Event:
    """创建事件（draft）。校验用户为关系参与方。"""
    rel = get_relationship_by_public_id(db, relationship_public_id)
    if user_id not in (rel.user_a_id, rel.user_b_id):
        raise AppError("无权在该关系中创建事件", code=FORBIDDEN)
    open_event = event_repo.get_open_event_for_relationship(db, rel.id)
    if open_event is not None:
        raise AppError("当前关系已有未完成事件，请先处理完成后再创建", code=INVALID_STATE)

    event = event_repo.create_event(
        db,
        public_id=generate_public_id(),
        relationship_id=rel.id,
        initiator_user_id=user_id,
        title=title,
    )
    db.commit()
    db.refresh(event)
    logger.info("事件创建成功 event=%s user=%s rel=%s", event.public_id, user_id, rel.public_id)
    return event


def commit_a(
    db: Session,
    user_id: int,
    event_public_id: str,
    confirm_text: str,
) -> tuple[Event, EventSnapshot]:
    """A 确认并冻结 Snapshot_A，状态 draft -> waiting_b。"""
    event, _rel = get_event_with_permission(db, event_public_id, user_id)

    if user_id != event.initiator_user_id:
        raise AppError("仅事件发起方可提交 Snapshot_A", code=FORBIDDEN)
    if event.status != EventStatus.DRAFT:
        raise AppError("当前状态不允许提交 Snapshot_A", code=INVALID_STATE)

    existing = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.A)
    if existing is not None:
        raise AppError("Snapshot_A 已存在", code=INVALID_STATE)

    snapshot = snapshot_repo.create_snapshot(
        db,
        public_id=generate_public_id(),
        event_id=event.id,
        side=SnapshotSide.A,
        summary=confirm_text,
        points_a=[],
        points_b=[],
        confirmed_by_user_id=user_id,
    )

    old_status = event.status
    event.status = EventStatus.WAITING_B
    db.flush()

    audit_repo.create_event_state_log(
        db,
        event_id=event.id,
        from_status=old_status,
        to_status=EventStatus.WAITING_B,
        action="commit_a",
        operator_user_id=user_id,
    )

    db.commit()
    db.refresh(event)
    db.refresh(snapshot)
    logger.info("Snapshot_A 已提交 event=%s user=%s", event.public_id, user_id)
    return event, snapshot


def get_invite(db: Session, event_public_id: str) -> Event:
    """获取邀请页最小信息（无需鉴权）。"""
    event = event_repo.get_event_by_public_id(db, event_public_id)
    if event is None:
        raise AppError("事件不存在", code=NOT_FOUND)
    return event


def get_snapshot_a(
    db: Session,
    user_id: int,
    event_public_id: str,
) -> tuple[Event, EventSnapshot]:
    """获取 Snapshot_A 内容（需鉴权 + 权限）。"""
    event, _rel = get_event_with_permission(db, event_public_id, user_id)

    snapshot = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.A)
    if snapshot is None:
        raise AppError("Snapshot_A 尚未提交", code=NOT_FOUND)
    return event, snapshot


def _execute_judge(
    db: Session,
    event: Event,
    rel: Relationship,
    snapshot_a: EventSnapshot,
    snapshot_b: EventSnapshot | None,
    operator_user_id: int,
) -> JudgeResult:
    """共用的裁判执行逻辑：生成结果 + 状态流转 + 日志 + 沉淀 review/calendar。"""
    try:
        return _execute_judge_inner(db, event, rel, snapshot_a, snapshot_b, operator_user_id)
    except IntegrityError:
        db.rollback()
        raise AppError("裁判已生成，请勿重复操作", code=INVALID_STATE)


def _execute_judge_inner(
    db: Session,
    event: Event,
    rel: Relationship,
    snapshot_a: EventSnapshot,
    snapshot_b: EventSnapshot | None,
    operator_user_id: int,
) -> JudgeResult:
    judge_result = judge_service.generate_judge_result(
        db,
        event_id=event.id,
        snapshot_a=snapshot_a,
        snapshot_b=snapshot_b,
    )

    old_status = event.status
    event.status = EventStatus.JUDGED
    event.judged_at = datetime.now(tz=UTC)
    db.flush()

    audit_repo.create_event_state_log(
        db,
        event_id=event.id,
        from_status=old_status,
        to_status=EventStatus.JUDGED,
        action="judge",
        operator_user_id=operator_user_id,
    )

    audit_repo.create_ai_call_log(
        db,
        event_id=event.id,
        scene="judge",
        model_name=judge_result.model_name or "mock-judge-v1",
        success=True,
        input_tokens=judge_result.input_tokens or 0,
        output_tokens=judge_result.output_tokens or 0,
    )

    review_service.create_review_from_judge(
        db,
        event_id=event.id,
        relationship_id=rel.id,
        content=judge_result.objective_summary,
    )

    db.commit()
    db.refresh(event)
    db.refresh(judge_result)
    try:
        from app.services.analysis_session_store import get_analysis_session_store

        get_analysis_session_store().clear_sessions_for_relationship(rel.public_id)
    except Exception:  # noqa: BLE001 - cache cleanup must not break committed result
        logger.warning("failed to clear analysis sessions for relationship=%s", rel.public_id)
    logger.info("裁判完成 event=%s judge=%s operator=%s", event.public_id, judge_result.public_id, operator_user_id)
    return judge_result


def b_agree(
    db: Session,
    user_id: int,
    event_public_id: str,
    agree: bool,
) -> tuple[Event, JudgeResult]:
    """B 同意并触发裁判（仅 snapshot_a），状态 waiting_b -> judged。"""
    if not agree:
        raise AppError("B 未同意，不触发裁判", code=INVALID_PARAMS)

    event, rel = get_event_with_permission(db, event_public_id, user_id)

    if user_id == event.initiator_user_id:
        raise AppError("事件发起方不能执行 B 侧操作", code=FORBIDDEN)
    if event.status != EventStatus.WAITING_B:
        raise AppError("当前状态不允许此操作", code=INVALID_STATE)

    snapshot_a = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.A)
    if snapshot_a is None:
        raise AppError("Snapshot_A 不存在，无法裁判", code=PREREQ_NOT_MET)

    judge_result = _execute_judge(db, event, rel, snapshot_a, None, user_id)
    return event, judge_result


def commit_b(
    db: Session,
    user_id: int,
    event_public_id: str,
    summary: str,
    points_a: list[str],
    points_b: list[str],
) -> tuple[Event, EventSnapshot, JudgeResult]:
    """B 提交 Snapshot_B 并触发裁判（双方视角），状态 waiting_b -> judged。"""
    event, rel = get_event_with_permission(db, event_public_id, user_id)

    if user_id == event.initiator_user_id:
        raise AppError("事件发起方不能执行 B 侧操作", code=FORBIDDEN)
    if event.status != EventStatus.WAITING_B:
        raise AppError("当前状态不允许此操作", code=INVALID_STATE)

    existing_b = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.B)
    if existing_b is not None:
        raise AppError("Snapshot_B 已存在", code=INVALID_STATE)

    snapshot_a = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.A)
    if snapshot_a is None:
        raise AppError("Snapshot_A 不存在，无法裁判", code=PREREQ_NOT_MET)

    snapshot_b = snapshot_repo.create_snapshot(
        db,
        public_id=generate_public_id(),
        event_id=event.id,
        side=SnapshotSide.B,
        summary=summary,
        points_a=points_a,
        points_b=points_b,
        confirmed_by_user_id=user_id,
    )

    judge_result = _execute_judge(db, event, rel, snapshot_a, snapshot_b, user_id)
    db.refresh(snapshot_b)
    return event, snapshot_b, judge_result


def get_judge_result(
    db: Session,
    user_id: int,
    event_public_id: str,
) -> tuple[Event, JudgeResult]:
    """只读查询裁判结果（严禁实时触发 AI）。"""
    event, _rel = get_event_with_permission(db, event_public_id, user_id)

    judge_result = judge_repo.get_judge_result_by_event_id(db, event.id)
    if judge_result is None:
        raise AppError("裁判结果尚未生成", code=PREREQ_NOT_MET)
    return event, judge_result

from app.core.config import settings


def _execute_judge_inner(
    db: Session,
    event: Event,
    rel: Relationship,
    snapshot_a: EventSnapshot,
    snapshot_b: EventSnapshot | None,
    operator_user_id: int,
) -> JudgeResult:
    judge_result = judge_service.generate_judge_result(
        db,
        event_id=event.id,
        snapshot_a=snapshot_a,
        snapshot_b=snapshot_b,
    )

    old_status = event.status
    event.status = EventStatus.JUDGED
    event.judged_at = datetime.now(tz=UTC)
    db.flush()

    audit_repo.create_event_state_log(
        db,
        event_id=event.id,
        from_status=old_status,
        to_status=EventStatus.JUDGED,
        action="judge",
        operator_user_id=operator_user_id,
    )

    audit_repo.create_ai_call_log(
        db,
        event_id=event.id,
        scene="judge",
        model_name=judge_result.model_name or settings.kimi_text_model,
        success=True,
        input_tokens=judge_result.input_tokens or 0,
        output_tokens=judge_result.output_tokens or 0,
    )

    try:
        review_ai_result = review_service.generate_review_content_from_judge(
            snapshot_a=snapshot_a,
            snapshot_b=snapshot_b,
            judge_result=judge_result,
        )
    except AppError as exc:
        logger.warning("review generation failed for event=%s: %s", event.public_id, exc.message)
        audit_repo.create_ai_call_log(
            db,
            event_id=event.id,
            scene="review",
            model_name=settings.kimi_text_model,
            success=False,
            error_code=str(exc.code),
        )
        review_content = review_service.build_fallback_review_content(judge_result)
    except Exception as exc:  # noqa: BLE001 - review fallback should not block judge
        logger.warning("unexpected review generation failure for event=%s: %s", event.public_id, exc)
        audit_repo.create_ai_call_log(
            db,
            event_id=event.id,
            scene="review",
            model_name=settings.kimi_text_model,
            success=False,
            error_code="unexpected",
        )
        review_content = review_service.build_fallback_review_content(judge_result)
    else:
        review_content = str(review_ai_result["content"])
        audit_repo.create_ai_call_log(
            db,
            event_id=event.id,
            scene="review",
            model_name=str(review_ai_result["model_name"]),
            success=True,
            input_tokens=int(review_ai_result["input_tokens"]),
            output_tokens=int(review_ai_result["output_tokens"]),
        )

    review_service.create_review_from_judge(
        db,
        event_id=event.id,
        relationship_id=rel.id,
        content=review_content,
    )

    db.commit()
    db.refresh(event)
    db.refresh(judge_result)
    try:
        from app.services.analysis_session_store import get_analysis_session_store

        get_analysis_session_store().clear_sessions_for_relationship(rel.public_id)
    except Exception:  # noqa: BLE001 - cache cleanup must not break committed result
        logger.warning("failed to clear analysis sessions for relationship=%s", rel.public_id)
    logger.info("judge completed event=%s judge=%s operator=%s", event.public_id, judge_result.public_id, operator_user_id)
    return judge_result
