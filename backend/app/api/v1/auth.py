from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.deps import Db
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
    db: Db,
) -> ApiEnvelope:
    user = auth_service.register_user(db, username=body.username, password=body.password)
    data = RegisterData(userId=user.id, publicId=user.public_id)
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/login", response_model=ApiEnvelope)
def login(
    body: LoginRequest,
    request: Request,
    db: Db,
) -> ApiEnvelope:
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
        accessToken=access_token,
        refreshToken=refresh_token,
        tokenType="bearer",
        userId=user.id,
        publicId=user.public_id,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/refresh", response_model=ApiEnvelope)
def refresh(
    body: RefreshRequest,
    db: Db,
) -> ApiEnvelope:
    access_token = auth_service.refresh_access_token(db, refresh_token=body.refresh_token)
    user_id = security.decode_access_token(access_token)
    data = AccessTokenData(accessToken=access_token, tokenType="bearer", userId=user_id)
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/logout", response_model=ApiEnvelope)
def logout(
    body: LogoutRequest,
    db: Db,
) -> ApiEnvelope:
    revoked = auth_service.logout_refresh_token(db, refresh_token=body.refresh_token)
    data = LogoutData(revoked=revoked)
    return envelope_success(data.model_dump(by_alias=True))
