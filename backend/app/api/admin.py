from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.department import Department
from app.models.role import Role
from app.models.user import User
from app.rbac.dependencies import require_admin
from app.repositories.audit import AuditLogRepository
from app.repositories.department import DepartmentRepository
from app.repositories.role import RoleRepository
from app.schemas.audit import AuditLogResponse
from app.schemas.department import DepartmentResponse
from app.schemas.monitoring import SystemMetrics
from app.schemas.role import RoleResponse
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


@router.get("/departments", response_model=list[DepartmentResponse])
async def get_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = DepartmentRepository(db)
    departments = await repo.list()
    return [
        DepartmentResponse(id=d.id, name=d.name) for d in departments
    ]


@router.get("/roles", response_model=list[RoleResponse])
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = RoleRepository(db)
    roles = await repo.list()
    return [RoleResponse(id=r.id, name=r.name) for r in roles]
