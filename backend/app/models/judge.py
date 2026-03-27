from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class JudgeResult(Base):
    __tablename__ = "judge_results"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 公开ID
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # 关联事件ID（唯一）
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), unique=True, nullable=False)
    # 客观事实摘要
    objective_summary: Mapped[str] = mapped_column(Text, nullable=False)
    # 触发点列表
    triggers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # 误解点列表
    misunderstandings: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # 给A的建议
    advice_for_a: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # 给B的建议
    advice_for_b: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # 模型名称
    model_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # 输入token数
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 输出token数
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
