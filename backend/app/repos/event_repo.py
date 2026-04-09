"""Event data access."""

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
    title: str | None,
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


def get_open_event_for_relationship(db: Session, relationship_id: int) -> Event | None:
    stmt = (
        select(Event)
        .where(
            Event.relationship_id == relationship_id,
            Event.status.in_((EventStatus.DRAFT, EventStatus.WAITING_B)),
        )
        .order_by(Event.created_at.desc())
    )
    return db.execute(stmt).scalars().first()
