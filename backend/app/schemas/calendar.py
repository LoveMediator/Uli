"""Calendar 模块 Pydantic schema。

仅定义 data 层结构，不含外层 code/message/data envelope。
字段名与类型严格对齐 API 文档 §6.1、§6.2。
"""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.review import ReviewListItem


# ---------------------------------------------------------------------------
# 月历查询 — GET /api/v1/calendar?month=YYYY-MM  (API §6.1)
# ---------------------------------------------------------------------------

class CalendarDayCount(BaseModel):
    """月历中某一天的冲突事件计数。"""

    date: date
    count: int


class CalendarMonthData(BaseModel):
    """月历查询响应 data 结构。"""

    month: str = Field(description="查询月份，格式 YYYY-MM")
    days: list[CalendarDayCount]


# ---------------------------------------------------------------------------
# 日期复盘列表 — GET /api/v1/calendar/days/{date}/reviews  (API §6.2)
# ---------------------------------------------------------------------------

class CalendarDayReviewsData(BaseModel):
    """日期复盘列表响应 data 结构。"""

    date: date
    items: list[ReviewListItem]
