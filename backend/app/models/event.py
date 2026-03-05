from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.constants.enums import EventStatus
from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 公开ID
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # 关联关系ID
    relationship_id: Mapped[int] = mapped_column(ForeignKey("relationships.id"), nullable=False)
    # 发起方用户ID
    initiator_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 事件标题
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # 事件状态
    status: Mapped[EventStatus] = mapped_column(SAEnum(EventStatus, name="event_status"), default=EventStatus.DRAFT, nullable=False)
    # 裁判完成时间
    judged_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 复盘完成时间
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 关闭时间
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 创建时间
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # 更新时间
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
