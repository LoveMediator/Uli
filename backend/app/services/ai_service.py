"""Shared LLM helpers."""

from __future__ import annotations

import json
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.errors import AppError

T = TypeVar("T", bound=BaseModel)

DEFAULT_SYSTEM_PROMPT = (
    "You are LoveMediator's backend AI assistant. "
    "Return calm, accurate, and actionable content. "
    "Do not invent facts that are not present in the provided context."
)


def _resolve_model(model_name: str | None) -> str:
    if model_name and not model_name.startswith("mock-"):
        return model_name
    return settings.kimi_text_model


def _is_kimi_k2_family(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    return normalized.startswith("kimi-k2")


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        return "\n".join(part for part in text_parts if part)
    return str(content or "")


def _request_chat_completion(
    *,
    messages: list[dict[str, Any]],
    model_name: str | None = None,
    temperature: float = 0.3,
) -> dict[str, Any]:
    if not settings.kimi_api_key:
        raise AppError("Kimi API Key 未配置", code=5000)

    resolved_model = _resolve_model(model_name)
    request_payload = {
        "model": resolved_model,
        "messages": messages,
    }
    if _is_kimi_k2_family(resolved_model):
        request_payload["thinking"] = {"type": "disabled"}
    else:
        request_payload["temperature"] = temperature
    try:
        with httpx.Client(
            base_url=settings.kimi_base_url,
            timeout=60.0,
            trust_env=False,
            verify=False,  # TODO: 生产环境应移除此行。开发环境中系统代理 MITM 会替换 SSL 证书导致失败
        ) as client:
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
        raise AppError(f"Kimi 服务调用失败: {exc}", code=5000) from exc

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
        raise AppError(
            f"Kimi 请求失败: {error_message}",
            code=1001 if response.status_code < 500 else 5000,
        )

    payload = response.json()
    choices = payload.get("choices") or []
    if not choices:
        raise AppError("Kimi 未返回可用结果", code=5000)

    message = choices[0].get("message", {})
    content = _extract_text_content(message.get("content")).strip()
    if not content:
        raise AppError("Kimi 未返回可用文本内容", code=5000)

    usage = payload.get("usage", {})
    return {
        "model_name": resolved_model,
        "input_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "output_tokens": int(usage.get("completion_tokens", 0) or 0),
        "content": content,
    }


def call_chat_llm(
    *,
    messages: list[dict[str, Any]],
    model_name: str | None = None,
    temperature: float = 0.3,
) -> dict[str, Any]:
    return _request_chat_completion(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
    )


def call_llm(
    *,
    prompt: str,
    model_name: str | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.3,
) -> dict[str, Any]:
    messages = [
        {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    return call_chat_llm(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
    )


def _extract_json_text(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def call_llm_json(
    *,
    prompt: str,
    response_model: type[T],
    model_name: str | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    schema_text = json.dumps(response_model.model_json_schema(), ensure_ascii=False)
    raw_result = call_llm(
        prompt=(
            f"{prompt}\n\n"
            "Return one valid JSON object only, without Markdown or extra commentary.\n"
            f"JSON Schema: {schema_text}"
        ),
        model_name=model_name,
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
        temperature=temperature,
    )

    json_text = _extract_json_text(str(raw_result["content"]))
    try:
        parsed = response_model.model_validate_json(json_text)
    except (ValidationError, ValueError) as exc:
        raise AppError(f"AI 返回格式无效: {exc}", code=5000) from exc

    raw_result["data"] = parsed
    return raw_result
