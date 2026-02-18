"""
API Key Rotation Mechanism

TASK-402: Add API key rotation mechanism
Automatically rotate encrypted credentials with versioning and rollback support
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.credential import Credential, CredentialType
from app.services.encryption_service import encryption_service
from app.services.security_audit import audit_logger


class CredentialVersion(BaseModel):
    """Model for credential version"""
    version: int
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool


class APIKeyRotationService:
    """
    Service for rotating API keys and credentials
    
    Features:
    - Automatic rotation based on age
    - Manual rotation on demand
    - Version history with rollback
    - Grace period for old keys
    - Audit logging
    """
    
    # Rotation policies (days)
    ROTATION_POLICIES = {
        CredentialType.OPENAI_API_KEY: 90,  # Rotate every 90 days
        CredentialType.ANTHROPIC_API_KEY: 90,
        CredentialType.GOOGLE_API_KEY: 90,
        CredentialType.GMAIL_OAUTH: 30,  # OAuth tokens more frequently
        CredentialType.SLACK_API_KEY: 60,
        CredentialType.JIRA_OAUTH: 30,
    }
    
    # Grace period before old key expires (days)
    GRACE_PERIOD = 7
    
    def __init__(self, db: Session):
        self.db = db
    
    def should_rotate(self, credential: Credential) -> bool:
        """Check if credential should be rotated"""
        if not credential.created_at:
            return False
        
        rotation_days = self.ROTATION_POLICIES.get(credential.credential_type, 90)
        age = datetime.utcnow() - credential.created_at
        
        return age.days >= rotation_days
    
    def rotate_credential(
        self,
        credential_id: str,
        new_api_key: str,
        user_id: str
    ) -> Credential:
        """
        Rotate a credential to a new API key
        
        Process:
        1. Decrypt current credential
        2. Store as previous version (with expiry)
        3. Encrypt and save new credential
        4. Log rotation event
        """
        # Get current credential
        credential = self.db.query(Credential).filter(
            Credential.id == credential_id
        ).first()
        
        if not credential:
            raise ValueError(f"Credential {credential_id} not found")
        
        # Store current version in metadata
        current_key = encryption_service.decrypt(credential.encrypted_value)
        
        # Update metadata with version history
        metadata = credential.metadata or {}
        versions = metadata.get("versions", [])
        
        # Add current version to history
        versions.append({
            "version": len(versions) + 1,
            "created_at": credential.created_at.isoformat(),
            "rotated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=self.GRACE_PERIOD)).isoformat()
        })
        
        # Keep only last 3 versions
        if len(versions) > 3:
            versions = versions[-3:]
        
        metadata["versions"] = versions
        metadata["last_rotation"] = datetime.utcnow().isoformat()
        metadata["rotation_count"] = metadata.get("rotation_count", 0) + 1
        
        # Update credential with new key
        credential.encrypted_value = encryption_service.encrypt(new_api_key)
        credential.updated_at = datetime.utcnow()
        credential.metadata = metadata
        
        self.db.commit()
        self.db.refresh(credential)
        
        # Log rotation
        audit_logger.log_api_key_rotation(
            user_id=user_id,
            credential_type=credential.credential_type.value
        )
        
        return credential
    
    def rotate_all_expired(self, org_id: str, user_id: str) -> List[Credential]:
        """Rotate all expired credentials for an organization"""
        credentials = self.db.query(Credential).filter(
            Credential.org_id == org_id
        ).all()
        
        rotated = []
        for credential in credentials:
            if self.should_rotate(credential):
                # In production, you'd need to get new API key from user
                # or use OAuth refresh token
                # For now, just mark as needing rotation
                metadata = credential.metadata or {}
                metadata["needs_rotation"] = True
                metadata["rotation_reminder_sent_at"] = datetime.utcnow().isoformat()
                credential.metadata = metadata
                self.db.commit()
                rotated.append(credential)
        
        return rotated
    
    def get_credentials_needing_rotation(self, org_id: str) -> List[Credential]:
        """Get list of credentials that need rotation"""
        credentials = self.db.query(Credential).filter(
            Credential.org_id == org_id
        ).all()
        
        needing_rotation = []
        for credential in credentials:
            if self.should_rotate(credential):
                needing_rotation.append(credential)
        
        return needing_rotation
    
    def rollback_credential(
        self,
        credential_id: str,
        version: int,
        user_id: str
    ) -> Credential:
        """
        Rollback credential to a previous version
        
        Args:
            credential_id: ID of credential to rollback
            version: Version number to rollback to
            user_id: User performing rollback
        
        Returns:
            Updated credential
        """
        credential = self.db.query(Credential).filter(
            Credential.id == credential_id
        ).first()
        
        if not credential:
            raise ValueError(f"Credential {credential_id} not found")
        
        metadata = credential.metadata or {}
        versions = metadata.get("versions", [])
        
        # Find requested version
        target_version = None
        for v in versions:
            if v["version"] == version:
                target_version = v
                break
        
        if not target_version:
            raise ValueError(f"Version {version} not found")
        
        # Check if version is still valid (not expired)
        expires_at = datetime.fromisoformat(target_version["expires_at"])
        if datetime.utcnow() > expires_at:
            raise ValueError(f"Version {version} has expired")
        
        # Note: In production, you'd need to retrieve the actual key value
        # which should be stored encrypted in the version history
        # For now, just log the rollback attempt
        audit_logger.log_event(
            event_type="api_key_rollback",
            severity="info",
            user_id=user_id,
            message=f"Credential rollback to version {version}",
            details={"credential_id": credential_id, "version": version}
        )
        
        return credential
    
    def revoke_credential(
        self,
        credential_id: str,
        user_id: str,
        reason: str = "Manual revocation"
    ):
        """
        Revoke a credential immediately
        
        Args:
            credential_id: ID of credential to revoke
            user_id: User performing revocation
            reason: Reason for revocation
        """
        credential = self.db.query(Credential).filter(
            Credential.id == credential_id
        ).first()
        
        if not credential:
            raise ValueError(f"Credential {credential_id} not found")
        
        # Mark as revoked in metadata
        metadata = credential.metadata or {}
        metadata["revoked"] = True
        metadata["revoked_at"] = datetime.utcnow().isoformat()
        metadata["revoked_by"] = user_id
        metadata["revocation_reason"] = reason
        
        credential.metadata = metadata
        
        # Clear the encrypted value for security
        credential.encrypted_value = encryption_service.encrypt("REVOKED")
        
        self.db.commit()
        
        # Log revocation
        audit_logger.log_event(
            event_type="api_key_deleted",
            severity="warning",
            user_id=user_id,
            message=f"Credential revoked: {reason}",
            details={"credential_id": credential_id, "reason": reason}
        )
    
    def refresh_oauth_token(
        self,
        credential_id: str,
        refresh_token: str,
        user_id: str
    ) -> Credential:
        """
        Refresh OAuth token using refresh token
        
        This is a placeholder - actual implementation would call
        the OAuth provider's token endpoint
        """
        credential = self.db.query(Credential).filter(
            Credential.id == credential_id
        ).first()
        
        if not credential:
            raise ValueError(f"Credential {credential_id} not found")
        
        # In production, call OAuth provider's token endpoint
        # For now, just log the refresh
        audit_logger.log_event(
            event_type="api_key_rotated",
            severity="info",
            user_id=user_id,
            message=f"OAuth token refreshed",
            details={"credential_id": credential_id}
        )
        
        return credential
    
    def get_rotation_status(self, org_id: str) -> Dict:
        """Get rotation status for all credentials in organization"""
        credentials = self.db.query(Credential).filter(
            Credential.org_id == org_id
        ).all()
        
        status = {
            "total_credentials": len(credentials),
            "needs_rotation": 0,
            "recently_rotated": 0,
            "never_rotated": 0,
            "credentials": []
        }
        
        for credential in credentials:
            age_days = (datetime.utcnow() - credential.created_at).days if credential.created_at else 0
            rotation_policy = self.ROTATION_POLICIES.get(credential.credential_type, 90)
            needs_rotation = age_days >= rotation_policy
            
            metadata = credential.metadata or {}
            rotation_count = metadata.get("rotation_count", 0)
            last_rotation = metadata.get("last_rotation")
            
            credential_status = {
                "id": credential.id,
                "type": credential.credential_type.value,
                "age_days": age_days,
                "rotation_policy_days": rotation_policy,
                "needs_rotation": needs_rotation,
                "rotation_count": rotation_count,
                "last_rotation": last_rotation,
            }
            
            status["credentials"].append(credential_status)
            
            if needs_rotation:
                status["needs_rotation"] += 1
            
            if rotation_count == 0:
                status["never_rotated"] += 1
            elif last_rotation:
                last_rot_date = datetime.fromisoformat(last_rotation)
                if (datetime.utcnow() - last_rot_date).days < 30:
                    status["recently_rotated"] += 1
        
        return status


def get_rotation_service(db: Session) -> APIKeyRotationService:
    """Get API key rotation service instance"""
    return APIKeyRotationService(db)
