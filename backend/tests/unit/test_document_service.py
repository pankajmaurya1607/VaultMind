from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.config.settings import settings
from app.models.document import Document, DocumentStatus
from app.services.document import DocumentService


async def make_upload(filename="test.txt", size=None):
    content = b"x" * size if size else b"hello"
    return UploadFile(filename=filename, file=BytesIO(content))


class TestDocumentServiceUpload:
    def setup_method(self):
        self.db = AsyncMock()
        self.service = DocumentService(self.db)
        self.service.repo = AsyncMock()

    @pytest.mark.asyncio
    async def test_rejects_unsupported_extension(self):
        file = await make_upload("notes.exe")
        with pytest.raises(HTTPException) as exc:
            await self.service.upload(file, user_id=1, department_id=1)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self):
        file = await make_upload("big.txt", size=settings.MAX_UPLOAD_SIZE + 1)
        with pytest.raises(HTTPException) as exc:
            await self.service.upload(file, user_id=1, department_id=1)
        assert exc.value.status_code == 413

    @pytest.mark.asyncio
    async def test_creates_document_and_enqueues(self, tmp_path, monkeypatch):
        uploaded_dir = str(tmp_path / "uploads")
        monkeypatch.setattr(settings, "UPLOAD_DIR", uploaded_dir)

        doc = Document(
            id=1,
            filename="abc.txt",
            original_filename="test.txt",
            file_path=f"{uploaded_dir}/abc.txt",
            file_size=5,
            mime_type="text/plain",
            uploaded_by=1,
            department_id=1,
            status=DocumentStatus.PENDING,
        )
        self.service.repo.create = AsyncMock(return_value=doc)

        with patch("app.services.document.process_document_task") as task:
            task.delay = MagicMock()
            result = await self.service.upload(await make_upload("test.txt"), 1, 1)

        assert result.id == 1
        assert result.status == DocumentStatus.PENDING
        task.delay.assert_called_once_with(1)


class TestDocumentServiceGetDelete:
    def setup_method(self):
        self.db = AsyncMock()
        self.service = DocumentService(self.db)
        self.service.repo = AsyncMock()

    @pytest.mark.asyncio
    async def test_get_document_returns_doc(self):
        doc = Document(id=1, original_filename="test.txt", file_path="/tmp/abc.txt")
        self.service.repo.get = AsyncMock(return_value=doc)
        result = await self.service.get_document(1)
        assert result is doc
        self.service.repo.get.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_get_document_missing_returns_none(self):
        self.service.repo.get = AsyncMock(return_value=None)
        assert await self.service.get_document(99) is None

    @pytest.mark.asyncio
    async def test_delete_document_removes_row_and_file(self, tmp_path):
        stored = tmp_path / "abc.txt"
        stored.write_text("data")
        doc = Document(id=1, original_filename="test.txt", file_path=str(stored))
        self.service.repo.get = AsyncMock(return_value=doc)
        self.service.repo.delete = AsyncMock(return_value=True)

        assert await self.service.delete_document(1) is True
        self.service.repo.delete.assert_awaited_once_with(1)
        assert not stored.exists()

    @pytest.mark.asyncio
    async def test_delete_document_succeeds_even_if_file_missing(self, tmp_path):
        doc = Document(id=1, original_filename="test.txt", file_path=str(tmp_path / "gone.txt"))
        self.service.repo.get = AsyncMock(return_value=doc)
        self.service.repo.delete = AsyncMock(return_value=True)

        assert await self.service.delete_document(1) is True

    @pytest.mark.asyncio
    async def test_delete_document_missing_returns_false(self):
        self.service.repo.get = AsyncMock(return_value=None)
        assert await self.service.delete_document(99) is False
        self.service.repo.delete.assert_not_awaited()
