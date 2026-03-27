from fastapi import APIRouter

from app.api.deps import CurrentActiveUser, Db, PublicId
from app.schemas.common import ApiEnvelope, envelope_success
from app.schemas.relationship import (
    RelationshipAcceptRequest,
    RelationshipCancelConfirmRequest,
)
from app.services import analysis_session_chat_service as analysis_session_service
from app.services import relationship_service

router = APIRouter()


@router.get("", response_model=ApiEnvelope)
def list_relationships(
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    data = relationship_service.list_relationships(db, user)
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/invite", response_model=ApiEnvelope)
def create_relationship_invite(
    user: CurrentActiveUser,
) -> ApiEnvelope:
    data = relationship_service.create_relationship_invite(user)
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/accept", response_model=ApiEnvelope)
def accept_relationship_invite(
    body: RelationshipAcceptRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    data = relationship_service.accept_relationship_invite(db, user, body.invite_token)
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{relationship_id}/analysis-sessions/a", response_model=ApiEnvelope)
def start_a_analysis_session(
    relationship_id: PublicId,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    data = analysis_session_service.start_a_analysis_session(
        db,
        current_user=user,
        relationship_public_id=relationship_id,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{relationship_id}/cancel-request", response_model=ApiEnvelope)
def create_relationship_cancel_request(
    relationship_id: PublicId,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    data = relationship_service.create_relationship_cancel_request(db, user, relationship_id)
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{relationship_id}/cancel-confirm", response_model=ApiEnvelope)
def confirm_relationship_cancel(
    relationship_id: PublicId,
    body: RelationshipCancelConfirmRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    data = relationship_service.confirm_relationship_cancel(
        db,
        user,
        relationship_id,
        body.cancel_token,
    )
    return envelope_success(data.model_dump(by_alias=True))
