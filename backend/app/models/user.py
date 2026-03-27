from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.constants.enums import UserStatus
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 公开ID（对外使用）
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # 用户名（唯一）
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    # 密码哈希
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # 账号状态
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus, name="user_status"), default=UserStatus.ACTIVE, nullable=False)
    # 连续失败登录次数
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 锁定截止时间
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 上次登录时间
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 关联用户ID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 刷新令牌哈希（唯一）
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    # 过期时间
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # 吊销时间
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuthLoginLog(Base):
    __tablename__ = "auth_login_logs"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 关联用户ID（可能为空）
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # 登录时输入的用户名
    username_input: Mapped[str] = mapped_column(String(32), nullable=False)
    # 是否成功
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # 错误码（可选）
    error_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # 登录IP
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    # User-Agent
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
