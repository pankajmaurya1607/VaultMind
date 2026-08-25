"""Unit tests for file validation logic.

These tests verify that file uploads are properly validated.
They test file type, size, and other validation rules.

Tests follow TDD approach:
- Red: Write failing test
- Green: Make test pass
- Refactor: Improve code while keeping tests green
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException, UploadFile

# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.validation,
]


class TestFileExtensionValidation:
    """Test file extension validation."""

    def test_allows_pdf_extension(self):
        """Test that PDF files are allowed."""
        from app.config.settings import settings
        assert ".pdf" in settings.ALLOWED_EXTENSIONS, "PDF should be allowed"

    def test_allows_docx_extension(self):
        """Test that DOCX files are allowed."""
        from app.config.settings import settings
        assert ".docx" in settings.ALLOWED_EXTENSIONS, "DOCX should be allowed"

    def test_allows_txt_extension(self):
        """Test that TXT files are allowed."""
        from app.config.settings import settings
        assert ".txt" in settings.ALLOWED_EXTENSIONS, "TXT should be allowed"

    def test_allows_md_extension(self):
        """Test that Markdown files are allowed."""
        from app.config.settings import settings
        assert ".md" in settings.ALLOWED_EXTENSIONS, "Markdown should be allowed"

    def test_allows_csv_extension(self):
        """Test that CSV files are allowed."""
        from app.config.settings import settings
        assert ".csv" in settings.ALLOWED_EXTENSIONS, "CSV should be allowed"

    def test_allows_xlsx_extension(self):
        """Test that XLSX files are allowed."""
        from app.config.settings import settings
        assert ".xlsx" in settings.ALLOWED_EXTENSIONS, "XLSX should be allowed"

    def test_rejects_exe_extension(self):
        """Test that EXE files are rejected."""
        from app.config.settings import settings
        assert ".exe" not in settings.ALLOWED_EXTENSIONS, "EXE should not be allowed"

    def test_rejects_bat_extension(self):
        """Test that BAT files are rejected."""
        from app.config.settings import settings
        assert ".bat" not in settings.ALLOWED_EXTENSIONS, "BAT should not be allowed"

    def test_rejects_sh_extension(self):
        """Test that SH files are rejected."""
        from app.config.settings import settings
        assert ".sh" not in settings.ALLOWED_EXTENSIONS, "SH should not be allowed"


class TestFileSizeValidation:
    """Test file size validation."""

    def test_max_upload_size_configured(self):
        """Test that max upload size is configured."""
        from app.config.settings import settings
        assert settings.MAX_UPLOAD_SIZE > 0, "Max upload size must be configured"

    def test_max_upload_size_reasonable(self):
        """Test that max upload size is reasonable (at least 1MB)."""
        from app.config.settings import settings
        assert settings.MAX_UPLOAD_SIZE >= 1024 * 1024, "Max upload size should be at least 1MB"


class TestDocumentServiceValidation:
    """Test DocumentService file validation."""

    @pytest.mark.asyncio
    async def test_rejects_unsupported_extension(self):
        """Test that unsupported file extensions are rejected."""
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.services.document import DocumentService

        db = AsyncMock(spec=AsyncSession)
        service = DocumentService(db)

        # Create mock file with unsupported extension
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "malware.exe"
        mock_file.content_type = "application/x-executable"

        with pytest.raises(HTTPException) as exc_info:
            await service.upload(mock_file, user_id=1, department_id=1)

        assert exc_info.value.status_code == 400
        assert "not supported" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self):
        """Test that files exceeding max size are rejected."""
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.config.settings import settings
        from app.services.document import DocumentService

        db = AsyncMock(spec=AsyncSession)
        service = DocumentService(db)

        # Create mock file with valid extension but oversized content
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "large_document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"x" * (settings.MAX_UPLOAD_SIZE + 1))

        with pytest.raises(HTTPException) as exc_info:
            await service.upload(mock_file, user_id=1, department_id=1)

        assert exc_info.value.status_code == 413
        assert "exceeds max size" in exc_info.value.detail


class TestRBACValidation:
    """Test RBAC role-based access control validation."""

    def test_role_checker_initialization(self):
        """Test that RoleChecker initializes with allowed roles."""
        from app.rbac.dependencies import RoleChecker

        checker = RoleChecker(["Admin", "Manager"])
        assert checker.allowed_roles == ["Admin", "Manager"]

    def test_get_effective_department_ids_admin(self):
        """Test that Admin users get empty department list (all access)."""
        from unittest.mock import Mock

        from app.rbac.dependencies import get_effective_department_ids

        user = Mock()
        user.role.name = "Admin"
        user.department_id = 1

        dept_ids = get_effective_department_ids(user)
        assert dept_ids == [], "Admin should have empty department list"

    def test_get_effective_department_ids_employee(self):
        """Test that Employee users get their department ID."""
        from unittest.mock import Mock

        from app.rbac.dependencies import get_effective_department_ids

        user = Mock()
        user.role.name = "Employee"
        user.department_id = 5

        dept_ids = get_effective_department_ids(user)
        assert dept_ids == [5], "Employee should have their department ID"

    def test_require_admin_role(self):
        """Test that require_admin only allows Admin role."""
        from app.rbac.dependencies import require_admin

        assert require_admin.allowed_roles == ["Admin"]

    def test_require_manager_role(self):
        """Test that require_manager allows Admin and Manager roles."""
        from app.rbac.dependencies import require_manager

        assert require_manager.allowed_roles == ["Admin", "Manager"]

    def test_require_employee_role(self):
        """Test that require_employee allows all roles."""
        from app.rbac.dependencies import require_employee

        assert require_employee.allowed_roles == ["Admin", "Manager", "Employee"]


class TestAuditService:
    """Test AuditService functionality."""

    @pytest.mark.asyncio
    async def test_audit_service_initialization(self):
        """Test that AuditService initializes correctly."""
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.services.audit import AuditService

        db = AsyncMock(spec=AsyncSession)
        service = AuditService(db)
        assert service.repo is not None

    @pytest.mark.asyncio
    async def test_get_client_ip_from_forwarded_header(self):
        """Test IP extraction from X-Forwarded-For header."""
        from unittest.mock import Mock

        from app.services.audit import AuditService

        request = Mock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client = None

        ip = AuditService.get_client_ip(request)
        assert ip == "192.168.1.1", "Should extract first IP from X-Forwarded-For"

    def test_get_client_ip_from_client(self):
        """Test IP extraction from request.client."""
        from unittest.mock import Mock

        from app.services.audit import AuditService

        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        ip = AuditService.get_client_ip(request)
        assert ip == "127.0.0.1", "Should use client.host when no X-Forwarded-For"

    def test_get_client_ip_unknown(self):
        """Test IP extraction when no client info available."""
        from unittest.mock import Mock

        from app.services.audit import AuditService

        request = Mock()
        request.headers = {}
        request.client = None

        ip = AuditService.get_client_ip(request)
        assert ip == "unknown", "Should return 'unknown' when no client info"
