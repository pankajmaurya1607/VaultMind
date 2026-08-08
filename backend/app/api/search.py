from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.rbac.dependencies import get_effective_department_ids
from app.schemas.chat import SearchRequest, SearchResponse, SearchResult
from app.services.chat import ChatService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    dept_ids = get_effective_department_ids(current_user)
    results = await service.search(body.query, dept_ids, body.top_k)
    return SearchResponse(
        results=[
            SearchResult(
                document_id=r["document_id"],
                filename=r["filename"],
                chunk_index=r["chunk_index"],
                text=r["text"],
                score=r["score"],
                metadata=r.get("metadata", {}),
            )
            for r in results
        ],
        total=len(results),
    )
