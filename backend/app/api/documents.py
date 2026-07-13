from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.rbac.dependencies import require_manager
from app.services.document import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    doc = await service.upload(file, current_user.id, current_user.department_id)
    return DocumentUploadResponse(id=doc.id, filename=doc.original_filename, status=doc.status.value)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    if current_user.role.name == "Admin":
        from app.repositories.document import DocumentRepository
        repo = DocumentRepository(db)
        docs = await repo.list(skip, limit)
    else:
        docs = await service.get_user_documents(current_user.id, skip, limit)

    return [
        DocumentResponse(
            id=d.id,
            original_filename=d.original_filename,
            file_size=d.file_size,
            mime_type=d.mime_type,
            status=d.status.value if hasattr(d.status, 'value') else d.status,
            uploaded_by=d.uploaded_by,
            department_id=d.department_id,
            chunk_count=d.chunk_count,
            error_message=d.error_message,
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    doc = await service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if current_user.role.name != "Admin" and doc.uploaded_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return DocumentResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        status=doc.status.value if hasattr(doc.status, 'value') else doc.status,
        uploaded_by=doc.uploaded_by,
        department_id=doc.department_id,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.rbac.dependencies import require_admin
    await require_admin(current_user)
    service = DocumentService(db)
    deleted = await service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"message": "Document deleted successfully"}
