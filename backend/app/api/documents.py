from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.rbac.dependencies import get_effective_department_ids, require_admin
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.audit import audit_event
from app.services.document import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    doc = await service.upload(file, current_user.id, current_user.department_id)
    await audit_event(
        request,
        db,
        action="upload",
        resource="document",
        resource_id=doc.id,
        details=doc.original_filename,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return DocumentUploadResponse(id=doc.id, filename=doc.original_filename, status=doc.status.value)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    dept_ids = get_effective_department_ids(current_user)
    if current_user.role.name == "Admin":
        docs = await service.get_all_documents(skip, limit)
    else:
        docs = await service.get_user_documents(current_user.id, dept_ids, skip, limit)
    return [
        DocumentResponse(
            id=d.id,
            original_filename=d.original_filename,
            file_size=d.file_size,
            mime_type=d.mime_type,
            status=d.status.value if hasattr(d.status, "value") else d.status,
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
        status=doc.status.value if hasattr(doc.status, "value") else doc.status,
        uploaded_by=doc.uploaded_by,
        department_id=doc.department_id,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await require_admin(current_user)
    except HTTPException as exc:
        await audit_event(
            request,
            db,
            action="rbac_denied",
            resource="document",
            resource_id=document_id,
            details=f"user {current_user.email} attempted admin delete",
            user_id=current_user.id,
            user_email=current_user.email,
            success=False,
        )
        raise exc

    service = DocumentService(db)
    deleted = await service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await audit_event(
        request,
        db,
        action="delete",
        resource="document",
        resource_id=document_id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return {"message": "Document deleted successfully"}
