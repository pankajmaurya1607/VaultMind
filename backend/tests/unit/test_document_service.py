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
