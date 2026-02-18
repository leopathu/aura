# Aura AI Agent Platform - System Architecture

## Executive Summary

The Aura AI Agent Platform is a trust-first AI agent system designed to observe and execute actions across multiple workplace applications (Gmail, Slack, Jira, Calendar) while maintaining strict security and providing transparent human-in-the-loop control.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│                     Next.js 15 (App Router)                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Global Search│  │ Review Drawer│  │ Audit Trail  │          │
│  │   Component  │  │  Component   │  │  Component   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  OAuth Setup │  │  Agent Chat  │  │ Settings/BYOK│          │
│  │  Components  │  │  Interface   │  │  Management  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                    HTTPS/TLS (REST + WebSocket)
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│                       FastAPI Backend                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Auth Service │  │ Search Service│  │Action Service│          │
│  │ (JWT/OAuth2) │  │ (Multi-source)│  │  (Executor)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │LLM Orchestr. │  │Vector Search │  │ Audit Logger │          │
│  │(LangChain)   │  │   Service    │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Internal Network
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │   PostgreSQL         │  │    Milvus/pgvector   │            │
│  │ (Primary Database)   │  │   (Vector Store)     │            │
│  │                      │  │                      │            │
│  │ - Users              │  │ - User Preferences   │            │
│  │ - Organizations      │  │ - Agent Memory       │            │
│  │ - Credentials        │  │ - Search Embeddings  │            │
│  │ - Agents             │  │ - Context History    │            │
│  │ - Audit Logs         │  │                      │            │
│  │ - Action History     │  │                      │            │
│  └──────────────────────┘  └──────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Outbound HTTPS
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   External Integrations                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Gmail   │  │  Slack   │  │   Jira   │  │ Calendar │       │
│  │   API    │  │   API    │  │   API    │  │   API    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ OpenAI   │  │Anthropic │  │  Gemini  │                     │
│  │   API    │  │   API    │  │   API    │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Core Architectural Principles

### 1. Trust-First Design
- **Explicit Consent**: Every action requires user approval via Review Drawer
- **Full Transparency**: Complete audit trail of AI reasoning and decisions
- **Minimal Permissions**: OAuth scopes limited to read-only for Phase 1

### 2. Clean Architecture
- **Separation of Concerns**: Clear boundaries between layers
- **Dependency Inversion**: Business logic independent of frameworks
- **Domain-Driven Design**: Core domain models drive the architecture

### 3. Security by Default
- **Defense in Depth**: Multiple layers of security controls
- **Zero Trust**: Verify every request, encrypt everything at rest
- **PII Protection**: Local sanitization before external API calls

### 4. Scalability
- **Horizontal Scaling**: Stateless API servers
- **Async Processing**: Background jobs for long-running tasks
- **Caching Strategy**: Redis for session/token caching

## Component Architecture

### Frontend Architecture (Next.js 15)

```
app/
├── (auth)/
│   ├── login/
│   └── signup/
├── (dashboard)/
│   ├── layout.tsx                 # Dashboard shell
│   ├── search/
│   │   └── page.tsx              # Global Search UI
│   ├── agents/
│   │   ├── page.tsx              # Agent list
│   │   └── [id]/
│   │       ├── page.tsx          # Agent chat interface
│   │       └── audit/
│   │           └── page.tsx      # Audit trail view
│   ├── settings/
│   │   ├── byok/
│   │   │   └── page.tsx          # BYOK configuration
│   │   ├── integrations/
│   │   │   └── page.tsx          # OAuth setup
│   │   └── organization/
│   │       └── page.tsx          # Org settings
│   └── actions/
│       └── page.tsx              # Action history
├── api/
│   ├── auth/
│   │   └── [...nextauth]/
│   │       └── route.ts          # NextAuth.js config
│   └── webhooks/
│       └── oauth-callback/
│           └── route.ts          # OAuth callback handler
├── components/
│   ├── search/
│   │   ├── GlobalSearchBar.tsx
│   │   ├── SearchResults.tsx
│   │   └── SearchFilters.tsx
│   ├── agents/
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   └── InputArea.tsx
│   ├── review/
│   │   ├── ReviewDrawer.tsx      # Phase 2
│   │   ├── ActionPreview.tsx
│   │   └── ApprovalControls.tsx
│   ├── audit/
│   │   ├── AuditTimeline.tsx
│   │   ├── ReasoningTree.tsx
│   │   └── ActionDetails.tsx
│   └── shared/
│       ├── AppShell.tsx
│       ├── Navigation.tsx
│       └── ErrorBoundary.tsx
├── lib/
│   ├── api-client.ts             # API wrapper
│   ├── websocket.ts              # Real-time connection
│   ├── auth.ts                   # Auth utilities
│   └── types.ts                  # TypeScript definitions
└── hooks/
    ├── useSearch.ts
    ├── useAgent.ts
    ├── useAudit.ts
    └── useWebSocket.ts
```

**Key Frontend Patterns:**
- **Server Components**: Default for data fetching
- **Client Components**: Interactive UI (search, chat, review drawer)
- **Real-time Updates**: WebSocket for agent responses and action notifications
- **Optimistic Updates**: Immediate UI feedback with rollback on error
- **Error Boundaries**: Graceful degradation

### Backend Architecture (FastAPI)

```
app/
├── main.py                       # FastAPI application entry
├── core/
│   ├── config.py                 # Settings (Pydantic BaseSettings)
│   ├── security.py               # JWT, password hashing
│   ├── encryption.py             # AES-256-GCM for credentials
│   ├── exceptions.py             # Custom exception handlers
│   └── middleware.py             # CORS, logging, rate limiting
├── api/
│   ├── dependencies.py           # Dependency injection
│   └── v1/
│       ├── router.py             # Main API router
│       └── endpoints/
│           ├── auth.py           # Login, signup, token refresh
│           ├── users.py          # User management
│           ├── organizations.py  # Org management
│           ├── credentials.py    # BYOK & OAuth credential mgmt
│           ├── integrations.py   # OAuth flow handlers
│           ├── agents.py         # Agent CRUD and chat
│           ├── search.py         # Global search endpoint
│           ├── actions.py        # Action execution (Phase 2)
│           └── audit.py          # Audit trail queries
├── domain/
│   ├── models/
│   │   ├── user.py               # User entity
│   │   ├── organization.py       # Organization entity
│   │   ├── credential.py         # Credential entity
│   │   ├── agent.py              # Agent entity
│   │   ├── audit_log.py          # Audit log entity
│   │   └── action.py             # Action entity (Phase 2)
│   ├── schemas/
│   │   ├── user.py               # Pydantic schemas
│   │   ├── organization.py
│   │   ├── credential.py
│   │   ├── agent.py
│   │   ├── search.py
│   │   ├── audit.py
│   │   └── action.py
│   └── enums/
│       ├── credential_type.py
│       ├── integration_type.py
│       └── action_status.py
├── services/
│   ├── auth_service.py           # Authentication logic
│   ├── encryption_service.py     # Credential encryption
│   ├── oauth_service.py          # OAuth 2.0 flows
│   ├── llm_service.py            # LLM provider abstraction
│   ├── agent_orchestrator.py    # LangChain orchestration
│   ├── search_service.py         # Multi-source search
│   ├── vector_service.py         # Milvus/pgvector operations
│   ├── integration_service.py    # External API connectors
│   ├── audit_service.py          # Audit logging
│   └── action_service.py         # Action execution (Phase 2)
├── integrations/
│   ├── base.py                   # Base integration interface
│   ├── gmail/
│   │   ├── client.py             # Gmail API wrapper
│   │   ├── search.py             # Gmail search implementation
│   │   └── actions.py            # Gmail write actions (Phase 2)
│   ├── slack/
│   │   ├── client.py
│   │   ├── search.py
│   │   └── actions.py
│   ├── jira/
│   │   ├── client.py
│   │   ├── search.py
│   │   └── actions.py
│   └── calendar/
│       ├── client.py
│       ├── search.py
│       └── actions.py
├── db/
│   ├── session.py                # Database session management
│   ├── base.py                   # Base model class
│   └── repositories/
│       ├── user_repository.py
│       ├── organization_repository.py
│       ├── credential_repository.py
│       ├── agent_repository.py
│       ├── audit_repository.py
│       └── action_repository.py
├── utils/
│   ├── logging.py                # Structured logging
│   ├── validators.py             # Custom validators
│   └── pii_sanitizer.py          # PII detection and removal
└── workers/
    ├── celery_app.py             # Celery configuration
    └── tasks/
        ├── sync_integrations.py  # Background sync jobs
        ├── process_search.py     # Async search aggregation
        └── execute_action.py     # Async action execution
```

**Key Backend Patterns:**
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic isolation
- **Dependency Injection**: FastAPI's built-in DI system
- **Event-Driven**: Celery for async tasks
- **CQRS-lite**: Separate read and write concerns for performance

### Integration Architecture

#### OAuth 2.0 Flow

```
User → Frontend: Click "Connect Gmail"
Frontend → Backend: POST /api/v1/integrations/gmail/authorize
Backend → Frontend: Return OAuth URL
Frontend → Browser: Redirect to Google OAuth
User → Google: Grant permissions
Google → Backend: Callback with auth code
Backend → Google: Exchange code for tokens
Backend → Database: Store encrypted tokens
Backend → Frontend: Redirect to success page
Frontend → User: Show connection status
```

**OAuth Scopes (Phase 1 - Read Only):**
- Gmail: `https://www.googleapis.com/auth/gmail.readonly`
- Slack: `search:read`, `channels:read`, `users:read`
- Jira: `read:jira-work`, `read:jira-user`
- Calendar: `https://www.googleapis.com/auth/calendar.readonly`

#### Search Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Global Search Flow (<3s latency)                │
└─────────────────────────────────────────────────────────────┘

User Query: "Find emails about Q4 budget from last week"
                              │
                              ▼
                    ┌──────────────────┐
                    │  Search Service  │
                    │  (FastAPI)       │
                    └──────────────────┘
                              │
              ┌───────────────┼───────────────┬──────────────┐
              ▼               ▼               ▼              ▼
        ┌─────────┐     ┌─────────┐    ┌─────────┐    ┌─────────┐
        │  Gmail  │     │  Slack  │    │  Jira   │    │Calendar │
        │ Adapter │     │ Adapter │    │ Adapter │    │ Adapter │
        └─────────┘     └─────────┘    └─────────┘    └─────────┘
              │               │               │              │
              ▼               ▼               ▼              ▼
        [Parallel API Calls with 2s timeout per source]
              │               │               │              │
              └───────────────┼───────────────┴──────────────┘
                              ▼
                    ┌──────────────────┐
                    │  Result Aggregator│
                    │  - Deduplicate    │
                    │  - Rank (TF-IDF)  │
                    │  - Limit (50)     │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Vector Enrichment│
                    │  (Semantic Search)│
                    └──────────────────┘
                              │
                              ▼
                      Return JSON Results
```

**Search Optimization Strategies:**
1. **Parallel Execution**: Async calls to all sources simultaneously
2. **Circuit Breaker**: Skip slow/failing sources after 2s
3. **Caching**: Redis cache for frequent queries (5 min TTL)
4. **Pagination**: Lazy load additional results
5. **Semantic Boost**: Use vector similarity for re-ranking

### Agent Orchestration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Agent Interaction Flow                        │
└─────────────────────────────────────────────────────────────┘

User: "Summarize my unread emails from sarah@company.com"
                              │
                              ▼
                    ┌──────────────────┐
                    │ Agent Orchestrator│
                    │   (LangChain)     │
                    └──────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐     ┌─────────┐    ┌─────────┐
        │  Intent │     │ Context │    │  Memory │
        │Classifier│    │ Fetcher │    │ Retrieval│
        └─────────┘     └─────────┘    └─────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌──────────────────┐
                    │   Tool Selection  │
                    │  (Gmail Search)   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Execute Tool     │
                    │  (with OAuth)     │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   LLM Synthesis   │
                    │ (User's BYOK Key) │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Audit Logging    │
                    │  - Query          │
                    │  - Tools Used     │
                    │  - LLM Reasoning  │
                    │  - Results        │
                    └──────────────────┘
                              │
                              ▼
                    Return Streaming Response
```

**LangChain Tools:**
- `GmailSearchTool`: Search emails
- `SlackSearchTool`: Search messages
- `JiraSearchTool`: Search issues
- `CalendarSearchTool`: Search events
- `VectorMemoryTool`: Retrieve user context
- Phase 2: `GmailActionTool`, `SlackActionTool`, etc.

### Security Architecture

#### Encryption Layer

```python
# Credential Encryption Flow
┌─────────────────────────────────────────────────────────────┐
│                  AES-256-GCM Encryption                      │
└─────────────────────────────────────────────────────────────┘

User API Key → Backend
                  │
                  ▼
        ┌─────────────────┐
        │ Generate Salt   │
        │ (16 bytes)      │
        └─────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │ Derive Key      │
        │ (PBKDF2)        │
        │ Master Key +    │
        │ Salt            │
        └─────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │ Encrypt with    │
        │ AES-256-GCM     │
        │ (12 byte nonce) │
        └─────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │ Store in DB:    │
        │ - encrypted_data│
        │ - salt          │
        │ - nonce         │
        │ - auth_tag      │
        └─────────────────┘
```

**Security Controls:**

1. **Authentication**
   - JWT tokens (15 min access, 7 day refresh)
   - HTTPOnly cookies for refresh tokens
   - CSRF protection via SameSite cookies

2. **Authorization**
   - Role-based access control (RBAC)
   - Organization-level isolation
   - API key permissions per user

3. **Data Protection**
   - All credentials encrypted at rest (AES-256-GCM)
   - TLS 1.3 for data in transit
   - Environment-based master key rotation

4. **PII Sanitization**
   ```python
   # Before sending to external LLM
   sanitized_text = pii_sanitizer.sanitize(user_query)
   # Removes: SSN, credit cards, phone numbers, emails
   ```

5. **Rate Limiting**
   - Per-user: 100 req/min
   - Per-IP: 1000 req/min
   - Per-endpoint: Custom limits

6. **Audit Logging**
   - Every API call logged
   - LLM reasoning captured
   - Action attempts tracked
   - Searchable via admin interface

### Data Architecture

#### Database Schema (PostgreSQL)

See [database-schema.md](./database-schema.md) for detailed ERD.

**Key Tables:**
- `users`: User accounts and profiles
- `organizations`: Multi-tenant organization support
- `organization_members`: User-org relationships
- `credentials`: Encrypted BYOK keys and OAuth tokens
- `agents`: Agent configurations and state
- `agent_conversations`: Chat history
- `audit_logs`: Comprehensive audit trail
- `actions`: Action queue and history (Phase 2)
- `integration_connections`: OAuth connection metadata

#### Vector Database (Milvus)

**Collections:**

1. **user_preferences**
   - Dimension: 1536 (OpenAI ada-002)
   - Fields: user_id, preference_text, embedding, metadata
   - Index: IVF_FLAT
   - Use: Store user preferences and habits

2. **conversation_context**
   - Dimension: 1536
   - Fields: conversation_id, message, embedding, timestamp
   - Index: IVF_FLAT
   - Use: Semantic search in conversation history

3. **search_cache**
   - Dimension: 1536
   - Fields: query_hash, source, embedding, results
   - Index: IVF_FLAT
   - TTL: 1 hour
   - Use: Cache search results for semantic similarity

### Performance Requirements

| Feature | Requirement | Strategy |
|---------|------------|----------|
| Global Search | <3s latency | Parallel API calls, circuit breaker, caching |
| Agent Response | <5s first token | Streaming LLM responses |
| OAuth Flow | <10s total | Async token exchange |
| Audit Log Query | <1s | Indexed queries, pagination |
| Action Review | <200ms render | Optimistic UI updates |

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Deployment                     │
└─────────────────────────────────────────────────────────────┘

                        ┌──────────────┐
                        │  CloudFlare  │
                        │  DNS + CDN   │
                        └──────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        ┌──────────────┐              ┌──────────────┐
        │   Frontend   │              │   Backend    │
        │  (Vercel)    │◄────────────►│  (Railway/  │
        │  Next.js     │   API calls  │   Render)    │
        └──────────────┘              └──────────────┘
                                              │
                ┌─────────────────────────────┼─────────────────┐
                ▼                             ▼                 ▼
        ┌──────────────┐          ┌──────────────┐   ┌──────────────┐
        │  PostgreSQL  │          │    Milvus    │   │    Redis     │
        │  (Supabase/  │          │  (Zilliz)    │   │  (Upstash)   │
        │   Neon)      │          │              │   │              │
        └──────────────┘          └──────────────┘   └──────────────┘
```

**Infrastructure Components:**
- Frontend: Vercel (serverless Next.js)
- Backend: Railway/Render (containerized FastAPI)
- Database: Supabase/Neon (managed PostgreSQL)
- Vector DB: Zilliz Cloud (managed Milvus) OR pgvector extension
- Cache: Upstash Redis (serverless)
- Background Jobs: Celery + Redis

### Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────┐
│                  Observability Stack                         │
└─────────────────────────────────────────────────────────────┘

Application Metrics → Prometheus
                          │
                          ▼
Logs (Structured) → Loki/DataDog
                          │
                          ▼
Traces (OpenTelemetry) → Jaeger/Honeycomb
                          │
                          ▼
                    Grafana Dashboard
```

**Key Metrics:**
- Request latency (p50, p95, p99)
- Error rates by endpoint
- LLM API usage and costs
- Search performance by source
- OAuth token refresh failures
- Database connection pool utilization

### Phase 2 Considerations

**Review Drawer Workflow:**
```
Agent suggests action → Create action record (pending)
                              │
                              ▼
                    Display in Review Drawer
                    - Preview action
                    - Show affected resources
                    - Display AI reasoning
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                Approve             Reject
                    │                   │
                    ▼                   ▼
            Execute action      Mark rejected
            Update status       Log reason
            Notify user         Return to chat
```

**Action Connectors (Write Access):**
- Gmail: Send email, archive, label
- Slack: Send message, create channel
- Notion: Create page, update database
- Requires elevated OAuth scopes (on-demand)

### Technology Stack Summary

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Frontend Framework | Next.js 15 | App Router, RSC, built-in API routes |
| UI Components | shadcn/ui + Tailwind | Accessible, customizable, modern |
| Backend Framework | FastAPI | High performance, async, auto-docs |
| ORM | SQLAlchemy 2.0 | Mature, type-safe, async support |
| Database | PostgreSQL 15+ | ACID, JSON support, reliability |
| Vector DB | Milvus (or pgvector) | Scalable vector search |
| Cache | Redis | Fast, mature, pub/sub support |
| Auth | NextAuth.js + JWT | OAuth providers, session management |
| Orchestration | LangChain | Tool abstraction, agent framework |
| Background Jobs | Celery | Mature, scalable, monitoring |
| API Validation | Pydantic | Type safety, automatic validation |
| Testing | Pytest + Playwright | Backend + E2E coverage |

## Development Phases

### Phase 1: The Observer (Weeks 1-6)

**Sprint 1-2: Foundation**
- Backend: Auth, user management, encryption
- Frontend: Login, dashboard shell
- Database: Core tables, migrations

**Sprint 3-4: BYOK & OAuth**
- Backend: Credential management, OAuth flows
- Frontend: Settings pages, OAuth connection UI
- Integrations: Gmail, Slack, Jira, Calendar read-only

**Sprint 5-6: Search & Agent**
- Backend: Search aggregation, agent orchestration
- Frontend: Global search bar, agent chat, audit trail
- Testing: End-to-end flows

### Phase 2: The Executor (Weeks 7-10)

**Sprint 7-8: Review System**
- Backend: Action queue, approval workflow
- Frontend: Review drawer, action preview
- Database: Action tables, state machine

**Sprint 9-10: Write Actions**
- Backend: Action executors for each integration
- Frontend: Action history, error handling
- Security: Enhanced audit logging

## Security Checklist

- [ ] AES-256-GCM encryption for all credentials
- [ ] TLS 1.3 for all network communication
- [ ] JWT with short expiration (15 min)
- [ ] Refresh token rotation
- [ ] Rate limiting on all endpoints
- [ ] CORS properly configured
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (Content Security Policy)
- [ ] CSRF protection (SameSite cookies)
- [ ] PII sanitization before external API calls
- [ ] Minimal OAuth scopes
- [ ] Regular dependency updates
- [ ] Audit logging for all sensitive operations
- [ ] Environment variable validation
- [ ] Secret rotation procedures

## Conclusion

This architecture provides a solid foundation for building a trust-first AI agent platform with the following strengths:

1. **Scalable**: Horizontal scaling, async processing, caching
2. **Secure**: Defense in depth, encryption, minimal permissions
3. **Maintainable**: Clean architecture, separation of concerns
4. **Observable**: Comprehensive logging, metrics, tracing
5. **Extensible**: Plugin architecture for new integrations

The design prioritizes user trust through transparency (audit trail), control (human-in-the-loop), and security (encryption, minimal scopes).
