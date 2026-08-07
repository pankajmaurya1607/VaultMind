import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.settings import settings

try:
    import redis.asyncio as aioredis
    _redis_available = True
except ImportError:
    _redis_available = False


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._redis = None
        self._local_requests: dict[str, list[float]] = {}

    async def _get_redis(self):
        if not _redis_available:
            return None
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60
        limit = settings.RATE_LIMIT_PER_MINUTE
        key = f"ratelimit:{client_ip}"

        redis = await self._get_redis()
        if redis:
            try:
                await redis.zremrangebyscore(key, 0, now - window)
                count = await redis.zcard(key)
                if count >= limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Try again later.",
                    )
                await redis.zadd(key, {str(now): now})
                await redis.expire(key, window)
                return await call_next(request)
            except HTTPException:
                raise
            except Exception:
                pass

        timestamps = self._local_requests.setdefault(client_ip, [])
        timestamps[:] = [t for t in timestamps if now - t < window]
        if len(timestamps) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )
        timestamps.append(now)
        return await call_next(request)
