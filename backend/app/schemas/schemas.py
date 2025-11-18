from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from app.models.models import BrainVisibility


# Organization Schemas
class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: int
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Role Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[dict] = {}


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[dict] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Department Schemas
class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Team Schemas
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: Optional[int] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str
    organization_name: str
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    role_ids: Optional[List[int]] = []


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    role_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    organization_id: int
    department_id: Optional[int]
    team_id: Optional[int]
    is_active: bool
    is_superuser: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    roles: List[RoleResponse] = []
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenWithUser(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Brain Schemas
class BrainBase(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: BrainVisibility = BrainVisibility.PRIVATE
    settings: Optional[dict] = {}


class BrainCreate(BrainBase):
    role_ids: Optional[List[int]] = []
    department_ids: Optional[List[int]] = []
    team_ids: Optional[List[int]] = []


class BrainUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[BrainVisibility] = None
    settings: Optional[dict] = None
    role_ids: Optional[List[int]] = None
    department_ids: Optional[List[int]] = None
    team_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class BrainResponse(BrainBase):
    id: int
    organization_id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    assigned_roles: List[RoleResponse] = []
    assigned_departments: List[DepartmentResponse] = []
    assigned_teams: List[TeamResponse] = []
    
    class Config:
        from_attributes = True


# Document Schemas
class DocumentBase(BaseModel):
    filename: str
    file_type: str
    source: str = "upload"


class DocumentResponse(DocumentBase):
    id: int
    brain_id: int
    original_filename: str
    file_path: str
    file_size: int
    source_url: Optional[str]
    is_processed: bool
    processing_error: Optional[str]
    metadata: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Chat Schemas
class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: List[dict] = []
    metadata: dict = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    brain_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    brain_id: int
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    session_id: int
    message: ChatMessageResponse
    sources: List[DocumentResponse] = []


# Search Schemas
class SearchRequest(BaseModel):
    query: str
    brain_id: int
    limit: int = 10


class SearchResult(BaseModel):
    document: DocumentResponse
    score: float
    content: str
    page: Optional[int] = None
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
