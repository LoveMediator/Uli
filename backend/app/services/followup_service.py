"""Followup 复盘聊天服务层。

核心逻辑：build_context → LLM 调用 → 写入 followup_messages + ai_call_logs。
LLM 调用当前为 mock 实现（标注 MOCK），待 AI 服务集成后替换。
"""

from sqlalchemy.orm import Session

from app.constants.enums import EventStatus
from app.constants.error_codes import INVALID_PARAMS, PREREQ_NOT_MET
from app.core.errors import AppError
from app.models.audit import AiCallLog
from app.repos import followup_repo
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

    # 记录 AI 调用日志（场景：followup）。当前为 mock，token 先记 0。
    db.add(
        AiCallLog(
            event_id=event.id,
            scene="followup",
            model_name="mock-followup-v1",
            input_tokens=0,
            output_tokens=0,
            success=True,
            error_code=None,
            trace_id=None,
        )
    )
    db.commit()

    return FollowupResponse(
        reply=reply_text,
        context_meta=FollowupContextMeta(
            recent_messages=ctx.meta["recentMessages"],
            snapshots=ctx.meta["snapshots"],
            judge_results=ctx.meta["judgeResults"],
        ),
    )
