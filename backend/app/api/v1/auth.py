from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.schemas.auth import (
    AccessTokenData,
    AuthTokensData,
    RegisterData,
    LoginRequest,
    LogoutData,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.schemas.common import ApiEnvelope, envelope_success
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=ApiEnvelope)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    user = auth_service.register_user(db, username=body.username, password=body.password)
    data = RegisterData(user_id=user.id, public_id=user.public_id)
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/login", response_model=ApiEnvelope)
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ip = None
    if request.client is not None:
        ip = request.client.host
    user_agent = request.headers.get("user-agent")

    access_token, refresh_token, user = auth_service.login_user(
        db,
        username=body.username,
        password=body.password,
        ip=ip,
        user_agent=user_agent,
    )

    data = AuthTokensData(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        public_id=user.public_id,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/refresh", response_model=ApiEnvelope)
def refresh(
    body: RefreshRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    # 仅刷新 access token（refresh token 明文由客户端保管，服务端按 hash 校验）
    access_token = auth_service.refresh_access_token(db, refresh_token=body.refresh_token)
    user_id = security.decode_access_token(access_token)
    data = AccessTokenData(access_token=access_token, token_type="bearer", user_id=user_id)
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/logout", response_model=ApiEnvelope)
def logout(
    body: LogoutRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    revoked = auth_service.logout_refresh_token(db, refresh_token=body.refresh_token)
    data = LogoutData(revoked=revoked)
    return envelope_success(data.model_dump(by_alias=True))
