"""Elf 互动服务层（小精灵代转达 + 过激语言检测）。"""

import logging
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.error_codes import FORBIDDEN, INVALID_PARAMS, NOT_FOUND
from app.constants.enums import ModerationRiskLevel
from app.core.errors import AppError
from app.models.user import User
from app.repos import audit_repo, elf_repo
from app.schemas.elf import ElfRelayResponse, ModerateResponse
from app.services import ai_service
from app.utils.ids import generate_public_id
from app.utils.permissions import get_event_with_permission

logger = logging.getLogger(__name__)


class ElfRelayAiPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    final_message: str = Field(alias="finalMessage", min_length=1, max_length=500)


class ModerateAiPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    risk_level: Literal["low", "medium", "high"] = Field(alias="riskLevel")
    blocked: bool
    suggested_message: str | None = Field(alias="suggestedMessage", default=None, max_length=500)


def _build_relay_prompt(raw_message: str) -> str:
    return (
        "请把下面这段想发给伴侣的话，整理成更温和、清晰、可被接住的表达。\n"
        "要求：\n"
        "1. 保留原意，不编造新事实。\n"
        "2. 不攻击、不羞辱、不命令。\n"
        "3. 使用第一人称表达感受和诉求。\n"
        "4. 最多 3 句，适合直接发送。\n\n"
        f"原始内容：{raw_message}"
    )


def _fallback_relay_message(raw_message: str) -> str:
    message = raw_message.strip().replace("\n", " ")
    if not message:
        return "我想先把自己的感受说清楚，再和你继续聊这件事。"
    return f"我想更平静地表达一下：{message}"


def _build_moderation_prompt(raw_message: str) -> str:
    return (
        "请判断下面这段话的沟通风险，并输出是否建议拦截以及更温和的替代表达。\n"
        "判断标准：\n"
        "- low: 基本温和，可直接发送\n"
        "- medium: 带有明显指责、讽刺或情绪升级风险，建议柔化\n"
        "- high: 含侮辱、威胁、羞辱、恐吓或明显攻击，建议拦截\n"
        "若 blocked=true，suggestedMessage 必须给出一句可替代的话；若 low 且无需修改，可返回 null。\n\n"
        f"原始内容：{raw_message}"
    )


def _fallback_moderation(raw_message: str) -> ModerateAiPayload:
    message = raw_message.strip()
    lowered = message.lower()
    high_risk_markers = ("滚", "去死", "废物", "垃圾", "傻逼", "你完了", "弄死", "威胁")
    medium_risk_markers = ("总是", "从来不", "烦死了", "受够了", "气死我了", "为什么你")

    if any(marker in message or marker in lowered for marker in high_risk_markers):
        return ModerateAiPayload(
            riskLevel="high",
            blocked=True,
            suggestedMessage="我现在情绪有点重，想先停一下，晚点再把我的感受认真说给你听。",
        )

    if any(marker in message or marker in lowered for marker in medium_risk_markers) or len(message) > 120:
        return ModerateAiPayload(
            riskLevel="medium",
            blocked=False,
            suggestedMessage=f"我想把这件事说清楚：{message[:80].strip()}",
        )

    return ModerateAiPayload(riskLevel="low", blocked=False, suggestedMessage=None)


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

    ai_success = True
    error_code: str | None = None
    model_name = "fallback-elf-relay-v1"

    try:
        ai_result = ai_service.call_llm_json(
            prompt=_build_relay_prompt(raw_message.strip()),
            response_model=ElfRelayAiPayload,
            model_name=None,
            system_prompt=(
                "你是情侣沟通润色助手。"
                "你只能输出合法 JSON。"
                "finalMessage 必须温和、克制、保留原意、避免攻击。"
            ),
            temperature=0.3,
        )
        data: ElfRelayAiPayload = ai_result["data"]
        final_message = data.final_message.strip()
        model_name = str(ai_result["model_name"])
        input_tokens = int(ai_result.get("input_tokens", 0) or 0)
        output_tokens = int(ai_result.get("output_tokens", 0) or 0)
    except AppError as exc:
        logger.warning("Elf relay fell back to local rewrite: %s", exc.message)
        ai_success = False
        error_code = str(exc.code)
        final_message = _fallback_relay_message(raw_message)
        input_tokens = 0
        output_tokens = 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Elf relay unexpected failure: %s", exc)
        ai_success = False
        error_code = "unexpected"
        final_message = _fallback_relay_message(raw_message)
        input_tokens = 0
        output_tokens = 0

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
        model_name=model_name,
        success=ai_success,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        error_code=error_code,
    )
    db.commit()

    logger.info("Elf 代转达成功 event=%s from=%s to=%s", event.public_id, user_id, target_user.public_id)
    return ElfRelayResponse(
        messageId=elf_msg.public_id,
        delivered=elf_msg.delivered,
        finalMessage=elf_msg.final_message,
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

    ai_success = True
    error_code: str | None = None
    model_name = "fallback-elf-moderate-v1"

    try:
        ai_result = ai_service.call_llm_json(
            prompt=_build_moderation_prompt(raw_message.strip()),
            response_model=ModerateAiPayload,
            model_name=None,
            system_prompt=(
                "你是情侣沟通风险判断助手。"
                "你只能输出合法 JSON。"
                "riskLevel 只能是 low/medium/high。"
                "只有在明显攻击、羞辱、威胁时 blocked 才能为 true。"
            ),
            temperature=0.2,
        )
        data: ModerateAiPayload = ai_result["data"]
        risk_level = data.risk_level
        blocked = data.blocked
        suggested_message = data.suggested_message.strip() if data.suggested_message else None
        model_name = str(ai_result["model_name"])
        input_tokens = int(ai_result.get("input_tokens", 0) or 0)
        output_tokens = int(ai_result.get("output_tokens", 0) or 0)
    except AppError as exc:
        logger.warning("Elf moderate fell back to local moderation: %s", exc.message)
        ai_success = False
        error_code = str(exc.code)
        fallback = _fallback_moderation(raw_message)
        risk_level = fallback.risk_level
        blocked = fallback.blocked
        suggested_message = fallback.suggested_message
        input_tokens = 0
        output_tokens = 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Elf moderate unexpected failure: %s", exc)
        ai_success = False
        error_code = "unexpected"
        fallback = _fallback_moderation(raw_message)
        risk_level = fallback.risk_level
        blocked = fallback.blocked
        suggested_message = fallback.suggested_message
        input_tokens = 0
        output_tokens = 0

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
        model_name=model_name,
        success=ai_success,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        error_code=error_code,
    )
    db.commit()

    return ModerateResponse(
        blocked=blocked,
        riskLevel=risk_level,
        suggestedMessage=suggested_message,
    )
