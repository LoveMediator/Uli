from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class PrivateSession(Base):
    __tablename__ = "private_sessions"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 公开ID
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # 关联事件ID
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    # 用户ID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 是否活跃
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PrivateMessage(Base):
    __tablename__ = "private_messages"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 会话ID
    session_id: Mapped[int] = mapped_column(ForeignKey("private_sessions.id"), nullable=False)
    # 发送角色（user/assistant）
    sender_role: Mapped[str] = mapped_column(String(10), nullable=False)
    # 消息内容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # token 数量（可选）
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
