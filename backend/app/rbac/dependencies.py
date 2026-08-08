from typing import List

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.models.user import User


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.name}' not authorized. Required: {self.allowed_roles}",
            )
        return current_user


def get_effective_department_ids(user: User) -> List[int]:
    if user.role.name == "Admin":
        return []
    return [user.department_id]


require_admin = RoleChecker(["Admin"])
require_manager = RoleChecker(["Admin", "Manager"])
require_employee = RoleChecker(["Admin", "Manager", "Employee"])
