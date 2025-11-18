from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from pathlib import Path
from app.db.session import get_db
from app.models.models import Document, Brain, User
from app.schemas.schemas import DocumentResponse
from app.api.deps import get_current_user
from app.api.v1.brains import check_brain_access
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store
from app.core.config import settings

router = APIRouter()


async def process_document_background(
    document_id: int,
    file_path: str,
    file_type: str,
    brain_id: int,
    db_url: str
):
    """Background task to process document."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            
            if document:
                # Process document
                vector_ids = await document_processor.process_document(
                    file_path=file_path,
                    file_type=file_type,
                    brain_id=brain_id,
                    document_id=document_id,
                    metadata={
                        "filename": document.original_filename,
                        "source": document.source
                    }
                )
                
                # Update document
                document.vector_ids = vector_ids
                document.is_processed = True
                await db.commit()
        except Exception as e:
            # Update document with error
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if document:
                document.processing_error = str(e)
                await db.commit()


@router.post("/{brain_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    brain_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload document to brain."""
    # Check brain access
    result = await db.execute(select(Brain).where(Brain.id == brain_id))
    brain = result.scalar_one_or_none()
    
    if not brain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain not found"
        )
    
    if not await check_brain_access(brain, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Get file type
    file_extension = Path(file.filename).suffix.lower().replace(".", "")
    allowed_types = ["pdf", "docx", "doc", "txt", "png", "jpg", "jpeg"]
    
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(allowed_types)}"
        )
    
    # Save file
    file_path = await document_processor.save_file(file_content, file.filename, brain_id)
    
    # Create document record
    document = Document(
        brain_id=brain_id,
        filename=Path(file_path).name,
        original_filename=file.filename,
        file_type=file_extension,
        file_path=file_path,
        file_size=len(file_content),
        source="upload"
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Process document in background
    background_tasks.add_task(
        process_document_background,
        document.id,
        file_path,
        file_extension,
        brain_id,
        str(settings.DATABASE_URL)
    )
    
    return document


@router.get("/{brain_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    brain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all documents in a brain."""
    # Check brain access
    result = await db.execute(select(Brain).where(Brain.id == brain_id))
    brain = result.scalar_one_or_none()
    
    if not brain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain not found"
        )
    
    if not await check_brain_access(brain, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get documents
    result = await db.execute(
        select(Document).where(Document.brain_id == brain_id).order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    
    return documents


@router.delete("/{brain_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    brain_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document."""
    # Check brain access
    result = await db.execute(select(Brain).where(Brain.id == brain_id))
    brain = result.scalar_one_or_none()
    
    if not brain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain not found"
        )
    
    if brain.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only brain owner can delete documents"
        )
    
    # Get document
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.brain_id == brain_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from vector store
    vector_store.delete_by_document(document_id)
    
    # Delete file
    await document_processor.delete_file(document.file_path)
    
    # Delete document record
    await db.delete(document)
    await db.commit()
    
    return None
