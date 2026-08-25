from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.cookies import ACCESS_COOKIE, REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.audit import audit_event
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    tokens = await service.register(body.name, body.email, body.password, body.department_id)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    await audit_event(request, db, action="register", resource="user", details=body.email, user_email=body.email)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        tokens = await service.login(body.email, body.password)
    except Exception:
        await audit_event(
            request,
            db,
            action="login_failed",
            resource="auth",
            details=body.email,
            user_email=body.email,
            success=False,
        )
        raise
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    await audit_event(request, db, action="login", resource="auth", details=body.email, user_email=body.email)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    authorization: str = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    # Cookie first (browser flow); fall back to body/header (API clients).
    refresh_token = request.cookies.get(REFRESH_COOKIE) or (body.refresh_token if body else None)
    if not refresh_token and authorization:
        refresh_token = authorization.removeprefix("Bearer ").strip()
    if not refresh_token:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    current_access_token = request.cookies.get(ACCESS_COOKIE)
    tokens = await service.refresh(refresh_token, current_access_token)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return tokens


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    authorization: str = Header(default=None),
    x_refresh_token: str = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    access_token = (
        request.cookies.get(ACCESS_COOKIE)
        or (authorization.removeprefix("Bearer ").strip() if authorization else "")
    )
    refresh_token = request.cookies.get(REFRESH_COOKIE) or x_refresh_token or ""
    result = await service.logout(access_token, refresh_token)
    clear_auth_cookies(response)
    await audit_event(request, db, action="logout", resource="auth")
    return result
