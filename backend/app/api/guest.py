import time
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.session import get_db
from app.rag.llm.generator import Generator
from app.rag.retriever.retriever import retriever
from app.schemas.chat import ChatResponse, Source
from app.services.guest import GuestService, cleanup_expired

router = APIRouter(prefix="/guest", tags=["Guest Quick-Try"])


def _guest_token_from_header(x_guest_token: Optional[str] = Header(default=None), guest_token: Optional[str] = None) -> Optional[str]:
    # Query param wins, then header
    return guest_token or x_guest_token


@router.post("/upload")
async def guest_upload(
    file: UploadFile = File(...),
    x_guest_token: Optional[str] = Header(default=None, alias="X-Guest-Token"),
    db: AsyncSession = Depends(get_db),
):
    service = GuestService(db)
    doc, token = await service.upload(file, x_guest_token)
    # return token so frontend can store it
    return {
        "id": doc.id,
        "guest_token": token,
        "filename": doc.original_filename,
        "status": doc.status,
        "expires_at": doc.expires_at.isoformat(),
        "ttl_minutes": settings.GUEST_TTL_MINUTES,
        "max_file_size": settings.GUEST_MAX_FILE_SIZE,
        "message": f"File uploaded. Auto-deletes in {settings.GUEST_TTL_MINUTES} minutes.",
    }


@router.get("/status")
async def guest_status(
    guest_token: Optional[str] = None,
    x_guest_token: Optional[str] = Header(default=None, alias="X-Guest-Token"),
    db: AsyncSession = Depends(get_db),
):
    token = _guest_token_from_header(x_guest_token, guest_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="guest_token required")
    service = GuestService(db)
    docs = await service.get_status(token)
    if not docs:
        # check if expired vs never existed - cleanup already handles
        return {"guest_token": token, "documents": [], "expires_in_seconds": 0, "ttl_minutes": settings.GUEST_TTL_MINUTES}
    # compute ttl for first doc
    import datetime

    now = datetime.datetime.now(datetime.timezone.utc)
    expires = docs[0].expires_at
    # ensure timezone aware
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=datetime.timezone.utc)
    ttl = max(0, int((expires - now).total_seconds()))
    return {
        "guest_token": token,
        "documents": [
            {
                "id": d.id,
                "filename": d.original_filename,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "error_message": d.error_message,
                "expires_at": d.expires_at.isoformat() if d.expires_at else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
        "expires_in_seconds": ttl,
        "ttl_minutes": settings.GUEST_TTL_MINUTES,
    }


@router.post("/chat", response_model=ChatResponse)
async def guest_chat(
    body: dict,
    x_guest_token: Optional[str] = Header(default=None, alias="X-Guest-Token"),
    db: AsyncSession = Depends(get_db),
):
    # body: {question, guest_token?, session_id?} - session_id ignored for guest (stateless)
    question = body.get("question") or body.get("query")
    guest_token = body.get("guest_token") or _guest_token_from_header(x_guest_token, None)
    if not question or not question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="question required")
    if not guest_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="guest_token required (upload a file first)")

    # lazy cleanup
    await cleanup_expired(db)

    # verify guest doc exists and is ready
    service = GuestService(db)
    docs = await service.get_status(guest_token)
    if not docs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active guest file. Upload a file (max 1MB) to start. It auto-deletes in 10 minutes.")
    ready = [d for d in docs if d.status == "ready"]
    if not ready:
        # if still processing, tell user to wait
        pending = [d for d in docs if d.status in ("pending", "processing")]
        if pending:
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY, detail="File is still processing. Please wait a few seconds and try again."
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ready document for chat")

    # RAG search scoped to guest_token
    import asyncio

    search_start = time.time()
    from app.monitoring.metrics import CHAT_LATENCY, LLM_LATENCY, record_search_latency

    documents = await retriever.search_guest(question, guest_token, db=db)
    search_time = (time.time() - search_start) * 1000
    record_search_latency(search_time)

    llm_start = time.time()
    generator = Generator()
    answer, sources, confidence = await asyncio.to_thread(generator.generate, question, documents)
    llm_time = (time.time() - llm_start) * 1000
    LLM_LATENCY.observe(llm_time)
    CHAT_LATENCY.observe(search_time + llm_time)

    # sources already filtered to guest doc
    return ChatResponse(
        session_id=0,
        answer=answer,
        sources=[Source(**s) for s in sources],
        confidence_score=confidence,
        tokens_used=generator.last_tokens,
        latency_ms=int(search_time + llm_time),
        model=getattr(generator, "model_name", "template"),
        model_provider=getattr(generator, "model_provider", "fallback"),
    )


@router.delete("/clear")
async def guest_clear(
    guest_token: Optional[str] = None,
    x_guest_token: Optional[str] = Header(default=None, alias="X-Guest-Token"),
    db: AsyncSession = Depends(get_db),
):
    token = _guest_token_from_header(x_guest_token, guest_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="guest_token required")
    service = GuestService(db)
    count = await service.delete_expired_for_token(token)
    return {"message": f"Cleared {count} guest file(s)", "guest_token": token}


@router.post("/cleanup")
async def guest_cleanup(db: AsyncSession = Depends(get_db)):
    """Manual trigger for expired cleanup (also called lazily)."""
    count = await cleanup_expired(db)
    return {"cleaned": count}
