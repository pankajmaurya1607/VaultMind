from unittest.mock import MagicMock
from app.models.department import Department
from app.models.role import Role
from app.models.user import User
from app.rbac.dependencies import get_effective_department_ids


def test_effective_department_ids_admin():
    admin_role = Role(id=1, name="Admin")
    admin_user = User(id=1, name="Admin", role=admin_role, department_id=2)

    dept_ids = get_effective_department_ids(admin_user)
    # Admins have access to all departments (represented by empty list filter)
    assert dept_ids == []


def test_effective_department_ids_employee():
    employee_role = Role(id=3, name="Employee")
    employee_user = User(id=2, name="Emp", role=employee_role, department_id=5)

    dept_ids = get_effective_department_ids(employee_user)
    # Non-admins are scoped only to their department
    assert dept_ids == [5]
