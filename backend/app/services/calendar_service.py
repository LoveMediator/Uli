"""Calendar 业务服务层。

负责月历聚合查询与日期复盘列表。
权限校验：通过 relationship 的 user_a_id / user_b_id 判断当前用户是否为关系参与方。
"""

from datetime import date

from sqlalchemy.orm import Session

from app.repos import review_repo
from app.schemas.calendar import CalendarDayCount, CalendarDayReviewsData, CalendarMonthData
from app.schemas.review import ReviewListItem
from app.utils.permissions import assert_relationship_member


def get_month_summary(
    db: Session,
    user_id: int,
    relationship_id: int,
    year: int,
    month: int,
) -> CalendarMonthData:
    """月历查询：按月聚合事件数量。

    对应 API §6.1 GET /calendar?month=YYYY-MM。
    """
    assert_relationship_member(db, relationship_id, user_id)

    rows = review_repo.get_month_day_counts(db, relationship_id, year, month)
    days = [
        CalendarDayCount(date=row[0], count=row[1])
        for row in rows
    ]
    return CalendarMonthData(
        month=f"{year:04d}-{month:02d}",
        days=days,
    )


def get_day_reviews(
    db: Session,
    user_id: int,
    relationship_id: int,
    target_date: date,
) -> CalendarDayReviewsData:
    """日期复盘列表：返回某天关系下所有复盘摘要。

    对应 API §6.2 GET /calendar/days/{date}/reviews。
    """
    assert_relationship_member(db, relationship_id, user_id)

    rows = review_repo.get_review_items_by_date(db, relationship_id, target_date)
    items = [
        ReviewListItem(
            reviewId=review.public_id,
            eventId=event.public_id,
            title=event.title,
            updatedAt=review.updated_at,
        )
        for review, event in rows
    ]

    return CalendarDayReviewsData(date=target_date, items=items)
