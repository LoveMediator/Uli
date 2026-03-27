"""Review / ReviewVersion / CalendarEntry 数据访问层。

所有方法接收 SQLAlchemy Session，不处理鉴权，不包含业务编排。
仅操作 3 号负责的表：reviews、review_versions、calendar_entries。
"""

from datetime import date

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.review import CalendarEntry, Review, ReviewVersion


# --- Review ---

def get_review_by_public_id(db: Session, public_id: str) -> Review | None:
    """按 public_id 查询单条复盘。"""
    stmt = select(Review).where(Review.public_id == public_id)
    return db.execute(stmt).scalar_one_or_none()


def get_review_by_event_id(db: Session, event_id: int) -> Review | None:
    """按 event_id 查询复盘（reviews 与 events 为 1:1）。"""
    stmt = select(Review).where(Review.event_id == event_id)
    return db.execute(stmt).scalar_one_or_none()


def create_review(
    db: Session,
    *,
    public_id: str,
    event_id: int,
    relationship_id: int,
    content: str,
    source: str = "judge_result",
    created_by_user_id: int | None = None,
) -> Review:
    """创建一条复盘记录。"""
    review = Review(
        public_id=public_id,
        event_id=event_id,
        relationship_id=relationship_id,
        content=content,
        source=source,
        created_by_user_id=created_by_user_id,
    )
    db.add(review)
    db.flush()
    return review


def update_review_content(
    db: Session,
    review: Review,
    *,
    content: str,
    updated_by_user_id: int,
) -> Review:
    """更新复盘正文，同时由调用方负责写入 review_version。"""
    review.content = content
    review.updated_by_user_id = updated_by_user_id
    db.flush()
    return review


# --- ReviewVersion ---

def get_latest_version_no(db: Session, review_id: int) -> int:
    """获取指定 review 的最新版本号；无历史版本时返回 0。"""
    stmt = (
        select(func.coalesce(func.max(ReviewVersion.version_no), 0))
        .where(ReviewVersion.review_id == review_id)
    )
    result = db.execute(stmt).scalar_one()
    return int(result)


def create_review_version(
    db: Session,
    *,
    review_id: int,
    version_no: int,
    content: str,
    edited_by_user_id: int,
) -> ReviewVersion:
    """插入一条复盘编辑版本记录。"""
    version = ReviewVersion(
        review_id=review_id,
        version_no=version_no,
        content=content,
        edited_by_user_id=edited_by_user_id,
    )
    db.add(version)
    db.flush()
    return version


# --- CalendarEntry ---

def get_month_day_counts(
    db: Session,
    relationship_id: int,
    year: int,
    month: int,
) -> list[tuple[date, int]]:
    """按月聚合 calendar_entries，返回 [(date, count), ...]。

    对应 API §6.1 GET /calendar?month=YYYY-MM，按 relationship 维度隔离。
    """
    stmt = (
        select(
            CalendarEntry.calendar_date,
            func.count().label("cnt"),
        )
        .where(
            CalendarEntry.relationship_id == relationship_id,
            extract("year", CalendarEntry.calendar_date) == year,
            extract("month", CalendarEntry.calendar_date) == month,
        )
        .group_by(CalendarEntry.calendar_date)
        .order_by(CalendarEntry.calendar_date)
    )
    return [
        (calendar_date, int(count))
        for calendar_date, count in db.execute(stmt).all()
    ]


def get_review_items_by_date(
    db: Session,
    relationship_id: int,
    target_date: date,
) -> list[tuple[Review, Event]]:
    """按日期查询关系下的复盘列表。

    通过 calendar_entries JOIN reviews 实现，对应 API §6.2。
    """
    stmt = (
        select(Review, Event)
        .join(CalendarEntry, CalendarEntry.review_id == Review.id)
        .join(Event, Event.id == Review.event_id)
        .where(
            CalendarEntry.relationship_id == relationship_id,
            CalendarEntry.calendar_date == target_date,
        )
        .order_by(Review.updated_at.desc())
    )
    return [
        (review, event)
        for review, event in db.execute(stmt).all()
    ]


def create_calendar_entry(
    db: Session,
    *,
    review_id: int,
    event_id: int,
    relationship_id: int,
    calendar_date: date,
) -> CalendarEntry:
    """创建一条日历条目（review_id 和 event_id 均有唯一约束）。"""
    entry = CalendarEntry(
        review_id=review_id,
        event_id=event_id,
        relationship_id=relationship_id,
        calendar_date=calendar_date,
    )
    db.add(entry)
    db.flush()
    return entry


def get_calendar_entry_by_event_id(db: Session, event_id: int) -> CalendarEntry | None:
    """按 event_id 查询日历条目（calendar_entries 与 events 为 1:1）。"""
    stmt = select(CalendarEntry).where(CalendarEntry.event_id == event_id)
    return db.execute(stmt).scalar_one_or_none()
