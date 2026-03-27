"""Events API 路由测试。"""

from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.constants.enums import EventStatus, UserStatus
from app.api.deps import get_current_active_user, get_db
from app.main import create_app


@pytest.fixture
def _app():
    app = create_app()

    mock_user = SimpleNamespace(
        id=1, public_id="u_test", username="test",
        status=UserStatus.ACTIVE, failed_login_count=0,
    )

    def _override_db():
        from unittest.mock import MagicMock
        yield MagicMock()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    return app


@pytest.fixture
def client(_app):
    return TestClient(_app)


def test_create_event_success(client):
    event = SimpleNamespace(public_id="ev_1", status=EventStatus.DRAFT)
    with patch("app.services.event_service.create_event", return_value=event):
        r = client.post("/api/v1/events", json={"title": "test", "relationshipId": "r_1"})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["eventId"] == "ev_1"
    assert body["data"]["status"] == "draft"


def test_commit_a_success(client):
    event = SimpleNamespace(public_id="ev_1", status=EventStatus.WAITING_B)
    snapshot = SimpleNamespace(public_id="sa_1")
    with patch("app.services.event_service.commit_a", return_value=(event, snapshot)):
        r = client.post(
            "/api/v1/events/ev_1/commit-a",
            json={"confirmText": "确认"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["snapshotAId"] == "sa_1"
    assert body["data"]["status"] == "waiting_b"


def test_invite_no_auth_needed():
    app = create_app()

    def _override_db():
        from unittest.mock import MagicMock
        yield MagicMock()

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)

    event = SimpleNamespace(
        public_id="ev_1", status=EventStatus.WAITING_B, title="test",
    )
    with patch("app.services.event_service.get_invite", return_value=event):
        r = client.get("/api/v1/events/ev_1/invite")
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["requiresAuth"] is True
    assert body["data"]["title"] == "test"


def test_b_agree_success(client):
    event = SimpleNamespace(public_id="ev_1", status=EventStatus.JUDGED)
    judge = SimpleNamespace(public_id="jr_1")
    with patch("app.services.event_service.b_agree", return_value=(event, judge)):
        r = client.post(
            "/api/v1/events/ev_1/b-agree",
            json={"agree": True},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["judgeResultId"] == "jr_1"
    assert body["data"]["status"] == "judged"


def test_judge_result_success(client):
    event = SimpleNamespace(public_id="ev_1", status=EventStatus.JUDGED)
    judge = SimpleNamespace(
        public_id="jr_1",
        objective_summary="summary",
        triggers=["t1"],
        misunderstandings=["m1"],
        advice_for_a=["a1"],
        advice_for_b=["b1"],
        created_at=datetime(2026, 3, 25, tzinfo=UTC),
    )
    with patch("app.services.event_service.get_judge_result", return_value=(event, judge)):
        r = client.get("/api/v1/events/ev_1/judge-result")
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["objectiveSummary"] == "summary"
    assert body["data"]["analysis"]["triggers"] == ["t1"]


def test_followup_chat_success(client):
    resp = SimpleNamespace(
        reply="mock reply",
        context_meta=SimpleNamespace(
            recent_messages=2, snapshots=1, judge_results=1,
        ),
    )
    # followup_service.followup_chat returns a FollowupResponse Pydantic model
    # We need to mock it to return something with model_dump
    from app.schemas.followup import FollowupContextMeta, FollowupResponse
    mock_resp = FollowupResponse(
        reply="mock reply",
        contextMeta=FollowupContextMeta(
            recentMessages=2, snapshots=1, judgeResults=1,
        ),
    )
    with patch("app.services.followup_service.followup_chat", return_value=mock_resp):
        r = client.post(
            "/api/v1/events/ev_1/followup-chat/messages",
            json={"message": "hello"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["reply"] == "mock reply"
    assert body["data"]["contextMeta"]["snapshots"] == 1
