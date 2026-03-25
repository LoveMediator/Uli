"""Event 数据访问。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.enums import EventStatus
from app.models.event import Event


def get_event_by_public_id(db: Session, event_public_id: str) -> Event | None:
    stmt = select(Event).where(Event.public_id == event_public_id)
    return db.execute(stmt).scalar_one_or_none()


def create_event(
    db: Session,
    *,
    public_id: str,
    relationship_id: int,
    initiator_user_id: int,
    title: str,
) -> Event:
    event = Event(
        public_id=public_id,
        relationship_id=relationship_id,
        initiator_user_id=initiator_user_id,
        title=title,
        status=EventStatus.DRAFT,
    )
    db.add(event)
    db.flush()
    return event
