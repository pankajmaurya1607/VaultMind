"""Integration tests for Docker Compose setup.

These tests verify that all services in docker-compose.yml are properly
configured and can communicate with each other.

Tests follow TDD approach:
- Red: Write failing test
- Green: Make test pass
- Refactor: Improve code while keeping tests green
"""

import re
from pathlib import Path

import pytest
from httpx import AsyncClient

# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
]


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent.parent


class TestDockerComposeConfiguration:
    """Test Docker Compose configuration files exist and are valid."""

    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists in project root."""
        compose_path = get_project_root() / "docker-compose.yml"
        assert compose_path.exists(), f"docker-compose.yml not found at {compose_path}"

    def test_docker_compose_valid_structure(self):
        """Test that docker-compose.yml has valid structure."""
        compose_path = get_project_root() / "docker-compose.yml"
        content = compose_path.read_text()

        # Check for required sections
        assert "services:" in content, "docker-compose.yml must define services"
        assert "postgres:" in content, "docker-compose.yml must define postgres service"
        assert "redis:" in content, "docker-compose.yml must define redis service"
        assert "backend:" in content, "docker-compose.yml must define backend service"
        assert "celery_worker:" in content, "docker-compose.yml must define celery_worker service"

    def test_postgres_health_check_configured(self):
        """Test that PostgreSQL has health check configured."""
        compose_path = get_project_root() / "docker-compose.yml"
        content = compose_path.read_text()

        # Check for healthcheck in postgres section
        postgres_section = content.split("postgres:")[1].split("\n\n")[0] if "postgres:" in content else ""
        assert "healthcheck:" in postgres_section, "PostgreSQL must have health check configured"
        assert "pg_isready" in postgres_section, "PostgreSQL health check must use pg_isready"

    def test_redis_health_check_configured(self):
        """Test that Redis has health check configured."""
        compose_path = get_project_root() / "docker-compose.yml"
        content = compose_path.read_text()

        # Check for healthcheck in redis section using regex
        match = re.search(r'redis:.*?healthcheck:', content, re.DOTALL)
        assert match is not None, "Redis must have health check configured"
        # Accepts both exec-form ["CMD", "redis-cli", "ping"] and shell form
        assert re.search(r"redis-cli['\"\], ]+ping", content), "Redis health check must use redis-cli ping"

    def test_backend_depends_on_postgres_and_redis(self):
        """Test that backend service depends on postgres and redis."""
        compose_path = get_project_root() / "docker-compose.yml"
        content = compose_path.read_text()

        # Check for depends_on in backend section
        backend_section = content.split("backend:")[1].split("\n\n")[0] if "backend:" in content else ""
        assert "depends_on:" in backend_section, "Backend must depend on other services"
        assert "postgres:" in backend_section, "Backend must depend on postgres"
        assert "redis:" in backend_section, "Backend must depend on redis"

    def test_celery_worker_depends_on_postgres_and_redis(self):
        """Test that Celery worker depends on postgres and redis."""
        compose_path = get_project_root() / "docker-compose.yml"
        content = compose_path.read_text()

        # Check for depends_on in celery_worker section
        worker_section = content.split("celery_worker:")[1].split("\n\n")[0] if "celery_worker:" in content else ""
        assert "depends_on:" in worker_section, "Celery worker must depend on other services"
        assert "postgres:" in worker_section, "Celery worker must depend on postgres"
        assert "redis:" in worker_section, "Celery worker must depend on redis"

    def test_volumes_defined(self):
        """Test that required volumes are defined."""
        compose_path = get_project_root() / "docker-compose.yml"
        content = compose_path.read_text()

        assert "volumes:" in content, "docker-compose.yml must define volumes"
        assert "postgres_data:" in content, "postgres_data volume must be defined"
        assert "uploads:" in content, "uploads volume must be defined"

    def test_environment_variables_configured(self):
        """Test that environment variables are properly configured."""
        compose_path = get_project_root() / "docker-compose.yml"
        content = compose_path.read_text()

        # Check for DATABASE_URL in backend
        assert "DATABASE_URL:" in content, "DATABASE_URL must be configured"
        assert "REDIS_URL:" in content, "REDIS_URL must be configured"
        assert "CELERY_BROKER_URL:" in content, "CELERY_BROKER_URL must be configured"


class TestBackendHealth:
    """Test backend health endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self, client: AsyncClient):
        """Test that /health endpoint returns 200 OK."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_json(self, client: AsyncClient):
        """Test that /health endpoint returns JSON response."""
        response = await client.get("/health")
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_status(self, client: AsyncClient):
        """Test that /health endpoint returns status field."""
        response = await client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_service_name(self, client: AsyncClient):
        """Test that /health endpoint returns service name."""
        response = await client.get("/health")
        data = response.json()
        assert "service" in data

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_version(self, client: AsyncClient):
        """Test that /health endpoint returns version."""
        response = await client.get("/health")
        data = response.json()
        assert "version" in data


class TestSeedData:
    """Test that seed data is properly created."""

    @pytest.mark.asyncio
    async def test_roles_created(self, db_session):
        """Test that roles are created by seed data."""
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT COUNT(*) FROM roles"))
        count = result.scalar()
        assert count >= 3, f"Expected at least 3 roles, got {count}"

    @pytest.mark.asyncio
    async def test_admin_role_exists(self, db_session):
        """Test that Admin role exists."""
        from sqlalchemy import text
        result = await db_session.execute(
            text("SELECT name FROM roles WHERE name = 'Admin'")
        )
        role = result.fetchone()
        assert role is not None, "Admin role not found"

    @pytest.mark.asyncio
    async def test_manager_role_exists(self, db_session):
        """Test that Manager role exists."""
        from sqlalchemy import text
        result = await db_session.execute(
            text("SELECT name FROM roles WHERE name = 'Manager'")
        )
        role = result.fetchone()
        assert role is not None, "Manager role not found"

    @pytest.mark.asyncio
    async def test_employee_role_exists(self, db_session):
        """Test that Employee role exists."""
        from sqlalchemy import text
        result = await db_session.execute(
            text("SELECT name FROM roles WHERE name = 'Employee'")
        )
        role = result.fetchone()
        assert role is not None, "Employee role not found"

    @pytest.mark.asyncio
    async def test_departments_created(self, db_session):
        """Test that departments are created by seed data."""
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT COUNT(*) FROM departments"))
        count = result.scalar()
        assert count >= 3, f"Expected at least 3 departments, got {count}"

    @pytest.mark.asyncio
    async def test_finance_department_exists(self, db_session):
        """Test that Finance department exists."""
        from sqlalchemy import text
        result = await db_session.execute(
            text("SELECT name FROM departments WHERE name = 'Finance'")
        )
        dept = result.fetchone()
        assert dept is not None, "Finance department not found"

    @pytest.mark.asyncio
    async def test_hr_department_exists(self, db_session):
        """Test that HR department exists."""
        from sqlalchemy import text
        result = await db_session.execute(
            text("SELECT name FROM departments WHERE name = 'HR'")
        )
        dept = result.fetchone()
        assert dept is not None, "HR department not found"

    @pytest.mark.asyncio
    async def test_engineering_department_exists(self, db_session):
        """Test that Engineering department exists."""
        from sqlalchemy import text
        result = await db_session.execute(
            text("SELECT name FROM departments WHERE name = 'Engineering'")
        )
        dept = result.fetchone()
        assert dept is not None, "Engineering department not found"


class TestAPIEndpoints:
    """Test API endpoints are accessible."""

    @pytest.mark.asyncio
    async def test_auth_register_endpoint_accessible(self, client: AsyncClient):
        """Test that /auth/register endpoint is accessible."""
        response = await client.post("/api/v1/auth/register", json={})
        # Should return 422 (validation error) not 404 (not found)
        assert response.status_code != 404, "Auth register endpoint not found"

    @pytest.mark.asyncio
    async def test_auth_login_endpoint_accessible(self, client: AsyncClient):
        """Test that /auth/login endpoint is accessible."""
        response = await client.post("/api/v1/auth/login", json={})
        # Should return 422 (validation error) not 404 (not found)
        assert response.status_code != 404, "Auth login endpoint not found"

    @pytest.mark.asyncio
    async def test_documents_endpoint_accessible(self, client: AsyncClient):
        """Test that /documents endpoint is accessible."""
        response = await client.get("/api/v1/documents")
        # Should return 401 (unauthorized) not 404 (not found)
        assert response.status_code != 404, "Documents endpoint not found"

    @pytest.mark.asyncio
    async def test_search_endpoint_accessible(self, client: AsyncClient):
        """Test that /search endpoint is accessible."""
        response = await client.get("/api/v1/search")
        # Should return 401 (unauthorized) not 404 (not found)
        assert response.status_code != 404, "Search endpoint not found"

    @pytest.mark.asyncio
    async def test_chat_endpoint_accessible(self, client: AsyncClient):
        """Test that /chat endpoint is accessible."""
        response = await client.get("/api/v1/chat")
        # Should return 401 (unauthorized) or 405 (method not allowed) not 404
        assert response.status_code != 404, "Chat endpoint not found"

    @pytest.mark.asyncio
    async def test_admin_endpoint_accessible(self, client: AsyncClient):
        """Test that /admin endpoint is accessible."""
        response = await client.get("/api/v1/admin/metrics")
        # Should return 401 (unauthorized) not 404 (not found)
        assert response.status_code != 404, "Admin endpoint not found"

    @pytest.mark.asyncio
    async def test_departments_endpoint_accessible(self, client: AsyncClient):
        """Test that /departments endpoint is accessible."""
        response = await client.get("/api/v1/departments")
        # Should return 200 or 401, not 404
        assert response.status_code != 404, "Departments endpoint not found"


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_200(self, client: AsyncClient):
        """Test that /metrics endpoint returns 200."""
        response = await client.get("/metrics", follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_text(self, client: AsyncClient):
        """Test that /metrics endpoint returns prometheus text format."""
        response = await client.get("/metrics", follow_redirects=True)
        assert "text/plain" in response.headers["content-type"]
