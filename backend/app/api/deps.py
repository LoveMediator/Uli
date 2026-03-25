from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.constants.enums import UserStatus
from app.core.errors import AccountLockedOrDisabledError, AuthError
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.repos import user_repo

bearer_scheme = HTTPBearer(auto_error=False)


PUBLIC_ID_MAX_LENGTH = 40


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """从 `Authorization: Bearer <access_jwt>` 解析用户。无效/过期 → `AuthError`（2001）。"""
    if creds is None or (creds.scheme or "").lower() != "bearer":
        raise AuthError("未登录或凭证无效")
    token = creds.credentials.strip()
    if not token:
        raise AuthError("未登录或凭证无效")

    user_id = decode_access_token(token)
    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise AuthError("用户不存在")
    return user


def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """在已认证用户基础上要求 `status == active`，否则 2003。"""
    if user.status != UserStatus.ACTIVE:
        raise AccountLockedOrDisabledError("账号已锁定或禁用")
    return user


Db = Annotated[Session, Depends(get_db)]
PublicId = Annotated[str, Path(max_length=PUBLIC_ID_MAX_LENGTH)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
