from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.constants.enums import EventStatus, SnapshotSide
from app.core.errors import AppError
from app.services import analysis_session_chat_service as analysis_session_service


class _Store:
    def __init__(self):
        self.sessions: dict[str, dict] = {}
        self.scoped: dict[tuple[str, str, int], dict] = {}

    def save_session(self, session: dict) -> None:
        stored = dict(session)
        self.sessions[session["sessionId"]] = stored
        scope_id = session.get("eventId") or session.get("relationshipId")
        if scope_id:
            self.scoped[(session["phase"], scope_id, int(session["userId"]))] = stored

    def get_session(self, session_id: str) -> dict | None:
        session = self.sessions.get(session_id)
        return None if session is None else dict(session)

    def get_scoped_session(self, scope: str, scope_id: str, user_id: int) -> dict | None:
        session = self.scoped.get((scope, scope_id, user_id))
        return None if session is None else dict(session)

    def clear_sessions_for_relationship(self, relationship_public_id: str) -> None:
        self.sessions = {
            session_id: session
            for session_id, session in self.sessions.items()
            if session.get("relationshipId") != relationship_public_id
        }


def test_start_a_analysis_session_rejects_open_event(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1")
    relationship = SimpleNamespace(public_id="rel_1", id=10, user_a_id=1, user_b_id=2)

    monkeypatch.setattr(analysis_session_service, "_get_store", lambda: _Store())
    monkeypatch.setattr(
        analysis_session_service,
        "get_relationship_by_public_id",
        lambda *_a, **_kw: relationship,
    )
    monkeypatch.setattr(
        analysis_session_service.event_repo,
        "get_open_event_for_relationship",
        lambda *_a, **_kw: SimpleNamespace(public_id="ev_open"),
    )

    with pytest.raises(AppError) as ex:
        analysis_session_service.start_a_analysis_session(SimpleNamespace(), current_user, "rel_1")
    assert ex.value.code == 1003


def test_send_analysis_message_appends_reply_and_commit_flag(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1")
    store = _Store()
    store.save_session(
        {
            "sessionId": "sess_1",
            "phase": "a",
            "status": "active",
            "userId": 1,
            "relationshipId": "rel_1",
            "eventId": None,
            "canCommit": False,
            "factSummary": None,
            "messages": [],
            "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            "expiresAt": datetime(2026, 3, 28, tzinfo=UTC).isoformat(),
            "updatedAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
        }
    )
    calls = {"committed": 0}

    class _DB:
        def commit(self):
            calls["committed"] += 1

    monkeypatch.setattr(analysis_session_service, "_get_store", lambda: store)
    monkeypatch.setattr(
        analysis_session_service.private_chat_ai_service,
        "call_private_chat_llm",
        lambda **_kw: {
            "model_name": "mock-private-chat-v1",
            "input_tokens": 0,
            "output_tokens": 0,
            "content": "I can now summarize the facts for your confirmation.",
            "can_confirm": True,
            "fact_summary": "You argued about chores after both of you felt overburdened.",
        },
    )
    monkeypatch.setattr(
        analysis_session_service.audit_repo,
        "create_ai_call_log",
        lambda *_a, **_kw: SimpleNamespace(),
    )

    data = analysis_session_service.send_analysis_message(
        _DB(),
        current_user,
        "sess_1",
        "Please help me sort out what happened.",
    )
    assert data.reply == "I can now summarize the facts for your confirmation."
    assert data.can_commit is True
    assert data.fact_summary == "You argued about chores after both of you felt overburdened."
    saved = store.get_session("sess_1")
    assert len(saved["messages"]) == 2
    assert saved["canCommit"] is True
    assert saved["factSummary"] == "You argued about chores after both of you felt overburdened."
    assert calls["committed"] == 1


def test_send_analysis_image_message_appends_image(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1")
    store = _Store()
    store.save_session(
        {
            "sessionId": "sess_img",
            "phase": "a",
            "status": "active",
            "userId": 1,
            "relationshipId": "rel_1",
            "eventId": None,
            "canCommit": False,
            "factSummary": None,
            "messages": [],
            "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            "expiresAt": datetime(2026, 3, 28, tzinfo=UTC).isoformat(),
            "updatedAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
        }
    )
    calls: dict[str, object] = {"committed": 0, "messages": None}

    class _DB:
        def commit(self):
            calls["committed"] = 1

    def _mock_llm(**kwargs):
        calls["messages"] = kwargs["messages"]
        return {
            "model_name": "mock-private-chat-v1",
            "input_tokens": 0,
            "output_tokens": 0,
            "content": "I still need one more detail.",
            "can_confirm": False,
            "fact_summary": None,
        }

    monkeypatch.setattr(analysis_session_service, "_get_store", lambda: store)
    monkeypatch.setattr(
        analysis_session_service.private_chat_ai_service,
        "call_private_chat_llm",
        _mock_llm,
    )
    monkeypatch.setattr(
        analysis_session_service.audit_repo,
        "create_ai_call_log",
        lambda *_a, **_kw: SimpleNamespace(),
    )

    data = analysis_session_service.send_analysis_image_message(
        _DB(),
        current_user,
        "sess_img",
        filename="shot.png",
        mime_type="image/png",
        image_bytes=b"png-bytes",
        message="look at this",
    )
    assert data.reply == "I still need one more detail."
    assert data.can_commit is False
    saved = store.get_session("sess_img")
    assert saved["messages"][0]["images"][0]["mimeType"] == "image/png"
    assert calls["committed"] == 1
    llm_messages = calls["messages"]
    assert isinstance(llm_messages, list)
    user_message = llm_messages[-1]
    assert isinstance(user_message["content"], list)
    assert user_message["content"][1]["type"] == "image_url"


def test_build_private_messages_prioritizes_latest_concrete_turn():
    session = {
        "phase": "b",
        "messages": [
            {
                "role": "user",
                "content": "??????",
                "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            },
            {
                "role": "assistant",
                "content": "Take a breath first.",
                "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            },
            {
                "role": "user",
                "content": "我的男朋友说我是猪",
                "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            },
        ],
    }

    messages = analysis_session_service._build_private_messages(session)
    assert len(messages) == 2
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "我的男朋友说我是猪"
    assert "Do not switch into breathing" in messages[0]["content"]
    assert "latest_message_is_concrete=true" in messages[0]["content"]


def test_get_analysis_image_success(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1")
    store = _Store()
    image_bytes = b"png-bytes"
    data_url = "data:image/png;base64," + "cG5nLWJ5dGVz"
    store.save_session(
        {
            "sessionId": "sess_img",
            "phase": "a",
            "status": "committed",
            "userId": 1,
            "relationshipId": "rel_1",
            "eventId": None,
            "messages": [
                {
                    "role": "user",
                    "content": "",
                    "images": [
                        {
                            "imageId": "img_1",
                            "mimeType": "image/png",
                            "filename": "shot.png",
                            "dataUrl": data_url,
                        }
                    ],
                    "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
                }
            ],
            "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            "expiresAt": datetime(2026, 3, 28, tzinfo=UTC).isoformat(),
            "updatedAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
        }
    )
    monkeypatch.setattr(analysis_session_service, "_get_store", lambda: store)

    got_bytes, mime_type, filename = analysis_session_service.get_analysis_image(
        "sess_img",
        current_user,
        "img_1",
    )
    assert got_bytes == image_bytes
    assert mime_type == "image/png"
    assert filename == "shot.png"


def test_commit_analysis_session_requires_fact_summary(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1")
    store = _Store()
    store.save_session(
        {
            "sessionId": "sess_a",
            "phase": "a",
            "status": "active",
            "userId": 1,
            "relationshipId": "rel_1",
            "eventId": None,
            "canCommit": False,
            "factSummary": None,
            "messages": [
                {
                    "role": "user",
                    "content": "We argued about chores.",
                    "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
                }
            ],
            "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            "expiresAt": datetime(2026, 3, 28, tzinfo=UTC).isoformat(),
            "updatedAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
        }
    )
    monkeypatch.setattr(analysis_session_service, "_get_store", lambda: store)

    with pytest.raises(AppError) as ex:
        analysis_session_service.commit_analysis_session(SimpleNamespace(), current_user, "sess_a")
    assert ex.value.code == 1003


def test_commit_a_analysis_session_creates_event_and_snapshot(monkeypatch):
    current_user = SimpleNamespace(id=1, public_id="u_1")
    relationship = SimpleNamespace(public_id="rel_1", id=10, user_a_id=1, user_b_id=2)
    store = _Store()
    store.save_session(
        {
            "sessionId": "sess_a",
            "phase": "a",
            "status": "active",
            "userId": 1,
            "relationshipId": "rel_1",
            "eventId": None,
            "canCommit": True,
            "factSummary": "Both sides argued about housework distribution.",
            "messages": [
                {
                    "role": "user",
                    "content": "We argued because I felt the chores were uneven.",
                    "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
                }
            ],
            "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            "expiresAt": datetime(2026, 3, 28, tzinfo=UTC).isoformat(),
            "updatedAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
        }
    )
    event = SimpleNamespace(
        id=100,
        public_id="ev_1",
        status=EventStatus.DRAFT,
        relationship_id=10,
        initiator_user_id=1,
        title=None,
    )
    snapshot = SimpleNamespace(public_id="sa_1")
    calls = {"committed": 0}

    class _DB:
        def commit(self):
            calls["committed"] += 1

        def refresh(self, _obj):
            pass

        def flush(self):
            pass

    monkeypatch.setattr(analysis_session_service, "_get_store", lambda: store)
    monkeypatch.setattr(
        analysis_session_service,
        "get_relationship_by_public_id",
        lambda *_a, **_kw: relationship,
    )
    monkeypatch.setattr(
        analysis_session_service.event_repo,
        "get_open_event_for_relationship",
        lambda *_a, **_kw: None,
    )
    monkeypatch.setattr(
        analysis_session_service.event_repo,
        "create_event",
        lambda *_a, **_kw: event,
    )
    monkeypatch.setattr(
        analysis_session_service.snapshot_repo,
        "create_snapshot",
        lambda *_a, **kwargs: snapshot if kwargs["side"] == SnapshotSide.A else None,
    )
    monkeypatch.setattr(
        analysis_session_service.audit_repo,
        "create_event_state_log",
        lambda *_a, **_kw: SimpleNamespace(),
    )

    data = analysis_session_service.commit_analysis_session(_DB(), current_user, "sess_a")
    assert data.event_id == "ev_1"
    assert data.snapshot_a_id == "sa_1"
    assert event.status == EventStatus.WAITING_B
    assert calls["committed"] == 1


def test_commit_b_analysis_session_generates_judge(monkeypatch):
    current_user = SimpleNamespace(id=2, public_id="u_2")
    relationship = SimpleNamespace(public_id="rel_1", id=10, user_a_id=1, user_b_id=2)
    event = SimpleNamespace(
        id=100,
        public_id="ev_1",
        status=EventStatus.WAITING_B,
        relationship_id=10,
        initiator_user_id=1,
    )
    snapshot_a = SimpleNamespace(public_id="sa_1")
    snapshot_b = SimpleNamespace(public_id="sb_1")
    judge = SimpleNamespace(public_id="jr_1")
    store = _Store()
    store.save_session(
        {
            "sessionId": "sess_b",
            "phase": "b",
            "status": "active",
            "userId": 2,
            "relationshipId": "rel_1",
            "eventId": "ev_1",
            "canCommit": True,
            "factSummary": "One side felt ignored after a long workday and the other responded defensively.",
            "messages": [
                {
                    "role": "user",
                    "content": "I felt ignored when they dismissed how tired I was.",
                    "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
                }
            ],
            "createdAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
            "expiresAt": datetime(2026, 3, 28, tzinfo=UTC).isoformat(),
            "updatedAt": datetime(2026, 3, 27, tzinfo=UTC).isoformat(),
        }
    )

    class _DB:
        def refresh(self, _obj):
            pass

    monkeypatch.setattr(analysis_session_service, "_get_store", lambda: store)
    monkeypatch.setattr(
        analysis_session_service,
        "get_event_with_permission",
        lambda *_a, **_kw: (event, relationship),
    )
    monkeypatch.setattr(
        analysis_session_service.snapshot_repo,
        "get_snapshot_by_event_and_side",
        lambda *_a, **_kw: snapshot_a if _a[-1] == SnapshotSide.A else None,
    )
    monkeypatch.setattr(
        analysis_session_service.snapshot_repo,
        "create_snapshot",
        lambda *_a, **kwargs: snapshot_b if kwargs["side"] == SnapshotSide.B else None,
    )
    monkeypatch.setattr(
        analysis_session_service.event_service,
        "execute_judge",
        lambda *_a, **_kw: judge,
    )

    data = analysis_session_service.commit_analysis_session(_DB(), current_user, "sess_b")
    assert data.snapshot_b_id == "sb_1"
    assert data.judge_result_id == "jr_1"
