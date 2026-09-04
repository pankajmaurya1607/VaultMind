from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.department import Department
from app.models.role import Role
from app.models.user import User
from app.rbac.dependencies import require_admin
from app.repositories.department import DepartmentRepository
from app.repositories.role import RoleRepository
from app.schemas.department import DepartmentResponse
from app.schemas.role import RoleResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


class CreateLabelIn(BaseModel):
    name: str


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


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    body: CreateLabelIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    name = body.name.strip()
    if not name or len(name) < 2 or len(name) > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department name must be 2-50 characters")
    existing = await db.execute(select(Department).where(Department.name == name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department already exists")
    dept = Department(name=name)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return DepartmentResponse(id=dept.id, name=dept.name)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: CreateLabelIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    name = body.name.strip()
    if not name or len(name) < 2 or len(name) > 30:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role name must be 2-30 characters")
    # Keep default 3 roles, but allow new ones
    existing = await db.execute(select(Role).where(Role.name == name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
    role = Role(name=name)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return RoleResponse(id=role.id, name=role.name)
