from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.credential import Credential
from app.schemas.credential import CredentialCreate, CredentialResponse, CredentialUpdate
from app.api.dependencies import get_current_user, get_current_org
from app.core.encryption import encryption_service
from typing import List
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    org_id: UUID,
    cred_data: CredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new credential (BYO API Key)."""
    # Verify org access
    await get_current_org(org_id, current_user, db)
    
    # Encrypt API key
    encrypted_key = encryption_service.encrypt(cred_data.api_key)
    
    # Create credential
    credential = Credential(
        user_id=current_user.id,
        org_id=org_id,
        credential_type=cred_data.credential_type,
        encrypted_api_key=encrypted_key,
        label=cred_data.label
    )
    
    db.add(credential)
    db.commit()
    db.refresh(credential)
    
    return credential

@router.get("/", response_model=List[CredentialResponse])
async def list_credentials(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all credentials for an organization."""
    # Verify org access
    await get_current_org(org_id, current_user, db)
    
    credentials = db.query(Credential).filter(
        Credential.org_id == org_id
    ).all()
    
    return credentials

@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    org_id: UUID,
    credential_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a credential."""
    # Verify org access
    await get_current_org(org_id, current_user, db)
    
    credential = db.query(Credential).filter(
        Credential.id == credential_id,
        Credential.org_id == org_id
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    db.delete(credential)
    db.commit()
    
    return None
