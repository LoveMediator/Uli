from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.constants.enums import EventStatus
from app.models.audit import AiCallLog
from app.core.errors import AppError
from app.services import elf_service, followup_service


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _ScalarsResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _ExecuteResult:
    def __init__(self, value=None, values=None):
        self._value = value
        self._values = values if values is not None else []

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return _ScalarsResult(self._values)


def test_followup_chat_success(monkeypatch):
    event = SimpleNamespace(id=7, relationship_id=1, status=EventStatus.JUDGED)
    rel = SimpleNamespace(id=1, user_a_id=10, user_b_id=20)

    class _DB:
        def __init__(self):
            self.commit_count = 0
            self._step = 0
            self.added = []

        def execute(self, *_):
            self._step += 1
            return _ScalarResult(event if self._step == 1 else rel)

        def add(self, obj):
            self.added.append(obj)

        def flush(self):
            pass

        def commit(self):
            self.commit_count += 1

    db = _DB()
    monkeypatch.setattr(
        "app.services.followup_service.build_context",
        lambda *_args, **_kwargs: SimpleNamespace(
            meta={"recentMessages": 1, "snapshots": 2, "judgeResults": 1},
            snapshot_a=None,
            snapshot_b=None,
            judge_result=None,
            review_content=None,
            recent_messages=[],
        ),
    )
    monkeypatch.setattr(
        followup_service.followup_repo,
        "create_followup_message",
        lambda *_args, **_kwargs: SimpleNamespace(),
    )
    monkeypatch.setattr(
        "app.services.followup_service.ai_service.call_chat_llm",
        lambda *_args, **_kwargs: {
            "content": "mock reply",
            "model_name": "mock-model",
            "input_tokens": 10,
            "output_tokens": 5,
        },
    )

    resp = followup_service.followup_chat(db, user_id=10, event_public_id="ev_1", message="hello")
    assert resp.context_meta.judge_results == 1
    assert db.commit_count == 1
    assert len(db.added) == 1
    assert isinstance(db.added[0], AiCallLog)


def test_elf_relay_forbidden_when_target_not_in_relationship(monkeypatch):
    event = SimpleNamespace(id=7, relationship_id=1, status=EventStatus.JUDGED)
    rel = SimpleNamespace(id=1, user_a_id=10, user_b_id=20)
    outsider = SimpleNamespace(id=999, public_id="u_out")

    class _DB:
        def __init__(self):
            self._step = 0

        def execute(self, *_):
            self._step += 1
            if self._step == 1:
                return _ScalarResult(event)
            if self._step == 2:
                return _ScalarResult(rel)
            if self._step == 3:
                return _ScalarResult(outsider)
            return _ScalarResult(rel)

    db = _DB()
    with pytest.raises(AppError) as ex:
        elf_service.relay_message(
            db,
            user_id=10,
            event_public_id="ev_1",
            target_user_public_id="u_out",
            raw_message="msg",
        )
    assert ex.value.code == 2002


def test_elf_inbox_lists_received_messages(monkeypatch):
    received_at = datetime(2026, 5, 9, tzinfo=UTC)
    message = SimpleNamespace(
        public_id="elf_1",
        event_id=None,
        from_user_id=20,
        final_message="我想把刚才那件事说清楚一点。",
        created_at=received_at,
    )
    sender = SimpleNamespace(id=20, public_id="u_20", username="bob")

    class _DB:
        def __init__(self):
            self._step = 0

        def execute(self, *_):
            self._step += 1
            if self._step == 1:
                return _ExecuteResult(values=[message])
            return _ExecuteResult(value=sender)

    resp = elf_service.list_inbox_messages(_DB(), user_id=10, limit=5)
    assert len(resp.items) == 1
    assert resp.items[0].message_id == "elf_1"
    assert resp.items[0].from_user_id == "u_20"
    assert resp.items[0].from_username == "bob"
    assert resp.items[0].final_message == "我想把刚才那件事说清楚一点。"


def test_elf_moderate_success(monkeypatch):
    called = {"logged": 0}

    class _DB:
        def __init__(self):
            self.commit_count = 0
            self.added = []

        def add(self, obj):
            self.added.append(obj)

        def flush(self):
            pass

        def commit(self):
            self.commit_count += 1

    db = _DB()

    def _create_log(*_args, **_kwargs):
        called["logged"] += 1
        return SimpleNamespace()

    monkeypatch.setattr(elf_service.elf_repo, "create_moderation_log", _create_log)
    monkeypatch.setattr(
        elf_service.ai_service,
        "call_llm_json",
        lambda **_kwargs: {
            "data": elf_service.ModerateAiPayload(
                riskLevel="medium",
                blocked=False,
                suggestedMessage="我想把这件事说清楚，我们能不能先平静聊一下？",
            ),
            "model_name": "mock-model",
            "input_tokens": 12,
            "output_tokens": 8,
        },
    )

    resp = elf_service.moderate_message(db, user_id=10, raw_message="a" * 120)
    assert called["logged"] == 1
    assert db.commit_count == 1
    assert resp.risk_level == "medium"
    assert resp.suggested_message == "我想把这件事说清楚，我们能不能先平静聊一下？"


def test_elf_relay_uses_ai_result(monkeypatch):
    event = SimpleNamespace(id=7, public_id="ev_1", relationship_id=1, status=EventStatus.REVIEWED)
    rel = SimpleNamespace(id=1, user_a_id=10, user_b_id=20)
    partner = SimpleNamespace(id=20, public_id="u_20")

    class _DB:
        def __init__(self):
            self.commit_count = 0
            self._step = 0
            self.added = []

        def execute(self, *_):
            self._step += 1
            if self._step == 1:
                return _ScalarResult(event)
            if self._step == 2:
                return _ScalarResult(rel)
            return _ScalarResult(partner)

        def add(self, obj):
            self.added.append(obj)

        def flush(self):
            pass

        def commit(self):
            self.commit_count += 1

    db = _DB()
    monkeypatch.setattr(
        elf_service.ai_service,
        "call_llm_json",
        lambda **_kwargs: {
            "data": elf_service.ElfRelayAiPayload(
                finalMessage="我想把刚才那件事说得更清楚一点，我们能不能晚些时候平静聊聊？",
            ),
            "model_name": "mock-model",
            "input_tokens": 11,
            "output_tokens": 9,
        },
    )

    resp = elf_service.relay_message(
        db,
        user_id=10,
        event_public_id="ev_1",
        target_user_public_id="u_20",
        raw_message="你为什么老是这样",
    )
    assert db.commit_count == 1
    assert resp.delivered is True
    assert "平静聊聊" in resp.final_message


def test_followup_chat_prereq_not_met():
    event = SimpleNamespace(id=7, relationship_id=1, status=EventStatus.DRAFT)
    rel = SimpleNamespace(id=1, user_a_id=10, user_b_id=20)

    class _DB:
        def __init__(self):
            self._step = 0

        def execute(self, *_):
            self._step += 1
            return _ScalarResult(event if self._step == 1 else rel)

    db = _DB()
    with pytest.raises(AppError) as ex:
        followup_service.followup_chat(db, user_id=10, event_public_id="ev_1", message="hello")
    assert ex.value.code == 3003
