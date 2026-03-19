"""Elf 互动模块 Pydantic schema。

仅定义 data 层结构，不含外层 code/message/data envelope。
字段名与类型严格对齐 API 文档 §7.1、§7.2。
"""

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 代转达 — POST /api/v1/elf/relay  (API §7.1)
# ---------------------------------------------------------------------------

class ElfRelayRequest(BaseModel):
    """小精灵代转达请求体。"""

    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    target_user_id: str = Field(alias="targetUserId")
    raw_message: str = Field(alias="rawMessage", min_length=1, max_length=2000)


class ElfRelayResponse(BaseModel):
    """代转达成功响应 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    message_id: str = Field(alias="messageId")
    delivered: bool
    final_message: str = Field(alias="finalMessage")


# ---------------------------------------------------------------------------
# 过激语言检测与柔化 — POST /api/v1/elf/moderate  (API §7.2)
# ---------------------------------------------------------------------------

class ModerateRequest(BaseModel):
    """过激语言检测请求体。"""

    model_config = ConfigDict(populate_by_name=True)

    raw_message: str = Field(alias="rawMessage", min_length=1, max_length=2000)


class ModerateResponse(BaseModel):
    """过激语言检测响应 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    blocked: bool
    risk_level: str = Field(alias="riskLevel")
    suggested_message: str | None = Field(default=None, alias="suggestedMessage")
