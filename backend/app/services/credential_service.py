"""
Credential Service
Business logic for credential management
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.credential import Credential
from app.services.encryption_service import encryption_service


async def create_credential(
    db: Session,
    org_id: UUID,
    credential_type: str,
    api_key: str,
    label: Optional[str] = None
) -> Credential:
    """
    Create a new encrypted credential
    
    Args:
        db: Database session
        org_id: Organization ID
        credential_type: Type of credential (openai, anthropic, gemini, etc.)
        api_key: API key to encrypt
        label: Optional label for the credential
        
    Returns:
        Created credential
    """
    # Encrypt the API key
    encrypted_value = encryption_service.encrypt(api_key)
    
    credential = Credential(
        org_id=org_id,
        credential_type=credential_type,
        encrypted_value=encrypted_value,
        label=label
    )
    
    db.add(credential)
    db.commit()
    db.refresh(credential)
    
    return credential


async def get_credential_by_id(db: Session, credential_id: UUID) -> Optional[Credential]:
    """
    Get credential by ID
    
    Args:
        db: Database session
        credential_id: Credential ID
        
    Returns:
        Credential or None
    """
    return db.query(Credential).filter(Credential.id == credential_id).first()


async def get_organization_credentials(
    db: Session,
    org_id: UUID,
    credential_type: Optional[str] = None
) -> List[Credential]:
    """
    Get all credentials for an organization
    
    Args:
        db: Database session
        org_id: Organization ID
        credential_type: Optional filter by credential type
        
    Returns:
        List of credentials
    """
    query = db.query(Credential).filter(Credential.org_id == org_id)
    
    if credential_type:
        query = query.filter(Credential.credential_type == credential_type)
    
    return query.order_by(Credential.created_at.desc()).all()


async def update_credential_label(
    db: Session,
    credential_id: UUID,
    label: str
) -> Optional[Credential]:
    """
    Update credential label
    
    Args:
        db: Database session
        credential_id: Credential ID
        label: New label
        
    Returns:
        Updated credential or None
    """
    credential = await get_credential_by_id(db, credential_id)
    if not credential:
        return None
    
    credential.label = label
    db.commit()
    db.refresh(credential)
    
    return credential


async def delete_credential(db: Session, credential_id: UUID) -> bool:
    """
    Delete a credential
    
    Args:
        db: Database session
        credential_id: Credential ID
        
    Returns:
        True if deleted, False if not found
    """
    credential = await get_credential_by_id(db, credential_id)
    if not credential:
        return False
    
    db.delete(credential)
    db.commit()
    
    return True


async def get_decrypted_api_key(db: Session, credential_id: UUID) -> Optional[str]:
    """
    Get decrypted API key from credential
    
    Args:
        db: Database session
        credential_id: Credential ID
        
    Returns:
        Decrypted API key or None
    """
    credential = await get_credential_by_id(db, credential_id)
    if not credential:
        return None
    
    return encryption_service.decrypt(credential.encrypted_value)


def validate_credential_type(credential_type: str) -> bool:
    """
    Validate credential type
    
    Args:
        credential_type: Type to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_types = [
        'openai',
        'anthropic',
        'google_gemini',
        'cohere',
        'huggingface'
    ]
    
    return credential_type in valid_types
