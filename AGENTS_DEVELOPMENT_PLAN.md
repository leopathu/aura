# Agents Feature — Development Plan

## Overview

Agents extend the RAG system with **live data connectors**. Instead of manually uploading files,
an Agent continuously syncs content from connected apps (Gmail, Google Drive, Jira, Slack, …),
keeps the vector store up to date, and can be chatted with just like a Brain — with source
citations linking back to the original item in the external app.

---

## Architecture Summary

```
User
 └── Agent (like a Brain, but data comes from connectors)
       ├── AgentConnection 1  (e.g. Google Drive — OAuth credentials, sync config)
       │     └── AgentDocuments (synced files/pages → chunks → embeddings)
       ├── AgentConnection 2  (e.g. Jira — issues, comments)
       │     └── AgentDocuments
       └── Chat (RAG over all synced AgentDocuments, with source URLs)
```

---

## Phase 1 — Data Model & Core Infrastructure

**Goal:** Database schema, ORM models, Alembic migration, repositories, and Pydantic schemas.
**Estimated time:** 3–4 days

### 1.1 New Database Tables

#### `agents`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | CASCADE DELETE |
| `name` | Text | |
| `description` | Text nullable | |
| `created_at` | Timestamptz | |
| `updated_at` | Timestamptz | |

#### `agent_connections`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `agent_id` | UUID FK → agents | CASCADE DELETE |
| `app_type` | Text | enum: see §1.3 |
| `display_name` | Text | user-friendly label |
| `credentials_enc` | Text | Fernet-encrypted JSON (OAuth tokens) |
| `config_json` | Text nullable | sync filter settings (folders, labels, …) |
| `sync_status` | Text | `idle \| syncing \| error` |
| `sync_error` | Text nullable | |
| `last_synced_at` | Timestamptz nullable | |
| `sync_interval_minutes` | Integer | default 60 |
| `created_at` | Timestamptz | |
| `updated_at` | Timestamptz | |

#### `agent_documents`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `agent_id` | UUID FK → agents | CASCADE DELETE |
| `connection_id` | UUID FK → agent_connections | CASCADE DELETE |
| `external_id` | Text | ID in the source app |
| `title` | Text | |
| `content` | Text | extracted plain text |
| `source_url` | Text nullable | link back to original item |
| `metadata_json` | Text nullable | author, labels, dates, etc. |
| `content_hash` | Text | SHA-256 of content — used for change detection |
| `embed_status` | Text | `pending \| processing \| ready \| failed` |
| `embed_error` | Text nullable | |
| `created_at` | Timestamptz | |
| `updated_at` | Timestamptz | |

#### `agent_chunks`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `agent_document_id` | UUID FK → agent_documents | CASCADE DELETE |
| `chunk_index` | Integer | |
| `content` | Text | |
| `embedding` | vector(1024) | pgvector |
| `created_at` | Timestamptz | |
| `updated_at` | Timestamptz | |

### 1.2 Backend Tasks

- [ ] Migration `0009_create_agents` — create all 4 tables, indexes, FK constraints
- [ ] `app/models/agent.py` — SQLAlchemy ORM models for all 4 tables
- [ ] Update `app/models/__init__.py` — export new models
- [ ] `app/repositories/agent_repository.py` — CRUD for `Agent`
- [ ] `app/repositories/agent_connection_repository.py` — CRUD + encrypt/decrypt helpers
- [ ] `app/repositories/agent_document_repository.py` — CRUD + `set_embed_status()`
- [ ] `app/repositories/agent_chunk_repository.py` — `create_bulk()`, `similarity_search()`, `delete_by_document()`
- [ ] `app/schemas/agent.py` — Pydantic v2 schemas:
  - `AgentCreate`, `AgentUpdate`, `AgentResponse`
  - `AgentConnectionCreate`, `AgentConnectionResponse`
  - `AgentDocumentResponse`

### 1.3 Supported `app_type` Values (initial set)

```
gmail | gdrive | jira | slack | notion | github | confluence | linear
```

### 1.4 Credential Encryption

All OAuth tokens stored in `credentials_enc` must be encrypted at rest:

```python
# app/core/security.py  (extend existing file)
from cryptography.fernet import Fernet

def encrypt_credentials(data: dict, key: str) -> str: ...
def decrypt_credentials(token: str, key: str) -> dict: ...
```

Add to `backend/.env`:
```env
CREDENTIALS_ENCRYPTION_KEY=<base64-url-safe-32-byte-key>
```

Add to `app/core/config.py`:
```python
credentials_encryption_key: str
```

---

## Phase 2 — OAuth 2.0 & Credential Management

**Goal:** Secure OAuth flows so users can authorise Aura to read their apps.
**Estimated time:** 2–3 days

### 2.1 Common Interface

```python
# app/services/oauth/base.py
class OAuthProvider(ABC):
    async def get_auth_url(self, state: str, redirect_uri: str) -> str: ...
    async def exchange_code(self, code: str, redirect_uri: str) -> Credentials: ...
    async def refresh_token(self, credentials: Credentials) -> Credentials: ...
```

### 2.2 Provider Implementations

| File | Provider | Scope needed |
|---|---|---|
| `app/services/oauth/google.py` | Google (Gmail + Drive) | `gmail.readonly`, `drive.readonly` |
| `app/services/oauth/slack.py` | Slack | `channels:history`, `files:read` |
| `app/services/oauth/jira.py` | Atlassian (Jira + Confluence) | `read:jira-work` |
| `app/services/oauth/github.py` | GitHub | `repo`, `read:org` |
| `app/services/oauth/notion.py` | Notion | `read_content` |
| `app/services/oauth/linear.py` | Linear | `read` |

### 2.3 API Endpoints

```
GET  /api/v1/agents/{agent_id}/connections/{conn_id}/oauth/start
     → returns { url: "https://accounts.google.com/o/oauth2/auth?..." }

GET  /api/v1/agents/oauth/callback/{app_type}?code=...&state=...
     → exchanges code, encrypts tokens, saves to DB, redirects to frontend
```

### 2.4 Environment Variables to Add

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
JIRA_CLIENT_ID=
JIRA_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
NOTION_CLIENT_ID=
NOTION_CLIENT_SECRET=
LINEAR_CLIENT_ID=
LINEAR_CLIENT_SECRET=
OAUTH_REDIRECT_BASE_URL=http://localhost:8000
```

### 2.5 Token Auto-Refresh

- Before every sync, call `refresh_token()` if access token expires within 5 minutes
- Save refreshed tokens back to `agent_connections.credentials_enc`

---

## Phase 3 — Connector Implementations

**Goal:** One connector per app that fetches, normalises, and returns plain-text documents.
**Estimated time:** 1–2 days per connector

### 3.1 Common Interface

```python
# app/services/connectors/base.py
@dataclass
class ExternalItem:
    external_id: str
    title: str
    content: str          # plain text
    source_url: str
    content_hash: str     # SHA-256(content)
    metadata: dict        # author, date, labels, …

class BaseConnector(ABC):
    async def list_items(self, credentials: Credentials) -> list[ExternalItem]: ...
    async def fetch_item(self, credentials: Credentials, item_id: str) -> ExternalItem: ...
```

### 3.2 Connector Details

| Connector | File | What it fetches |
|---|---|---|
| **Google Drive** | `gdrive.py` | Docs, Sheets, PDFs — converted to plain text |
| **Gmail** | `gmail.py` | Emails (subject + body) from inbox or specific label |
| **Jira** | `jira.py` | Issues + comments, filtered by project |
| **Slack** | `slack.py` | Messages + threads from selected channels |
| **Notion** | `notion.py` | Pages and database rows |
| **GitHub** | `github.py` | Issues, PRs, README, wiki pages |
| **Confluence** | `confluence.py` | Pages from selected spaces |
| **Linear** | `linear.py` | Issues + comments via GraphQL |

### 3.3 Connector Registry

```python
# app/services/connectors/__init__.py
CONNECTORS: dict[str, type[BaseConnector]] = {
    "gdrive": GDriveConnector,
    "gmail": GmailConnector,
    "jira": JiraConnector,
    "slack": SlackConnector,
    ...
}
```

### 3.4 Build Order (recommended)

1. **Google Drive** — most common, richest content
2. **Jira** — high enterprise demand
3. **Slack** — real-time knowledge
4. **Gmail** — email threads
5. Remaining connectors

---

## Phase 4 — Sync Engine

**Goal:** Background pipeline that pulls from connectors, diffs against stored content, and keeps the vector store current.
**Estimated time:** 3–4 days

### 4.1 Sync Pipeline (`app/services/sync_service.py`)

```
SyncService.sync_connection(connection_id: UUID)
  1. Load AgentConnection, decrypt credentials
  2. Set sync_status = "syncing"
  3. Refresh OAuth token if expiring soon
  4. Instantiate connector via CONNECTORS registry
  5. Fetch all external items (paginated)
  6. For each item:
     a. Lookup existing AgentDocument by (connection_id, external_id)
     b. If content_hash unchanged → skip
     c. If changed or new:
        - Delete old AgentChunks
        - Re-chunk content
        - Re-embed chunks (using user's AI settings)
        - Upsert AgentDocument + insert AgentChunks
  7. Delete AgentDocuments whose external_id no longer exists (item deleted upstream)
  8. Set sync_status = "idle", update last_synced_at
  9. On error: set sync_status = "error", save sync_error
```

### 4.2 Scheduling

- Use **APScheduler** (add `apscheduler>=3.10` to `pyproject.toml`)
- On app startup: schedule a job per connection based on `sync_interval_minutes`
- Jobs run `SyncService.sync_connection()` in a background async task

```python
# app/main.py — startup event
@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
    # Load all connections and schedule their sync jobs
```

### 4.3 API Endpoints

```
POST /api/v1/agents/{agent_id}/connections/{conn_id}/sync
     → triggers an immediate manual sync (background task)

GET  /api/v1/agents/{agent_id}/connections/{conn_id}/sync/status
     → { sync_status, last_synced_at, sync_error, total_docs, ready_docs }
```

### 4.4 Incremental Sync

- `content_hash = sha256(content)` stored on `AgentDocument`
- On each sync run: only items whose hash has changed are re-embedded
- This keeps sync fast and Ollama/OpenAI API costs low

---

## Phase 5 — Agent Chat (RAG over Synced Data)

**Goal:** Chat with an Agent using streaming SSE — identical UX to Brain chat, but queries across all connected app data.
**Estimated time:** 2 days

### 5.1 Backend Tasks

- [ ] `AgentChunkRepository.similarity_search(query_embedding, agent_id, top_k)` — scoped to agent
- [ ] Extend `RAGService`:
  - `query_agent(request, agent_id)` — non-streaming query
  - `stream_agent_answer(query, agent_id, history)` — streaming generator
- [ ] Reuse `ConversationRepository` with an `agent_id` column (migration `0010_add_agent_id_to_conversations`)
- [ ] New endpoints under `/api/v1/agents/{agent_id}/chat/`:
  ```
  POST   /stream                          ← SSE streaming chat
  GET    /conversations                   ← list conversations
  POST   /conversations                   ← create conversation
  GET    /conversations/{conv_id}         ← full conversation with messages
  DELETE /conversations/{conv_id}         ← delete
  ```

### 5.2 Source Citations Enhancement

Each source chunk returned includes:
```json
{
  "document_title": "Q2 Roadmap",
  "source_url": "https://docs.google.com/...",
  "app_type": "gdrive",
  "chunk_index": 3,
  "similarity": 0.87
}
```

The frontend renders these as clickable links with the app's icon.

---

## Phase 6 — Frontend UI

**Goal:** Full agent management UI — create agents, connect apps, view synced docs, chat.
**Estimated time:** 3–4 days

### 6.1 New Routes

```
/agents                        ← agent list
/agents/[id]                   ← agent detail (tabbed)
  /agents/[id]?tab=connections ← manage connected apps
  /agents/[id]?tab=chat        ← chat with agent
  /agents/[id]?tab=documents   ← view all synced documents
```

### 6.2 New Components

| Component | Description |
|---|---|
| `AgentSidebar.tsx` | Left nav listing agents (mirrors `BrainSidebar`) |
| `AgentPanel.tsx` | Tabbed panel: Connections / Chat / Documents |
| `AgentConnectionCard.tsx` | Per-app card: icon, status, last synced, Sync Now, Disconnect |
| `AddConnectionModal.tsx` | App picker grid → initiates OAuth flow |
| `AgentDocumentList.tsx` | Table of synced items with app icon + embed status badges |
| `AgentChat.tsx` | Streaming chat (extends `BrainChat` patterns) with source URL links |

### 6.3 New Services & Types

```
frontend/src/services/agent-service.ts     ← CRUD for agents + connections
frontend/src/services/agent-chat-service.ts ← SSE streaming (mirrors chat-service.ts)
frontend/src/types/agent.ts                ← Agent, AgentConnection, AgentDocument types
```

### 6.4 App Icons

Add SVG icons to `frontend/public/icons/`:
`gmail.svg`, `gdrive.svg`, `jira.svg`, `slack.svg`, `notion.svg`, `github.svg`,
`confluence.svg`, `linear.svg`

---

## Phase 7 — Hardening & Production Readiness

**Goal:** Make the feature production-safe.
**Estimated time:** Ongoing

### 7.1 Security
- [ ] Verify `agent_id` is owned by `current_user` on every endpoint (no cross-user access)
- [ ] Rotate `CREDENTIALS_ENCRYPTION_KEY` support (re-encrypt on key rotation)
- [ ] Audit log: who triggered a sync, when, what changed
- [ ] Rate limit `/sync` endpoints per user (prevent abuse)

### 7.2 Webhooks (push over poll)
- [ ] **Slack Events API** — receive message events, trigger incremental sync
- [ ] **GitHub Webhooks** — receive push/issue events
- [ ] **Google Drive Push Notifications** — Drive → webhook → incremental sync
- [ ] Webhook endpoint: `POST /api/v1/webhooks/{app_type}`

### 7.3 Selective Sync (per connection config)
Store user preferences in `agent_connections.config_json`:

```json
{
  "gdrive": { "folder_ids": ["1abc...", "2def..."] },
  "gmail":  { "label": "INBOX", "max_days": 30 },
  "jira":   { "project_keys": ["PROJ", "ENG"] },
  "slack":  { "channel_ids": ["C012AB3CD"] }
}
```

### 7.4 Sync History
- [ ] `agent_sync_logs` table: `connection_id, started_at, finished_at, items_total, items_changed, items_failed, error`
- [ ] `GET /api/v1/agents/{id}/connections/{conn_id}/sync/history`

### 7.5 Tests
- [ ] Mock all external APIs (use `respx` for httpx mocking)
- [ ] Unit tests for each connector: pagination, content normalisation, hash comparison
- [ ] Unit tests for `SyncService`: new item, changed item, deleted item, auth error
- [ ] Integration tests for OAuth flow (mocked provider)
- [ ] Target ≥ 80% coverage on `services/connectors/` and `services/sync_service.py`

---

## Recommended Build Order

| Phase | Duration | Dependency |
|---|---|---|
| Phase 1 — Models & Migrations | 3–4 days | None |
| Phase 2 — OAuth | 2–3 days | Phase 1 |
| Phase 3 — Connectors (GDrive + Jira first) | 2–3 days each | Phase 2 |
| Phase 4 — Sync Engine | 3–4 days | Phase 3 |
| Phase 5 — Agent Chat | 2 days | Phase 4 |
| Phase 6 — Frontend UI | 3–4 days | Phase 5 |
| Phase 7 — Hardening | Ongoing | Phase 6 |

**Total MVP estimate (GDrive + Jira only):** ~3–4 weeks

---

## New Dependencies to Add

### `backend/pyproject.toml`

```toml
"cryptography>=42.0.0",      # Fernet credential encryption
"apscheduler>=3.10.0",       # periodic sync scheduling
"google-auth>=2.29.0",       # Google OAuth
"google-auth-oauthlib>=1.2.0",
"google-api-python-client>=2.126.0",
"slack-sdk>=3.27.0",         # Slack connector
"atlassian-python-api>=3.41.0",  # Jira + Confluence
"PyGithub>=2.3.0",           # GitHub connector
```

### `frontend/package.json`

```json
"@radix-ui/react-dialog": "^1.0.5",   // AddConnectionModal
"@radix-ui/react-tabs": "^1.0.4"      // AgentPanel tabs
```

---

## Migration Sequence

```
0009_create_agents.py             ← agents, agent_connections, agent_documents, agent_chunks
0010_add_agent_id_to_conversations.py  ← nullable agent_id FK on conversations table
```
