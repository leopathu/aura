from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List
from app.db.models.organization import MemberRole

class OrganizationBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MembershipBase(BaseModel):
    role: MemberRole

class MembershipCreate(BaseModel):
    user_email: str
    role: MemberRole = MemberRole.MEMBER

class MembershipResponse(BaseModel):
    user_id: UUID4
    org_id: UUID4
    role: MemberRole
    joined_at: datetime
    
    class Config:
        from_attributes = True

class OrganizationWithRole(OrganizationResponse):
    role: MemberRole
