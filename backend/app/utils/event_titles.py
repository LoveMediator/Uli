from __future__ import annotations

import re

_GARBLED_CHARS = {"?", "？", "�"}


def _looks_garbled(text: str) -> bool:
    garbled_count = sum(char in _GARBLED_CHARS for char in text)
    return garbled_count >= max(3, len(text) // 2)


def _first_meaningful_line(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _normalize_display_text(text: str | None, *, max_length: int) -> str | None:
    if text is None:
        return None

    line = _first_meaningful_line(text.strip())
    if not line or _looks_garbled(line):
        return None

    sentence = re.split(r"(?<=[。！？!?])", line, maxsplit=1)[0].strip()
    candidate = sentence or line
    if len(candidate) <= max_length:
        return candidate
    return f"{candidate[: max_length - 1].rstrip()}…"


def build_event_display_title(
    title: str | None,
    *fallback_texts: str | None,
    max_length: int = 40,
) -> str | None:
    candidates = (title, *fallback_texts)
    for candidate in candidates:
        normalized = _normalize_display_text(candidate, max_length=max_length)
        if normalized is not None:
            return normalized
    return None
