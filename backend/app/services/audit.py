from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit import AuditLogRepository


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
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


async def log_request(
    request: Request, db: AsyncSession, user_id: int | None, action: str, resource: str, success: bool = True
):
    audit = AuditService(db)
    await audit.log(
        user_id=user_id,
        user_email=None,
        action=action,
        resource=resource,
        ip_address=audit.get_client_ip(request),
        success=success,
    )
