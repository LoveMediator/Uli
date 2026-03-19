"""ElfMessage / ModerationLog 数据访问层。

仅操作 elf_messages、moderation_logs 表。
"""

from sqlalchemy.orm import Session

from app.constants.enums import ModerationRiskLevel
from app.models.elf import ElfMessage, ModerationLog


def create_elf_message(
    db: Session,
    *,
    public_id: str,
    event_id: int | None,
    from_user_id: int,
    to_user_id: int,
    raw_message: str,
    final_message: str,
    delivered: bool = False,
) -> ElfMessage:
    """创建一条小精灵代转达消息记录。"""
    msg = ElfMessage(
        public_id=public_id,
        event_id=event_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        raw_message=raw_message,
        final_message=final_message,
        delivered=delivered,
    )
    db.add(msg)
    db.flush()
    return msg


def create_moderation_log(
    db: Session,
    *,
    user_id: int,
    raw_message: str,
    risk_level: str,
    blocked: bool,
    suggested_message: str | None = None,
) -> ModerationLog:
    """创建一条过激语言检测审计记录。"""
    log = ModerationLog(
        user_id=user_id,
        raw_message=raw_message,
        risk_level=ModerationRiskLevel(risk_level),
        blocked=blocked,
        suggested_message=suggested_message,
    )
    db.add(log)
    db.flush()
    return log
