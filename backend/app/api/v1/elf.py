"""Elf 互动路由（3 号）。"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentActiveUser, Db
from app.schemas.common import ApiEnvelope, envelope_success
from app.schemas.elf import ElfRelayRequest, ModerateRequest
from app.services import elf_service

router = APIRouter()


@router.get("/messages", response_model=ApiEnvelope)
def list_messages(
    user: CurrentActiveUser,
    db: Db,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> ApiEnvelope:
    resp = elf_service.list_inbox_messages(db, user_id=user.id, limit=limit)
    return envelope_success(resp.model_dump(by_alias=True))


@router.post("/relay", response_model=ApiEnvelope)
def relay_message(
    body: ElfRelayRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    resp = elf_service.relay_message(
        db,
        user_id=user.id,
        event_public_id=body.event_id,
        target_user_public_id=body.target_user_id,
        raw_message=body.raw_message,
    )
    return envelope_success(resp.model_dump(by_alias=True))


@router.post("/moderate", response_model=ApiEnvelope)
def moderate_message(
    body: ModerateRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    resp = elf_service.moderate_message(
        db, user_id=user.id, raw_message=body.raw_message,
    )
    return envelope_success(resp.model_dump(by_alias=True))
