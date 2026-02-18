# Database Documentation

## Overview

Aura uses PostgreSQL 16 with the pgvector extension for storing vector embeddings. The database supports multi-tenant architecture with organization-level data isolation.

## Schema

### Core Tables

#### users
User account information
- `id` (UUID, PK)
- `email` (VARCHAR, unique, indexed)
- `hashed_password` (VARCHAR)
- `full_name` (VARCHAR)
- `is_active` (BOOLEAN)
- `is_verified` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

#### organizations
Organization/workspace management
- `id` (UUID, PK)
- `name` (VARCHAR)
- `slug` (VARCHAR, unique, indexed)
- `created_at`, `updated_at` (TIMESTAMP)

#### memberships
User-organization relationships
- `id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `org_id` (UUID, FK → organizations)
- `role` (ENUM: owner, admin, member)
- `joined_at` (TIMESTAMP)
- Unique constraint on (user_id, org_id)

### AI & Automation Tables

#### agents
AI agent configurations
- `id` (UUID, PK)
- `org_id` (UUID, FK → organizations)
- `name`, `description` (VARCHAR/TEXT)
- `system_prompt` (TEXT)
- `config` (JSONB)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

#### agent_memory
Vector embeddings for agent memory
- `id` (UUID, PK)
- `agent_id` (UUID, FK → agents)
- `content` (TEXT)
- `embedding` (VECTOR(1536)) - pgvector
- `memory_metadata` (JSONB)
- `created_at` (TIMESTAMP)
- IVFFlat index for fast similarity search

#### credentials
Encrypted API keys and tokens
- `id` (UUID, PK)
- `org_id` (UUID, FK → organizations)
- `credential_type` (VARCHAR: openai, anthropic, gemini, etc.)
- `encrypted_value` (TEXT)
- `label` (VARCHAR)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

### Activity & Logging

#### activity_logs
Audit trail of all actions
- `id` (UUID, PK)
- `org_id` (UUID, FK → organizations)
- `agent_id` (UUID, FK → agents, nullable)
- `user_id` (UUID, FK → users, nullable)
- `action` (VARCHAR)
- `details` (JSONB)
- `created_at` (TIMESTAMP, indexed)

### Chat & Conversations

#### conversations
Chat conversation threads
- `id` (UUID, PK)
- `org_id` (UUID, FK → organizations)
- `agent_id` (UUID, FK → agents)
- `user_id` (UUID, FK → users)
- `title` (VARCHAR)
- `created_at`, `updated_at` (TIMESTAMP)

#### messages
Individual chat messages
- `id` (UUID, PK)
- `conversation_id` (UUID, FK → conversations)
- `role` (ENUM: user, assistant, system)
- `content` (TEXT)
- `metadata` (JSONB)
- `created_at` (TIMESTAMP)

### Automation

#### automations
Workflow definitions
- `id` (UUID, PK)
- `org_id` (UUID, FK → organizations)
- `name`, `description` (VARCHAR/TEXT)
- `workflow_definition` (JSONB)
- `schedule` (VARCHAR - cron format)
- `trigger_config` (JSONB)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

#### automation_runs
Automation execution history
- `id` (UUID, PK)
- `automation_id` (UUID, FK → automations)
- `status` (ENUM: pending, running, completed, failed)
- `started_at`, `completed_at` (TIMESTAMP)
- `logs` (JSONB array)
- `error_message` (TEXT)

### Integrations

#### app_connections
OAuth tokens for app integrations
- `id` (UUID, PK)
- `org_id` (UUID, FK → organizations)
- `app_name` (VARCHAR: gmail, jira, slack, etc.)
- `encrypted_tokens` (TEXT)
- `connection_metadata` (JSONB)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)
- `expires_at` (TIMESTAMP)

## Indexes

Performance indexes created on:
- Foreign keys
- Frequently queried columns (email, slug, org_id, etc.)
- Timestamp columns for sorting
- Vector embeddings (IVFFlat for similarity search)

## Triggers

Automatic `updated_at` triggers on tables that need timestamp tracking.

## Migrations

Managed with Alembic:

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Backups

Automated backup scripts in `database/`:
- `backup.sh` - Create compressed backup
- `restore.sh` - Restore from backup
- Retention: 7 days by default

## Demo Data

Development database includes:
- Demo user: `demo@aura.com` / `demo123`
- Demo organization: "Demo Organization"

## Vector Search

Agent memory uses pgvector for semantic search:

```sql
-- Find similar memories (cosine similarity)
SELECT * FROM agent_memory
WHERE agent_id = $1
ORDER BY embedding <=> $2
LIMIT 5;
```

## Security

- All passwords hashed with bcrypt
- API keys encrypted with Fernet (AES-256)
- OAuth tokens encrypted before storage
- Row-level security via org_id FK constraints
