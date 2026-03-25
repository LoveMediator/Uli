"""Elf 互动路由（3 号）。"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentActiveUser, Db
from app.schemas.common import ApiEnvelope, envelope_success
from app.schemas.elf import ElfRelayRequest, ModerateRequest
from app.services import elf_service

router = APIRouter()


@router.post("/relay", response_model=ApiEnvelope)
def relay_message(
    body: ElfRelayRequest,
    user: CurrentActiveUser,
    db: Db,
) -> dict[str, Any]:
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
) -> dict[str, Any]:
    resp = elf_service.moderate_message(
        db, user_id=user.id, raw_message=body.raw_message,
    )
    return envelope_success(resp.model_dump(by_alias=True))
