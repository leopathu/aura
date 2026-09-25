from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# Auth
class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization_name: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    organization: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    is_superuser: bool

# Organization
class OrganizationCreate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime

# RBAC
class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_codes: List[str] = Field(default_factory=list)

class RoleResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    is_system: bool
    permissions: List[str] = Field(default_factory=list)

class AssignRoleRequest(BaseModel):
    user_id: str
    role_id: str

# AI Models
class AIProviderCreate(BaseModel):
    name: str
    provider_type: str  # OPENAI, ANTHROPIC, OLLAMA, CUSTOM_OPENAI, MOCK
    base_url: Optional[str] = None
    api_key: Optional[str] = None

class AIProviderResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    base_url: Optional[str]
    is_active: bool

# Data Sources
class DataSourceCreate(BaseModel):
    name: str
    type: str  # POSTGRES, MYSQL, SQLITE
    connection_uri: str
    description: Optional[str] = None
    is_read_only: bool = True

class DataSourceResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    type: str
    description: Optional[str]
    is_active: bool
    is_read_only: bool
    created_at: datetime

class DirectQueryRequest(BaseModel):
    sql_query: str

# Documents
class DocumentResponse(BaseModel):
    id: str
    title: str
    file_name: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: Optional[str]
    created_at: datetime

# Policies
class PolicyRuleCreate(BaseModel):
    role_id: Optional[str] = None
    resource_type: str  # TABLE, COLUMN, TOOL
    resource_name: str
    effect: str = "ALLOW"  # ALLOW, DENY
    row_filter_expr: Optional[str] = None
    allowed_columns: Optional[List[str]] = None
    data_masking_rule: Optional[str] = None

class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rules: List[PolicyRuleCreate] = Field(default_factory=list)

class PolicyResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    is_active: bool
    rules: List[Dict[str, Any]] = Field(default_factory=list)

# MCP
class MCPServerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    transport_type: str = "STDIO"
    endpoint_url: Optional[str] = None
    command: Optional[str] = None

class MCPServerResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    transport_type: str
    endpoint_url: Optional[str]
    status: str
    tools: List[Dict[str, Any]] = Field(default_factory=list)

# Chat & Conversation
class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    sender: str
    content: str
    reasoning_summary: Optional[str]
    tool_calls: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    created_at: datetime

# Reports
class ReportResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str]
    content_markdown: str
    data_sources: List[str] = Field(default_factory=list)
    created_at: datetime

# Audit
class AuditLogResponse(BaseModel):
    id: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    status: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
