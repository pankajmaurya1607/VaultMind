"""Security regression tests for role assignment at registration.

A caller must never be able to self-assign a privileged role: registration
pins the Employee role server-side, ignoring any client-supplied role_id.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.schemas.auth import RegisterRequest
from app.services.auth import AuthService

pytestmark = pytest.mark.security


def _service_with_role(role):
    db = AsyncMock()
    service = AuthService(db)
    service.user_repo = AsyncMock()
    service.role_repo = AsyncMock()
    service.user_repo.get_by_email = AsyncMock(return_value=None)
    service.user_repo.create = AsyncMock(
        side_effect=lambda **kwargs: MagicMock(id=1, **kwargs)
    )
    service.role_repo.get_by_name = AsyncMock(return_value=role)
    return service


class TestRegistrationRoleAssignment:
    @pytest.mark.asyncio
    async def test_register_request_schema_has_no_role_field(self):
        assert "role_id" not in RegisterRequest.model_fields

    @pytest.mark.asyncio
    async def test_register_pins_employee_role(self):
        employee = MagicMock(id=3, name="Employee")
        service = _service_with_role(employee)

        await service.register("Alice", "a@x.com", "secret123", department_id=2)

        _, kwargs = service.user_repo.create.call_args
        assert kwargs["role_id"] == 3

    @pytest.mark.asyncio
    async def test_register_ignores_client_supplied_admin_role(self):
        """Even if a role object were injected, only Employee lookup is used."""
        admin = MagicMock(id=1, name="Admin")
        employee = MagicMock(id=3, name="Employee")
        service = _service_with_role(employee)

        await service.register("Bob", "b@x.com", "secret123", department_id=2)

        service.role_repo.get_by_name.assert_called_once_with("Employee")
        _, kwargs = service.user_repo.create.call_args
        assert kwargs["role_id"] == employee.id
        assert kwargs["role_id"] != admin.id

    @pytest.mark.asyncio
    async def test_register_fails_closed_when_roles_unseeded(self):
        service = _service_with_role(None)
        service.role_repo.get_by_name = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await service.register("Cara", "c@x.com", "secret123", department_id=2)
        assert exc.value.status_code == 503
