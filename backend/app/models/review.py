from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 公开ID
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # 关联事件ID（唯一）
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), unique=True, nullable=False)
    # 关联关系ID
    relationship_id: Mapped[int] = mapped_column(ForeignKey("relationships.id"), nullable=False)
    # 复盘正文
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 来源（如 judge_result）
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="judge_result")
    # 创建人用户ID
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # 更新人用户ID
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ReviewVersion(Base):
    __tablename__ = "review_versions"
    __table_args__ = (
        UniqueConstraint("review_id", "version_no", name="ux_review_versions_review_id_version_no"),
    )

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 关联复盘ID
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    # 版本号
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # 版本内容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 编辑人用户ID
    edited_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 编辑时间
    edited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CalendarEntry(Base):
    __tablename__ = "calendar_entries"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 关联复盘ID（唯一）
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), unique=True, nullable=False)
    # 关联事件ID（唯一）
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), unique=True, nullable=False)
    # 关联关系ID
    relationship_id: Mapped[int] = mapped_column(ForeignKey("relationships.id"), nullable=False)
    # 日历日期
    calendar_date: Mapped[date] = mapped_column(Date, nullable=False)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FollowupMessage(Base):
    __tablename__ = "followup_messages"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 关联事件ID
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    # 用户ID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 用户输入
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    # AI 回复
    assistant_reply: Mapped[str] = mapped_column(Text, nullable=False)
    # 上下文元信息
    context_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
