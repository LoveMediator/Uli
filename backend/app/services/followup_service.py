"""Followup 复盘聊天服务层。

核心逻辑：build_context → LLM 调用 → 写入 followup_messages + ai_call_logs。
LLM 调用当前为 mock 实现（标注 MOCK），待 AI 服务集成后替换。
"""

from sqlalchemy.orm import Session

from app.constants.enums import EventStatus
from app.constants.error_codes import INVALID_PARAMS, PREREQ_NOT_MET
from app.core.errors import AppError
from app.repos import audit_repo, followup_repo
from app.schemas.followup import FollowupContextMeta, FollowupResponse
from app.utils.context_builder import build_context
from app.utils.permissions import get_event_with_permission


def followup_chat(
    db: Session,
    user_id: int,
    event_public_id: str,
    message: str,
) -> FollowupResponse:
    """复盘聊天：构建上下文 → 调用 LLM → 落库。

    对应 API §5.9 POST /events/{eventId}/followup-chat/messages。
    API 实现约束：必须走 build_context，禁止裸调 LLM。
    """
    event, _rel = get_event_with_permission(db, event_public_id, user_id)

    # followup 仅允许在裁判完成后进行，避免绕过主链。
    if event.status not in (EventStatus.JUDGED, EventStatus.REVIEWED, EventStatus.CLOSED):
        raise AppError("事件尚未满足复盘聊天前置条件", code=PREREQ_NOT_MET)

    if not message or not message.strip():
        raise AppError("消息不能为空", code=INVALID_PARAMS)

    ctx = build_context(db, user_id, event.id)

    # MOCK: LLM 调用 —— 待 ai_service 集成后替换为真实调用。
    # 真实实现应将 ctx 中的 snapshot_a/b、judge_result、recent_messages
    # 拼入 prompt 模板，调用 LLM 并用 Pydantic 校验输出。
    reply_text = (
        f"[MOCK] 收到你的问题：「{message}」。"
        f"基于 {ctx.meta['snapshots']} 份快照和 "
        f"{ctx.meta['judgeResults']} 份裁判结果，建议你们……"
    )

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
        model_name="mock-followup-v1",
        success=True,
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

from app.services import ai_service


def _build_followup_system_prompt(ctx) -> str:
    return (
        "你是 LoveMediator 的复盘陪伴助手。\n"
        "你只能基于已落库的上下文回复，不能编造数据库里没有的事实。\n"
        "你的目标是帮助用户复盘、理解冲突、形成下一步沟通策略。\n"
        "回复要求：\n"
        "- 使用中文\n"
        "- 语气温和、具体、可执行\n"
        "- 不要替用户做医学、法律结论\n"
        f"- 本次上下文命中：recentMessages={ctx.meta['recentMessages']}, "
        f"snapshots={ctx.meta['snapshots']}, judgeResults={ctx.meta['judgeResults']}\n\n"
        f"Snapshot_A: {ctx.snapshot_a or '无'}\n"
        f"Snapshot_B: {ctx.snapshot_b or '无'}\n"
        f"JudgeResult: {ctx.judge_result or '无'}\n"
        f"Review: {ctx.review_content or '无'}"
    )


def _build_followup_messages(ctx, message: str) -> list[dict[str, str]]:
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
        model_name="followup-v1",
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
