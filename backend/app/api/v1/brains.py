"""Brain CRUD and document-association routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import AuraException
from app.db.session import get_db
from app.models.user import User
from app.schemas.brain import BrainCreate, BrainDocumentResponse, BrainResponse, BrainUpdate
from app.services.brain_service import BrainService

router = APIRouter(prefix="/brains", tags=["Brains"])


@router.post("", response_model=BrainResponse, status_code=status.HTTP_201_CREATED)
async def create_brain(
    payload: BrainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrainResponse:
    """Create a new brain."""
    svc = BrainService(db)
    brain = await svc.create(current_user.id, payload)
    return BrainResponse.model_validate(brain)


@router.get("", response_model=list[BrainResponse])
async def list_brains(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BrainResponse]:
    """List all brains owned by the current user."""
    svc = BrainService(db)
    brains = await svc.list_for_user(current_user.id)
    return [BrainResponse.model_validate(b) for b in brains]


@router.get("/{brain_id}", response_model=BrainResponse)
async def get_brain(
    brain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrainResponse:
    """Fetch a single brain."""
    try:
        svc = BrainService(db)
        brain = await svc.get(brain_id, current_user.id)
        return BrainResponse.model_validate(brain)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.patch("/{brain_id}", response_model=BrainResponse)
async def update_brain(
    brain_id: uuid.UUID,
    payload: BrainUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrainResponse:
    """Update a brain's name or description."""
    try:
        svc = BrainService(db)
        brain = await svc.update(brain_id, current_user.id, payload)
        return BrainResponse.model_validate(brain)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.delete("/{brain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brain(
    brain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a brain."""
    try:
        svc = BrainService(db)
        await svc.delete(brain_id, current_user.id)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


# ------------------------------------------------------------------
# Document association endpoints
# ------------------------------------------------------------------


@router.get("/{brain_id}/documents", response_model=list[BrainDocumentResponse])
async def list_brain_documents(
    brain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BrainDocumentResponse]:
    """List all documents connected to a brain."""
    try:
        svc = BrainService(db)
        docs = await svc.list_documents(brain_id, current_user.id)
        return [BrainDocumentResponse.model_validate(d) for d in docs]
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.post("/{brain_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_document_to_brain(
    brain_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Attach a document to a brain."""
    try:
        svc = BrainService(db)
        await svc.add_document(brain_id, document_id, current_user.id)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.delete("/{brain_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document_from_brain(
    brain_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Detach a document from a brain."""
    try:
        svc = BrainService(db)
        await svc.remove_document(brain_id, document_id, current_user.id)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
