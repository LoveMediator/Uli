"""Private analysis chat LLM service.

Uses the shared chat_completion() for the HTTP layer,
adds private-chat-specific model resolution, structured reply parsing,
and vision/image detection.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.services.ai_service import chat_completion


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
        return settings.effective_llm_vision_model
    return settings.effective_llm_text_model


def _extract_json_text(content: str) -> str | None:
    text = content.strip()
    if not text:
        return None
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    return text[start : end + 1]


def _parse_structured_private_reply(raw_content: str) -> tuple[str, bool, str | None]:
    reply = raw_content.strip()
    can_confirm = False
    fact_summary: str | None = None

    json_text = _extract_json_text(raw_content)
    if json_text is None:
        return reply, can_confirm, fact_summary

    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError:
        return reply, can_confirm, fact_summary
    if not isinstance(payload, dict):
        return reply, can_confirm, fact_summary

    payload_reply = str(payload.get("reply", "")).strip()
    if payload_reply:
        reply = payload_reply

    raw_can_confirm = payload.get("can_confirm")
    if raw_can_confirm is None:
        raw_can_confirm = payload.get("canConfirm")
    can_confirm = bool(raw_can_confirm)

    raw_fact_summary = payload.get("fact_summary")
    if raw_fact_summary is None:
        raw_fact_summary = payload.get("factSummary")
    if raw_fact_summary is not None:
        candidate = str(raw_fact_summary).strip()
        if candidate:
            fact_summary = candidate

    if not fact_summary:
        can_confirm = False
    return reply, can_confirm, fact_summary


def call_private_chat_llm(
    *,
    messages: list[dict[str, Any]],
    model_name: str = "mock-private-chat-v1",
) -> dict[str, Any]:
    """LLM entrypoint for private analysis chat."""
    resolved_model = _resolve_model(model_name, messages)

    result = chat_completion(
        messages=messages,
        model=resolved_model,
    )

    raw_content = result["raw_content"]
    text_chars, image_count = _count_message_metrics(messages)
    if not raw_content:
        raw_content = (
            f"[EMPTY] LLM returned no text content for {len(messages)} messages, "
            f"{text_chars} text chars, {image_count} images."
        )

    content, can_confirm, fact_summary = _parse_structured_private_reply(raw_content)
    return {
        "model_name": result["model_name"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "content": content,
        "can_confirm": can_confirm,
        "fact_summary": fact_summary,
        "raw_content": raw_content,
    }
