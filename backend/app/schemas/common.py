"""统一 API 响应 envelope（任务 A1）。

与 `docs/openapi.yaml` 中 `ApiEnvelope`、`ErrorResponseEnvelope` 对齐。
各业务模块只定义 `data` 内层结构，外层一律通过本模块包装。
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

OK_CODE = 0
DEFAULT_OK_MESSAGE = "ok"


class ApiEnvelope(BaseModel):
    """所有 JSON 响应的公共外形：{ code, message, data }。"""

    model_config = ConfigDict(
        json_schema_extra={"example": {"code": 0, "message": "ok", "data": {}}}
    )

    code: int = Field(..., description="0 表示成功；非 0 为业务错误码")
    message: str
    # 与 openapi ApiEnvelope.required 一致：键必须出现，值可为 null
    data: Any | None = Field(..., description="业务载荷；错误时一般为 null")


class ApiResponse(BaseModel, Generic[T]):
    """带类型参数的 envelope，供 FastAPI `response_model` 与 OpenAPI 生成使用。"""

    code: int = OK_CODE
    message: str = DEFAULT_OK_MESSAGE
    data: T | None = Field(..., description="与 ApiEnvelope.data 相同：必填键，可为 null")


class ErrorResponseEnvelope(ApiEnvelope):
    """错误响应（与 OpenAPI `ErrorResponseEnvelope` 一致：code != 0，data 为 null）。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 2001,
                "message": "用户名或密码错误",
                "data": None,
            }
        }
    )


def envelope_success(data: Any = None, *, message: str = DEFAULT_OK_MESSAGE) -> ApiEnvelope:
    """构造成功响应（code=0）。"""
    return ApiEnvelope(code=OK_CODE, message=message, data=data)


def envelope_error(*, code: int, message: str) -> ApiEnvelope:
    """构造错误响应（data 固定为 null）。"""
    return ApiEnvelope(code=code, message=message, data=None)
