from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.rbac.dependencies import require_admin
from app.repositories.user import UserRepository
from app.schemas.pagination import Paginated
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_with_relations(current_user.id)
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role_id=user.role_id,
        role_name=user.role.name if user.role else None,
        created_at=user.created_at,
    )


@router.get("", response_model=Paginated[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = UserRepository(db)
    users, total = await repo.list_with_total(skip, limit)
    return Paginated[UserResponse](
        items=[
            UserResponse(
                id=u.id,
                name=u.name,
                email=u.email,
                department_id=u.department_id,
                department_name=u.department.name if u.department else None,
                role_id=u.role_id,
                role_name=u.role.name if u.role else None,
                created_at=u.created_at,
            )
            for u in users
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = UserRepository(db)
    updates = body.model_dump(exclude_none=True)
    user = await repo.update(user_id, **updates)
    if not user:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = await repo.get_with_relations(user_id)
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role_id=user.role_id,
        role_name=user.role.name if user.role else None,
        created_at=user.created_at,
    )
