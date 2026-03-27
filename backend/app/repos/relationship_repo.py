from typing import Any, cast

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from app.constants.enums import RelationshipStatus
from app.models.audit import AiCallLog, EventStateLog
from app.models.elf import ElfMessage
from app.models.event import Event
from app.models.judge import JudgeResult
from app.models.relationship import Relationship
from app.models.review import CalendarEntry, FollowupMessage, Review, ReviewVersion
from app.models.session import PrivateMessage, PrivateSession
from app.models.snapshot import EventSnapshot


def _delete_rowcount(db: Session, stmt: Any) -> int:
    return cast(CursorResult[Any], db.execute(stmt)).rowcount or 0


def list_relationships_for_user(db: Session, user_id: int) -> list[Relationship]:
    stmt = (
        select(Relationship)
        .where(
            or_(
                Relationship.user_a_id == user_id,
                Relationship.user_b_id == user_id,
            )
        )
        .order_by(Relationship.updated_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_active_relationship_between_users(
    db: Session,
    user_a_id: int,
    user_b_id: int,
) -> Relationship | None:
    stmt = select(Relationship).where(
        Relationship.status == RelationshipStatus.ACTIVE,
        or_(
            and_(
                Relationship.user_a_id == user_a_id,
                Relationship.user_b_id == user_b_id,
            ),
            and_(
                Relationship.user_a_id == user_b_id,
                Relationship.user_b_id == user_a_id,
            ),
        ),
    )
    return db.execute(stmt).scalar_one_or_none()


def create_relationship(
    db: Session,
    *,
    public_id: str,
    user_a_id: int,
    user_b_id: int,
    status: RelationshipStatus = RelationshipStatus.ACTIVE,
) -> Relationship:
    relationship = Relationship(
        public_id=public_id,
        user_a_id=user_a_id,
        user_b_id=user_b_id,
        status=status,
    )
    db.add(relationship)
    db.flush()
    return relationship


def get_relationship_by_public_id(db: Session, relationship_public_id: str) -> Relationship | None:
    stmt = select(Relationship).where(Relationship.public_id == relationship_public_id)
    return db.execute(stmt).scalar_one_or_none()


def delete_relationship_graph(db: Session, relationship_id: int) -> dict[str, int]:
    event_ids = list(
        db.execute(select(Event.id).where(Event.relationship_id == relationship_id)).scalars().all()
    )
    review_ids = list(
        db.execute(select(Review.id).where(Review.relationship_id == relationship_id)).scalars().all()
    )
    session_ids: list[int] = []
    if event_ids:
        session_ids = list(
            db.execute(select(PrivateSession.id).where(PrivateSession.event_id.in_(event_ids))).scalars().all()
        )

    deleted_counts = {
        "privateMessages": 0,
        "privateSessions": 0,
        "followupMessages": 0,
        "eventStateLogs": 0,
        "aiCallLogs": 0,
        "elfMessages": 0,
        "judgeResults": 0,
        "eventSnapshots": 0,
        "calendarEntries": 0,
        "reviewVersions": 0,
        "reviews": 0,
        "events": 0,
        "relationships": 0,
    }

    if session_ids:
        deleted_counts["privateMessages"] = _delete_rowcount(
            db,
            delete(PrivateMessage).where(PrivateMessage.session_id.in_(session_ids)),
        )
    if event_ids:
        deleted_counts["privateSessions"] = _delete_rowcount(
            db,
            delete(PrivateSession).where(PrivateSession.event_id.in_(event_ids)),
        )
        deleted_counts["followupMessages"] = _delete_rowcount(
            db,
            delete(FollowupMessage).where(FollowupMessage.event_id.in_(event_ids)),
        )
        deleted_counts["eventStateLogs"] = _delete_rowcount(
            db,
            delete(EventStateLog).where(EventStateLog.event_id.in_(event_ids)),
        )
        deleted_counts["aiCallLogs"] = _delete_rowcount(
            db,
            delete(AiCallLog).where(AiCallLog.event_id.in_(event_ids)),
        )
        deleted_counts["elfMessages"] = _delete_rowcount(
            db,
            delete(ElfMessage).where(ElfMessage.event_id.in_(event_ids)),
        )
        deleted_counts["judgeResults"] = _delete_rowcount(
            db,
            delete(JudgeResult).where(JudgeResult.event_id.in_(event_ids)),
        )
        deleted_counts["eventSnapshots"] = _delete_rowcount(
            db,
            delete(EventSnapshot).where(EventSnapshot.event_id.in_(event_ids)),
        )
    deleted_counts["calendarEntries"] = _delete_rowcount(
        db,
        delete(CalendarEntry).where(CalendarEntry.relationship_id == relationship_id),
    )
    if review_ids:
        deleted_counts["reviewVersions"] = _delete_rowcount(
            db,
            delete(ReviewVersion).where(ReviewVersion.review_id.in_(review_ids)),
        )
    deleted_counts["reviews"] = _delete_rowcount(
        db,
        delete(Review).where(Review.relationship_id == relationship_id),
    )
    deleted_counts["events"] = _delete_rowcount(
        db,
        delete(Event).where(Event.relationship_id == relationship_id),
    )
    deleted_counts["relationships"] = _delete_rowcount(
        db,
        delete(Relationship).where(Relationship.id == relationship_id),
    )
    return deleted_counts
