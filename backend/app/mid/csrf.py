import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth.cookies import ACCESS_COOKIE, REFRESH_COOKIE

logger = logging.getLogger("eka")

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_HEADER = "x-requested-with"
CSRF_HEADER_VALUE = "XMLHttpRequest"

# Pre-auth / token-issuing endpoints: a stale session cookie must never block
# login/register/refresh/logout flows.
EXEMPT_PREFIXES = ("/api/v1/auth/",)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Defense-in-depth CSRF guard for cookie-based auth.

    Bearer-token clients (scripts, tests) are exempt: they present an
    Authorization header, which browsers never attach cross-site. Browser
    clients authenticated via HttpOnly cookies must send the custom
    X-Requested-With header on state-changing requests - a cross-site
    attacker cannot set custom headers on form/flash submissions.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method in SAFE_METHODS:
            return await call_next(request)

        if any(request.url.path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)

        has_auth_header = bool(request.headers.get("authorization"))
        has_auth_cookie = ACCESS_COOKIE in request.cookies or REFRESH_COOKIE in request.cookies

        if has_auth_cookie and not has_auth_header:
            header_value = request.headers.get(CSRF_HEADER)
            if header_value != CSRF_HEADER_VALUE:
                logger.warning(
                    "CSRF check failed for %s %s from %s",
                    request.method,
                    request.url.path,
                    request.client.host if request.client else "unknown",
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Missing CSRF protection header"},
                )

        return await call_next(request)
