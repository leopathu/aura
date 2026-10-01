import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.models import Document, DocumentChunk, User, AuditLog
from app.schemas.domain import DocumentResponse
from app.api.deps import get_current_user, get_current_organization_id, require_permission
from app.worker.tasks import run_document_ingestion_job
from app.brains.service import BrainService

router = APIRouter(prefix="/documents", tags=["Documents & Knowledge"])

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    accessible_ids = await BrainService.get_user_accessible_brain_ids(db, current_user.id, org_id)
    stmt = select(Document).where(Document.organization_id == org_id)
    if accessible_ids is not None:
        stmt = stmt.where((Document.brain_id.in_(accessible_ids)) | (Document.brain_id == None))
    stmt = stmt.order_by(Document.created_at.desc())

    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/upload", dependencies=[Depends(require_permission("document.upload"))])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    brain_id: Optional[str] = Form(None),
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    filename = file.filename or "uploaded_file"
    file_ext = filename.split(".")[-1].lower() if "." in filename else "txt"

    allowed_exts = {"pdf", "docx", "doc", "xlsx", "xls", "csv", "txt", "md", "json"}
    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type .{file_ext}. Allowed: {', '.join(allowed_exts)}"
        )

    # Ensure storage directory exists
    org_storage_dir = os.path.join(settings.STORAGE_DIR, org_id)
    os.makedirs(org_storage_dir, exist_ok=True)

    dest_path = os.path.join(org_storage_dir, filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(dest_path)

    doc = Document(
        organization_id=org_id,
        brain_id=brain_id,
        title=filename.rsplit(".", 1)[0].replace("_", " ").title(),
        file_name=filename,
        file_type=file_ext,
        file_size=file_size,
        storage_path=dest_path,
        status="PROCESSING",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Queue background parsing, chunking, and embedding
    background_tasks.add_task(run_document_ingestion_job, doc.id)

    audit = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action="DOCUMENT_UPLOADED",
        resource_type="DOCUMENT",
        resource_id=doc.id,
        status="SUCCESS",
        metadata_json={"filename": filename, "size_bytes": file_size}
    )
    db.add(audit)
    await db.commit()

    return {
        "id": doc.id,
        "title": doc.title,
        "file_name": doc.file_name,
        "status": doc.status,
        "message": "Document uploaded and processing queued"
    }

@router.get("/{id}")
async def get_document(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Document).where(Document.id == id, Document.organization_id == org_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_res = await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index).limit(5)
    )
    sample_chunks = chunks_res.scalars().all()

    return {
        "id": doc.id,
        "title": doc.title,
        "file_name": doc.file_name,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "created_at": doc.created_at.isoformat(),
        "sample_chunks": [
            {
                "chunk_index": c.chunk_index,
                "content": c.content[:300] + ("..." if len(c.content) > 300 else ""),
                "metadata": c.metadata_json
            }
            for c in sample_chunks
        ]
    }

@router.delete("/{id}", dependencies=[Depends(require_permission("document.delete"))])
async def delete_document(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Document).where(Document.id == id, Document.organization_id == org_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove file from disk
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception:
            pass

    await db.delete(doc)
    await db.commit()
    return {"status": "success", "message": "Document deleted"}

@router.post("/{id}/retry", dependencies=[Depends(require_permission("document.upload"))])
async def retry_document_indexing(
    id: str,
    background_tasks: BackgroundTasks,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Document).where(Document.id == id, Document.organization_id == org_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Clear old chunks
    old_chunks = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    for c in old_chunks.scalars().all():
        await db.delete(c)

    doc.status = "PROCESSING"
    doc.error_message = None
    doc.chunk_count = 0
    await db.commit()

    background_tasks.add_task(run_document_ingestion_job, doc.id)
    return {"status": "success", "message": "Document re-indexing queued"}
