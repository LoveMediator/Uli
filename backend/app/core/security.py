"""密码哈希与 JWT（任务 A3）。

行为约定（与 A4 登录/刷新/登出衔接）：
- **access token**：短期 JWT，`token_type=access`。过期、伪造、缺字段 → 解析时抛 `AuthError`（HTTP 401 / 业务码 2001）。
- **refresh token**：长期凭证由 `generate_refresh_token_pair` 生成随机串；**明文仅返回客户端一次**，
  库内存 `sha256` 摘要（见 `refresh_tokens.token_hash`）。吊销、轮换在 A4 写入 `revoked_at` 等字段完成；
  **登出后** access 在过期前仍可能有效（靠短有效期控制）；refresh 应以吊销为准。
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import AuthError

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    """bcrypt 哈希，适用于注册/改密入库。"""
    if len(plain_password.encode("utf-8")) > 72:
        plain_password = plain_password[:72]
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("ascii")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """校验明文与库中 bcrypt 哈希。"""
    try:
        if len(plain_password.encode("utf-8")) > 72:
            plain_password = plain_password[:72]
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("ascii"),
        )
    except ValueError:
        return False


def create_access_token(
    user_id: int,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """签发 access JWT（`sub` 为用户主键 id 字符串）。"""
    now = datetime.now(tz=UTC)
    ttl = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "token_type": TOKEN_TYPE_ACCESS,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token_jwt(
    user_id: int,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """签发 **无状态** refresh JWT（仅便于联调；生产可与 opaque + DB 方案二选一，由 A4 定稿）。"""
    now = datetime.now(tz=UTC)
    ttl = expires_delta or timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "token_type": TOKEN_TYPE_REFRESH,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> int:
    """解析 access JWT，返回用户主键 id。失败或类型不符抛 `AuthError`（业务码 2001）。"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "token_type"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthError("access token 已过期") from None
    except jwt.InvalidTokenError:
        raise AuthError("access token 无效") from None

    if payload.get("token_type") != TOKEN_TYPE_ACCESS:
        raise AuthError("令牌类型错误")

    try:
        return int(payload["sub"])
    except (TypeError, ValueError, KeyError):
        raise AuthError("access token 载荷无效") from None


def hash_refresh_token_secret(raw_token: str) -> str:
    """refresh 明文 → 入库用 sha256 十六进制摘要。"""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_refresh_token_pair() -> tuple[str, str]:
    """生成 opaque refresh：`(返回给客户端的明文, 写入 refresh_tokens.token_hash 的摘要)`。"""
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token_secret(raw)
