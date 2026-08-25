import logging
import os
from typing import List

from app.rag.retriever.retriever import retriever
from app.workers.celery_app import celery_app

logger = logging.getLogger("eka")


def parse_file(file_path: str, mime_type: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif ext == ".docx":
        from docx import Document

        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    elif ext == ".md":
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8")

    elif ext == ".csv":
        import pandas as pd

        df = pd.read_csv(file_path)
        return df.to_string()

    elif ext == ".xlsx":
        import pandas as pd

        df = pd.read_excel(file_path)
        return df.to_string()

    elif ext == ".txt":
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8")

    return ""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    if not text or chunk_size <= 0:
        return []
    overlap = min(overlap, chunk_size - 1) if chunk_size > 1 else 0
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            space = text.rfind(" ", start, end)
            if space > start + chunk_size // 2:
                end = space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 1
        start = next_start
    return chunks


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, document_id: int):
    from sqlalchemy.orm import Session

    from app.db.sync_engine import get_sync_engine

    engine = get_sync_engine()

    try:
        with Session(engine) as db:
            from app.models.document import Document, DocumentStatus

            doc = db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                logger.error(f"Document {document_id} not found")
                return

            doc.status = DocumentStatus.PROCESSING
            db.commit()

            text = parse_file(doc.file_path, doc.mime_type)
            if not text.strip():
                doc.status = DocumentStatus.FAILED
                doc.error_message = "No text could be extracted"
                db.commit()
                return

            raw_chunks = chunk_text(text)

            # Idempotency: purge chunks from a previous partial run before
            # inserting again so retries never duplicate embeddings.
            from sqlalchemy import delete as sa_delete

            from app.models.chunk import Chunk

            await_cleanup = db.execute(sa_delete(Chunk).where(Chunk.document_id == doc.id))
            db.commit()
            logger.debug(f"Purged {await_cleanup.rowcount} stale chunks for document {document_id}")

            chunk_objects = []
            for i, chunk_text_content in enumerate(raw_chunks):
                chunk = Chunk(
                    document_id=doc.id,
                    text=chunk_text_content,
                    chunk_index=i,
                    chunk_metadata={
                        "filename": doc.original_filename,
                        "department_id": doc.department_id,
                        "page": None,
                        "author": None,
                    },
                )
                db.add(chunk)
                db.flush()
                chunk_objects.append(
                    {
                        "chunk_id": chunk.id,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                        "metadata": {
                            "filename": doc.original_filename,
                            "department_id": doc.department_id,
                        },
                    }
                )

            db.commit()

            retriever.store_chunks(
                document_id=doc.id,
                chunks=chunk_objects,
                filename=doc.original_filename,
                department_id=doc.department_id,
            )

            doc.status = DocumentStatus.READY
            doc.chunk_count = len(raw_chunks)
            db.commit()

            logger.info(f"Document {document_id} processed: {len(raw_chunks)} chunks")

    except Exception as exc:
        logger.error(f"Failed to process document {document_id}: {exc}")
        try:
            with Session(engine) as db:
                from app.models.document import Document, DocumentStatus

                doc = db.query(Document).filter(Document.id == document_id).first()
                if doc:
                    doc.status = DocumentStatus.FAILED
                    doc.error_message = str(exc)
                    db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
