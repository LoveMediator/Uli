from datetime import date
from types import SimpleNamespace

from app.constants.enums import EventStatus, RelationshipStatus, SnapshotSide
from app.services import calendar_service, relationship_service


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


def test_calendar_day_reviews_falls_back_to_review_content(monkeypatch):
    rel = SimpleNamespace(id=1, user_a_id=10, user_b_id=20)
    db = SimpleNamespace(execute=lambda *_: _ScalarResult(rel))
    row = (
        SimpleNamespace(
            public_id="rv_1",
            updated_at=date(2026, 4, 9),
            content="这次争执发生在吃饭时。对方用玩笑语气说了伤人的话。",
        ),
        SimpleNamespace(public_id="ev_1", title="?????????"),
    )

    monkeypatch.setattr(calendar_service.review_repo, "get_review_items_by_date", lambda *_: [row])

    data = calendar_service.get_day_reviews(
        db,
        user_id=10,
        relationship_id=1,
        target_date=date(2026, 4, 9),
    )

    assert data.items[0].title == "这次争执发生在吃饭时。"


def test_relationship_list_falls_back_to_snapshot_summary(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1", username="alice")
    relationship = SimpleNamespace(
        id=1,
        public_id="rel_1",
        user_a_id=1,
        user_b_id=2,
        status=RelationshipStatus.ACTIVE,
    )
    partner = SimpleNamespace(id=2, public_id="u_2", username="bob")
    open_event = SimpleNamespace(
        id=11,
        public_id="ev_1",
        status=EventStatus.WAITING_B,
        initiator_user_id=1,
        title=None,
    )

    monkeypatch.setattr(
        relationship_service.relationship_repo,
        "list_relationships_for_user",
        lambda *_a, **_kw: [relationship],
    )
    monkeypatch.setattr(
        relationship_service.event_repo,
        "get_open_event_for_relationship",
        lambda *_a, **_kw: open_event,
    )
    monkeypatch.setattr(relationship_service, "_get_user_or_fail", lambda _db, _user_id: partner)
    monkeypatch.setattr(
        relationship_service.snapshot_repo,
        "get_snapshot_by_event_and_side",
        lambda _db, _event_id, side: (
            SimpleNamespace(summary="吃饭时对方半开玩笑地说我是猪。")
            if side == SnapshotSide.A
            else None
        ),
    )

    data = relationship_service.list_relationships(SimpleNamespace(), current_user)

    assert data.items[0].current_event is not None
    assert data.items[0].current_event.title == "吃饭时对方半开玩笑地说我是猪。"
