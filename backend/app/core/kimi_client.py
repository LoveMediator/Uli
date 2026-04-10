"""Kimi API HTTP 客户端单例。

提供模块级连接池，避免每次 AI 调用都新建 TCP 连接 + TLS 握手。
应用关闭时通过 close_kimi_client() 释放资源。
"""

from __future__ import annotations

import httpx

from app.core.config import settings

_client: httpx.Client | None = None


def get_kimi_client() -> httpx.Client:
    """获取 Kimi API 的 httpx 连接池单例。

    首次调用时创建，后续复用同一连接池。
    verify 由 settings.debug 控制：debug=True 时跳过 SSL 验证。
    """
    global _client  # noqa: PLW0603
    if _client is None:
        _client = httpx.Client(
            base_url=settings.kimi_base_url,
            timeout=60.0,
            trust_env=False,
            verify=not settings.debug,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
    return _client


def close_kimi_client() -> None:
    """关闭连接池，在应用 shutdown 时调用。"""
    global _client  # noqa: PLW0603
    if _client is not None:
        _client.close()
        _client = None
