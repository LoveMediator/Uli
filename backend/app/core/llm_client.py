"""Shared LLM API HTTP client singleton."""

from __future__ import annotations

import httpx

from app.core.config import settings

_client: httpx.Client | None = None
_client_base_url: str | None = None


def get_llm_client() -> httpx.Client:
    """Return a reusable HTTP client for the configured LLM provider."""
    global _client, _client_base_url  # noqa: PLW0603
    base_url = settings.effective_llm_base_url.rstrip("/")
    if _client is None or _client_base_url != base_url:
        if _client is not None:
            _client.close()
        _client = httpx.Client(
            base_url=base_url,
            timeout=60.0,
            trust_env=False,
            verify=not settings.debug,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        _client_base_url = base_url
    return _client


def close_llm_client() -> None:
    """Close the shared LLM HTTP connection pool."""
    global _client, _client_base_url  # noqa: PLW0603
    if _client is not None:
        _client.close()
        _client = None
        _client_base_url = None
