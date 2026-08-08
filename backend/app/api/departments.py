from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.department import Department
from app.models.role import Role
from app.models.user import User

router = APIRouter(prefix="/departments", tags=["Departments"])


class LabelOut(BaseModel):
    id: int
    name: str


@router.get("", response_model=list[LabelOut])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Department).order_by(Department.id))
    return [LabelOut(id=d.id, name=d.name) for d in result.scalars().all()]


@router.get("/roles", response_model=list[LabelOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Role).order_by(Role.id))
    return [LabelOut(id=r.id, name=r.name) for r in result.scalars().all()]
