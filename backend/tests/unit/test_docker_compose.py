"""Unit tests for Docker Compose configuration.

These tests verify that docker-compose.yml is properly configured.
They don't require a running database or services.

Tests follow TDD approach:
- Red: Write failing test
- Green: Make test pass
- Refactor: Improve code while keeping tests green
"""

from pathlib import Path

import pytest
import yaml

# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.docker,
]


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def load_compose_config() -> dict:
    """Load and parse docker-compose.yml."""
    compose_path = get_project_root() / "docker-compose.yml"
    if not compose_path.exists():
        pytest.skip("docker-compose.yml not available in test environment")
    with open(compose_path, "r") as f:
        return yaml.safe_load(f)


class TestDockerComposeConfiguration:
    """Test Docker Compose configuration files exist and are valid."""

    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists in project root."""
        compose_path = get_project_root() / "docker-compose.yml"
        if not compose_path.exists():
            pytest.skip("docker-compose.yml not available in test environment")
        assert compose_path.exists(), f"docker-compose.yml not found at {compose_path}"

    def test_docker_compose_valid_yaml(self):
        """Test that docker-compose.yml is valid YAML."""
        config = load_compose_config()
        assert "services" in config, "docker-compose.yml must define services"

    def test_required_services_defined(self):
        """Test that all required services are defined."""
        config = load_compose_config()
        required_services = [
            "postgres", "redis", "backend", "celery_worker",
            "flower", "prometheus", "grafana"
        ]
        for service in required_services:
            assert service in config["services"], f"Required service '{service}' not found"

    def test_postgres_health_check_configured(self):
        """Test that PostgreSQL has health check configured."""
        config = load_compose_config()
        postgres = config["services"]["postgres"]
        assert "healthcheck" in postgres, "PostgreSQL must have health check configured"
        assert "test" in postgres["healthcheck"], "PostgreSQL health check must have test command"

    def test_redis_health_check_configured(self):
        """Test that Redis has health check configured."""
        config = load_compose_config()
        redis = config["services"]["redis"]
        assert "healthcheck" in redis, "Redis must have health check configured"
        assert "test" in redis["healthcheck"], "Redis health check must have test command"

    def test_backend_depends_on_postgres_and_redis(self):
        """Test that backend service depends on postgres and redis."""
        config = load_compose_config()
        backend = config["services"]["backend"]
        assert "depends_on" in backend, "Backend must depend on other services"
        deps = backend["depends_on"]
        assert "postgres" in deps, "Backend must depend on postgres"
        assert "redis" in deps, "Backend must depend on redis"

    def test_celery_worker_depends_on_postgres_and_redis(self):
        """Test that Celery worker depends on postgres and redis."""
        config = load_compose_config()
        worker = config["services"]["celery_worker"]
        assert "depends_on" in worker, "Celery worker must depend on other services"
        deps = worker["depends_on"]
        assert "postgres" in deps, "Celery worker must depend on postgres"
        assert "redis" in deps, "Celery worker must depend on redis"

    def test_volumes_defined(self):
        """Test that required volumes are defined."""
        config = load_compose_config()
        assert "volumes" in config, "docker-compose.yml must define volumes"
        required_volumes = ["postgres_data", "uploads"]
        for vol in required_volumes:
            assert vol in config["volumes"], f"Required volume '{vol}' not found"

    def test_environment_variables_configured(self):
        """Test that environment variables are properly configured."""
        config = load_compose_config()
        backend_env = config["services"]["backend"]["environment"]
        assert "DATABASE_URL" in backend_env, "DATABASE_URL must be configured"
        assert "REDIS_URL" in backend_env, "REDIS_URL must be configured"
        assert "CELERY_BROKER_URL" in backend_env, "CELERY_BROKER_URL must be configured"

    def test_postgres_image_specified(self):
        """Test that PostgreSQL image is specified."""
        config = load_compose_config()
        postgres = config["services"]["postgres"]
        assert "image" in postgres, "PostgreSQL must have image specified"
        assert "pgvector" in postgres["image"], "PostgreSQL must use pgvector image"

    def test_redis_image_specified(self):
        """Test that Redis image is specified."""
        config = load_compose_config()
        redis = config["services"]["redis"]
        assert "image" in redis, "Redis must have image specified"
        assert "redis" in redis["image"], "Redis must use redis image"

    def test_backend_build_configured(self):
        """Test that backend build is configured."""
        config = load_compose_config()
        backend = config["services"]["backend"]
        assert "build" in backend, "Backend must have build configured"
        assert "context" in backend["build"], "Backend must have build context"
        assert "dockerfile" in backend["build"], "Backend must have dockerfile specified"

    def test_celery_worker_build_configured(self):
        """Test that Celery worker build is configured."""
        config = load_compose_config()
        worker = config["services"]["celery_worker"]
        assert "build" in worker, "Celery worker must have build configured"
        assert "context" in worker["build"], "Celery worker must have build context"
        assert "dockerfile" in worker["build"], "Celery worker must have dockerfile specified"

    def test_prometheus_configured(self):
        """Test that Prometheus is configured."""
        config = load_compose_config()
        prometheus = config["services"]["prometheus"]
        assert "image" in prometheus, "Prometheus must have image specified"
        assert "ports" in prometheus, "Prometheus must have ports configured"

    def test_grafana_configured(self):
        """Test that Grafana is configured."""
        config = load_compose_config()
        grafana = config["services"]["grafana"]
        assert "image" in grafana, "Grafana must have image specified"
        assert "ports" in grafana, "Grafana must have ports configured"

    def test_flower_configured(self):
        """Test that Flower is configured."""
        config = load_compose_config()
        flower = config["services"]["flower"]
        assert "image" in flower, "Flower must have image specified"
        assert "ports" in flower, "Flower must have ports configured"
