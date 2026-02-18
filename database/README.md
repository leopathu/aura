# Database Scripts and Configuration

This directory contains database initialization and migration scripts for Aura.

## Files

- `init.sql` - PostgreSQL initialization script with schema and demo data
- Alembic migrations will be stored in `../backend/alembic/` directory

## PostgreSQL with pgvector

The database uses PostgreSQL 16 with the pgvector extension for storing vector embeddings.

### Tables

1. **users** - User accounts
2. **organizations** - Organization workspaces
3. **memberships** - User-organization relationships with roles
4. **credentials** - Encrypted API keys and credentials
5. **agents** - AI agent configurations
6. **agent_memory** - Vector embeddings for agent memory (1536 dimensions)
7. **activity_logs** - Audit trail of all actions
8. **conversations** - Chat conversation threads
9. **messages** - Individual chat messages
10. **automations** - Workflow automation definitions
11. **automation_runs** - Automation execution history
12. **app_connections** - OAuth tokens for app integrations

### Indexes

- B-tree indexes on foreign keys and frequently queried columns
- IVFFlat index on vector embeddings for fast similarity search

### Demo Data

The initialization script creates a demo user:
- **Email**: demo@aura.com
- **Password**: demo123
- **Organization**: Demo Organization

## Usage

The database is automatically initialized when running with Docker Compose.

For manual initialization:
```bash
psql -U aura_user -d aura_db -f init.sql
```
