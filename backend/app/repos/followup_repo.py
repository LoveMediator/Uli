"""FollowupMessage 数据访问层。

仅操作 followup_messages 表。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import FollowupMessage


def get_recent_messages(
    db: Session,
    event_id: int,
    limit: int = 10,
) -> list[FollowupMessage]:
    """获取指定事件的近期复盘对话，按创建时间倒序，最多 limit 条。

    FD §5.9 约定最近对话 ≤10 条。
    """
    stmt = (
        select(FollowupMessage)
        .where(FollowupMessage.event_id == event_id)
        .order_by(FollowupMessage.created_at.desc())
        .limit(limit)
    )
    rows = list(db.execute(stmt).scalars().all())
    rows.reverse()
    return rows


def create_followup_message(
    db: Session,
    *,
    event_id: int,
    user_id: int,
    user_message: str,
    assistant_reply: str,
    context_meta: dict | None = None,
) -> FollowupMessage:
    """创建一条复盘聊天记录。"""
    msg = FollowupMessage(
        event_id=event_id,
        user_id=user_id,
        user_message=user_message,
        assistant_reply=assistant_reply,
        context_meta=context_meta,
    )
    db.add(msg)
    db.flush()
    return msg
