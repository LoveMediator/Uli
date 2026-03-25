"""3 号公共权限校验工具。

抽离各 service 中重复的「关系成员校验」和「事件+关系」查询逻辑。
仅做只读查询 + 抛异常，不包含业务编排。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.error_codes import FORBIDDEN, NOT_FOUND
from app.core.errors import AppError
from app.models.event import Event
from app.models.relationship import Relationship


def get_relationship_by_public_id(db: Session, relationship_public_id: str) -> Relationship:
    """按 public_id 查询 relationship，不存在则抛 NOT_FOUND。"""
    stmt = select(Relationship).where(Relationship.public_id == relationship_public_id)
    rel = db.execute(stmt).scalar_one_or_none()
    if rel is None:
        raise AppError("关系不存在", code=NOT_FOUND)
    return rel


def get_relationship_or_fail(db: Session, relationship_id: int) -> Relationship:
    """按内部 ID 查询 relationship，不存在则抛 NOT_FOUND。"""
    stmt = select(Relationship).where(Relationship.id == relationship_id)
    rel = db.execute(stmt).scalar_one_or_none()
    if rel is None:
        raise AppError("关系不存在", code=NOT_FOUND)
    return rel


def assert_relationship_member(db: Session, relationship_id: int, user_id: int) -> Relationship:
    """校验 user_id 是否为 relationship 的 A 或 B 方，不是则抛 FORBIDDEN；通过则返回 relationship。"""
    rel = get_relationship_or_fail(db, relationship_id)
    if user_id not in (rel.user_a_id, rel.user_b_id):
        raise AppError("无权访问该资源", code=FORBIDDEN)
    return rel


def get_event_with_permission(db: Session, event_public_id: str, user_id: int) -> tuple[Event, Relationship]:
    """通过 public_id 查事件并校验用户是该关系参与方，返回 (event, relationship)。"""
    stmt = select(Event).where(Event.public_id == event_public_id)
    event = db.execute(stmt).scalar_one_or_none()
    if event is None:
        raise AppError("事件不存在", code=NOT_FOUND)
    rel = assert_relationship_member(db, event.relationship_id, user_id)
    return event, rel
