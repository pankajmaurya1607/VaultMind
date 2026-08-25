import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("eka")


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # exc.errors() can contain non-serializable objects in ctx (e.g. ValueError
    # instances raised by custom pydantic validators) - sanitize them.
    errors = []
    for error in exc.errors():
        clean = {k: v for k, v in error.items() if k != "ctx"}
        if "ctx" in error and isinstance(error["ctx"], dict):
            clean["ctx"] = {k: str(v) for k, v in error["ctx"].items()}
        errors.append(clean)
    return JSONResponse(
        status_code=422,
        content={"detail": errors, "body": exc.body},
    )
