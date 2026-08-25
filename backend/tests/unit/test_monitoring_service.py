"""Unit tests for MonitoringService.

These tests verify that monitoring and metrics collection works correctly.
They test the MonitoringService class and its methods.

Tests follow TDD approach:
- Red: Write failing test
- Green: Make test pass
- Refactor: Improve code while keeping tests green
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.monitoring,
]


class TestMonitoringServiceInitialization:
    """Test MonitoringService initialization."""

    def test_monitoring_service_initializes_with_db(self):
        """Test that MonitoringService initializes with database session."""
        from app.services.monitoring import MonitoringService

        db = AsyncMock(spec=AsyncSession)
        service = MonitoringService(db)
        assert service.doc_repo is not None
        assert service.msg_repo is not None
        assert service.session_repo is not None
        assert service.audit_repo is not None
        assert service.user_repo is not None

    def test_monitoring_service_has_get_metrics_method(self):
        """Test that MonitoringService has get_metrics method."""
        from app.services.monitoring import MonitoringService

        db = AsyncMock(spec=AsyncSession)
        service = MonitoringService(db)
        assert hasattr(service, "get_metrics")
        assert callable(service.get_metrics)


class TestMonitoringServiceGetMetrics:
    """Test MonitoringService.get_metrics method."""

    @pytest.mark.asyncio
    async def test_get_metrics_returns_dict(self):
        """Test that get_metrics returns a dictionary."""
        from app.services.monitoring import MonitoringService

        db = AsyncMock(spec=AsyncSession)
        service = MonitoringService(db)

        # Mock repository methods
        service.doc_repo = AsyncMock()
        service.doc_repo.list = AsyncMock(return_value=[])
        service.doc_repo.count_by_status = AsyncMock(return_value={})

        service.msg_repo = AsyncMock()
        service.msg_repo.count_tokens = AsyncMock(return_value=0)
        service.msg_repo.avg_latency = AsyncMock(return_value=0.0)

        service.audit_repo = AsyncMock()
        service.audit_repo.count_errors = AsyncMock(return_value=0)

        service.user_repo = AsyncMock()
        service.user_repo.count = AsyncMock(return_value=0)

        service.session_repo = AsyncMock()
        service.session_repo.count = AsyncMock(return_value=0)

        with patch("app.services.monitoring.search_latency_stats", return_value=(0.0, 0.0)):
            result = await service.get_metrics()

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_metrics_contains_required_keys(self):
        """Test that get_metrics returns all required keys."""
        from app.services.monitoring import MonitoringService

        db = AsyncMock(spec=AsyncSession)
        service = MonitoringService(db)

        # Mock repository methods
        service.doc_repo = AsyncMock()
        service.doc_repo.list = AsyncMock(return_value=[])
        service.doc_repo.count_by_status = AsyncMock(return_value={})

        service.msg_repo = AsyncMock()
        service.msg_repo.count_tokens = AsyncMock(return_value=0)
        service.msg_repo.avg_latency = AsyncMock(return_value=0.0)

        service.audit_repo = AsyncMock()
        service.audit_repo.count_errors = AsyncMock(return_value=0)

        service.user_repo = AsyncMock()
        service.user_repo.count = AsyncMock(return_value=0)

        service.session_repo = AsyncMock()
        service.session_repo.count = AsyncMock(return_value=0)

        with patch("app.services.monitoring.search_latency_stats", return_value=(0.0, 0.0)):
            result = await service.get_metrics()

        required_keys = [
            "total_documents",
            "total_users",
            "total_chat_sessions",
            "documents_by_status",
            "total_tokens_used",
            "avg_chat_latency_ms",
            "avg_search_latency_ms",
            "error_count",
        ]

        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    @pytest.mark.asyncio
    async def test_get_metrics_calls_repositories(self):
        """Test that get_metrics calls all repository methods."""
        from app.services.monitoring import MonitoringService

        db = AsyncMock(spec=AsyncSession)
        service = MonitoringService(db)

        # Mock repository methods
        service.doc_repo = AsyncMock()
        service.doc_repo.list = AsyncMock(return_value=[])
        service.doc_repo.count_by_status = AsyncMock(return_value={"ready": 5})

        service.msg_repo = AsyncMock()
        service.msg_repo.count_tokens = AsyncMock(return_value=1000)
        service.msg_repo.avg_latency = AsyncMock(return_value=150.5)

        service.audit_repo = AsyncMock()
        service.audit_repo.count_errors = AsyncMock(return_value=2)

        service.user_repo = AsyncMock()
        service.user_repo.count = AsyncMock(return_value=10)

        service.session_repo = AsyncMock()
        service.session_repo.count = AsyncMock(return_value=25)

        with patch("app.services.monitoring.search_latency_stats", return_value=(50.0, 10.0)):
            await service.get_metrics()

        service.doc_repo.list.assert_called_once()
        service.doc_repo.count_by_status.assert_called_once()
        service.msg_repo.count_tokens.assert_called_once()
        service.msg_repo.avg_latency.assert_called_once()
        service.audit_repo.count_errors.assert_called_once()
        service.user_repo.count.assert_called_once()
        service.session_repo.count.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_metrics_returns_correct_values(self):
        """Test that get_metrics returns correct values from repositories."""
        from app.services.monitoring import MonitoringService

        db = AsyncMock(spec=AsyncSession)
        service = MonitoringService(db)

        # Mock repository methods with specific values
        service.doc_repo = AsyncMock()
        service.doc_repo.list = AsyncMock(return_value=[Mock(), Mock(), Mock()])
        service.doc_repo.count_by_status = AsyncMock(return_value={"ready": 2, "pending": 1})

        service.msg_repo = AsyncMock()
        service.msg_repo.count_tokens = AsyncMock(return_value=5000)
        service.msg_repo.avg_latency = AsyncMock(return_value=125.75)

        service.audit_repo = AsyncMock()
        service.audit_repo.count_errors = AsyncMock(return_value=3)

        service.user_repo = AsyncMock()
        service.user_repo.count = AsyncMock(return_value=15)

        service.session_repo = AsyncMock()
        service.session_repo.count = AsyncMock(return_value=50)

        with patch("app.services.monitoring.search_latency_stats", return_value=(75.0, 25.0)):
            result = await service.get_metrics()

        assert result["total_documents"] == 3
        assert result["total_users"] == 15
        assert result["total_chat_sessions"] == 50
        assert result["documents_by_status"] == {"ready": 2, "pending": 1}
        assert result["total_tokens_used"] == 5000
        assert result["avg_chat_latency_ms"] == 125.75
        assert result["avg_search_latency_ms"] == 75.0
        assert result["error_count"] == 3
