from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from app.services import review_service


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


def test_get_review_success(monkeypatch):
    review = SimpleNamespace(public_id="rv_1", relationship_id=10)
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)

    db = SimpleNamespace(execute=lambda *_: _ScalarResult(rel))
    monkeypatch.setattr(review_service.review_repo, "get_review_by_public_id", lambda *_: review)

    got = review_service.get_review(db, user_id=1, review_public_id="rv_1")
    assert got is review


def test_get_review_forbidden(monkeypatch):
    review = SimpleNamespace(public_id="rv_1", relationship_id=10)
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)

    db = SimpleNamespace(execute=lambda *_: _ScalarResult(rel))
    monkeypatch.setattr(review_service.review_repo, "get_review_by_public_id", lambda *_: review)

    with pytest.raises(AppError) as ex:
        review_service.get_review(db, user_id=99, review_public_id="rv_1")
    assert ex.value.code == "2002"


def test_update_review_writes_version(monkeypatch):
    review = SimpleNamespace(id=1, relationship_id=10, content="old", updated_by_user_id=None)
    rel = SimpleNamespace(id=10, user_a_id=1, user_b_id=2)

    calls = {"version": 0, "commit": 0, "refresh": 0}

    class _DB:
        def execute(self, *_):
            return _ScalarResult(rel)

        def commit(self):
            calls["commit"] += 1

        def refresh(self, _obj):
            calls["refresh"] += 1

    db = _DB()

    monkeypatch.setattr(review_service.review_repo, "get_review_by_public_id", lambda *_: review)
    monkeypatch.setattr(review_service.review_repo, "get_latest_version_no", lambda *_: 2)
    monkeypatch.setattr(
        review_service.review_repo,
        "update_review_content",
        lambda *_args, **kwargs: SimpleNamespace(**{**review.__dict__, "content": kwargs["content"]}),
    )

    def _create_review_version(*_args, **_kwargs):
        calls["version"] += 1
        return SimpleNamespace()

    monkeypatch.setattr(review_service.review_repo, "create_review_version", _create_review_version)

    review_service.update_review(db, user_id=1, review_public_id="rv_1", content="new content")

    assert calls["version"] == 1
    assert calls["commit"] == 1
    assert calls["refresh"] == 1


def test_create_review_from_judge_idempotent(monkeypatch):
    existing = SimpleNamespace(public_id="rv_existing")
    db = SimpleNamespace()

    monkeypatch.setattr(review_service.review_repo, "get_review_by_event_id", lambda *_: existing)
    monkeypatch.setattr(review_service.review_repo, "get_calendar_entry_by_event_id", lambda *_: SimpleNamespace())

    got = review_service.create_review_from_judge(
        db,
        event_id=1,
        relationship_id=1,
        content="content",
    )
    assert got is existing
