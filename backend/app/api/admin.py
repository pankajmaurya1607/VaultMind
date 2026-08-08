from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.rbac.dependencies import require_admin
from app.repositories.audit import AuditLogRepository
from app.schemas.audit import AuditLogResponse
from app.schemas.monitoring import SystemMetrics
from app.services.monitoring import MonitoringService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/metrics", response_model=SystemMetrics)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = MonitoringService(db)
    return await service.get_metrics()


@router.get("/audit", response_model=list[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = AuditLogRepository(db)
    logs = await repo.list_recent(limit)
    return [
        AuditLogResponse(
            id=log.id,
            user_email=log.user_email,
            action=log.action,
            resource=log.resource,
            details=log.details,
            ip_address=log.ip_address,
            success=log.success,
            created_at=log.created_at,
        )
        for log in logs
    ]
