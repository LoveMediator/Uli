from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.constants.enums import EventStatus, SnapshotSide
from app.constants.error_codes import FORBIDDEN, INVALID_PARAMS, INVALID_STATE
from app.core.config import settings
from app.core.errors import AppError
from app.models.user import User
from app.repos import audit_repo, event_repo, snapshot_repo
from app.schemas.analysis_session import (
    AnalysisSessionCommitData,
    AnalysisSessionData,
    AnalysisSessionMessageData,
    AnalysisSessionMessagePayload,
)
from app.services import ai_service, analysis_session_store, event_service
from app.utils.ids import generate_public_id
from app.utils.permissions import get_event_with_permission, get_relationship_by_public_id

PHASE_A = "a"
PHASE_B = "b"
STATUS_ACTIVE = "active"
STATUS_COMMITTED = "committed"


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _session_expiry() -> datetime:
    return _now() + timedelta(seconds=settings.analysis_session_ttl_seconds)


def _touch_session(session: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    session["updatedAt"] = now.isoformat()
    session["expiresAt"] = _session_expiry().isoformat()
    return session


def _build_session_data(session: dict[str, Any]) -> AnalysisSessionData:
    return AnalysisSessionData(
        sessionId=session["sessionId"],
        phase=session["phase"],
        relationshipId=session.get("relationshipId"),
        eventId=session.get("eventId"),
        expiresAt=datetime.fromisoformat(session["expiresAt"]),
        messages=[
            AnalysisSessionMessagePayload(
                role=message["role"],
                content=message["content"],
                createdAt=datetime.fromisoformat(message["createdAt"]),
            )
            for message in session.get("messages", [])
        ],
    )


def _append_message(session: dict[str, Any], *, role: str, content: str) -> None:
    session.setdefault("messages", []).append(
        {
            "role": role,
            "content": content,
            "createdAt": _now().isoformat(),
        }
    )


def _infer_reply_language(session: dict[str, Any]) -> str:
    for item in reversed(session.get("messages", [])):
        if item.get("role") != "user":
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        if any("\u4e00" <= ch <= "\u9fff" for ch in content):
            return "简体中文"
        if any(ch.isascii() and ch.isalpha() for ch in content):
            return "English"
    return "简体中文"


def _build_private_prompt(session: dict[str, Any], message: str) -> str:
    history_lines = [
        f"{item['role']}: {item['content']}"
        for item in session.get("messages", [])[-8:]
    ]
    history = "\n".join(history_lines)
    reply_language = _infer_reply_language(session)
    return (
        "You are LoveMediator's private mediation assistant.\n"
        "你是 LoveMediator 的私有调解分析助手。\n"
        "Help the user organize facts, clarify emotions, and identify viewpoints without "
        "advancing business state or pretending the event is committed.\n"
        f"Mandatory reply language: {reply_language}.\n"
        "If the mandatory reply language is 简体中文, reply only in 简体中文.\n"
        "If the mandatory reply language is English, reply only in English.\n"
        f"phase={session['phase']}\n"
        f"history=\n{history}\n"
        f"user={message}"
    )


def _build_structured_snapshot(session: dict[str, Any]) -> tuple[str, list[str], list[str], dict[str, Any]]:
    user_messages = [
        item["content"].strip()
        for item in session.get("messages", [])
        if item["role"] == "user" and item["content"].strip()
    ]
    if not user_messages:
        raise AppError("当前分析会话没有可确认的内容", code=INVALID_STATE)

    summary = user_messages[-1]
    unique_points: list[str] = []
    for item in user_messages:
        if item not in unique_points:
            unique_points.append(item)
        if len(unique_points) >= 3:
            break

    if session["phase"] == PHASE_A:
        points_a = unique_points
        points_b: list[str] = []
    else:
        points_a = []
        points_b = unique_points

    raw_payload = {
        "phase": session["phase"],
        "messages": session.get("messages", []),
    }
    return summary, points_a, points_b, raw_payload


def _get_store() -> analysis_session_store.AnalysisSessionStore:
    return analysis_session_store.get_analysis_session_store()


def _get_owned_session(session_id: str, current_user: User) -> dict[str, Any]:
    session = _get_store().get_session(session_id)
    if session is None:
        raise AppError("分析会话不存在或已过期", code=INVALID_STATE)
    if session["status"] != STATUS_ACTIVE:
        raise AppError("分析会话已确认，不能重复提交", code=INVALID_STATE)
    if int(session["userId"]) != current_user.id:
        raise AppError("无权访问该分析会话", code=FORBIDDEN)
    return session


def start_a_analysis_session(
    db: Session,
    current_user: User,
    relationship_public_id: str,
) -> AnalysisSessionData:
    relationship = get_relationship_by_public_id(db, relationship_public_id)
    if current_user.id not in (relationship.user_a_id, relationship.user_b_id):
        raise AppError("无权在该关系下发起分析", code=FORBIDDEN)
    if event_repo.get_open_event_for_relationship(db, relationship.id) is not None:
        raise AppError("当前关系已有未完成事件，请先处理完成后再创建", code=INVALID_STATE)

    store = _get_store()
    session = store.get_scoped_session(PHASE_A, relationship_public_id, current_user.id)
    if session is None:
        session = {
            "sessionId": generate_public_id(),
            "phase": PHASE_A,
            "status": STATUS_ACTIVE,
            "userId": current_user.id,
            "relationshipId": relationship.public_id,
            "relationshipDbId": relationship.id,
            "eventId": None,
            "eventDbId": None,
            "messages": [],
            "createdAt": _now().isoformat(),
        }
    store.save_session(_touch_session(session))
    return _build_session_data(session)


def start_b_analysis_session(
    db: Session,
    current_user: User,
    event_public_id: str,
) -> AnalysisSessionData:
    event, relationship = get_event_with_permission(db, event_public_id, current_user.id)
    if current_user.id == event.initiator_user_id:
        raise AppError("发起方不能进入 B 侧私有分析", code=FORBIDDEN)
    if event.status != EventStatus.WAITING_B:
        raise AppError("当前状态不允许开启 B 侧分析", code=INVALID_STATE)

    store = _get_store()
    session = store.get_scoped_session(PHASE_B, event_public_id, current_user.id)
    if session is None:
        session = {
            "sessionId": generate_public_id(),
            "phase": PHASE_B,
            "status": STATUS_ACTIVE,
            "userId": current_user.id,
            "relationshipId": relationship.public_id,
            "relationshipDbId": relationship.id,
            "eventId": event.public_id,
            "eventDbId": event.id,
            "messages": [],
            "createdAt": _now().isoformat(),
        }
    store.save_session(_touch_session(session))
    return _build_session_data(session)


def send_analysis_message(
    db: Session,
    current_user: User,
    session_id: str,
    message: str,
) -> AnalysisSessionMessageData:
    if not message or not message.strip():
        raise AppError("消息不能为空", code=INVALID_PARAMS)

    session = _get_owned_session(session_id, current_user)
    if session["phase"] == PHASE_B and session.get("eventId") is not None:
        event, _relationship = get_event_with_permission(db, str(session["eventId"]), current_user.id)
        if event.status != EventStatus.WAITING_B:
            raise AppError("当前状态不允许继续 B 侧分析", code=INVALID_STATE)

    clean_message = message.strip()
    _append_message(session, role="user", content=clean_message)
    prompt = _build_private_prompt(session, clean_message)
    ai_result = ai_service.call_llm(prompt=prompt, model_name="mock-private-chat-v1")
    reply = ai_result["content"]
    _append_message(session, role="assistant", content=reply)

    _get_store().save_session(_touch_session(session))
    audit_repo.create_ai_call_log(
        db,
        event_id=session.get("eventDbId"),
        scene="private_chat",
        model_name=ai_result.get("model_name", "mock-private-chat-v1"),
        success=True,
        input_tokens=int(ai_result.get("input_tokens", 0) or 0),
        output_tokens=int(ai_result.get("output_tokens", 0) or 0),
        trace_id=session_id,
    )
    db.commit()
    return AnalysisSessionMessageData(sessionId=session_id, reply=reply)


def _mark_session_committed(session: dict[str, Any], **result_fields: str | None) -> None:
    session["status"] = STATUS_COMMITTED
    session["committedAt"] = _now().isoformat()
    for key, value in result_fields.items():
        session[key] = value
    _get_store().save_session(_touch_session(session))


def commit_analysis_session(
    db: Session,
    current_user: User,
    session_id: str,
) -> AnalysisSessionCommitData:
    session = _get_owned_session(session_id, current_user)
    summary, points_a, points_b, raw_payload = _build_structured_snapshot(session)

    if session["phase"] == PHASE_A:
        relationship = get_relationship_by_public_id(db, str(session["relationshipId"]))
        if current_user.id not in (relationship.user_a_id, relationship.user_b_id):
            raise AppError("无权在该关系下确认分析", code=FORBIDDEN)
        if event_repo.get_open_event_for_relationship(db, relationship.id) is not None:
            raise AppError("当前关系已有未完成事件，请先处理完成后再创建", code=INVALID_STATE)

        event = event_repo.create_event(
            db,
            public_id=generate_public_id(),
            relationship_id=relationship.id,
            initiator_user_id=current_user.id,
            title=None,
        )
        snapshot = snapshot_repo.create_snapshot(
            db,
            public_id=generate_public_id(),
            event_id=event.id,
            side=SnapshotSide.A,
            summary=summary,
            points_a=points_a,
            points_b=points_b,
            raw_payload=raw_payload,
            confirmed_by_user_id=current_user.id,
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
            operator_user_id=current_user.id,
            trace_id=session_id,
        )
        db.commit()
        db.refresh(event)
        db.refresh(snapshot)
        _mark_session_committed(
            session,
            eventId=event.public_id,
            eventDbId=str(event.id),
            snapshotAId=snapshot.public_id,
        )
        return AnalysisSessionCommitData(
            sessionId=session_id,
            eventId=event.public_id,
            status=event.status.value,
            snapshotAId=snapshot.public_id,
        )

    event, relationship = get_event_with_permission(db, str(session["eventId"]), current_user.id)
    if current_user.id == event.initiator_user_id:
        raise AppError("发起方不能确认 B 侧分析", code=FORBIDDEN)
    if event.status != EventStatus.WAITING_B:
        raise AppError("当前状态不允许确认 B 侧分析", code=INVALID_STATE)
    existing_b = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.B)
    if existing_b is not None:
        raise AppError("Snapshot_B 已存在", code=INVALID_STATE)
    snapshot_a = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.A)
    if snapshot_a is None:
        raise AppError("Snapshot_A 不存在，无法继续", code=INVALID_STATE)

    snapshot_b = snapshot_repo.create_snapshot(
        db,
        public_id=generate_public_id(),
        event_id=event.id,
        side=SnapshotSide.B,
        summary=summary,
        points_a=points_a,
        points_b=points_b,
        raw_payload=raw_payload,
        confirmed_by_user_id=current_user.id,
    )
    judge_result = event_service._execute_judge(
        db,
        event,
        relationship,
        snapshot_a,
        snapshot_b,
        current_user.id,
    )
    db.refresh(snapshot_b)
    _mark_session_committed(
        session,
        judgeResultId=judge_result.public_id,
        snapshotBId=snapshot_b.public_id,
    )
    return AnalysisSessionCommitData(
        sessionId=session_id,
        eventId=event.public_id,
        status=event.status.value,
        snapshotBId=snapshot_b.public_id,
        judgeResultId=judge_result.public_id,
    )
