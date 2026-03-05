from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.constants.enums import SnapshotSide
from app.db.base import Base


class EventSnapshot(Base):
    __tablename__ = "event_snapshots"
    __table_args__ = (
        UniqueConstraint("event_id", "side", name="ux_event_snapshots_event_side"),
    )

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 公开ID
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # 关联事件ID
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    # 快照侧（A / B）
    side: Mapped[SnapshotSide] = mapped_column(SAEnum(SnapshotSide, name="snapshot_side"), nullable=False)
    # 客观摘要
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    # A方观点要点
    points_a: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # B方观点要点
    points_b: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # 原始结构化内容（可选）
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # 是否冻结（不可改）
    is_frozen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # 确认人用户ID
    confirmed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 确认时间
    confirmed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # 创建时间
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # 更新时间
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

