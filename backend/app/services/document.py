import logging
import os
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.document import Document, DocumentStatus
from app.repositories.document import DocumentRepository
from app.tasks.process import process_document_task

logger = logging.getLogger("eka")

_UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def _zip_magic(head: bytes) -> bool:
    # docx/xlsx are ZIP containers
    return head.startswith(b"PK\x03\x04")


def _text_magic(head: bytes) -> bool:
    # txt/md/csv: reject binary payloads (NUL byte heuristic)
    return b"\x00" not in head


_MAGIC_VALIDATORS = {
    ".pdf": lambda head: head.startswith(b"%PDF"),
    ".docx": _zip_magic,
    ".xlsx": _zip_magic,
    ".txt": _text_magic,
    ".md": _text_magic,
    ".csv": _text_magic,
}


def validate_content_signature(ext: str, head: bytes) -> bool:
    """Best-effort magic-byte check for known extensions."""
    validator = _MAGIC_VALIDATORS.get(ext)
    if validator is None:
        return True
    return validator(head)


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.repo = DocumentRepository(db)
        self.db = db

    async def upload(self, file: UploadFile, user_id: int, department_id: int) -> Document:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type '{ext}' not supported")

        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        stored_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(upload_dir, stored_filename)

        # Stream to disk so oversized uploads never sit fully in memory;
        # enforce the size cap per chunk.
        size = 0
        head = b""
        try:
            with open(file_path, "wb") as out:
                while chunk := await file.read(_UPLOAD_CHUNK_SIZE):
                    if size == 0:
                        head = chunk[:16]
                    size += len(chunk)
                    if size > settings.MAX_UPLOAD_SIZE:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds max size of {settings.MAX_UPLOAD_SIZE} bytes",
                        )
                    out.write(chunk)
        except HTTPException:
            os.remove(file_path)
            raise

        if size == 0:
            os.remove(file_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

        if not validate_content_signature(ext, head):
            os.remove(file_path)
            logger.warning("Content signature mismatch for %s upload (user %s)", ext, user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content does not match declared type '{ext}'",
            )

        document = await self.repo.create(
            filename=stored_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=size,
            mime_type=file.content_type or "application/octet-stream",
            uploaded_by=user_id,
            department_id=department_id,
            status=DocumentStatus.PENDING,
        )

        process_document_task.delay(document.id)
        return document

    async def get_user_documents(
        self, user_id: int, department_ids: list[int], skip: int = 0, limit: int = 100
    ) -> list[Document]:
        """Get documents uploaded by user, filtered to their department."""
        return await self.repo.get_by_user_with_dept_filter(user_id, department_ids, skip, limit)

    async def get_user_documents_with_total(
        self, user_id: int, department_ids: list[int], skip: int = 0, limit: int = 100
    ) -> tuple[list[Document], int]:
        return await self.repo.get_user_with_total(user_id, department_ids, skip, limit)

    async def get_all_documents(self, skip: int = 0, limit: int = 100) -> list[Document]:
        """Get all documents (Admin only)."""
        return await self.repo.list(skip, limit)

    async def get_all_documents_with_total(self, skip: int = 0, limit: int = 100) -> tuple[list[Document], int]:
        return await self.repo.get_all_with_total(skip, limit)

    async def get_document(self, document_id: int) -> Document | None:
        """Get a single document by id (access control enforced by caller)."""
        return await self.repo.get(document_id)

    async def delete_document(self, document_id: int) -> bool:
        """Delete a document row and its stored file. Chunks cascade via FK."""
        document = await self.repo.get(document_id)
        if document is None:
            return False
        deleted = await self.repo.delete(document_id)
        if deleted:
            # Evict any cached fallback-store entries so deleted docs
            # disappear from search immediately.
            from app.rag.retriever.retriever import retriever

            retriever.evict_document(document_id)
            if document.file_path and os.path.exists(document.file_path):
                try:
                    os.remove(document.file_path)
                except OSError as exc:
                    logger.warning("Failed to remove file %s for document %s: %s", document.file_path, document_id, exc)
        return deleted
