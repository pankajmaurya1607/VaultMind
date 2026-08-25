from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.auth.cookies import ACCESS_COOKIE
from app.auth.jwt import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.auth import AuthRepository

# auto_error=False so cookie-authenticated browser requests (no Authorization
# header) don't get rejected before we can fall back to the access cookie.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_401_HEADERS = {"WWW-Authenticate": "Bearer"}


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers=_401_HEADERS)


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # HttpOnly cookie first (browser flow), Bearer header fallback (API clients/tests).
    raw_token = request.cookies.get(ACCESS_COOKIE) or token
    if not raw_token:
        raise _unauthorized("Not authenticated")

    payload = decode_token(raw_token)
    if payload is None or payload.get("type") != "access":
        raise _unauthorized("Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise _unauthorized("Invalid token payload")

    jti = payload.get("jti")
    if jti:
        auth_repo = AuthRepository(db)
        if await auth_repo.is_blacklisted(jti):
            raise _unauthorized("Token has been revoked")

    result = await db.execute(
        select(User).options(joinedload(User.role), joinedload(User.department)).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    try:
        return await get_current_user(request, token, db)
    except HTTPException:
        return None
