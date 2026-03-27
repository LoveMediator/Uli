from datetime import datetime
from types import SimpleNamespace

from app.constants.enums import EventStatus, RelationshipStatus
from app.services import relationship_service


def test_create_relationship_invite_success():
    user = SimpleNamespace(id=1, public_id="u_1", username="alice")
    data = relationship_service.create_relationship_invite(user)
    assert data.invite_token
    assert data.invite_url.startswith("/relationship-invite?token=")
    assert isinstance(data.expires_at, datetime)


def test_accept_relationship_invite_creates_relationship(monkeypatch):
    inviter = SimpleNamespace(id=1, public_id="u_1", username="alice")
    current_user = SimpleNamespace(id=2, public_id="u_2", username="bob")
    created = SimpleNamespace(public_id="rel_1", status=RelationshipStatus.ACTIVE)
    calls = {"committed": 0, "refreshed": 0}

    class _DB:
        def commit(self):
            calls["committed"] += 1

        def refresh(self, _obj):
            calls["refreshed"] += 1

    monkeypatch.setattr(relationship_service, "_decode_invite_token", lambda _token: 1)
    monkeypatch.setattr(relationship_service, "_get_user_or_fail", lambda _db, _user_id: inviter)
    monkeypatch.setattr(
        relationship_service.relationship_repo,
        "get_active_relationship_between_users",
        lambda *_a, **_kw: None,
    )
    monkeypatch.setattr(
        relationship_service.relationship_repo,
        "create_relationship",
        lambda *_a, **_kw: created,
    )

    data = relationship_service.accept_relationship_invite(_DB(), current_user, "invite-token")
    assert calls["committed"] == 1
    assert data.relationship_id == "rel_1"
    assert data.partner_username == "alice"


def test_accept_relationship_invite_reuses_existing_relationship(monkeypatch):
    inviter = SimpleNamespace(id=1, public_id="u_1", username="alice")
    current_user = SimpleNamespace(id=2, public_id="u_2", username="bob")
    existing = SimpleNamespace(public_id="rel_1", status=RelationshipStatus.ACTIVE)

    class _DB:
        def commit(self):
            raise AssertionError("should not commit when relationship already exists")

        def refresh(self, _obj):
            raise AssertionError("should not refresh when relationship already exists")

    monkeypatch.setattr(relationship_service, "_decode_invite_token", lambda _token: 1)
    monkeypatch.setattr(relationship_service, "_get_user_or_fail", lambda _db, _user_id: inviter)
    monkeypatch.setattr(
        relationship_service.relationship_repo,
        "get_active_relationship_between_users",
        lambda *_a, **_kw: existing,
    )

    data = relationship_service.accept_relationship_invite(_DB(), current_user, "invite-token")
    assert data.relationship_id == "rel_1"
    assert data.partner_user_id == "u_1"


def test_list_relationships_success(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1", username="alice")
    relationship = SimpleNamespace(
        public_id="rel_1",
        user_a_id=1,
        user_b_id=2,
        status=RelationshipStatus.ACTIVE,
    )
    partner = SimpleNamespace(id=2, public_id="u_2", username="bob")

    monkeypatch.setattr(
        relationship_service.relationship_repo,
        "list_relationships_for_user",
        lambda *_a, **_kw: [relationship],
    )
    monkeypatch.setattr(
        relationship_service.event_repo,
        "get_open_event_for_relationship",
        lambda *_a, **_kw: SimpleNamespace(
            public_id="ev_1",
            status=EventStatus.WAITING_B,
            initiator_user_id=2,
            title="一次争执",
        ),
    )
    monkeypatch.setattr(relationship_service, "_get_user_or_fail", lambda _db, _user_id: partner)

    data = relationship_service.list_relationships(SimpleNamespace(), current_user)
    assert data.items[0].relationship_id == "rel_1"
    assert data.items[0].partner_username == "bob"
    assert data.items[0].current_event.event_id == "ev_1"


def test_create_relationship_cancel_request_success(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1", username="alice")
    relationship = SimpleNamespace(
        id=10,
        public_id="rel_1",
        user_a_id=1,
        user_b_id=2,
        status=RelationshipStatus.ACTIVE,
    )

    monkeypatch.setattr(
        relationship_service.relationship_repo,
        "get_relationship_by_public_id",
        lambda *_a, **_kw: relationship,
    )

    data = relationship_service.create_relationship_cancel_request(SimpleNamespace(), current_user, "rel_1")
    assert data.cancel_token
    assert "relationshipId=rel_1" in data.cancel_url


def test_confirm_relationship_cancel_success(monkeypatch):
    current_user = SimpleNamespace(id=2, public_id="u_2", username="bob")
    relationship = SimpleNamespace(
        id=10,
        public_id="rel_1",
        user_a_id=1,
        user_b_id=2,
        status=RelationshipStatus.ACTIVE,
    )
    calls = {"committed": 0}

    class _DB:
        def commit(self):
            calls["committed"] += 1

    monkeypatch.setattr(
        relationship_service,
        "_decode_cancel_token",
        lambda _token: ("rel_1", 1),
    )
    monkeypatch.setattr(
        relationship_service.relationship_repo,
        "get_relationship_by_public_id",
        lambda *_a, **_kw: relationship,
    )
    monkeypatch.setattr(
        relationship_service.relationship_repo,
        "delete_relationship_graph",
        lambda *_a, **_kw: {
            "privateMessages": 0,
            "privateSessions": 0,
            "followupMessages": 1,
            "eventStateLogs": 2,
            "aiCallLogs": 3,
            "elfMessages": 0,
            "judgeResults": 1,
            "eventSnapshots": 2,
            "calendarEntries": 1,
            "reviewVersions": 1,
            "reviews": 1,
            "events": 1,
            "relationships": 1,
        },
    )
    monkeypatch.setattr(
        relationship_service,
        "get_analysis_session_store",
        lambda: SimpleNamespace(clear_sessions_for_relationship=lambda _relationship_id: None),
    )

    data = relationship_service.confirm_relationship_cancel(_DB(), current_user, "rel_1", "cancel-token")
    assert calls["committed"] == 1
    assert data.relationship_id == "rel_1"
    assert data.deleted_counts.relationships == 1
