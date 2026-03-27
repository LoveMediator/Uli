from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.constants.enums import ModerationRiskLevel
from app.db.base import Base


class ElfMessage(Base):
    __tablename__ = "elf_messages"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 公开ID
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # 关联事件ID
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    # 发送方用户ID
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 接收方用户ID
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 原始消息
    raw_message: Mapped[str] = mapped_column(Text, nullable=False)
    # 润色后消息
    final_message: Mapped[str] = mapped_column(Text, nullable=False)
    # 是否送达
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 送达时间
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ModerationLog(Base):
    __tablename__ = "moderation_logs"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 用户ID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 原始消息
    raw_message: Mapped[str] = mapped_column(Text, nullable=False)
    # 风险等级
    risk_level: Mapped[ModerationRiskLevel] = mapped_column(SAEnum(ModerationRiskLevel, name="moderation_risk_level"), nullable=False)
    # 是否拦截
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 建议替换文本
    suggested_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
