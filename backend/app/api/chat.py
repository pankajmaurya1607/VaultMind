from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.rbac.dependencies import get_effective_department_ids
from pydantic import BaseModel

from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse, MessageResponse, Source
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


class RenameRequest(BaseModel):
    title: str


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    dept_ids = get_effective_department_ids(current_user)
    result = await service.chat(body.question, current_user.id, dept_ids, body.session_id)
    return ChatResponse(
        session_id=result["session_id"],
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
        confidence_score=result["confidence_score"],
        tokens_used=result["tokens_used"],
        latency_ms=result["latency_ms"],
        model=result.get("model", "template"),
        model_provider=result.get("model_provider", "fallback"),
    )


@router.get("/history", response_model=list[ChatHistoryResponse])
async def chat_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    sessions = await service.get_history_with_counts(current_user.id)
    return [
        ChatHistoryResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            message_count=count,
        )
        for s, count in sessions
    ]


@router.get("/history/{session_id}", response_model=list[MessageResponse])
async def chat_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    messages = await service.get_messages(session_id, current_user.id)
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=m.sources,
            confidence_score=m.confidence_score,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.patch("/history/{session_id}", response_model=ChatHistoryResponse)
async def rename_chat(
    session_id: int,
    body: RenameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    session = await service.rename_session(session_id, current_user.id, body.title)
    if not session:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    # get count
    from app.repositories.chat import ChatSessionRepository, MessageRepository

    # reuse count logic
    count = len(await service.get_messages(session_id, current_user.id))
    return ChatHistoryResponse(id=session.id, title=session.title, created_at=session.created_at, message_count=count)


@router.delete("/history/{session_id}")
async def delete_chat(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    ok = await service.delete_session(session_id, current_user.id)
    if not ok:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return {"message": "Chat deleted"}
