from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import AppError


def _count_message_metrics(messages: list[dict[str, Any]]) -> tuple[int, int]:
    text_chars = 0
    image_count = 0

    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            text_chars += len(content)
            continue
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                text_chars += len(str(block.get("text", "")))
            elif block.get("type") == "image_url":
                image_count += 1
    return text_chars, image_count


def _contains_image(messages: list[dict[str, Any]]) -> bool:
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "image_url":
                return True
    return False


def _resolve_model(model_name: str | None, messages: list[dict[str, Any]]) -> str:
    if model_name and not model_name.startswith("mock-"):
        return model_name
    if _contains_image(messages):
        return settings.kimi_vision_model
    return settings.kimi_text_model


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        return "\n".join(part for part in text_parts if part)
    return str(content or "")


def call_private_chat_llm(
    *,
    messages: list[dict[str, Any]],
    model_name: str = "mock-private-chat-v1",
) -> dict[str, Any]:
    """私聊分析专用的 LLM 出口。"""
    if not settings.kimi_api_key:
        raise AppError("Kimi API Key 未配置", code=5000)

    resolved_model = _resolve_model(model_name, messages)
    request_payload = {
        "model": resolved_model,
        "messages": messages,
    }
    try:
        with httpx.Client(base_url=settings.kimi_base_url, timeout=60.0) as client:
            response = client.post(
                "/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.kimi_api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
            )
    except httpx.TimeoutException as exc:
        raise AppError("Kimi 请求超时，请稍后重试", code=5000) from exc
    except httpx.HTTPError as exc:
        raise AppError(f"Kimi 服务调用失败：{exc}", code=5000) from exc

    if response.status_code == 401:
        raise AppError("Kimi API 认证失败，请检查 API Key", code=5000)
    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {"error": {"message": response.text}}
        error_message = str(
            error_payload.get("error", {}).get("message")
            or error_payload.get("message")
            or response.text
        )
        raise AppError(f"Kimi 请求失败：{error_message}", code=1001 if response.status_code < 500 else 5000)

    payload = response.json()
    choices = payload.get("choices") or []
    if not choices:
        raise AppError("Kimi 未返回可用结果", code=5000)

    message = choices[0].get("message", {})
    usage = payload.get("usage", {})
    text_chars, image_count = _count_message_metrics(messages)
    content = _extract_text_content(message.get("content")).strip()
    if not content:
        content = (
            f"[EMPTY] Kimi returned no text content for {len(messages)} messages, "
            f"{text_chars} text chars, {image_count} images."
        )
    return {
        "model_name": resolved_model,
        "input_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "output_tokens": int(usage.get("completion_tokens", 0) or 0),
        "content": content,
    }
