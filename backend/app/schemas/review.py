"""Review 模块 Pydantic schema。

仅定义 data 层结构，不含外层 code/message/data envelope（由 1 号 common.py 提供）。
字段名与类型严格对齐 API 文档 §6.3、§6.4。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.validators import reject_null_bytes


# ---------------------------------------------------------------------------
# 复盘详情 — GET /api/v1/reviews/{reviewId}  (API §6.3)
# ---------------------------------------------------------------------------

class ReviewDetail(BaseModel):
    """复盘详情响应 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    review_id: str = Field(alias="reviewId")
    event_id: str = Field(alias="eventId")
    content: str
    source: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


# ---------------------------------------------------------------------------
# 编辑复盘 — PUT /api/v1/reviews/{reviewId}  (API §6.4)
# ---------------------------------------------------------------------------

class ReviewUpdateRequest(BaseModel):
    """编辑复盘请求体。"""

    content: str = Field(min_length=1, max_length=10000)

    _no_null = field_validator("content", mode="before")(reject_null_bytes)


class ReviewUpdateResponse(BaseModel):
    """编辑复盘成功响应 data 结构。"""

    model_config = ConfigDict(populate_by_name=True)

    review_id: str = Field(alias="reviewId")
    updated_at: datetime = Field(alias="updatedAt")
    updated_by: str = Field(alias="updatedBy")


# ---------------------------------------------------------------------------
# 日期复盘列表项 — GET /api/v1/calendar/days/{date}/reviews  (API §6.2)
# ---------------------------------------------------------------------------

class ReviewListItem(BaseModel):
    """单条复盘在日历日期列表中的摘要。"""

    model_config = ConfigDict(populate_by_name=True)

    review_id: str = Field(alias="reviewId")
    event_id: str = Field(alias="eventId")
    title: str | None = None
    updated_at: datetime = Field(alias="updatedAt")
