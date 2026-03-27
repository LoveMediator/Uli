"""EventSnapshot 数据访问。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.enums import SnapshotSide
from app.models.snapshot import EventSnapshot


def get_snapshot_by_event_and_side(
    db: Session,
    event_id: int,
    side: SnapshotSide,
) -> EventSnapshot | None:
    stmt = select(EventSnapshot).where(
        EventSnapshot.event_id == event_id,
        EventSnapshot.side == side,
    )
    return db.execute(stmt).scalar_one_or_none()


def create_snapshot(
    db: Session,
    *,
    public_id: str,
    event_id: int,
    side: SnapshotSide,
    summary: str,
    points_a: list[str],
    points_b: list[str],
    raw_payload: dict | None = None,
    confirmed_by_user_id: int,
) -> EventSnapshot:
    snapshot = EventSnapshot(
        public_id=public_id,
        event_id=event_id,
        side=side,
        summary=summary,
        points_a=points_a,
        points_b=points_b,
        raw_payload=raw_payload,
        confirmed_by_user_id=confirmed_by_user_id,
        is_frozen=True,
    )
    db.add(snapshot)
    db.flush()
    return snapshot
