import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# -------------------------------------------------------------
# Multi-Tenancy: Organizations & Users
# -------------------------------------------------------------
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    memberships = relationship("OrganizationUser", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="organization", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="organization", cascade="all, delete-orphan")
    ai_providers = relationship("AIProvider", back_populates="organization", cascade="all, delete-orphan")
    mcp_servers = relationship("MCPServer", back_populates="organization", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="organization", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    memberships = relationship("OrganizationUser", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class OrganizationUser(Base):
    __tablename__ = "organization_users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, INVITED, SUSPENDED
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")
    role = relationship("Role")


# -------------------------------------------------------------
# RBAC: Roles & Permissions
# -------------------------------------------------------------
class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="roles")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'source.read', 'database.query'
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # source, document, database, report, mcp, web, agent, admin

    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


# -------------------------------------------------------------
# AI Gateway: Providers & Models
# -------------------------------------------------------------
class AIProvider(Base):
    __tablename__ = "ai_providers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(String(50), nullable=False)  # OPENAI, ANTHROPIC, OLLAMA, CUSTOM_OPENAI, MOCK
    base_url = Column(String(500), nullable=True)
    encrypted_api_key = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="ai_providers")
    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")


class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider_id = Column(String(36), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    model_id = Column(String(100), nullable=False)  # e.g., 'gpt-4o', 'claude-3-5-sonnet', 'text-embedding-3-small'
    model_type = Column(String(50), default="CHAT")  # CHAT, EMBEDDING, RERANK
    context_window = Column(Integer, default=128000)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    provider = relationship("AIProvider", back_populates="models")


# -------------------------------------------------------------
# Brains & Knowledge Scopes
# -------------------------------------------------------------
class Brain(Base):
    __tablename__ = "brains"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization")
    roles = relationship("BrainRole", back_populates="brain", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="brain")
    documents = relationship("Document", back_populates="brain")


class BrainRole(Base):
    __tablename__ = "brain_roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    brain_id = Column(String(36), ForeignKey("brains.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)

    brain = relationship("Brain", back_populates="roles")
    role = relationship("Role")


# -------------------------------------------------------------
# Data Sources & Schemas
# -------------------------------------------------------------
class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    brain_id = Column(String(36), ForeignKey("brains.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # POSTGRES, MYSQL, SQLITE, MONGODB
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_read_only = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="data_sources")
    brain = relationship("Brain", back_populates="data_sources")
    credentials = relationship("DataSourceCredential", back_populates="data_source", uselist=False, cascade="all, delete-orphan")
    schemas = relationship("DataSourceSchema", back_populates="data_source", cascade="all, delete-orphan")


class DataSourceCredential(Base):
    __tablename__ = "data_source_credentials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, unique=True)
    encrypted_connection_uri = Column(Text, nullable=False)
    encrypted_options = Column(Text, nullable=True)

    data_source = relationship("DataSource", back_populates="credentials")


class DataSourceSchema(Base):
    __tablename__ = "data_source_schemas"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1)
    raw_schema_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now)

    data_source = relationship("DataSource", back_populates="schemas")
    tables = relationship("DataSourceTable", back_populates="schema", cascade="all, delete-orphan")


class DataSourceTable(Base):
    __tablename__ = "data_source_tables"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    schema_id = Column(String(36), ForeignKey("data_source_schemas.id", ondelete="CASCADE"), nullable=False, index=True)
    table_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    row_count = Column(Integer, default=0)

    schema = relationship("DataSourceSchema", back_populates="tables")
    columns = relationship("DataSourceColumn", back_populates="table", cascade="all, delete-orphan")


class DataSourceColumn(Base):
    __tablename__ = "data_source_columns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    table_id = Column(String(36), ForeignKey("data_source_tables.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name = Column(String(100), nullable=False)
    data_type = Column(String(100), nullable=False)
    is_nullable = Column(Boolean, default=True)
    is_primary_key = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

    table = relationship("DataSourceTable", back_populates="columns")


# -------------------------------------------------------------
# Knowledge & RAG: Documents & Chunks
# -------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    brain_id = Column(String(36), ForeignKey("brains.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, csv, xlsx, md
    file_size = Column(Integer, default=0)
    storage_path = Column(String(500), nullable=False)
    status = Column(String(50), default="PROCESSING")  # PROCESSING, INDEXED, FAILED
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="documents")
    brain = relationship("Brain", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)  # page, section, classification, access_group
    embedding_vector = Column(JSON, nullable=True)  # Stored as list of floats for universal DB support

    document = relationship("Document", back_populates="chunks")


# -------------------------------------------------------------
# MCP: Model Context Protocol
# -------------------------------------------------------------
class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    transport_type = Column(String(50), default="STDIO")  # STDIO, SSE
    endpoint_url = Column(String(500), nullable=True)
    command = Column(String(500), nullable=True)
    status = Column(String(50), default="CONNECTED")  # CONNECTED, DISCONNECTED, ERROR
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="mcp_servers")
    tools = relationship("MCPTool", back_populates="server", cascade="all, delete-orphan")


class MCPTool(Base):
    __tablename__ = "mcp_tools"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    input_schema = Column(JSON, default=dict)
    is_approved = Column(Boolean, default=False)
    permission_required = Column(String(100), default="mcp.use")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    server = relationship("MCPServer", back_populates="tools")


# -------------------------------------------------------------
# Web Sources & Pages
# -------------------------------------------------------------
class WebSource(Base):
    __tablename__ = "web_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=False)
    crawl_depth = Column(Integer, default=1)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    pages = relationship("WebPage", back_populates="web_source", cascade="all, delete-orphan")


class WebPage(Base):
    __tablename__ = "web_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    web_source_id = Column(String(36), ForeignKey("web_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    web_source = relationship("WebSource", back_populates="pages")


# -------------------------------------------------------------
# Policy Engine: RBAC + Data Policies
# -------------------------------------------------------------
class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="policies")
    rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=True)
    resource_type = Column(String(50), nullable=False)  # SOURCE, TABLE, COLUMN, TOOL
    resource_name = Column(String(255), nullable=False)  # e.g., 'customers', 'employees.salary', 'sales_db'
    effect = Column(String(20), default="ALLOW")  # ALLOW, DENY
    row_filter_expr = Column(String(500), nullable=True)  # e.g., "country = 'IN'"
    allowed_columns = Column(JSON, nullable=True)  # List of allowed column names or None for all
    data_masking_rule = Column(String(100), nullable=True)  # REDACT, MASK_EMAIL, MASK_NUMERIC

    policy = relationship("Policy", back_populates="rules")
    role = relationship("Role")


# -------------------------------------------------------------
# Chat & Conversations
# -------------------------------------------------------------
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # USER, ASSISTANT, SYSTEM
    content = Column(Text, nullable=False)
    reasoning_summary = Column(Text, nullable=True)
    tool_calls_json = Column(JSON, default=list)
    citations_json = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")


# -------------------------------------------------------------
# Agent Runs, Execution Steps & Tool Calls
# -------------------------------------------------------------
class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="RUNNING")  # RUNNING, COMPLETED, FAILED
    intent = Column(String(100), nullable=True)
    plan_json = Column(JSON, default=list)
    intermediate_findings_json = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    conversation = relationship("Conversation", back_populates="agent_runs")
    steps = relationship("AgentStep", back_populates="agent_run", cascade="all, delete-orphan")
    tool_calls = relationship("ToolCall", back_populates="agent_run", cascade="all, delete-orphan")


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    step_type = Column(String(50), nullable=False)  # INTENT, PLAN, PERMISSION, TOOL, REASON, REPORT
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="COMPLETED")  # RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), default=utc_now)

    agent_run = relationship("AgentRun", back_populates="steps")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    tool_input = Column(JSON, default=dict)
    status = Column(String(50), default="RUNNING")  # RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), default=utc_now)

    agent_run = relationship("AgentRun", back_populates="tool_calls")
    result = relationship("ToolResult", back_populates="tool_call", uselist=False, cascade="all, delete-orphan")


class ToolResult(Base):
    __tablename__ = "tool_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tool_call_id = Column(String(36), ForeignKey("tool_calls.id", ondelete="CASCADE"), nullable=False, unique=True)
    output_json = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    tool_call = relationship("ToolCall", back_populates="result")


# -------------------------------------------------------------
# First-Class Reports
# -------------------------------------------------------------
class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content_markdown = Column(Text, nullable=False)
    data_sources_json = Column(JSON, default=list)
    query_references_json = Column(JSON, default=list)
    chart_configs_json = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="reports")


# -------------------------------------------------------------
# Audit Logs
# -------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    conversation_id = Column(String(36), nullable=True)
    agent_run_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)  # USER_LOGIN, SQL_QUERY_EXECUTED, DOCUMENT_ACCESSED, POLICY_DENIED, etc.
    resource_type = Column(String(50), nullable=True)  # DATABASE, TABLE, DOCUMENT, TOOL, REPORT
    resource_id = Column(String(255), nullable=True)
    status = Column(String(50), default="SUCCESS")  # SUCCESS, DENIED, ERROR
    ip_address = Column(String(45), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="audit_logs")
