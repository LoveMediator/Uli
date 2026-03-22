"""A2：异常处理器返回统一 envelope 且错误码为整型。"""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.exception_handlers import register_exception_handlers
from app.constants.error_codes import FORBIDDEN, INTERNAL_ERROR, INVALID_PARAMS, NOT_FOUND
from app.core.errors import AppError, NotFoundError


def test_app_error_returns_envelope_and_http_status() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/t")
    def _route() -> None:
        raise AppError("复盘不存在", code=NOT_FOUND)

    client = TestClient(app)
    r = client.get("/t")
    assert r.status_code == 404
    assert r.json() == {"code": 1002, "message": "复盘不存在", "data": None}


def test_subclass_not_found_default_code() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/t")
    def _route() -> None:
        raise NotFoundError("关系不存在")

    client = TestClient(app)
    r = client.get("/t")
    assert r.json()["code"] == NOT_FOUND


def test_request_validation_maps_to_1001() -> None:
    class _Body(BaseModel):
        n: int

    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/p")
    def _route(_body: _Body) -> dict:
        return {}

    client = TestClient(app)
    r = client.post("/p", json={})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == INVALID_PARAMS
    assert body["data"] is None
    assert "message" in body


def test_http_exception_maps_to_business_code() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/u")
    def _route() -> None:
        raise HTTPException(status_code=401, detail="未登录")

    client = TestClient(app)
    r = client.get("/u")
    assert r.status_code == 401
    assert r.json()["code"] == 2001
    assert r.json()["message"] == "未登录"


def test_unhandled_exception_returns_5000() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def _route() -> None:
        raise RuntimeError("unexpected")

    # 默认 TestClient 会把未捕获异常再次抛出，需关闭以便断言 JSON 响应体
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 500
    assert r.json() == {
        "code": INTERNAL_ERROR,
        "message": "系统内部错误",
        "data": None,
    }


def test_main_app_registers_handlers() -> None:
    from app.main import create_app

    app = create_app()

    @app.get("/__a2_probe")
    def _probe() -> None:
        raise AppError("x", code=FORBIDDEN)

    client = TestClient(app)
    r = client.get("/__a2_probe")
    assert r.json()["code"] == FORBIDDEN
