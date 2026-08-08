import os
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.document import Document, DocumentStatus
from app.repositories.document import DocumentRepository
from app.tasks.process import process_document_task


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
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
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

    async def get_user_documents(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Document]:
        return await self.repo.get_by_user(user_id, skip, limit)

    async def get_document(self, id: int) -> Document | None:
        return await self.repo.get(id)

    async def delete_document(self, id: int) -> bool:
        doc = await self.repo.get(id)
        if doc and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        return await self.repo.delete(id)
