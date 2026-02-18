"""
Credentials API Endpoints
Handles encrypted credential management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import httpx

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.credential import (
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialTestRequest,
    CredentialTestResponse
)
from app.services import credential_service, organization_service


router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.get("", response_model=List[CredentialResponse])
async def list_credentials(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all credentials for an organization
    
    Requires organization membership
    """
    # Check if user is a member
    is_member = await organization_service.is_org_member(db, current_user.id, org_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    
    credentials = await credential_service.get_organization_credentials(db, org_id)
    
    # Add masked keys to response
    response_credentials = []
    for cred in credentials:
        cred_dict = CredentialResponse.from_orm(cred).dict()
        
        # Decrypt and mask the API key (show only last 4 chars)
        try:
            decrypted = await credential_service.get_decrypted_api_key(db, cred.id)
            if decrypted and len(decrypted) > 4:
                cred_dict['masked_key'] = '••••' + decrypted[-4:]
            else:
                cred_dict['masked_key'] = '••••••'
        except Exception:
            cred_dict['masked_key'] = '••••••'
        
        response_credentials.append(CredentialResponse(**cred_dict))
    
    return response_credentials


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    org_id: UUID,
    credential_data: CredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new encrypted credential
    
    Requires admin or owner role
    """
    # Check if user is admin or owner
    is_admin = await organization_service.is_org_admin(db, current_user.id, org_id)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can add credentials"
        )
    
    # Validate credential type
    if not credential_service.validate_credential_type(credential_data.credential_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credential type"
        )
    
    # Create credential
    credential = await credential_service.create_credential(
        db,
        org_id,
        credential_data.credential_type,
        credential_data.api_key,
        credential_data.label
    )
    
    # Return response with masked key
    response = CredentialResponse.from_orm(credential)
    if len(credential_data.api_key) > 4:
        response.masked_key = '••••' + credential_data.api_key[-4:]
    else:
        response.masked_key = '••••••'
    
    return response


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: UUID,
    credential_data: CredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update credential label
    
    Requires admin or owner role
    """
    # Get credential
    credential = await credential_service.get_credential_by_id(db, credential_id)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    # Check if user is admin or owner
    is_admin = await organization_service.is_org_admin(db, current_user.id, credential.org_id)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can update credentials"
        )
    
    # Update credential
    updated_credential = await credential_service.update_credential_label(
        db,
        credential_id,
        credential_data.label
    )
    
    # Return response with masked key
    response = CredentialResponse.from_orm(updated_credential)
    try:
        decrypted = await credential_service.get_decrypted_api_key(db, credential_id)
        if decrypted and len(decrypted) > 4:
            response.masked_key = '••••' + decrypted[-4:]
        else:
            response.masked_key = '••••••'
    except Exception:
        response.masked_key = '••••••'
    
    return response


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a credential
    
    Requires admin or owner role
    """
    # Get credential
    credential = await credential_service.get_credential_by_id(db, credential_id)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    # Check if user is admin or owner
    is_admin = await organization_service.is_org_admin(db, current_user.id, credential.org_id)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can delete credentials"
        )
    
    # Delete credential
    await credential_service.delete_credential(db, credential_id)
    
    return None


@router.post("/test", response_model=CredentialTestResponse)
async def test_credential(
    test_request: CredentialTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test if a credential is valid by making a simple API call
    
    Requires organization membership
    """
    # Get credential
    credential = await credential_service.get_credential_by_id(db, test_request.credential_id)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    # Check if user is a member
    is_member = await organization_service.is_org_member(db, current_user.id, credential.org_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    
    # Get decrypted API key
    api_key = await credential_service.get_decrypted_api_key(db, test_request.credential_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt API key"
        )
    
    # Test based on provider
    try:
        if credential.credential_type == 'openai':
            # Test OpenAI API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {api_key}'},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return CredentialTestResponse(
                        success=True,
                        message="OpenAI API key is valid",
                        provider="OpenAI"
                    )
                else:
                    return CredentialTestResponse(
                        success=False,
                        message=f"Invalid API key: {response.status_code}",
                        provider="OpenAI"
                    )
        
        elif credential.credential_type == 'anthropic':
            # Test Anthropic API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': api_key,
                        'anthropic-version': '2023-06-01',
                        'content-type': 'application/json'
                    },
                    json={
                        'model': 'claude-3-haiku-20240307',
                        'max_tokens': 1,
                        'messages': [{'role': 'user', 'content': 'test'}]
                    },
                    timeout=10.0
                )
                
                if response.status_code in [200, 400]:  # 400 is OK for validation
                    return CredentialTestResponse(
                        success=True,
                        message="Anthropic API key is valid",
                        provider="Anthropic"
                    )
                else:
                    return CredentialTestResponse(
                        success=False,
                        message=f"Invalid API key: {response.status_code}",
                        provider="Anthropic"
                    )
        
        elif credential.credential_type == 'google_gemini':
            # Test Google Gemini API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://generativelanguage.googleapis.com/v1/models?key={api_key}',
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return CredentialTestResponse(
                        success=True,
                        message="Google Gemini API key is valid",
                        provider="Google Gemini"
                    )
                else:
                    return CredentialTestResponse(
                        success=False,
                        message=f"Invalid API key: {response.status_code}",
                        provider="Google Gemini"
                    )
        
        else:
            return CredentialTestResponse(
                success=False,
                message=f"Testing not implemented for {credential.credential_type}",
                provider=credential.credential_type
            )
    
    except httpx.TimeoutException:
        return CredentialTestResponse(
            success=False,
            message="Request timeout - API may be unavailable",
            provider=credential.credential_type
        )
    except Exception as e:
        return CredentialTestResponse(
            success=False,
            message=f"Error testing credential: {str(e)}",
            provider=credential.credential_type
        )
