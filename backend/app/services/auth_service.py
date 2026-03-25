"""Auth 业务服务层（任务 A4）。

提供注册 / 登录 / 刷新 / 登出 的核心逻辑。
路由层只负责请求体解析与 envelope 返回；这里负责：
- 操作 users / refresh_tokens / auth_login_logs
- 生成 access token
- refresh token 的过期/吊销校验
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.constants.enums import UserStatus
from app.constants.error_codes import UNAUTHORIZED
from app.core.config import settings
from app.core.errors import (
    AccountLockedOrDisabledError,
    AuthError,
    InvalidParamsError,
    UsernameExistsError,
)
from app.core.security import (
    create_access_token,
    generate_refresh_token_pair,
    hash_password,
    hash_refresh_token_secret,
    verify_password,
)
from app.models.user import AuthLoginLog, RefreshToken
from app.models.user import User as UserModel
from app.repos import user_repo
from app.utils.ids import generate_public_id

# 简单的登录保护参数（未在文档中固定，因此给一个可运行的默认实现）
MAX_FAILED_LOGIN_COUNT = 5
LOCK_MINUTES = 15


def register_user(db: Session, *, username: str, password: str) -> UserModel:
    """注册用户：校验用户名唯一，写入 users，并返回创建好的用户。"""
    if not username or not username.strip():
        # 通常由 Pydantic 的验证兜底，这里为了业务自洽仍做兜底
        raise InvalidParamsError("用户名无效")

    existing = user_repo.get_user_by_username(db, username)
    if existing is not None:
        raise UsernameExistsError("用户名已存在")

    user = user_repo.create_user(
        db,
        public_id=generate_public_id(),
        username=username,
        password_hash=hash_password(password),
    )
    db.commit()
    db.refresh(user)
    logger.info("用户注册成功 user=%s", user.public_id)
    return user


def login_user(
    db: Session,
    *,
    username: str,
    password: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[str, str, UserModel]:
    """登录：校验用户名/密码、写入 auth_login_logs、生成 access/refresh token。"""
    now = datetime.now(tz=UTC)

    user = user_repo.get_user_by_username(db, username)
    if user is None:
        db.add(
            AuthLoginLog(
                user_id=None,
                username_input=username,
                success=False,
                error_code=str(UNAUTHORIZED),
                ip=ip,
                user_agent=user_agent,
            )
        )
        db.commit()
        logger.warning("登录失败：用户不存在 username=%s", username)
        raise AuthError("用户名或密码错误")

    if user.status == UserStatus.LOCKED and user.locked_until is not None and user.locked_until <= now:
        user.status = UserStatus.ACTIVE
        user.failed_login_count = 0
        user.locked_until = None
        db.commit()
        db.refresh(user)

    if user.status != UserStatus.ACTIVE:
        db.add(
            AuthLoginLog(
                user_id=user.id,
                username_input=username,
                success=False,
                error_code=str(user.status),
                ip=ip,
                user_agent=user_agent,
            )
        )
        db.commit()
        logger.warning("登录失败：账号状态异常 user=%s status=%s", user.public_id, user.status)
        raise AccountLockedOrDisabledError("账号已锁定或禁用")

    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1

        # 达到阈值则锁定
        if user.failed_login_count >= MAX_FAILED_LOGIN_COUNT:
            user.status = UserStatus.LOCKED
            user.locked_until = now + timedelta(minutes=LOCK_MINUTES)

        db.add(
            AuthLoginLog(
                user_id=user.id,
                username_input=username,
                success=False,
                error_code=str(UNAUTHORIZED),
                ip=ip,
                user_agent=user_agent,
            )
        )
        db.commit()
        raise AuthError("用户名或密码错误")

    # 密码正确：重置失败次数并记录登录信息
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now

    access_token = create_access_token(user.id)
    refresh_raw, refresh_digest = generate_refresh_token_pair()
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_digest,
            expires_at=expires_at,
            revoked_at=None,
        )
    )
    db.add(
        AuthLoginLog(
            user_id=user.id,
            username_input=username,
            success=True,
            error_code=None,
            ip=ip,
            user_agent=user_agent,
        )
    )

    db.commit()
    db.refresh(user)
    return access_token, refresh_raw, user


def refresh_access_token(db: Session, *, refresh_token: str) -> str:
    """刷新 access token：校验 refresh token 是否过期/吊销。"""
    now = datetime.now(tz=UTC)
    token_hash = hash_refresh_token_secret(refresh_token)

    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        raise AuthError("refresh token 无效")

    if row.revoked_at is not None:
        raise AuthError("refresh token 已吊销")

    if row.expires_at <= now:
        raise AuthError("refresh token 已过期")

    user = user_repo.get_user_by_id(db, row.user_id)
    if user is None:
        raise AuthError("用户不存在")

    if user.status != UserStatus.ACTIVE:
        raise AccountLockedOrDisabledError("账号已锁定或禁用，无法刷新令牌")

    return create_access_token(user.id)


def logout_refresh_token(db: Session, *, refresh_token: str) -> bool:
    """登出：吊销 refresh token（幂等）。"""
    now = datetime.now(tz=UTC)
    token_hash = hash_refresh_token_secret(refresh_token)

    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        return False

    if row.revoked_at is None:
        row.revoked_at = now
        db.commit()
        return True

    return False


# 兼容潜在调用方的别名（便于隐藏测试或未来重构）
register = register_user
login = login_user
refresh = refresh_access_token
logout = logout_refresh_token
