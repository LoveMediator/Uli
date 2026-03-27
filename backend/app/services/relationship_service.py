from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.orm import Session

from app.constants.error_codes import FORBIDDEN, INVALID_PARAMS, NOT_FOUND
from app.core.config import settings
from app.core.errors import AppError
from app.models.relationship import Relationship
from app.models.user import User
from app.repos import event_repo, relationship_repo, user_repo
from app.constants.enums import EventStatus
from app.schemas.relationship import (
    RelationshipAcceptData,
    RelationshipCancelData,
    RelationshipCancelRequestData,
    RelationshipCurrentEvent,
    RelationshipDeleteCounts,
    RelationshipInviteData,
    RelationshipListData,
    RelationshipSummary,
)
from app.services.analysis_session_store import get_analysis_session_store
from app.utils.ids import generate_public_id

INVITE_TOKEN_TYPE = "relationship_invite"
INVITE_EXPIRE_DAYS = 7
INVITE_FRONTEND_PATH = "/relationship-invite"
CANCEL_TOKEN_TYPE = "relationship_cancel"
CANCEL_EXPIRE_DAYS = 7
CANCEL_FRONTEND_PATH = "/relationship-cancel"


def _create_invite_token(inviter_user_id: int, expires_at: datetime) -> str:
    payload = {
        "sub": str(inviter_user_id),
        "token_type": INVITE_TOKEN_TYPE,
        "iat": datetime.now(tz=UTC),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def _decode_invite_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "token_type"]},
        )
    except jwt.ExpiredSignatureError:
        raise AppError("邀请已过期，请让对方重新发起邀请", code=INVALID_PARAMS) from None
    except jwt.InvalidTokenError:
        raise AppError("邀请无效", code=INVALID_PARAMS) from None

    if payload.get("token_type") != INVITE_TOKEN_TYPE:
        raise AppError("邀请无效", code=INVALID_PARAMS)

    try:
        return int(payload["sub"])
    except (TypeError, ValueError, KeyError):
        raise AppError("邀请无效", code=INVALID_PARAMS) from None


def _create_cancel_token(
    relationship_public_id: str,
    requester_user_id: int,
    expires_at: datetime,
) -> str:
    payload = {
        "sub": str(requester_user_id),
        "relationship_public_id": relationship_public_id,
        "token_type": CANCEL_TOKEN_TYPE,
        "iat": datetime.now(tz=UTC),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def _decode_cancel_token(token: str) -> tuple[str, int]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "relationship_public_id", "token_type"]},
        )
    except jwt.ExpiredSignatureError:
        raise AppError("解除关系确认已过期，请重新发起", code=INVALID_PARAMS) from None
    except jwt.InvalidTokenError:
        raise AppError("解除关系确认无效", code=INVALID_PARAMS) from None

    if payload.get("token_type") != CANCEL_TOKEN_TYPE:
        raise AppError("解除关系确认无效", code=INVALID_PARAMS)

    try:
        return str(payload["relationship_public_id"]), int(payload["sub"])
    except (TypeError, ValueError, KeyError):
        raise AppError("解除关系确认无效", code=INVALID_PARAMS) from None


def _get_user_or_fail(db: Session, user_id: int) -> User:
    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise AppError("用户不存在", code=NOT_FOUND)
    return user


def _get_relationship_or_fail(db: Session, relationship_public_id: str) -> Relationship:
    relationship = relationship_repo.get_relationship_by_public_id(db, relationship_public_id)
    if relationship is None:
        raise AppError("关系不存在", code=NOT_FOUND)
    return relationship


def _assert_relationship_member(relationship: Relationship, user_id: int) -> None:
    if user_id not in (relationship.user_a_id, relationship.user_b_id):
        raise AppError("无权操作该关系", code=FORBIDDEN)


def _build_current_event_summary(event: object, current_user_id: int) -> RelationshipCurrentEvent:
    pending_action = "respond" if getattr(event, "initiator_user_id", None) != current_user_id else "wait_partner"
    if getattr(event, "status", None) == EventStatus.DRAFT:
        pending_action = (
            "continue_analysis"
            if getattr(event, "initiator_user_id", None) == current_user_id
            else "wait_partner"
        )
    return RelationshipCurrentEvent(
        eventId=getattr(event, "public_id"),
        status=getattr(getattr(event, "status"), "value", getattr(event, "status")),
        pendingAction=pending_action,
        title=getattr(event, "title", None),
    )


def _build_summary(
    db: Session,
    relationship: Relationship,
    current_user_id: int,
    partner: User,
) -> RelationshipSummary:
    open_event = event_repo.get_open_event_for_relationship(db, relationship.id)
    current_event = None
    if open_event is not None:
        current_event = _build_current_event_summary(open_event, current_user_id)
    return RelationshipSummary(
        relationshipId=relationship.public_id,
        partnerUserId=partner.public_id,
        partnerUsername=partner.username,
        status=relationship.status.value,
        currentEvent=current_event,
    )


def create_relationship_invite(current_user: User) -> RelationshipInviteData:
    expires_at = datetime.now(tz=UTC) + timedelta(days=INVITE_EXPIRE_DAYS)
    invite_token = _create_invite_token(current_user.id, expires_at)
    return RelationshipInviteData(
        inviteToken=invite_token,
        inviteUrl=f"{INVITE_FRONTEND_PATH}?token={invite_token}",
        expiresAt=expires_at,
    )


def accept_relationship_invite(
    db: Session,
    current_user: User,
    invite_token: str,
) -> RelationshipAcceptData:
    inviter_user_id = _decode_invite_token(invite_token)
    if inviter_user_id == current_user.id:
        raise AppError("不能接受自己发出的邀请", code=INVALID_PARAMS)

    inviter = _get_user_or_fail(db, inviter_user_id)
    existing = relationship_repo.get_active_relationship_between_users(
        db,
        inviter.id,
        current_user.id,
    )
    relationship = existing
    if relationship is None:
        relationship = relationship_repo.create_relationship(
            db,
            public_id=generate_public_id(),
            user_a_id=inviter.id,
            user_b_id=current_user.id,
        )
        db.commit()
        db.refresh(relationship)

    return RelationshipAcceptData(
        relationshipId=relationship.public_id,
        partnerUserId=inviter.public_id,
        partnerUsername=inviter.username,
        status=relationship.status.value,
    )


def list_relationships(
    db: Session,
    current_user: User,
) -> RelationshipListData:
    items: list[RelationshipSummary] = []
    for relationship in relationship_repo.list_relationships_for_user(db, current_user.id):
        partner_user_id = (
            relationship.user_b_id
            if relationship.user_a_id == current_user.id
            else relationship.user_a_id
        )
        partner = _get_user_or_fail(db, partner_user_id)
        items.append(_build_summary(db, relationship, current_user.id, partner))
    return RelationshipListData(items=items)


def create_relationship_cancel_request(
    db: Session,
    current_user: User,
    relationship_public_id: str,
) -> RelationshipCancelRequestData:
    relationship = _get_relationship_or_fail(db, relationship_public_id)
    _assert_relationship_member(relationship, current_user.id)

    expires_at = datetime.now(tz=UTC) + timedelta(days=CANCEL_EXPIRE_DAYS)
    cancel_token = _create_cancel_token(relationship.public_id, current_user.id, expires_at)
    return RelationshipCancelRequestData(
        cancelToken=cancel_token,
        cancelUrl=f"{CANCEL_FRONTEND_PATH}?relationshipId={relationship.public_id}&token={cancel_token}",
        expiresAt=expires_at,
    )


def confirm_relationship_cancel(
    db: Session,
    current_user: User,
    relationship_public_id: str,
    cancel_token: str,
) -> RelationshipCancelData:
    token_relationship_public_id, requester_user_id = _decode_cancel_token(cancel_token)
    if token_relationship_public_id != relationship_public_id:
        raise AppError("解除关系确认无效", code=INVALID_PARAMS)
    if requester_user_id == current_user.id:
        raise AppError("需要由另一方确认后才能解除关系", code=INVALID_PARAMS)

    relationship = _get_relationship_or_fail(db, relationship_public_id)
    _assert_relationship_member(relationship, current_user.id)
    _assert_relationship_member(relationship, requester_user_id)

    get_analysis_session_store().clear_sessions_for_relationship(relationship.public_id)
    deleted_counts = relationship_repo.delete_relationship_graph(db, relationship.id)
    db.commit()

    return RelationshipCancelData(
        relationshipId=relationship_public_id,
        deletedCounts=RelationshipDeleteCounts(**deleted_counts),
        deletedAt=datetime.now(tz=UTC),
    )
