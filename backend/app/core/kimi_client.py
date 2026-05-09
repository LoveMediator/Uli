"""Compatibility wrapper for the shared LLM HTTP client."""

from __future__ import annotations

import httpx

from app.core.llm_client import close_llm_client, get_llm_client


def get_kimi_client() -> httpx.Client:
    """Return the configured LLM client for older imports."""
    return get_llm_client()


def close_kimi_client() -> None:
    """Close the configured LLM client for older imports."""
    close_llm_client()
