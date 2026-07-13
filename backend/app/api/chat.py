from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, Source, ChatHistoryResponse, MessageResponse
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.rbac.dependencies import get_effective_department_ids
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


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
    )


@router.get("/history", response_model=list[ChatHistoryResponse])
async def chat_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    sessions = await service.get_history(current_user.id)
    return [
        ChatHistoryResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            message_count=len(s.messages) if hasattr(s, 'messages') and s.messages else 0,
        )
        for s in sessions
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
