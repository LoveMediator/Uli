"""Auth 模块 Pydantic schema。

约定：
- 本文件只定义 `data` 内层结构（不包含 code/message/data envelope）。
- 字段命名按 API camelCase（通过 Field(alias=...) + by_alias dump）。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.validators import reject_null_bytes


class RegisterRequest(BaseModel):
    """POST /api/v1/auth/register 请求体。"""

    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)

    _no_null = field_validator("username", "password", mode="before")(reject_null_bytes)


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login 请求体。"""

    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)

    _no_null = field_validator("username", "password", mode="before")(reject_null_bytes)


class RefreshRequest(BaseModel):
    """POST /api/v1/auth/refresh 请求体。"""

    model_config = ConfigDict(populate_by_name=True)

    refresh_token: str = Field(min_length=10, max_length=2048, alias="refreshToken")


class LogoutRequest(BaseModel):
    """POST /api/v1/auth/logout 请求体。"""

    model_config = ConfigDict(populate_by_name=True)

    refresh_token: str = Field(min_length=10, max_length=2048, alias="refreshToken")


class AuthTokensData(BaseModel):
    """登录成功 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken", description="JWT access token")
    refresh_token: str = Field(alias="refreshToken", description="refresh token（明文只返回一次）")
    token_type: str = Field(alias="tokenType", description="通常为 bearer")
    user_id: int = Field(alias="userId", description="用户内部主键 id")
    public_id: str = Field(alias="publicId", description="用户对外公开 id")


class RegisterData(BaseModel):
    """注册成功 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId", description="用户内部主键 id")
    public_id: str = Field(alias="publicId", description="用户对外公开 id")


class AccessTokenData(BaseModel):
    """刷新成功 / access-only 成功 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    token_type: str = Field(alias="tokenType")
    user_id: int = Field(alias="userId")


class LogoutData(BaseModel):
    """登出成功 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    revoked: bool = Field(description="是否成功吊销该 refresh token")

