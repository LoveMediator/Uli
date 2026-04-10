"""公共 Pydantic 校验器。

集中管理跨 schema 共享的字段校验逻辑。
"""

from __future__ import annotations


def reject_null_bytes(v: str) -> str:
    """拒绝包含 null byte 的字符串输入。

    PostgreSQL text 列不允许 \\x00，该校验器在 Pydantic 层统一拦截。
    """
    if isinstance(v, str) and "\x00" in v:
        raise ValueError("输入包含非法字符")
    return v
