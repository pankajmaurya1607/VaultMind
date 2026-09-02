import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.guest_document import GuestDocument
from app.services.document import validate_content_signature

UPLOAD_CHUNK_SIZE = 1024 * 1024


def _get_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.GUEST_TTL_MINUTES)


async def cleanup_expired(db: AsyncSession) -> int:
    """Delete expired guest docs + files. Returns count deleted."""
    cutoff = datetime.now(timezone.utc)
    result = await db.execute(select(GuestDocument).where(GuestDocument.expires_at < cutoff))
    expired = result.scalars().all()
    count = 0
    for doc in expired:
        # file cleanup
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError:
                pass
        await db.delete(doc)
        count += 1
    if count:
        await db.commit()
    return count


async def cleanup_expired_sync() -> int:
    """Sync version for Celery worker (uses sync engine)."""
    from sqlalchemy.orm import Session

    from app.db.sync_engine import get_sync_engine

    engine = get_sync_engine()
    cutoff = datetime.now(timezone.utc)
    with Session(engine) as db:
        docs = db.query(GuestDocument).filter(GuestDocument.expires_at < cutoff).all()
        count = 0
        for doc in docs:
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except OSError:
                    pass
            db.delete(doc)
            count += 1
        if count:
            db.commit()
        return count


class GuestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload(self, file: UploadFile, guest_token: str | None) -> tuple[GuestDocument, str]:
        if not guest_token:
            guest_token = uuid.uuid4().hex

        # Lazy cleanup on each upload
        await cleanup_expired(self.db)

        # Enforce 1 file per token
        existing = await self.db.execute(
            select(GuestDocument).where(GuestDocument.guest_token == guest_token).where(GuestDocument.expires_at > datetime.now(timezone.utc))
        )
        if len(existing.scalars().all()) >= settings.GUEST_MAX_FILES_PER_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Quick Try allows {settings.GUEST_MAX_FILES_PER_TOKEN} file per session. Wait for expiry or clear session.",
            )

        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type '{ext}' not supported")

        # Stream to disk with 1MB cap
        upload_dir = os.path.join(settings.UPLOAD_DIR, "guest", guest_token)
        os.makedirs(upload_dir, exist_ok=True)
        stored_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(upload_dir, stored_filename)

        size = 0
        head = b""
        try:
            with open(file_path, "wb") as out:
                while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                    if size == 0:
                        head = chunk[:16]
                    size += len(chunk)
                    if size > settings.GUEST_MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Quick Try limit is {settings.GUEST_MAX_FILE_SIZE // (1024*1024)}MB. Please sign up for larger files.",
                        )
                    out.write(chunk)
        except HTTPException:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

        if size == 0:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

        if not validate_content_signature(ext, head):
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"File content does not match declared type '{ext}'"
            )

        doc = GuestDocument(
            guest_token=guest_token,
            filename=stored_filename,
            original_filename=file.filename or stored_filename,
            file_path=file_path,
            file_size=size,
            mime_type=file.content_type or "application/octet-stream",
            status="pending",
            expires_at=_get_expires_at(),
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        # Enqueue processing
        from app.tasks.process import process_guest_document_task

        process_guest_document_task.delay(doc.id)

        return doc, guest_token

    async def get_status(self, guest_token: str) -> list[GuestDocument]:
        await cleanup_expired(self.db)
        result = await self.db.execute(
            select(GuestDocument)
            .where(GuestDocument.guest_token == guest_token)
            .where(GuestDocument.expires_at > datetime.now(timezone.utc))
            .order_by(GuestDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_expired_for_token(self, guest_token: str) -> int:
        result = await self.db.execute(select(GuestDocument).where(GuestDocument.guest_token == guest_token))
        docs = result.scalars().all()
        count = 0
        for doc in docs:
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except OSError:
                    pass
            await self.db.delete(doc)
            count += 1
        if count:
            await self.db.commit()
        return count
