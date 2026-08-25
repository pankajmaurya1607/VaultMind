import logging
import time
from collections import OrderedDict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config.settings import settings

logger = logging.getLogger("eka")

try:
    import redis.asyncio as aioredis

    _redis_available = True
except ImportError:  # pragma: no cover - optional dependency path
    _redis_available = False

_WINDOW_SECONDS = 60
_LOCAL_FALLBACK_MAX_CLIENTS = 10_000


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding-window rate limiter (multi-worker safe).

    - 429 responses are returned directly (raising inside BaseHTTPMiddleware
      would bubble up as a 500 via ServerErrorMiddleware).
    - Client IP resolution honors X-Forwarded-For only when
      TRUST_PROXY_HEADERS is enabled (i.e. deployed behind a known proxy);
      otherwise a client could spoof the header to rotate buckets.
    - Redis outages degrade to a bounded in-memory limiter per process and
      log exactly once instead of silently disabling limiting.
    """

    def __init__(self, app):
        super().__init__(app)
        self._redis = None
        self._local_requests: OrderedDict[str, list[float]] = OrderedDict()
        self._degraded_logged = False

    async def _get_redis(self):
        if not _redis_available:
            return None
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    @staticmethod
    def _client_ip(request: Request) -> str:
        if settings.TRUST_PROXY_HEADERS:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if settings.ENVIRONMENT == "testing":
            return await call_next(request)

        limit = settings.RATE_LIMIT_PER_MINUTE
        key = f"ratelimit:{self._client_ip(request)}"

        redis = await self._get_redis()
        if redis is not None:
            try:
                allowed = await self._check_redis(redis, key, limit)
                return await self._finalize(allowed, call_next, request)
            except Exception as exc:
                if not self._degraded_logged:
                    logger.warning("Rate-limit Redis unavailable (%s); degrading to in-memory limiter", exc)
                    self._degraded_logged = True

        allowed = self._check_local(key, limit)
        return await self._finalize(allowed, call_next, request)

    async def _check_redis(self, redis, key: str, limit: int) -> bool:
        now = time.time()
        await redis.zremrangebyscore(key, 0, now - _WINDOW_SECONDS)
        count = await redis.zcard(key)
        if count >= limit:
            return False
        await redis.zadd(key, {str(now): now})
        await redis.expire(key, _WINDOW_SECONDS)
        return True

    def _check_local(self, key: str, limit: int) -> bool:
        now = time.time()
        timestamps = self._local_requests.setdefault(key, [])
        timestamps[:] = [t for t in timestamps if now - t < _WINDOW_SECONDS]
        if len(timestamps) >= limit:
            # Keep the entry fresh so LRU ordering reflects activity.
            self._local_requests.move_to_end(key)
            return False
        timestamps.append(now)
        self._local_requests.move_to_end(key)
        while len(self._local_requests) > _LOCAL_FALLBACK_MAX_CLIENTS:
            self._local_requests.popitem(last=False)
        return True

    async def _finalize(self, allowed: bool, call_next, request: Request):
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )
        return await call_next(request)
