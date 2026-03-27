from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.constants.enums import EventStatus
from app.db.base import Base


class EventStateLog(Base):
    __tablename__ = "event_state_logs"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 关联事件ID
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    # 变更前状态
    from_status: Mapped[EventStatus] = mapped_column(SAEnum(EventStatus, name="event_status"), nullable=False)
    # 变更后状态
    to_status: Mapped[EventStatus] = mapped_column(SAEnum(EventStatus, name="event_status"), nullable=False)
    # 动作标识
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    # 操作人用户ID
    operator_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # 追踪ID
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AiCallLog(Base):
    __tablename__ = "ai_call_logs"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 关联事件ID（可空）
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    # 场景标识
    scene: Mapped[str] = mapped_column(String(40), nullable=False)
    # 模型名称
    model_name: Mapped[str] = mapped_column(String(60), nullable=False)
    # 输入token
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 输出token
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 是否成功
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # 错误码
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # 追踪ID
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
