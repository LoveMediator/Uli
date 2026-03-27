"""Event service 单元测试。"""

from types import SimpleNamespace

import pytest

from app.constants.enums import EventStatus, SnapshotSide
from app.core.errors import AppError
from app.services import event_service


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


def test_create_event_success(monkeypatch):
    rel = SimpleNamespace(id=10, public_id="r_2001", user_a_id=1, user_b_id=2)
    created_event = SimpleNamespace(
        public_id="ev_new", status=EventStatus.DRAFT,
        relationship_id=10, initiator_user_id=1,
    )
    calls = {"committed": False}

    class _DB:
        def execute(self, *_):
            return _ScalarResult(rel)
        def commit(self):
            calls["committed"] = True
        def refresh(self, _obj):
            pass

    db = _DB()
    monkeypatch.setattr(event_service.event_repo, "get_open_event_for_relationship", lambda *_a, **_kw: None)
    monkeypatch.setattr(event_service.event_repo, "create_event", lambda *_a, **_kw: created_event)

    event = event_service.create_event(db, user_id=1, title="test", relationship_public_id="r_2001")
    assert event.public_id == "ev_new"
    assert calls["committed"]


def test_create_event_forbidden_for_non_member():
    rel = SimpleNamespace(id=10, public_id="r_2001", user_a_id=1, user_b_id=2)

    class _DB:
        def execute(self, *_):
            return _ScalarResult(rel)

    with pytest.raises(AppError) as ex:
        event_service.create_event(_DB(), user_id=99, title="test", relationship_public_id="r_2001")
    assert ex.value.code == 2002


def test_create_event_rejects_when_open_event_exists(monkeypatch):
    rel = SimpleNamespace(id=10, public_id="r_2001", user_a_id=1, user_b_id=2)
    open_event = SimpleNamespace(public_id="ev_open", status=EventStatus.WAITING_B)

    class _DB:
        def execute(self, *_):
            return _ScalarResult(rel)

    monkeypatch.setattr(
        event_service.event_repo,
        "get_open_event_for_relationship",
        lambda *_a, **_kw: open_event,
    )

    with pytest.raises(AppError) as ex:
        event_service.create_event(_DB(), user_id=1, title="test", relationship_public_id="r_2001")
    assert ex.value.code == 1003


def test_commit_a_success(monkeypatch):
    event = SimpleNamespace(
        id=100, public_id="ev_1", status=EventStatus.DRAFT,
        relationship_id=10, initiator_user_id=1,
    )
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)
    snapshot = SimpleNamespace(public_id="sa_1")
    calls = {"state_log": 0, "committed": 0}

    class _DB:
        def __init__(self):
            self._step = 0
        def execute(self, *_):
            self._step += 1
            return _ScalarResult(event if self._step == 1 else rel)
        def flush(self):
            pass
        def commit(self):
            calls["committed"] += 1
        def refresh(self, _obj):
            pass

    db = _DB()
    monkeypatch.setattr(event_service.snapshot_repo, "get_snapshot_by_event_and_side", lambda *_a: None)
    monkeypatch.setattr(event_service.snapshot_repo, "create_snapshot", lambda *_a, **_kw: snapshot)
    monkeypatch.setattr(event_service.audit_repo, "create_event_state_log", lambda *_a, **_kw: SimpleNamespace())

    ev, snap = event_service.commit_a(db, user_id=1, event_public_id="ev_1", confirm_text="确认")
    assert calls["committed"] == 1
    assert snap.public_id == "sa_1"


def test_commit_a_rejects_non_initiator():
    event = SimpleNamespace(
        id=100, public_id="ev_1", status=EventStatus.DRAFT,
        relationship_id=10, initiator_user_id=1,
    )
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)

    class _DB:
        def __init__(self):
            self._step = 0
        def execute(self, *_):
            self._step += 1
            return _ScalarResult(event if self._step == 1 else rel)

    with pytest.raises(AppError) as ex:
        event_service.commit_a(_DB(), user_id=2, event_public_id="ev_1", confirm_text="x")
    assert ex.value.code == 2002


def test_commit_a_rejects_wrong_status():
    event = SimpleNamespace(
        id=100, public_id="ev_1", status=EventStatus.WAITING_B,
        relationship_id=10, initiator_user_id=1,
    )
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)

    class _DB:
        def __init__(self):
            self._step = 0
        def execute(self, *_):
            self._step += 1
            return _ScalarResult(event if self._step == 1 else rel)

    with pytest.raises(AppError) as ex:
        event_service.commit_a(_DB(), user_id=1, event_public_id="ev_1", confirm_text="x")
    assert ex.value.code == 1003


def test_b_agree_success(monkeypatch):
    event = SimpleNamespace(
        id=100, public_id="ev_1", status=EventStatus.WAITING_B,
        relationship_id=10, initiator_user_id=1, judged_at=None,
    )
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)
    snapshot_a = SimpleNamespace(id=1, summary="test", points_a=[], points_b=[])
    judge = SimpleNamespace(
        public_id="jr_1", objective_summary="test",
        model_name="mock", input_tokens=0, output_tokens=0,
    )
    review = SimpleNamespace(public_id="rv_1")

    class _DB:
        def __init__(self):
            self._step = 0
            self.committed = 0
        def execute(self, *_):
            self._step += 1
            return _ScalarResult(event if self._step == 1 else rel)
        def flush(self):
            pass
        def add(self, _obj):
            pass
        def commit(self):
            self.committed += 1
        def refresh(self, _obj):
            pass

    db = _DB()
    monkeypatch.setattr(event_service.snapshot_repo, "get_snapshot_by_event_and_side", lambda *_a: snapshot_a)
    monkeypatch.setattr(event_service.judge_service, "generate_judge_result", lambda *_a, **_kw: judge)
    monkeypatch.setattr(event_service.audit_repo, "create_event_state_log", lambda *_a, **_kw: SimpleNamespace())
    monkeypatch.setattr(event_service.audit_repo, "create_ai_call_log", lambda *_a, **_kw: SimpleNamespace())
    monkeypatch.setattr(event_service.review_service, "create_review_from_judge", lambda *_a, **_kw: review)

    ev, jr = event_service.b_agree(db, user_id=2, event_public_id="ev_1")
    assert jr.public_id == "jr_1"
    assert event.status == EventStatus.JUDGED


def test_b_agree_rejects_initiator():
    event = SimpleNamespace(
        id=100, public_id="ev_1", status=EventStatus.WAITING_B,
        relationship_id=10, initiator_user_id=1,
    )
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)

    class _DB:
        def __init__(self):
            self._step = 0
        def execute(self, *_):
            self._step += 1
            return _ScalarResult(event if self._step == 1 else rel)

    with pytest.raises(AppError) as ex:
        event_service.b_agree(_DB(), user_id=1, event_public_id="ev_1")
    assert ex.value.code == 2002


def test_get_judge_result_prereq_not_met(monkeypatch):
    event = SimpleNamespace(
        id=100, public_id="ev_1", status=EventStatus.DRAFT,
        relationship_id=10, initiator_user_id=1,
    )
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)

    class _DB:
        def __init__(self):
            self._step = 0
        def execute(self, *_):
            self._step += 1
            return _ScalarResult(event if self._step == 1 else rel)

    monkeypatch.setattr(event_service.judge_repo, "get_judge_result_by_event_id", lambda *_a: None)

    with pytest.raises(AppError) as ex:
        event_service.get_judge_result(_DB(), user_id=1, event_public_id="ev_1")
    assert ex.value.code == 3003
