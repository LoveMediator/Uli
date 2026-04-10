from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db
from app.constants.enums import UserStatus
from app.main import create_app
from app.schemas.relationship import (
    RelationshipAcceptData,
    RelationshipCancelData,
    RelationshipCancelRequestData,
    RelationshipCurrentEvent,
    RelationshipDeleteCounts,
    RelationshipInviteData,
    RelationshipListData,
    RelationshipSummary,
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


def test_create_relationship_invite_success(client):
    data = RelationshipInviteData(
        inviteToken="invite-token",
        inviteUrl="/relationship-invite?token=invite-token",
        expiresAt=datetime(2026, 3, 27, tzinfo=UTC),
    )
    with patch("app.services.relationship_service.create_relationship_invite", return_value=data):
        r = client.post("/api/v1/relationships/invite")
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["inviteToken"] == "invite-token"


def test_accept_relationship_invite_success(client):
    data = RelationshipAcceptData(
        relationshipId="rel_1",
        partnerUserId="u_partner",
        partnerUsername="bob",
        status="active",
    )
    with patch("app.services.relationship_service.accept_relationship_invite", return_value=data):
        r = client.post(
            "/api/v1/relationships/accept",
            json={"inviteToken": "invite-token-xxxxxxxxxxxx"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["relationshipId"] == "rel_1"
    assert body["data"]["partnerUsername"] == "bob"


def test_list_relationships_success(client):
    data = RelationshipListData(
        items=[
            RelationshipSummary(
                relationshipId="rel_1",
                partnerUserId="u_partner",
                partnerUsername="bob",
                status="active",
                currentEvent=RelationshipCurrentEvent(
                    eventId="ev_1",
                    status="waiting_b",
                    pendingAction="respond",
                    title="一次争执",
                ),
            )
        ]
    )
    with patch("app.services.relationship_service.list_relationships", return_value=data):
        r = client.get("/api/v1/relationships")
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["items"][0]["relationshipId"] == "rel_1"
    assert body["data"]["items"][0]["currentEvent"]["eventId"] == "ev_1"


def test_create_relationship_cancel_request_success(client):
    data = RelationshipCancelRequestData(
        cancelToken="cancel-token",
        cancelUrl="/relationship-cancel?relationshipId=rel_1&token=cancel-token",
        expiresAt=datetime(2026, 3, 27, tzinfo=UTC),
    )
    with patch("app.services.relationship_service.create_relationship_cancel_request", return_value=data):
        r = client.post("/api/v1/relationships/rel_1/cancel-request")
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["cancelToken"] == "cancel-token"


def test_confirm_relationship_cancel_success(client):
    data = RelationshipCancelData(
        relationshipId="rel_1",
        deletedCounts=RelationshipDeleteCounts(
            privateMessages=0,
            privateSessions=0,
            followupMessages=0,
            eventStateLogs=0,
            aiCallLogs=0,
            elfMessages=0,
            judgeResults=0,
            eventSnapshots=0,
            calendarEntries=0,
            reviewVersions=0,
            reviews=0,
            events=0,
            relationships=1,
        ),
        deletedAt=datetime(2026, 3, 27, tzinfo=UTC),
    )
    with patch("app.services.relationship_service.confirm_relationship_cancel", return_value=data):
        r = client.post(
            "/api/v1/relationships/rel_1/cancel-confirm",
            json={"cancelToken": "cancel-token-xxxxxxxxxxxx"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["relationshipId"] == "rel_1"
    assert body["data"]["deletedCounts"]["relationships"] == 1
