from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.event import Event
from app.models.judge import JudgeResult
from app.models.relationship import Relationship
from app.models.snapshot import EventSnapshot
from app.models.user import User
from app.constants.enums import EventStatus, RelationshipStatus, SnapshotSide, UserStatus
from app.utils.ids import generate_public_id


# 为了可重复执行（幂等），seed 使用固定 public_id + username。
SEED_USER_A = {"username": "alice", "public_id": "u_seed_a_1", "password": "Secret123!"}
SEED_USER_B = {"username": "bob", "public_id": "u_seed_b_1", "password": "Secret123!"}
SEED_RELATIONSHIP = {"public_id": "r_seed_ab_1", "status": RelationshipStatus.ACTIVE}
SEED_EVENT_DRAFT = {"public_id": "e_seed_draft_1", "status": EventStatus.DRAFT, "title": "seed draft"}
SEED_EVENT_WAITING_B = {
    "public_id": "e_seed_waiting_b_1",
    "status": EventStatus.WAITING_B,
    "title": "seed waiting_b",
}

# 可选：用于后续联调快速跳转
SEED_EVENT_JUDGED = {"public_id": "e_seed_judged_1", "status": EventStatus.JUDGED, "title": "seed judged"}
SEED_EVENT_REVIEWED = {
    "public_id": "e_seed_reviewed_1",
    "status": EventStatus.REVIEWED,
    "title": "seed reviewed",
}


def _get_user_by_username(db: Session, *, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalar_one_or_none()


def _get_user_by_public_id(db: Session, *, public_id: str) -> User | None:
    stmt = select(User).where(User.public_id == public_id)
    return db.execute(stmt).scalar_one_or_none()


def ensure_user(db: Session, *, username: str, public_id: str, password: str) -> User:
    existing = _get_user_by_username(db, username=username) or _get_user_by_public_id(db, public_id=public_id)
    if existing is not None:
        return existing

    user = User(
        public_id=public_id,
        username=username,
        password_hash=hash_password(password),
        status=UserStatus.ACTIVE,
        failed_login_count=0,
        locked_until=None,
        last_login_at=None,
    )
    db.add(user)
    db.flush()
    return user


def ensure_relationship(db: Session, *, public_id: str, user_a_id: int, user_b_id: int) -> Relationship:
    stmt = select(Relationship).where(Relationship.public_id == public_id)
    rel = db.execute(stmt).scalar_one_or_none()
    if rel is not None:
        return rel

    rel = Relationship(
        public_id=public_id,
        user_a_id=user_a_id,
        user_b_id=user_b_id,
        status=SEED_RELATIONSHIP["status"],
    )
    db.add(rel)
    db.flush()
    return rel


def ensure_event(
    db: Session,
    *,
    public_id: str,
    relationship_id: int,
    initiator_user_id: int,
    status: EventStatus,
    title: str | None,
) -> Event:
    stmt = select(Event).where(Event.public_id == public_id)
    event = db.execute(stmt).scalar_one_or_none()
    if event is not None:
        # 保证状态一致，方便反复 seed
        event.status = status
        event.title = title
        if status == EventStatus.JUDGED:
            event.judged_at = datetime.now(tz=UTC)
        if status == EventStatus.REVIEWED:
            event.reviewed_at = datetime.now(tz=UTC)
        return event

    event = Event(
        public_id=public_id,
        relationship_id=relationship_id,
        initiator_user_id=initiator_user_id,
        title=title,
        status=status,
    )
    if status == EventStatus.JUDGED:
        event.judged_at = datetime.now(tz=UTC)
    if status == EventStatus.REVIEWED:
        event.reviewed_at = datetime.now(tz=UTC)

    db.add(event)
    db.flush()
    return event


def _ensure_snapshot(
    db: Session,
    *,
    event_id: int,
    side: SnapshotSide,
    confirmed_by_user_id: int,
    summary: str,
    points_a: list[str],
    points_b: list[str],
) -> EventSnapshot:
    stmt = select(EventSnapshot).where(EventSnapshot.event_id == event_id, EventSnapshot.side == side)
    snap = db.execute(stmt).scalar_one_or_none()
    if snap is not None:
        return snap

    snap = EventSnapshot(
        public_id=generate_public_id(),
        event_id=event_id,
        side=side,
        summary=summary,
        points_a=points_a,
        points_b=points_b,
        is_frozen=True,
        confirmed_by_user_id=confirmed_by_user_id,
    )
    db.add(snap)
    db.flush()
    return snap


def _ensure_judge_result(
    db: Session,
    *,
    event_id: int,
    objective_summary: str,
    triggers: list[str],
    misunderstandings: list[str],
    advice_for_a: list[str],
    advice_for_b: list[str],
) -> JudgeResult:
    stmt = select(JudgeResult).where(JudgeResult.event_id == event_id)
    judge = db.execute(stmt).scalar_one_or_none()
    if judge is not None:
        return judge

    judge = JudgeResult(
        public_id=generate_public_id(),
        event_id=event_id,
        objective_summary=objective_summary,
        triggers=triggers,
        misunderstandings=misunderstandings,
        advice_for_a=advice_for_a,
        advice_for_b=advice_for_b,
    )
    db.add(judge)
    db.flush()
    return judge


def seed_db() -> None:
    db = SessionLocal()
    try:
        user_a = ensure_user(db, **SEED_USER_A)
        user_b = ensure_user(db, **SEED_USER_B)

        rel = ensure_relationship(
            db,
            public_id=SEED_RELATIONSHIP["public_id"],
            user_a_id=user_a.id,
            user_b_id=user_b.id,
        )

        # A：draft
        ensure_event(
            db,
            public_id=SEED_EVENT_DRAFT["public_id"],
            relationship_id=rel.id,
            initiator_user_id=user_a.id,
            status=SEED_EVENT_DRAFT["status"],
            title=SEED_EVENT_DRAFT["title"],
        )

        # A 提交后：waiting_b（含 Snapshot_A）
        ev_wb = ensure_event(
            db,
            public_id=SEED_EVENT_WAITING_B["public_id"],
            relationship_id=rel.id,
            initiator_user_id=user_a.id,
            status=SEED_EVENT_WAITING_B["status"],
            title=SEED_EVENT_WAITING_B["title"],
        )
        # 确保 waiting_b 事件有 Snapshot_A
        _ensure_snapshot(
            db,
            event_id=ev_wb.id,
            side=SnapshotSide.A,
            confirmed_by_user_id=user_a.id,
            summary="seed: alice 认为双方因家务分工产生分歧，争吵发生在厨房。",
            points_a=["我认为应该轮流做饭", "我觉得她不够公平"],
            points_b=["她认为我应该每天做饭", "她觉得我不够体贴"],
        )

        # 可选：judged（含 Snapshot_A + Snapshot_B + JudgeResult）
        ev_j = ensure_event(
            db,
            public_id=SEED_EVENT_JUDGED["public_id"],
            relationship_id=rel.id,
            initiator_user_id=user_a.id,
            status=SEED_EVENT_JUDGED["status"],
            title=SEED_EVENT_JUDGED["title"],
        )
        _ensure_snapshot(
            db,
            event_id=ev_j.id,
            side=SnapshotSide.A,
            confirmed_by_user_id=user_a.id,
            summary="seed: alice 认为因外出计划产生矛盾。",
            points_a=["我想周末去爬山", "我提前一周说了"],
            points_b=["她想周末休息", "她说我没提前说"],
        )
        _ensure_snapshot(
            db,
            event_id=ev_j.id,
            side=SnapshotSide.B,
            confirmed_by_user_id=user_b.id,
            summary="seed: bob 认为 alice 临时改变计划。",
            points_a=["她想去爬山但我太累了", "她没有考虑我的感受"],
            points_b=["我只想在家休息", "我觉得她总是自作主张"],
        )
        _ensure_judge_result(
            db,
            event_id=ev_j.id,
            objective_summary="seed: 双方因周末计划不一致产生矛盾，核心在于沟通不充分。",
            triggers=["计划冲突", "沟通不足"],
            misunderstandings=["alice 以为 bob 同意了", "bob 以为 alice 会改主意"],
            advice_for_a=["提前协商", "尊重对方的休息需求"],
            advice_for_b=["明确表达需求", "不要消极回避"],
        )

        # reviewed
        ensure_event(
            db,
            public_id=SEED_EVENT_REVIEWED["public_id"],
            relationship_id=rel.id,
            initiator_user_id=user_a.id,
            status=SEED_EVENT_REVIEWED["status"],
            title=SEED_EVENT_REVIEWED["title"],
        )

        db.commit()
        print("seed_db: done")
        print(f"  user_a: {user_a.id} ({user_a.username})")
        print(f"  user_b: {user_b.id} ({user_b.username})")
        print(f"  relationship: {rel.id} ({rel.public_id})")
    finally:
        db.close()


if __name__ == "__main__":
    # 打印配置不暴露 SECRET_KEY，只给出环境信息，便于排错。
    print(f"seed_db: start (DEBUG={settings.debug})")
    seed_db()

