"""Elf 互动服务层（小精灵代转达 + 过激语言检测）。

LLM 润色 / 检测当前为 mock 实现（标注 MOCK），待 AI 服务集成后替换。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.error_codes import FORBIDDEN, INVALID_PARAMS, NOT_FOUND
from app.core.errors import AppError
from app.models.event import Event
from app.models.relationship import Relationship
from app.models.user import User
from app.repos import elf_repo
from app.schemas.elf import ElfRelayResponse, ModerateResponse
from app.utils.ids import generate_public_id


def _resolve_event_and_check(
    db: Session,
    event_public_id: str,
    user_id: int,
) -> Event:
    """通过 public_id 找到 event 并校验用户属于关系参与方。"""
    stmt = select(Event).where(Event.public_id == event_public_id)
    event = db.execute(stmt).scalar_one_or_none()
    if event is None:
        raise AppError("事件不存在", code=NOT_FOUND)

    rel_stmt = select(Relationship).where(Relationship.id == event.relationship_id)
    rel = db.execute(rel_stmt).scalar_one_or_none()
    if rel is None:
        raise AppError("关系不存在", code=NOT_FOUND)
    if user_id not in (rel.user_a_id, rel.user_b_id):
        raise AppError("无权操作", code=FORBIDDEN)

    return event


def _resolve_target_user(db: Session, target_public_id: str) -> User:
    """通过 public_id 找到目标用户。"""
    stmt = select(User).where(User.public_id == target_public_id)
    user = db.execute(stmt).scalar_one_or_none()
    if user is None:
        raise AppError("目标用户不存在", code=NOT_FOUND)
    return user


def relay_message(
    db: Session,
    user_id: int,
    event_public_id: str,
    target_user_public_id: str,
    raw_message: str,
) -> ElfRelayResponse:
    """小精灵代转达。

    对应 API §7.1 POST /elf/relay。
    """
    event = _resolve_event_and_check(db, event_public_id, user_id)
    target_user = _resolve_target_user(db, target_user_public_id)

    if not raw_message or not raw_message.strip():
        raise AppError("消息不能为空", code=INVALID_PARAMS)

    rel_stmt = select(Relationship).where(Relationship.id == event.relationship_id)
    rel = db.execute(rel_stmt).scalar_one_or_none()
    if rel is None:
        raise AppError("关系不存在", code=NOT_FOUND)
    if target_user.id not in (rel.user_a_id, rel.user_b_id):
        raise AppError("目标用户不在当前关系内", code=FORBIDDEN)
    if target_user.id == user_id:
        raise AppError("目标用户不能是自己", code=FORBIDDEN)

    # MOCK: LLM 润色 —— 待 ai_service 集成后替换。
    # 真实实现应调用 LLM 对 raw_message 进行情绪柔化与措辞润色。
    final_message = f"[MOCK] 你的 Ta 说：「{raw_message}」（已润色）"

    elf_msg = elf_repo.create_elf_message(
        db,
        public_id=generate_public_id(),
        event_id=event.id,
        from_user_id=user_id,
        to_user_id=target_user.id,
        raw_message=raw_message,
        final_message=final_message,
        delivered=True,
    )
    db.commit()

    return ElfRelayResponse(
        message_id=elf_msg.public_id,
        delivered=elf_msg.delivered,
        final_message=elf_msg.final_message,
    )


def moderate_message(
    db: Session,
    user_id: int,
    raw_message: str,
) -> ModerateResponse:
    if not raw_message or not raw_message.strip():
        raise AppError("消息不能为空", code=INVALID_PARAMS)

    """过激语言检测与柔化。

    对应 API §7.2 POST /elf/moderate。
    """
    # MOCK: LLM 检测 —— 待 ai_service 集成后替换。
    # 真实实现应调用 LLM 或规则引擎对 raw_message 做风险评估。
    risk_level = "low"
    blocked = False
    suggested_message: str | None = None

    if len(raw_message) > 100:
        risk_level = "medium"
        suggested_message = f"[MOCK] 建议改为更温和的表达：「{raw_message[:20]}……」"

    elf_repo.create_moderation_log(
        db,
        user_id=user_id,
        raw_message=raw_message,
        risk_level=risk_level,
        blocked=blocked,
        suggested_message=suggested_message,
    )
    db.commit()

    return ModerateResponse(
        blocked=blocked,
        risk_level=risk_level,
        suggested_message=suggested_message,
    )
