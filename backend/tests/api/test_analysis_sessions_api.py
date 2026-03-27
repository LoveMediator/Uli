from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db
from app.constants.enums import UserStatus
from app.main import create_app
from app.schemas.analysis_session import (
    AnalysisSessionCommitData,
    AnalysisSessionData,
    AnalysisSessionMessageData,
    AnalysisSessionMessagePayload,
)


@pytest.fixture
def _app():
    app = create_app()
    mock_user = SimpleNamespace(
        id=1,
        public_id="u_test",
        username="alice",
        status=UserStatus.ACTIVE,
        failed_login_count=0,
    )

    def _override_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    return app


@pytest.fixture
def client(_app):
    return TestClient(_app)


def test_start_a_analysis_session_success(client):
    data = AnalysisSessionData(
        sessionId="sess_a_1",
        phase="a",
        relationshipId="rel_1",
        expiresAt=datetime(2026, 3, 27, tzinfo=UTC),
        messages=[],
    )
    with patch("app.services.analysis_session_chat_service.start_a_analysis_session", return_value=data):
        response = client.post("/api/v1/relationships/rel_1/analysis-sessions/a")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["sessionId"] == "sess_a_1"
    assert body["data"]["phase"] == "a"


def test_start_b_analysis_session_success(client):
    data = AnalysisSessionData(
        sessionId="sess_b_1",
        phase="b",
        relationshipId="rel_1",
        eventId="ev_1",
        expiresAt=datetime(2026, 3, 27, tzinfo=UTC),
        messages=[
            AnalysisSessionMessagePayload(
                role="assistant",
                content="先说说你的视角。",
                createdAt=datetime(2026, 3, 27, tzinfo=UTC),
            )
        ],
    )
    with patch("app.services.analysis_session_chat_service.start_b_analysis_session", return_value=data):
        response = client.post("/api/v1/events/ev_1/analysis-sessions/b")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["eventId"] == "ev_1"
    assert body["data"]["messages"][0]["role"] == "assistant"


def test_send_analysis_message_success(client):
    data = AnalysisSessionMessageData(sessionId="sess_a_1", reply="我们先把事实分开。")
    with patch("app.services.analysis_session_chat_service.send_analysis_message", return_value=data):
        response = client.post(
            "/api/v1/analysis-sessions/sess_a_1/messages",
            json={"message": "我想先整理一下这次争执。"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["reply"] == "我们先把事实分开。"


def test_commit_analysis_session_success(client):
    data = AnalysisSessionCommitData(
        sessionId="sess_a_1",
        eventId="ev_1",
        status="waiting_b",
        snapshotAId="sa_1",
    )
    with patch("app.services.analysis_session_chat_service.commit_analysis_session", return_value=data):
        response = client.post("/api/v1/analysis-sessions/sess_a_1/commit")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["eventId"] == "ev_1"
    assert body["data"]["snapshotAId"] == "sa_1"


def test_send_analysis_image_message_success(client):
    data = AnalysisSessionMessageData(sessionId="sess_a_1", reply="[MOCK] image analyzed")
    with patch("app.services.analysis_session_chat_service.send_analysis_image_message", return_value=data):
        response = client.post(
            "/api/v1/analysis-sessions/sess_a_1/images",
            files={"image": ("test.png", b"fake-image-bytes", "image/png")},
            data={"message": "look at this"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["reply"] == "[MOCK] image analyzed"


def test_get_analysis_image_success(client):
    with patch(
        "app.services.analysis_session_chat_service.get_analysis_image",
        return_value=(b"png-bytes", "image/png", "shot.png"),
    ):
        response = client.get("/api/v1/analysis-sessions/sess_a_1/images/img_1")
    assert response.status_code == 200
    assert response.content == b"png-bytes"
    assert response.headers["content-type"] == "image/png"
