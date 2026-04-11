"""Shared LLM helpers."""

from __future__ import annotations

import json
from typing import Any, TypeVar

import httpx

from app.core.kimi_client import get_kimi_client
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.errors import AppError

T = TypeVar("T", bound=BaseModel)

DEFAULT_SYSTEM_PROMPT = (
    "你是 Uli 的后端 AI 助手。"
    "你需要输出冷静、准确、可执行的中文内容。"
    "不要编造数据库里不存在的事实，不要输出攻击性建议。"
)


def _resolve_model(model_name: str | None) -> str:
    if model_name and not model_name.startswith("mock-"):
        return model_name
    return settings.kimi_text_model


def _is_kimi_k2_family(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    return normalized.startswith("kimi-k2")


def kimi_chat_completion(
    *,
    messages: list[dict[str, Any]],
    model: str,
    temperature: float | None = None,
) -> dict[str, Any]:
    """底层 Kimi API 调用：发送请求、处理错误、解析响应。

    返回 {"model_name", "input_tokens", "output_tokens", "raw_content"}。
    调用方自行决定如何处理 raw_content（可能为空字符串）。
    """
    if not settings.kimi_api_key:
        raise AppError("Kimi API Key 未配置", code=5000)

    request_payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if _is_kimi_k2_family(model):
        request_payload["thinking"] = {"type": "disabled"}
    elif temperature is not None:
        request_payload["temperature"] = temperature

    try:
        response = get_kimi_client().post(
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
    raw_content = extract_text_content(message.get("content")).strip()
    usage = payload.get("usage", {})
    return {
        "model_name": model,
        "input_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "output_tokens": int(usage.get("completion_tokens", 0) or 0),
        "raw_content": raw_content,
    }


def extract_text_content(content: Any) -> str:
    """从 Kimi 响应的 content 字段中提取纯文本（兼容 string / list-of-blocks 两种格式）。"""
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
    resolved_model = _resolve_model(model_name)
    result = kimi_chat_completion(
        messages=messages,
        model=resolved_model,
        temperature=temperature,
    )
    content = result["raw_content"]
    if not content:
        raise AppError("Kimi 未返回可用文本内容", code=5000)
    return {
        "model_name": result["model_name"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
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
