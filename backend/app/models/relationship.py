from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.constants.enums import RelationshipStatus
from app.db.base import Base


class Relationship(Base):
    __tablename__ = "relationships"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 公开ID
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # 用户A
    user_a_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 用户B
    user_b_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 关系状态
    status: Mapped[RelationshipStatus] = mapped_column(SAEnum(RelationshipStatus, name="relationship_status"), default=RelationshipStatus.ACTIVE, nullable=False)
    # 创建时间
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # 更新时间
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
