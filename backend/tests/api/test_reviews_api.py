"""Reviews API 路由测试。"""

from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.constants.enums import UserStatus
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
        yield MagicMock()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    return app


@pytest.fixture
def client(_app):
    return TestClient(_app)


def test_get_review_success(client):
    review = SimpleNamespace(
        public_id="rv_1", event_id=100, content="复盘内容",
        source="judge_result",
        created_at=datetime(2026, 3, 25, tzinfo=UTC),
        updated_at=datetime(2026, 3, 25, tzinfo=UTC),
    )
    event = SimpleNamespace(public_id="ev_1")

    with patch("app.services.review_service.get_review", return_value=review):
        # Mock the inline Event query in the route handler
        with patch("app.api.v1.reviews.select") as mock_select:
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none.return_value = event
            # The db.execute().scalar_one_or_none() chain
            r = client.get("/api/v1/reviews/rv_1")

    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["reviewId"] == "rv_1"


def test_update_review_success(client):
    review = SimpleNamespace(
        public_id="rv_1",
        updated_at=datetime(2026, 3, 25, tzinfo=UTC),
    )
    with patch("app.services.review_service.update_review", return_value=review):
        r = client.put(
            "/api/v1/reviews/rv_1",
            json={"content": "新的复盘内容"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["reviewId"] == "rv_1"
