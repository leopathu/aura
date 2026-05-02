"""Document ingestion and management routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    payload: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Ingest a document into the RAG pipeline (chunk + embed + store)."""
    svc = RAGService(db)
    return await svc.ingest_document(payload)


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DocumentResponse]:
    """Return a paginated list of all ingested documents."""
    repo = DocumentRepository(db)
    documents = await repo.list_all(limit=limit, offset=offset)
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentResponse:
    """Fetch a single document by UUID."""
    repo = DocumentRepository(db)
    document = await repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    payload: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentResponse:
    """Update document metadata (title, source)."""
    repo = DocumentRepository(db)
    document = await repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    updated = await repo.update(document, payload)
    return DocumentResponse.model_validate(updated)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    """Delete a document and all its associated chunks."""
    repo = DocumentRepository(db)
    document = await repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await repo.delete(document)
