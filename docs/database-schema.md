# Aura AI Agent Platform - Database Schema

## Overview

The Aura platform uses PostgreSQL as the primary relational database and Milvus (or pgvector) for vector embeddings. This document defines the complete database schema with entity relationships, constraints, and indexes.

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Database Schema ERD                               │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  organizations   │         │      users       │
├──────────────────┤         ├──────────────────┤
│ id (PK)          │────┐    │ id (PK)          │
│ name             │    │    │ email (UNIQUE)   │
│ slug (UNIQUE)    │    │    │ hashed_password  │
│ settings         │    │    │ full_name        │
│ created_at       │    │    │ is_active        │
│ updated_at       │    │    │ is_verified      │
└──────────────────┘    │    │ created_at       │
                        │    │ updated_at       │
                        │    └──────────────────┘
                        │              │
                        │              │
                        ▼              ▼
              ┌───────────────────────────┐
              │  organization_members     │
              ├───────────────────────────┤
              │ id (PK)                   │
              │ organization_id (FK)      │
              │ user_id (FK)              │
              │ role (ENUM)               │
              │ joined_at                 │
              │ UNIQUE(org_id, user_id)   │
              └───────────────────────────┘
                        │
                        │
      ┌─────────────────┼─────────────────┬─────────────────┐
      │                 │                 │                 │
      ▼                 ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ credentials  │  │   agents     │  │ audit_logs   │  │   actions    │
├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤
│ id (PK)      │  │ id (PK)      │  │ id (PK)      │  │ id (PK)      │
│ user_id (FK) │  │ user_id (FK) │  │ user_id (FK) │  │ user_id (FK) │
│ org_id (FK)  │  │ org_id (FK)  │  │ org_id (FK)  │  │ org_id (FK)  │
│ type (ENUM)  │  │ name         │  │ action_type  │  │ agent_id(FK) │
│ provider     │  │ description  │  │ resource     │  │ type         │
│ encrypted_*  │  │ config       │  │ details      │  │ status       │
│ scope        │  │ is_active    │  │ ip_address   │  │ preview      │
│ expires_at   │  │ created_at   │  │ user_agent   │  │ created_at   │
│ created_at   │  │ updated_at   │  │ created_at   │  │ approved_at  │
└──────────────┘  └──────────────┘  └──────────────┘  │ executed_at  │
      │                  │                             │ approved_by  │
      │                  │                             └──────────────┘
      │                  ▼
      │         ┌───────────────────┐
      │         │ agent_conversations│
      │         ├───────────────────┤
      │         │ id (PK)           │
      │         │ agent_id (FK)     │
      │         │ title             │
      │         │ created_at        │
      │         │ updated_at        │
      │         └───────────────────┘
      │                  │
      │                  ▼
      │         ┌───────────────────┐
      │         │ agent_messages    │
      │         ├───────────────────┤
      │         │ id (PK)           │
      │         │ conversation_id(FK)│
      │         │ role (ENUM)       │
      │         │ content           │
      │         │ metadata          │
      │         │ created_at        │
      │         └───────────────────┘
      │
      ▼
┌──────────────────────┐
│ integration_connections│
├──────────────────────┤
│ id (PK)              │
│ credential_id (FK)   │
│ integration_type     │
│ status               │
│ last_sync_at         │
│ sync_errors          │
│ metadata             │
│ created_at           │
│ updated_at           │
└──────────────────────┘
```

## Table Definitions

### Core Tables

#### `organizations`

Multi-tenant organization management.

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    settings JSONB DEFAULT '{}',
    max_users INTEGER DEFAULT 10,
    plan_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_created_at ON organizations(created_at DESC);
```

**Fields:**
- `id`: Unique organization identifier
- `name`: Human-readable organization name
- `slug`: URL-safe identifier (e.g., "acme-corp")
- `settings`: JSON configuration (theme, defaults, etc.)
- `max_users`: Maximum allowed users (for plan limits)
- `plan_tier`: Subscription tier (free, pro, enterprise)

#### `users`

User account management.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_users_email ON users(LOWER(email));
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

**Fields:**
- `id`: Unique user identifier
- `email`: Email address (case-insensitive unique)
- `hashed_password`: Bcrypt hashed password
- `is_active`: Account enabled status
- `is_verified`: Email verification status
- `preferences`: User preferences (UI settings, notifications)

#### `organization_members`

User membership in organizations with role-based access.

```sql
CREATE TYPE member_role AS ENUM ('owner', 'admin', 'member', 'viewer');

CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role member_role NOT NULL DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    invited_by UUID REFERENCES users(id),
    UNIQUE(organization_id, user_id)
);

CREATE INDEX idx_org_members_org_id ON organization_members(organization_id);
CREATE INDEX idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX idx_org_members_role ON organization_members(role);
```

**Roles:**
- `owner`: Full control, billing, delete org
- `admin`: Manage members, settings
- `member`: Create agents, use integrations
- `viewer`: Read-only access

### Credential Management

#### `credentials`

Encrypted storage for BYOK API keys and OAuth tokens.

```sql
CREATE TYPE credential_type AS ENUM (
    'llm_api_key',      -- OpenAI, Anthropic, Gemini
    'oauth_token'       -- Gmail, Slack, Jira, Calendar
);

CREATE TYPE llm_provider AS ENUM ('openai', 'anthropic', 'gemini', 'azure_openai');
CREATE TYPE integration_provider AS ENUM ('gmail', 'slack', 'jira', 'google_calendar', 'notion');

CREATE TABLE credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type credential_type NOT NULL,
    
    -- For LLM API Keys
    llm_provider llm_provider,
    
    -- For OAuth Tokens
    integration_provider integration_provider,
    
    -- Encrypted data (AES-256-GCM)
    encrypted_value BYTEA NOT NULL,
    encryption_salt BYTEA NOT NULL,
    encryption_nonce BYTEA NOT NULL,
    encryption_tag BYTEA NOT NULL,
    
    -- OAuth specific
    encrypted_refresh_token BYTEA,
    refresh_token_salt BYTEA,
    refresh_token_nonce BYTEA,
    refresh_token_tag BYTEA,
    
    scope TEXT[],
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_llm_credential CHECK (
        type != 'llm_api_key' OR llm_provider IS NOT NULL
    ),
    CONSTRAINT valid_oauth_credential CHECK (
        type != 'oauth_token' OR integration_provider IS NOT NULL
    )
);

CREATE INDEX idx_credentials_user_id ON credentials(user_id);
CREATE INDEX idx_credentials_org_id ON credentials(organization_id);
CREATE INDEX idx_credentials_type ON credentials(type);
CREATE INDEX idx_credentials_provider ON credentials(llm_provider, integration_provider);
CREATE INDEX idx_credentials_active ON credentials(is_active);
CREATE INDEX idx_credentials_expires ON credentials(expires_at) WHERE expires_at IS NOT NULL;
```

**Security Features:**
- All sensitive values encrypted with AES-256-GCM
- Separate encryption for access and refresh tokens
- Salt and nonce stored per credential
- Expiration tracking for automatic refresh

#### `integration_connections`

Tracks OAuth connection status and sync metadata.

```sql
CREATE TYPE connection_status AS ENUM ('active', 'expired', 'revoked', 'error');

CREATE TABLE integration_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credential_id UUID NOT NULL REFERENCES credentials(id) ON DELETE CASCADE,
    integration_type integration_provider NOT NULL,
    status connection_status DEFAULT 'active',
    
    -- Connection metadata
    external_user_id VARCHAR(255),
    external_user_email VARCHAR(255),
    workspace_id VARCHAR(255),
    workspace_name VARCHAR(255),
    
    -- Sync tracking
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_successful_sync_at TIMESTAMP WITH TIME ZONE,
    sync_errors JSONB DEFAULT '[]',
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_integration_connections_credential ON integration_connections(credential_id);
CREATE INDEX idx_integration_connections_status ON integration_connections(status);
CREATE INDEX idx_integration_connections_type ON integration_connections(integration_type);
```

### Agent Management

#### `agents`

AI agent configurations.

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT,
    
    -- Configuration
    config JSONB DEFAULT '{
        "temperature": 0.7,
        "max_tokens": 2000,
        "tools_enabled": ["search", "memory"]
    }',
    
    -- LLM settings (references user's BYOK credential)
    llm_credential_id UUID REFERENCES credentials(id) ON DELETE SET NULL,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_agents_org_id ON agents(organization_id);
CREATE INDEX idx_agents_active ON agents(is_active);
CREATE INDEX idx_agents_created_at ON agents(created_at DESC);
```

#### `agent_conversations`

Conversation threads for each agent.

```sql
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    title VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_agent_id ON agent_conversations(agent_id);
CREATE INDEX idx_conversations_created_at ON agent_conversations(created_at DESC);
```

#### `agent_messages`

Individual messages within conversations.

```sql
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system', 'tool');

CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    
    -- For tool calls/results
    tool_calls JSONB,
    tool_results JSONB,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    tokens_used INTEGER,
    latency_ms INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation_id ON agent_messages(conversation_id);
CREATE INDEX idx_messages_created_at ON agent_messages(created_at DESC);
CREATE INDEX idx_messages_role ON agent_messages(role);
```

### Audit & Compliance

#### `audit_logs`

Comprehensive audit trail for all system actions.

```sql
CREATE TYPE audit_action_type AS ENUM (
    'auth.login',
    'auth.logout',
    'auth.password_change',
    'user.create',
    'user.update',
    'user.delete',
    'org.create',
    'org.update',
    'org.member_add',
    'org.member_remove',
    'credential.create',
    'credential.update',
    'credential.delete',
    'credential.decrypt',
    'agent.create',
    'agent.update',
    'agent.delete',
    'agent.query',
    'search.execute',
    'action.propose',
    'action.approve',
    'action.reject',
    'action.execute',
    'integration.connect',
    'integration.disconnect',
    'integration.sync'
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    
    action_type audit_action_type NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    
    -- Details
    details JSONB DEFAULT '{}',
    changes JSONB,  -- Before/after for updates
    
    -- Result
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_org_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);

-- Partitioning for performance (optional, for high volume)
-- CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Action Management (Phase 2)

#### `actions`

Proposed actions awaiting approval or executed.

```sql
CREATE TYPE action_type AS ENUM (
    'gmail.send_email',
    'gmail.archive',
    'gmail.label',
    'slack.send_message',
    'slack.create_channel',
    'notion.create_page',
    'notion.update_database',
    'jira.create_issue',
    'jira.update_issue',
    'calendar.create_event'
);

CREATE TYPE action_status AS ENUM (
    'pending',      -- Awaiting user approval
    'approved',     -- Approved, queued for execution
    'executing',    -- Currently executing
    'completed',    -- Successfully executed
    'failed',       -- Execution failed
    'rejected',     -- User rejected
    'expired'       -- Approval timeout
);

CREATE TABLE actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES agent_conversations(id) ON DELETE SET NULL,
    
    type action_type NOT NULL,
    status action_status DEFAULT 'pending',
    
    -- Action details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    parameters JSONB NOT NULL,
    
    -- Preview/context
    preview JSONB,  -- What will be created/modified
    ai_reasoning TEXT,  -- Why the AI suggested this
    
    -- Approval tracking
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_by UUID REFERENCES users(id),
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    
    -- Execution tracking
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT,
    
    -- Timeout
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 hour'),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_actions_user_id ON actions(user_id);
CREATE INDEX idx_actions_org_id ON actions(organization_id);
CREATE INDEX idx_actions_agent_id ON actions(agent_id);
CREATE INDEX idx_actions_status ON actions(status);
CREATE INDEX idx_actions_type ON actions(type);
CREATE INDEX idx_actions_created_at ON actions(created_at DESC);
CREATE INDEX idx_actions_expires_at ON actions(expires_at) WHERE status = 'pending';
```

### Search Optimization

#### `search_cache`

Cache for global search results.

```sql
CREATE TABLE search_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 of normalized query
    query_text TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Results by source
    results JSONB NOT NULL,
    
    -- Metadata
    sources TEXT[] NOT NULL,  -- ['gmail', 'slack', 'jira']
    total_results INTEGER,
    execution_time_ms INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '5 minutes')
);

CREATE INDEX idx_search_cache_query_hash ON search_cache(query_hash);
CREATE INDEX idx_search_cache_user_id ON search_cache(user_id);
CREATE INDEX idx_search_cache_expires_at ON search_cache(expires_at);

-- Auto-delete expired cache entries
CREATE INDEX idx_search_cache_cleanup ON search_cache(expires_at) 
    WHERE expires_at < CURRENT_TIMESTAMP;
```

## Vector Database Schema (Milvus)

### Collection: `user_preferences`

Stores user preferences and habits as embeddings for contextual memory.

```python
# Collection Schema
{
    "collection_name": "user_preferences",
    "dimension": 1536,  # OpenAI ada-002 embedding size
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "fields": [
        {"name": "id", "type": "VARCHAR", "max_length": 36, "primary": True},
        {"name": "user_id", "type": "VARCHAR", "max_length": 36, "index": True},
        {"name": "organization_id", "type": "VARCHAR", "max_length": 36},
        {"name": "preference_text", "type": "VARCHAR", "max_length": 2000},
        {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "category", "type": "VARCHAR", "max_length": 100},
        {"name": "metadata", "type": "JSON"},
        {"name": "created_at", "type": "INT64"}  # Unix timestamp
    ]
}
```

**Example entries:**
- "Always CC jane@company.com on budget-related emails"
- "Prefer morning meetings between 9-11am"
- "Flag high-priority items from the CEO"

### Collection: `conversation_context`

Stores conversation history as embeddings for semantic search.

```python
{
    "collection_name": "conversation_context",
    "dimension": 1536,
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "fields": [
        {"name": "id", "type": "VARCHAR", "max_length": 36, "primary": True},
        {"name": "conversation_id", "type": "VARCHAR", "max_length": 36, "index": True},
        {"name": "message_id", "type": "VARCHAR", "max_length": 36},
        {"name": "user_id", "type": "VARCHAR", "max_length": 36, "index": True},
        {"name": "message_content", "type": "VARCHAR", "max_length": 5000},
        {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "role", "type": "VARCHAR", "max_length": 20},
        {"name": "created_at", "type": "INT64"}
    ]
}
```

### Collection: `search_embeddings`

Pre-computed embeddings for frequently searched content.

```python
{
    "collection_name": "search_embeddings",
    "dimension": 1536,
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "fields": [
        {"name": "id", "type": "VARCHAR", "max_length": 36, "primary": True},
        {"name": "user_id", "type": "VARCHAR", "max_length": 36, "index": True},
        {"name": "source", "type": "VARCHAR", "max_length": 50},  # gmail, slack, etc.
        {"name": "external_id", "type": "VARCHAR", "max_length": 255},
        {"name": "content", "type": "VARCHAR", "max_length": 10000},
        {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "metadata", "type": "JSON"},
        {"name": "created_at", "type": "INT64"}
    ]
}
```

## Alternative: pgvector Schema

If using PostgreSQL's pgvector extension instead of Milvus:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- User preferences
CREATE TABLE user_preferences_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    preference_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    category VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_prefs_user_id ON user_preferences_vectors(user_id);
CREATE INDEX idx_user_prefs_embedding ON user_preferences_vectors 
    USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- Conversation context
CREATE TABLE conversation_context_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES agent_messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    role message_role NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conv_context_conv_id ON conversation_context_vectors(conversation_id);
CREATE INDEX idx_conv_context_user_id ON conversation_context_vectors(user_id);
CREATE INDEX idx_conv_context_embedding ON conversation_context_vectors 
    USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- Search embeddings cache
CREATE TABLE search_embeddings_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(255),
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
);

CREATE INDEX idx_search_emb_user_id ON search_embeddings_vectors(user_id);
CREATE INDEX idx_search_emb_source ON search_embeddings_vectors(source);
CREATE INDEX idx_search_emb_embedding ON search_embeddings_vectors 
    USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
CREATE INDEX idx_search_emb_expires ON search_embeddings_vectors(expires_at);
```

## Database Migrations

Use Alembic for PostgreSQL schema migrations:

```bash
# Initialize migrations
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create core tables"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Sample Queries

### Get user's active LLM credentials

```sql
SELECT 
    c.id,
    c.llm_provider,
    c.name,
    c.last_used_at
FROM credentials c
JOIN organization_members om ON c.user_id = om.user_id 
    AND c.organization_id = om.organization_id
WHERE c.user_id = $1
    AND c.type = 'llm_api_key'
    AND c.is_active = true
ORDER BY c.last_used_at DESC NULLS LAST;
```

### Get user's connected integrations

```sql
SELECT 
    c.integration_provider,
    ic.status,
    ic.external_user_email,
    ic.last_successful_sync_at,
    c.scope
FROM credentials c
JOIN integration_connections ic ON ic.credential_id = c.id
WHERE c.user_id = $1
    AND c.type = 'oauth_token'
    AND c.is_active = true
ORDER BY ic.last_successful_sync_at DESC;
```

### Get pending actions for review

```sql
SELECT 
    a.id,
    a.type,
    a.title,
    a.description,
    a.preview,
    a.ai_reasoning,
    a.created_at,
    a.expires_at,
    ag.name as agent_name
FROM actions a
LEFT JOIN agents ag ON ag.id = a.agent_id
WHERE a.user_id = $1
    AND a.status = 'pending'
    AND a.expires_at > CURRENT_TIMESTAMP
ORDER BY a.created_at DESC;
```

### Audit trail for a user

```sql
SELECT 
    al.action_type,
    al.resource_type,
    al.details,
    al.status,
    al.created_at,
    u.full_name as performed_by
FROM audit_logs al
LEFT JOIN users u ON u.id = al.user_id
WHERE al.user_id = $1
    OR al.organization_id IN (
        SELECT organization_id 
        FROM organization_members 
        WHERE user_id = $1
    )
ORDER BY al.created_at DESC
LIMIT 100;
```

### Vector similarity search (pgvector)

```sql
-- Find similar user preferences
SELECT 
    preference_text,
    1 - (embedding <=> $1::vector) as similarity
FROM user_preferences_vectors
WHERE user_id = $2
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

## Data Retention Policies

| Table | Retention | Archive Strategy |
|-------|-----------|------------------|
| `audit_logs` | 90 days active, 2 years archive | Partition by month, move to cold storage |
| `agent_messages` | Unlimited | None (user data) |
| `actions` | 90 days | Soft delete after completion |
| `search_cache` | 5 minutes | Auto-delete via TTL |
| `search_embeddings_vectors` | 24 hours | Auto-delete via TTL |

## Backup Strategy

- **PostgreSQL**: Daily full backup + WAL archiving
- **Milvus**: Daily collection snapshots
- **RPO**: 1 hour (via WAL)
- **RTO**: 4 hours

## Indexes Summary

### Critical for Performance
- All foreign keys indexed
- User queries: `idx_users_email`, `idx_users_is_active`
- Agent queries: `idx_agents_user_id`, `idx_agents_org_id`
- Search: `idx_search_cache_query_hash`
- Audit: `idx_audit_logs_created_at`, `idx_audit_logs_user_id`
- Actions: `idx_actions_status`, `idx_actions_expires_at`

### Composite Indexes (if needed)
```sql
-- For org member queries
CREATE INDEX idx_org_members_lookup ON organization_members(organization_id, user_id, role);

-- For credential lookups
CREATE INDEX idx_credentials_lookup ON credentials(user_id, type, is_active);

-- For conversation queries
CREATE INDEX idx_messages_lookup ON agent_messages(conversation_id, created_at DESC);
```

## Security Considerations

1. **Row-Level Security (RLS)**: Consider enabling for multi-tenant isolation
2. **Encryption**: All credential fields encrypted at application level
3. **Audit Logging**: Trigger-based logging for sensitive table modifications
4. **Connection Pooling**: Use PgBouncer for efficient connection management
5. **Prepared Statements**: Always use parameterized queries (SQLAlchemy handles this)

## Conclusion

This schema provides:
- ✅ Multi-tenant organization support
- ✅ Secure credential storage with encryption
- ✅ Comprehensive audit trail
- ✅ Scalable conversation storage
- ✅ Action approval workflow
- ✅ Vector search capabilities
- ✅ Performance optimizations via indexes
- ✅ Data retention and archival strategies
