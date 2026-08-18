"""Unit tests for AuditService.

These tests verify that audit logging works correctly.
They test the AuditService class and its methods.

Tests follow TDD approach:
- Red: Write failing test
- Green: Make test pass
- Refactor: Improve code while keeping tests green
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.audit,
]


class TestAuditServiceInitialization:
    """Test AuditService initialization."""

    def test_audit_service_initializes_with_db(self):
        """Test that AuditService initializes with database session."""
        from app.services.audit import AuditService
        
        db = AsyncMock(spec=AsyncSession)
        service = AuditService(db)
        assert service.repo is not None

    def test_audit_service_has_log_method(self):
        """Test that AuditService has log method."""
        from app.services.audit import AuditService
        
        db = AsyncMock(spec=AsyncSession)
        service = AuditService(db)
        assert hasattr(service, "log")
        assert callable(service.log)

    def test_audit_service_has_get_client_ip_method(self):
        """Test that AuditService has get_client_ip static method."""
        from app.services.audit import AuditService
        
        assert hasattr(AuditService, "get_client_ip")
        assert callable(AuditService.get_client_ip)


class TestAuditServiceLogMethod:
    """Test AuditService.log method."""

    @pytest.mark.asyncio
    async def test_log_calls_repo_create(self):
        """Test that log method calls repository create."""
        from app.services.audit import AuditService
        
        db = AsyncMock(spec=AsyncSession)
        service = AuditService(db)
        service.repo = AsyncMock()
        
        await service.log(
            user_id=1,
            user_email="test@example.com",
            action="login",
            resource="auth",
            resource_id=None,
            details=None,
            ip_address="127.0.0.1",
            success=True,
        )
        
        service.repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_passes_parameters_to_repo(self):
        """Test that log method passes correct parameters to repository."""
        from app.services.audit import AuditService
        
        db = AsyncMock(spec=AsyncSession)
        service = AuditService(db)
        service.repo = AsyncMock()
        
        await service.log(
            user_id=42,
            user_email="admin@example.com",
            action="upload",
            resource="document",
            resource_id="doc-123",
            details="Uploaded file.pdf",
            ip_address="192.168.1.1",
            success=True,
        )
        
        service.repo.create.assert_called_once_with(
            user_id=42,
            user_email="admin@example.com",
            action="upload",
            resource="document",
            resource_id="doc-123",
            details="Uploaded file.pdf",
            ip_address="192.168.1.1",
            success=1,
        )

    @pytest.mark.asyncio
    async def test_log_converts_success_to_integer(self):
        """Test that log method converts success boolean to integer."""
        from app.services.audit import AuditService
        
        db = AsyncMock(spec=AsyncSession)
        service = AuditService(db)
        service.repo = AsyncMock()
        
        await service.log(
            user_id=1,
            user_email="test@example.com",
            action="login",
            resource="auth",
            success=True,
        )
        
        call_kwargs = service.repo.create.call_args[1]
        assert call_kwargs["success"] == 1

    @pytest.mark.asyncio
    async def test_log_converts_failure_to_integer(self):
        """Test that log method converts failure boolean to integer."""
        from app.services.audit import AuditService
        
        db = AsyncMock(spec=AsyncSession)
        service = AuditService(db)
        service.repo = AsyncMock()
        
        await service.log(
            user_id=1,
            user_email="test@example.com",
            action="login",
            resource="auth",
            success=False,
        )
        
        call_kwargs = service.repo.create.call_args[1]
        assert call_kwargs["success"] == 0


class TestAuditServiceGetClientIp:
    """Test AuditService.get_client_ip static method."""

    def test_extracts_ip_from_x_forwarded_for_header(self):
        """Test IP extraction from X-Forwarded-For header."""
        from app.services.audit import AuditService
        
        request = Mock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client = None
        
        ip = AuditService.get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_extracts_first_ip_from_multiple_forwarded(self):
        """Test that first IP is extracted from multiple forwarded IPs."""
        from app.services.audit import AuditService
        
        request = Mock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1, 172.16.0.1"}
        request.client = None
        
        ip = AuditService.get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_uses_client_host_when_no_forwarded_header(self):
        """Test that client.host is used when no X-Forwarded-For header."""
        from app.services.audit import AuditService
        
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        ip = AuditService.get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_returns_unknown_when_no_client_info(self):
        """Test that 'unknown' is returned when no client info available."""
        from app.services.audit import AuditService
        
        request = Mock()
        request.headers = {}
        request.client = None
        
        ip = AuditService.get_client_ip(request)
        assert ip == "unknown"

    def test_strips_whitespace_from_forwarded_ip(self):
        """Test that whitespace is stripped from forwarded IP."""
        from app.services.audit import AuditService
        
        request = Mock()
        request.headers = {"X-Forwarded-For": "  192.168.1.1  , 10.0.0.1"}
        request.client = None
        
        ip = AuditService.get_client_ip(request)
        assert ip == "192.168.1.1"


class TestLogRequestFunction:
    """Test log_request helper function."""

    @pytest.mark.asyncio
    async def test_log_request_creates_audit_service(self):
        """Test that log_request creates AuditService."""
        from app.services.audit import log_request
        
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        db = AsyncMock(spec=AsyncSession)
        
        with patch("app.services.audit.AuditService") as MockAuditService:
            mock_service = AsyncMock()
            MockAuditService.return_value = mock_service
            
            await log_request(
                request=request,
                db=db,
                user_id=1,
                action="login",
                resource="auth",
                success=True,
            )
            
            MockAuditService.assert_called_once_with(db)

    @pytest.mark.asyncio
    async def test_log_request_calls_audit_log(self):
        """Test that log_request calls audit.log method."""
        from app.services.audit import log_request
        
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        db = AsyncMock(spec=AsyncSession)
        
        with patch("app.services.audit.AuditService") as MockAuditService:
            mock_service = AsyncMock()
            mock_service.get_client_ip.return_value = "127.0.0.1"
            MockAuditService.return_value = mock_service
            
            await log_request(
                request=request,
                db=db,
                user_id=1,
                action="login",
                resource="auth",
                success=True,
            )
            
            mock_service.log.assert_called_once()
