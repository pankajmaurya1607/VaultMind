from fastapi import Response

from app.config.settings import settings

ACCESS_COOKIE = "eka_access"
REFRESH_COOKIE = "eka_refresh"

# Refresh cookie is scoped to the auth endpoints; access cookie is app-wide.
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _cookie_secure() -> bool:
    # Only force Secure over HTTPS deployments; dev/test run on plain HTTP.
    return settings.ENVIRONMENT == "production"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=ACCESS_COOKIE, path="/")
    response.delete_cookie(key=REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
