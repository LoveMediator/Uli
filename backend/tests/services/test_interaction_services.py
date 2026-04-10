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

    resp = elf_service.moderate_message(db, user_id=10, raw_message="a" * 120)
    assert called["logged"] == 1
    assert db.commit_count == 1
    assert resp.risk_level == "medium"


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
