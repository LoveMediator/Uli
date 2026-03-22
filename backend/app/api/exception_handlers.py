"""FastAPI 全局异常处理（任务 A2）。"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import AppError, http_status_for_code
from app.schemas.common import ApiEnvelope

logger = logging.getLogger(__name__)


def _envelope_json(code: int, message: str) -> dict[str, Any]:
    return ApiEnvelope(code=code, message=message, data=None).model_dump()


def _http_exception_to_code(status_code: int) -> int:
    from app.constants import error_codes as ec

    if status_code == 401:
        return ec.UNAUTHORIZED
    if status_code == 403:
        return ec.FORBIDDEN
    if status_code == 404:
        return ec.NOT_FOUND
    if status_code == 422:
        return ec.INVALID_PARAMS
    if status_code == 429:
        return ec.RATE_LIMITED
    return ec.INTERNAL_ERROR


def _detail_to_message(detail: Any) -> str:
    if detail is None:
        return "请求处理失败"
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list | dict):
        return str(detail)
    return str(detail)


def register_exception_handlers(app: Any) -> None:
    """注册统一 envelope 异常响应。"""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        status = http_status_for_code(exc.code)
        return JSONResponse(
            status_code=status,
            content=_envelope_json(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        from app.constants.error_codes import INVALID_PARAMS

        errors = exc.errors()
        if errors:
            first = errors[0]
            loc = " -> ".join(str(x) for x in first.get("loc", ()))
            msg = first.get("msg", "参数校验失败")
            message = f"{loc}: {msg}" if loc else msg
        else:
            message = "参数校验失败"
        return JSONResponse(
            status_code=422,
            content=_envelope_json(INVALID_PARAMS, message),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request, exc: HTTPException
    ) -> JSONResponse:
        code = _http_exception_to_code(exc.status_code)
        message = _detail_to_message(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope_json(code, message),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        from app.constants.error_codes import INTERNAL_ERROR

        logger.exception("未处理异常: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_envelope_json(INTERNAL_ERROR, "系统内部错误"),
        )
