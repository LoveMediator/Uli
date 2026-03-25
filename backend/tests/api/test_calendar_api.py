"""Calendar API 路由测试。"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.constants.enums import UserStatus
from app.api.deps import get_current_active_user, get_db
from app.main import create_app
from app.schemas.calendar import CalendarDayCount, CalendarMonthData, CalendarDayReviewsData
from app.schemas.review import ReviewListItem


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


def test_get_month_calendar_success(client):
    rel = SimpleNamespace(id=10, public_id="r_1", user_a_id=1, user_b_id=2)
    data = CalendarMonthData(
        month="2026-03",
        days=[CalendarDayCount(date=date(2026, 3, 1), count=2)],
    )

    with patch("app.api.v1.calendar.get_relationship_by_public_id", return_value=rel):
        with patch("app.services.calendar_service.get_month_summary", return_value=data):
            r = client.get("/api/v1/calendar?month=2026-03&relationshipId=r_1")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["month"] == "2026-03"
    assert body["data"]["days"][0]["count"] == 2


def test_get_day_reviews_success(client):
    rel = SimpleNamespace(id=10, public_id="r_1", user_a_id=1, user_b_id=2)
    data = CalendarDayReviewsData(date=date(2026, 3, 1), items=[])

    with patch("app.api.v1.calendar.get_relationship_by_public_id", return_value=rel):
        with patch("app.services.calendar_service.get_day_reviews", return_value=data):
            r = client.get("/api/v1/calendar/days/2026-03-01/reviews?relationshipId=r_1")
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["items"] == []
