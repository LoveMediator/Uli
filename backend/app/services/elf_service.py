"""Elf 互动服务层（小精灵代转达 + 过激语言检测）。

LLM 润色 / 检测当前为 mock 实现（标注 MOCK），待 AI 服务集成后替换。
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.error_codes import FORBIDDEN, INVALID_PARAMS, NOT_FOUND
from app.core.errors import AppError
from app.models.user import User
from app.repos import audit_repo, elf_repo
from app.schemas.elf import ElfRelayResponse, ModerateResponse
from app.utils.ids import generate_public_id
from app.utils.permissions import get_event_with_permission

logger = logging.getLogger(__name__)

MOCK_MODERATE_THRESHOLD = 100
MOCK_SUGGEST_PREVIEW_LEN = 20


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
    event, rel = get_event_with_permission(db, event_public_id, user_id)
    target_user = _resolve_target_user(db, target_user_public_id)

    if not raw_message or not raw_message.strip():
        raise AppError("消息不能为空", code=INVALID_PARAMS)
    if target_user.id not in (rel.user_a_id, rel.user_b_id):
        raise AppError("目标用户不在当前关系内", code=FORBIDDEN)
    if target_user.id == user_id:
        raise AppError("目标用户不能是自己", code=FORBIDDEN)

    # MOCK: LLM 润色 —— 待 ai_service 集成后替换。
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

    audit_repo.create_ai_call_log(
        db,
        event_id=event.id,
        scene="elf_relay",
        model_name="mock-elf-relay-v1",
        success=True,
    )
    db.commit()

    logger.info("Elf 代转达成功 event=%s from=%s to=%s", event.public_id, user_id, target_user.public_id)
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
    """过激语言检测与柔化。

    对应 API §7.2 POST /elf/moderate。
    """
    if not raw_message or not raw_message.strip():
        raise AppError("消息不能为空", code=INVALID_PARAMS)

    # MOCK: LLM 检测 —— 待 ai_service 集成后替换。
    risk_level = "low"
    blocked = False
    suggested_message: str | None = None

    if len(raw_message) > MOCK_MODERATE_THRESHOLD:
        risk_level = "medium"
        suggested_message = f"[MOCK] 建议改为更温和的表达：「{raw_message[:MOCK_SUGGEST_PREVIEW_LEN]}……」"

    elf_repo.create_moderation_log(
        db,
        user_id=user_id,
        raw_message=raw_message,
        risk_level=risk_level,
        blocked=blocked,
        suggested_message=suggested_message,
    )

    audit_repo.create_ai_call_log(
        db,
        event_id=None,
        scene="elf_moderate",
        model_name="mock-elf-moderate-v1",
        success=True,
    )
    db.commit()

    return ModerateResponse(
        blocked=blocked,
        risk_level=risk_level,
        suggested_message=suggested_message,
    )
