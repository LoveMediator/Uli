"""A1 验收：统一响应模型与 docs/openapi.yaml 对齐、序列化形态正确。"""

from __future__ import annotations

import typing

from fastapi.routing import APIRoute

from app.main import app
from app.schemas.common import (
    ApiEnvelope,
    ApiResponse,
    DEFAULT_OK_MESSAGE,
    OK_CODE,
    envelope_error,
    envelope_success,
)


def test_openapi_alignment_api_envelope_required_fields() -> None:
    """与 openapi `ApiEnvelope.required: [code, message, data]` 一致。"""
    schema = ApiEnvelope.model_json_schema()
    assert set(schema.get("required", [])) == {"code", "message", "data"}
    props = schema["properties"]
    assert props["code"]["type"] == "integer"
    assert props["message"]["type"] == "string"


def test_openapi_alignment_error_envelope_is_api_envelope_shape() -> None:
    """错误响应与 ErrorResponseEnvelope 相同外形（仍为 code/message/data）。"""
    err = envelope_error(code=2001, message="用户名或密码错误")
    dumped = err.model_dump()
    assert dumped == {"code": 2001, "message": "用户名或密码错误", "data": None}


def test_success_envelope_shape() -> None:
    ok = envelope_success({"userId": "u_1"})
    assert ok.code == OK_CODE
    assert ok.message == DEFAULT_OK_MESSAGE
    assert ok.model_dump() == {"code": 0, "message": "ok", "data": {"userId": "u_1"}}


def test_api_response_generic_requires_data_key_in_schema() -> None:
    """泛型 envelope 在 JSON Schema 中仍要求出现 data 键（可为 null）。"""
    schema = ApiResponse[dict].model_json_schema()
    assert "data" in schema.get("required", [])


def test_all_api_prefixed_routes_use_envelope_response_model() -> None:
    """验收：所有已实现且纳入 schema 的 /api 路由使用统一响应包装。

    当前 v1 子路由多为占位（无具体 endpoint）；一旦有路由，须声明
    `response_model` 为 ApiEnvelope / ApiResponse[...] / 或其子类。
    """
    def _is_envelope_model(model: type | None) -> bool:
        if model is None:
            return False
        origin = typing.get_origin(model)
        if origin is ApiResponse:
            return True
        cls = origin if origin is not None else model
        if cls in (ApiEnvelope, ApiResponse):
            return True
        try:
            return issubclass(cls, ApiEnvelope)
        except TypeError:
            return False

    violations: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith("/api"):
            continue
        if not route.include_in_schema:
            continue
        if route.response_model is None or not _is_envelope_model(route.response_model):
            methods = ",".join(sorted(route.methods))
            violations.append(f"{methods} {route.path}")

    assert not violations, (
        "以下 /api 路由未使用 ApiEnvelope / ApiResponse 作为 response_model：\n"
        + "\n".join(violations)
    )
