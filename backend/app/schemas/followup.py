"""Followup 复盘聊天 Pydantic schema。

仅定义 data 层结构，不含外层 code/message/data envelope。
字段名与类型严格对齐 API 文档 §5.9。
"""

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 复盘聊天 — POST /api/v1/events/{eventId}/followup-chat/messages  (API §5.9)
# ---------------------------------------------------------------------------

class FollowupRequest(BaseModel):
    """复盘聊天请求体。"""

    message: str = Field(min_length=1, max_length=5000)


class FollowupContextMeta(BaseModel):
    """上下文拼接元信息，用于向前端透出本次请求使用了哪些上下文。"""

    model_config = ConfigDict(populate_by_name=True)

    recent_messages: int = Field(alias="recentMessages")
    snapshots: int
    judge_results: int = Field(alias="judgeResults")


class FollowupResponse(BaseModel):
    """复盘聊天响应 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    reply: str
    context_meta: FollowupContextMeta = Field(alias="contextMeta")
