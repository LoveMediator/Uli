"""A7：测试基建（fixtures）。

目标：
- 提供测试用户/关系/事件的基础 fixture（不依赖真实数据库建表）。
- 提供鉴权 header fixture（Bearer access token）。
- 提供一个可复用的 TestClient 工厂：通过依赖覆盖 `get_db`，
  让 `get_current_user` / `get_current_active_user` 在测试中可控。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Callable
from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_current_user, get_db
from app.api.exception_handlers import register_exception_handlers
from app.constants.enums import EventStatus, RelationshipStatus, UserStatus
from app.core import security
from app.models.event import Event
from app.models.relationship import Relationship
from app.models.user import User


@pytest.fixture
def test_user_a() -> User:
    """测试用户 A（active）。"""
    return User(
        id=1,
        public_id="u_1001",
        username="alice",
        password_hash="unused_for_db_fixtures",
        status=UserStatus.ACTIVE,
        failed_login_count=0,
        locked_until=None,
        last_login_at=None,
    )


@pytest.fixture
def test_user_b() -> User:
    """测试用户 B（active）。"""
    return User(
        id=2,
        public_id="u_1002",
        username="bob",
        password_hash="unused_for_db_fixtures",
        status=UserStatus.ACTIVE,
        failed_login_count=0,
        locked_until=None,
        last_login_at=None,
    )


@pytest.fixture
def test_relationship(test_user_a: User, test_user_b: User) -> Relationship:
    """测试关系（active）。"""
    return Relationship(
        id=10,
        public_id="r_2001",
        user_a_id=test_user_a.id,
        user_b_id=test_user_b.id,
        status=RelationshipStatus.ACTIVE,
    )


@pytest.fixture
def test_event(test_relationship: Relationship, test_user_a: User) -> Event:
    """测试事件（draft）。"""
    return Event(
        id=100,
        public_id="e_3001",
        relationship_id=test_relationship.id,
        initiator_user_id=test_user_a.id,
        title="test-event",
        status=EventStatus.DRAFT,
    )


@pytest.fixture
def auth_headers_for_user_a(test_user_a: User) -> dict[str, str]:
    """用户 A 的鉴权 header。"""
    token = security.create_access_token(test_user_a.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_for_user_b(test_user_b: User) -> dict[str, str]:
    """用户 B 的鉴权 header。"""
    token = security.create_access_token(test_user_b.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_for_user() -> Callable[[User], dict[str, str]]:
    """工厂：给任意 user 生成鉴权 header。"""

    def _make(user: User) -> dict[str, str]:
        token = security.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def test_client_for_user() -> Callable[[User | None], TestClient]:
    """工厂：构造一个可测试鉴权依赖的 TestClient。

    通过依赖覆盖 `get_db`，让 repo 查询始终返回指定的 user。
    """

    def _client_for_user(user: User | None) -> TestClient:
        app = FastAPI()
        register_exception_handlers(app)

        def _override_get_db():
            mock_db = MagicMock()

            def _execute(_stmt: object) -> SimpleNamespace:
                # 复用 A3 的约定：repo 会调用 scalar_one_or_none()。
                return SimpleNamespace(scalar_one_or_none=lambda: user)

            mock_db.execute = _execute
            yield mock_db

        app.dependency_overrides[get_db] = _override_get_db

        @app.get("/me")
        def _me(u: User = Depends(get_current_user)) -> dict[str, int]:
            return {"user_id": u.id}

        @app.get("/me-active")
        def _me_active(u: User = Depends(get_current_active_user)) -> dict[str, int]:
            return {"user_id": u.id}

        return TestClient(app)

    return _client_for_user

