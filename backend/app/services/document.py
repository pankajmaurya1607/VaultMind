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


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.repo = DocumentRepository(db)
        self.db = db

    async def upload(self, file: UploadFile, user_id: int, department_id: int) -> Document:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type '{ext}' not supported")

        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds max size of {settings.MAX_UPLOAD_SIZE} bytes",
            )

        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        stored_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(upload_dir, stored_filename)
        with open(file_path, "wb") as f:
            f.write(content)

        document = await self.repo.create(
            filename=stored_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
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

    async def get_all_documents(self, skip: int = 0, limit: int = 100) -> list[Document]:
        """Get all documents (Admin only)."""
        return await self.repo.list(skip, limit)

    async def get_document(self, document_id: int) -> Document | None:
        """Get a single document by id (access control enforced by caller)."""
        return await self.repo.get(document_id)

    async def delete_document(self, document_id: int) -> bool:
        """Delete a document row and its stored file. Chunks cascade via FK."""
        document = await self.repo.get(document_id)
        if document is None:
            return False
        deleted = await self.repo.delete(document_id)
        if deleted and document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except OSError as exc:
                logger.warning("Failed to remove file %s for document %s: %s", document.file_path, document_id, exc)
        return deleted
