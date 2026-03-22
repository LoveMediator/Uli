"""应用业务异常与错误码映射（任务 A2）。

错误码口径：`docs/API_LoveMediator_v1.md` §2.4。
HTTP 状态码：在 `http_status_for_code` 中按语义映射，响应体仍为统一 envelope。
"""

from __future__ import annotations

from typing import ClassVar

from app.constants import error_codes as ec


def http_status_for_code(code: int) -> int:
    """业务错误码 → HTTP 状态码（响应 body 始终含 code/message/data）。"""
    return _HTTP_STATUS_BY_CODE.get(code, 500)


_HTTP_STATUS_BY_CODE: dict[int, int] = {
    ec.INVALID_PARAMS: 422,
    ec.NOT_FOUND: 404,
    ec.INVALID_STATE: 409,
    ec.UNAUTHORIZED: 401,
    ec.FORBIDDEN: 403,
    ec.ACCOUNT_LOCKED: 403,
    ec.RATE_LIMITED: 429,
    ec.USERNAME_EXISTS: 409,
    ec.SNAPSHOT_FROZEN: 409,
    ec.PREREQ_NOT_MET: 409,
    ec.INTERNAL_ERROR: 500,
}


class AppError(Exception):
    """可预期的业务异常；由全局处理器转换为 JSON envelope，不当作未处理 500。"""

    default_code: ClassVar[int] = ec.INTERNAL_ERROR

    def __init__(self, message: str, *, code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = self.default_code if code is None else code


class InvalidParamsError(AppError):
    """参数校验失败 — 1001"""

    default_code: ClassVar[int] = ec.INVALID_PARAMS


class NotFoundError(AppError):
    """资源不存在 — 1002"""

    default_code: ClassVar[int] = ec.NOT_FOUND


class StateNotAllowedError(AppError):
    """状态不允许该操作 — 1003"""

    default_code: ClassVar[int] = ec.INVALID_STATE


class AuthError(AppError):
    """认证失败（未登录 / 凭证无效）— 2001"""

    default_code: ClassVar[int] = ec.UNAUTHORIZED


class ForbiddenError(AppError):
    """无权限访问资源 — 2002"""

    default_code: ClassVar[int] = ec.FORBIDDEN


class AccountLockedOrDisabledError(AppError):
    """账号锁定或禁用 — 2003"""

    default_code: ClassVar[int] = ec.ACCOUNT_LOCKED


class RateLimitedError(AppError):
    """请求过频 — 2004"""

    default_code: ClassVar[int] = ec.RATE_LIMITED


class UsernameExistsError(AppError):
    """用户名已存在 — 3001"""

    default_code: ClassVar[int] = ec.USERNAME_EXISTS


class SnapshotFrozenError(AppError):
    """快照已冻结不可修改 — 3002"""

    default_code: ClassVar[int] = ec.SNAPSHOT_FROZEN


class PrerequisiteNotMetError(AppError):
    """事件尚未满足分析 / 复盘等前置条件 — 3003"""

    default_code: ClassVar[int] = ec.PREREQ_NOT_MET


class InternalError(AppError):
    """系统内部错误 — 5000"""

    default_code: ClassVar[int] = ec.INTERNAL_ERROR
