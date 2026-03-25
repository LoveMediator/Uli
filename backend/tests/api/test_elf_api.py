"""Elf API 路由测试。"""

from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.constants.enums import UserStatus
from app.api.deps import get_current_active_user, get_db
from app.main import create_app
from app.schemas.elf import ElfRelayResponse, ModerateResponse


@pytest.fixture
def _app():
    app = create_app()
    mock_user = SimpleNamespace(
        id=1, public_id="u_test", username="test",
        status=UserStatus.ACTIVE, failed_login_count=0,
    )

    def _override_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    return app


@pytest.fixture
def client(_app):
    return TestClient(_app)


def test_relay_success(client):
    resp = ElfRelayResponse(
        message_id="em_1", delivered=True, final_message="已润色",
    )
    with patch("app.services.elf_service.relay_message", return_value=resp):
        r = client.post("/api/v1/elf/relay", json={
            "eventId": "ev_1",
            "targetUserId": "u_2",
            "rawMessage": "你好",
        })
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["messageId"] == "em_1"
    assert body["data"]["delivered"] is True


def test_moderate_success(client):
    resp = ModerateResponse(
        blocked=False, risk_level="low", suggested_message=None,
    )
    with patch("app.services.elf_service.moderate_message", return_value=resp):
        r = client.post("/api/v1/elf/moderate", json={
            "rawMessage": "正常的消息",
        })
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["blocked"] is False
    assert body["data"]["riskLevel"] == "low"
