import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.monitoring.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.services.audit import log_request

logger = logging.getLogger("eka")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(duration_ms)

        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms) "
            f"[{request.client.host if request.client else 'unknown'}]"
        )
        return response
