from datetime import date
from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from app.services import calendar_service


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


def test_get_month_summary_success(monkeypatch):
    rel = SimpleNamespace(id=1, user_a_id=10, user_b_id=20)

    db = SimpleNamespace(execute=lambda *_: _ScalarResult(rel))
    monkeypatch.setattr(
        calendar_service.review_repo,
        "get_month_day_counts",
        lambda *_: [(date(2026, 2, 3), 1), (date(2026, 2, 9), 2)],
    )

    data = calendar_service.get_month_summary(
        db,
        user_id=10,
        relationship_id=1,
        year=2026,
        month=2,
    )
    assert data.month == "2026-02"
    assert len(data.days) == 2
    assert data.days[1].count == 2


def test_get_month_summary_forbidden():
    rel = SimpleNamespace(id=1, user_a_id=10, user_b_id=20)
    db = SimpleNamespace(execute=lambda *_: _ScalarResult(rel))

    with pytest.raises(AppError) as ex:
        calendar_service.get_month_summary(
            db,
            user_id=99,
            relationship_id=1,
            year=2026,
            month=2,
        )
    assert ex.value.code == "2002"


def test_get_day_reviews_maps_event_and_review(monkeypatch):
    rel = SimpleNamespace(id=1, user_a_id=10, user_b_id=20)
    db = SimpleNamespace(execute=lambda *_: _ScalarResult(rel))

    row = (
        SimpleNamespace(public_id="rv_1", updated_at=date(2026, 2, 9)),
        SimpleNamespace(public_id="ev_1", title="2月争吵"),
    )
    monkeypatch.setattr(calendar_service.review_repo, "get_review_items_by_date", lambda *_: [row])

    data = calendar_service.get_day_reviews(
        db,
        user_id=10,
        relationship_id=1,
        target_date=date(2026, 2, 9),
    )
    assert data.items[0].review_id == "rv_1"
    assert data.items[0].event_id == "ev_1"
