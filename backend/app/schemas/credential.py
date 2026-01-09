from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
from app.db.models.credential import CredentialType

class CredentialBase(BaseModel):
    credential_type: CredentialType
    label: Optional[str] = None

class CredentialCreate(CredentialBase):
    api_key: str  # Will be encrypted before storage

class CredentialUpdate(BaseModel):
    label: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None

class CredentialResponse(CredentialBase):
    id: UUID4
    org_id: UUID4
    is_active: bool
    created_at: datetime
    # Note: Never return the encrypted_api_key
    
    class Config:
        from_attributes = True
