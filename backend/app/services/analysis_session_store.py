from __future__ import annotations

import json
from typing import Any, cast

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.errors import InternalError
from app.core.redis_client import get_redis_client

SESSION_KEY_PREFIX = "analysis_session"
RELATIONSHIP_SET_PREFIX = "analysis_session:relationship"
EVENT_SET_PREFIX = "analysis_session:event"
SCOPE_INDEX_PREFIX = "analysis_session:index"


def _json_dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return cast(dict[str, Any], json.loads(value))


class AnalysisSessionStore:
    def __init__(self, client: Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    def _session_key(self, session_id: str) -> str:
        return f"{SESSION_KEY_PREFIX}:{session_id}"

    def _relationship_set_key(self, relationship_public_id: str) -> str:
        return f"{RELATIONSHIP_SET_PREFIX}:{relationship_public_id}"

    def _event_set_key(self, event_public_id: str) -> str:
        return f"{EVENT_SET_PREFIX}:{event_public_id}"

    def _scope_index_key(self, scope: str, scope_id: str, user_id: int) -> str:
        return f"{SCOPE_INDEX_PREFIX}:{scope}:{scope_id}:user:{user_id}"

    def _get_text(self, key: str) -> str | None:
        return cast(str | None, self._client.get(key))

    def _get_members(self, key: str) -> set[str]:
        return cast(set[str], self._client.smembers(key))

    def _refresh_indexes(self, session: dict[str, Any]) -> None:
        relationship_public_id = cast(str | None, session.get("relationshipId"))
        if relationship_public_id:
            relationship_key = self._relationship_set_key(relationship_public_id)
            self._client.sadd(relationship_key, session["sessionId"])
            self._client.expire(relationship_key, self._ttl_seconds)

        event_public_id = cast(str | None, session.get("eventId"))
        if event_public_id:
            event_key = self._event_set_key(event_public_id)
            self._client.sadd(event_key, session["sessionId"])
            self._client.expire(event_key, self._ttl_seconds)

        scope_id = event_public_id or relationship_public_id
        if scope_id:
            scope_key = self._scope_index_key(
                str(session["phase"]),
                scope_id,
                int(session["userId"]),
            )
            self._client.set(scope_key, session["sessionId"], ex=self._ttl_seconds)

    def save_session(self, session: dict[str, Any]) -> None:
        try:
            self._client.set(
                self._session_key(str(session["sessionId"])),
                _json_dumps(session),
                ex=self._ttl_seconds,
            )
            self._refresh_indexes(session)
        except RedisError as exc:
            raise InternalError("分析会话缓存不可用") from exc

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        try:
            session = _json_loads(self._get_text(self._session_key(session_id)))
            if session is not None:
                self.save_session(session)
            return session
        except RedisError as exc:
            raise InternalError("分析会话缓存不可用") from exc

    def get_scoped_session(
        self,
        scope: str,
        scope_id: str,
        user_id: int,
    ) -> dict[str, Any] | None:
        try:
            session_id = self._get_text(self._scope_index_key(scope, scope_id, user_id))
            if not session_id:
                return None

            session = _json_loads(self._get_text(self._session_key(session_id)))
            if session is None:
                self._client.delete(self._scope_index_key(scope, scope_id, user_id))
                return None

            self.save_session(session)
            return session
        except RedisError as exc:
            raise InternalError("分析会话缓存不可用") from exc

    def clear_sessions_for_relationship(self, relationship_public_id: str) -> None:
        try:
            relationship_key = self._relationship_set_key(relationship_public_id)
            session_ids = [session_id for session_id in self._get_members(relationship_key) if session_id]
            for session_id in session_ids:
                session = _json_loads(self._get_text(self._session_key(session_id)))
                if session is None:
                    self._client.delete(self._session_key(session_id))
                    continue

                scope_id = cast(str | None, session.get("eventId")) or cast(
                    str | None,
                    session.get("relationshipId"),
                )
                if scope_id:
                    self._client.delete(
                        self._scope_index_key(
                            str(session["phase"]),
                            scope_id,
                            int(session["userId"]),
                        )
                    )

                event_public_id = cast(str | None, session.get("eventId"))
                if event_public_id:
                    self._client.srem(self._event_set_key(event_public_id), session_id)

                self._client.delete(self._session_key(session_id))

            self._client.delete(relationship_key)
        except RedisError as exc:
            raise InternalError("分析会话缓存不可用") from exc


_store: AnalysisSessionStore | None = None


def get_analysis_session_store() -> AnalysisSessionStore:
    global _store
    if _store is None:
        _store = AnalysisSessionStore(
            client=get_redis_client(),
            ttl_seconds=settings.analysis_session_ttl_seconds,
        )
    return _store
