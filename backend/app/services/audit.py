import logging

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit import AuditLogRepository

logger = logging.getLogger("eka")


class AuditService:
    def __init__(self, db: AsyncSession):
        self.repo = AuditLogRepository(db)

    async def log(
        self,
        user_id: int | None,
        user_email: str | None,
        action: str,
        resource: str,
        resource_id: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
        success: bool = True,
    ):
        await self.repo.create(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            success=1 if success else 0,
        )

    @staticmethod
    def get_client_ip(request: Request) -> str:
        from app.config.settings import settings

        if settings.TRUST_PROXY_HEADERS:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


async def audit_event(
    request: Request,
    db: AsyncSession,
    *,
    action: str,
    resource: str,
    resource_id: str | None = None,
    details: str | None = None,
    user_id: int | None = None,
    user_email: str | None = None,
    success: bool = True,
) -> None:
    """Best-effort audit write - must never break the main request flow.

    Commits immediately because audit rows are most critical exactly when
    the surrounding request fails and its transaction gets rolled back
    (failed logins, RBAC denials).
    """
    try:
        service = AuditService(db)
        await service.log(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details,
            ip_address=service.get_client_ip(request),
            success=success,
        )
        await db.commit()
    except Exception as exc:
        logger.warning("Audit write failed for %s/%s: %s", action, resource, exc)
        try:
            await db.rollback()
        except Exception:
            pass


async def log_request(
    request: Request, db: AsyncSession, user_id: int | None, action: str, resource: str, success: bool = True
):
    await audit_event(request, db, action=action, resource=resource, user_id=user_id, success=success)
