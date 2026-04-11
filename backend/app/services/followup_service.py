"""Follow-up chat service."""

from __future__ import annotations


from sqlalchemy.orm import Session

from app.constants.enums import EventStatus
from app.constants.error_codes import INVALID_PARAMS, PREREQ_NOT_MET
from app.core.errors import AppError
from app.repos import audit_repo, followup_repo
from app.schemas.followup import FollowupContextMeta, FollowupResponse
from app.services import ai_service
from app.utils.context_builder import ContextPayload, build_context
from app.utils.permissions import get_event_with_permission


def _build_followup_system_prompt(ctx: ContextPayload) -> str:
    return (
        "你是 Uli 的复盘陪伴助手。\n"
        "你只能基于已落库的上下文回复，不能编造数据库里没有的事实。\n"
        "你的目标是帮助用户复盘、理解冲突、形成下一步沟通策略。\n"
        "回复要求：\n"
        "- 使用中文\n"
        "- 语气温和、具体、可执行\n"
        "- 不要替用户做医学、法律结论\n"
        f"- 本次上下文命中：recentMessages={ctx.meta['recentMessages']}, "
        f"snapshots={ctx.meta['snapshots']}, judgeResults={ctx.meta['judgeResults']}\n\n"
        f"Snapshot_A: {ctx.snapshot_a or 'none'}\n"
        f"Snapshot_B: {ctx.snapshot_b or 'none'}\n"
        f"JudgeResult: {ctx.judge_result or 'none'}\n"
        f"Review: {ctx.review_content or 'none'}"
    )


def _build_followup_messages(ctx: ContextPayload, message: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": _build_followup_system_prompt(ctx)}
    ]
    messages.extend(
        {
            "role": str(item["role"]),
            "content": str(item["content"]),
        }
        for item in ctx.recent_messages[-8:]
    )
    messages.append({"role": "user", "content": message})
    return messages


def followup_chat(
    db: Session,
    user_id: int,
    event_public_id: str,
    message: str,
) -> FollowupResponse:
    event, _rel = get_event_with_permission(db, event_public_id, user_id)

    if event.status not in (EventStatus.JUDGED, EventStatus.REVIEWED, EventStatus.CLOSED):
        raise AppError("事件尚未满足复盘聊天前置条件", code=PREREQ_NOT_MET)
    if not message or not message.strip():
        raise AppError("消息不能为空", code=INVALID_PARAMS)

    ctx = build_context(db, user_id, event.id)
    ai_result = ai_service.call_chat_llm(
        messages=_build_followup_messages(ctx, message.strip()),
        model_name=None,  # 使用默认 Kimi 模型
        temperature=0.45,
    )
    reply_text = str(ai_result["content"])

    followup_repo.create_followup_message(
        db,
        event_id=event.id,
        user_id=user_id,
        user_message=message,
        assistant_reply=reply_text,
        context_meta=ctx.meta,
    )

    audit_repo.create_ai_call_log(
        db,
        event_id=event.id,
        scene="followup",
        model_name=str(ai_result["model_name"]),
        success=True,
        input_tokens=int(ai_result.get("input_tokens", 0) or 0),
        output_tokens=int(ai_result.get("output_tokens", 0) or 0),
    )
    db.commit()

    return FollowupResponse(
        reply=reply_text,
        contextMeta=FollowupContextMeta(
            recentMessages=ctx.meta["recentMessages"],
            snapshots=ctx.meta["snapshots"],
            judgeResults=ctx.meta["judgeResults"],
        ),
    )
