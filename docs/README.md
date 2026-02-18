# Aura AI Agent Platform - Architecture Documentation

This directory contains comprehensive architecture and design documentation for the Aura AI Agent Platform.

## 📚 Documentation Index

### 1. [System Architecture](./architecture.md)
**Complete technical architecture overview**

- High-level system architecture diagrams
- Component architecture (Frontend, Backend, Data Layer)
- Integration architecture for OAuth providers
- Agent orchestration workflow
- Security architecture overview
- Deployment architecture
- Technology stack justification
- Performance requirements
- Scalability considerations

**Read this first** to understand the overall system design.

### 2. [Database Schema](./database-schema.md)
**Detailed database design with ERDs**

- Entity Relationship Diagrams
- PostgreSQL table definitions
- Vector database schema (Milvus/pgvector)
- Indexes and performance optimizations
- Sample queries
- Data retention policies
- Backup strategies

**Essential for** understanding data models and relationships.

### 3. [API Contracts](./api-contracts.md)
**Complete REST API and WebSocket specifications**

- All REST endpoints with request/response schemas
- WebSocket protocol for real-time agent interactions
- Authentication and authorization flows
- Error handling and status codes
- Rate limiting policies
- Pagination strategies
- OpenAPI/Swagger documentation

**Reference this** when implementing frontend or backend features.

### 4. [Security Architecture](./security-architecture.md)
**Comprehensive security design and controls**

- Threat model and risk assessment
- Authentication mechanisms (JWT, OAuth2)
- Authorization (RBAC) implementation
- Data encryption (AES-256-GCM)
- PII sanitization strategies
- Rate limiting implementation
- Audit logging requirements
- Incident response procedures
- Compliance considerations (GDPR, SOC 2)

**Critical reading** before implementing any security-sensitive features.

### 5. [Implementation Guide](./implementation-guide.md)
**Step-by-step development roadmap**

- Phase-by-phase implementation plan
- Code samples for critical components
- Testing strategies (unit, integration, E2E)
- Deployment configuration
- Monitoring and observability setup
- Development workflow

**Follow this** for actual implementation work.

## 🎯 Quick Start

### For Architects
1. Read [architecture.md](./architecture.md) for system overview
2. Review [database-schema.md](./database-schema.md) for data design
3. Check [security-architecture.md](./security-architecture.md) for security patterns

### For Backend Developers
1. Start with [api-contracts.md](./api-contracts.md) for endpoint specifications
2. Reference [database-schema.md](./database-schema.md) for data models
3. Follow [implementation-guide.md](./implementation-guide.md) for code samples
4. Review [security-architecture.md](./security-architecture.md) for security requirements

### For Frontend Developers
1. Study [api-contracts.md](./api-contracts.md) for API integration
2. Review [architecture.md](./architecture.md) for component structure
3. Follow [implementation-guide.md](./implementation-guide.md) for UI patterns

### For Security Engineers
1. Read [security-architecture.md](./security-architecture.md) thoroughly
2. Review [api-contracts.md](./api-contracts.md) for authentication flows
3. Check [database-schema.md](./database-schema.md) for data protection

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js 15)                   │
│  Global Search | Agent Chat | Review Drawer | Audit Trail   │
└─────────────────────────────────────────────────────────────┘
                              │
                         HTTPS/TLS
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  Auth | Search | Agent Orchestration | Actions | Audit      │
└─────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │  PostgreSQL  │          │    Milvus    │
        │  (Primary)   │          │  (Vectors)   │
        └──────────────┘          └──────────────┘
                              │
                         OAuth/APIs
                              │
┌─────────────────────────────────────────────────────────────┐
│         External Services (Gmail, Slack, Jira, etc.)        │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Key Features

### Phase 1 - The Observer
- **F1.1**: BYOK Interface (OpenAI/Anthropic/Gemini)
- **F1.2**: OAuth2 Integration (Gmail, Slack, Jira, Calendar)
- **F1.3**: Global Search (<3s latency)
- **F1.4**: Audit Trail (AI reasoning transparency)

### Phase 2 - The Executor
- **F2.1**: Review Drawer (action approval UI)
- **F2.2**: Action Connectors (write access)
- **F2.3**: Contextual Memory (vector-based)

## 🔐 Security Principles

1. **Trust-First**: Every action requires explicit user approval
2. **Encryption**: AES-256-GCM for all credentials at rest
3. **Minimal Scopes**: Read-only OAuth in Phase 1
4. **Transparency**: Complete audit trail of all AI decisions
5. **PII Protection**: Local sanitization before external API calls

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 15 | React framework with App Router |
| Backend | FastAPI | High-performance Python API |
| Database | PostgreSQL 15+ | Primary relational database |
| Vector DB | Milvus / pgvector | Semantic search and memory |
| Cache | Redis | Session management and caching |
| Auth | JWT + OAuth2 | Authentication and authorization |
| Orchestration | LangChain | AI agent framework |
| Background Jobs | Celery | Async task processing |

## 📊 Database Tables

**Core Tables:**
- `users` - User accounts
- `organizations` - Multi-tenant organizations
- `organization_members` - User-org relationships with roles
- `credentials` - Encrypted API keys and OAuth tokens
- `agents` - AI agent configurations
- `agent_conversations` - Chat history
- `agent_messages` - Individual messages
- `audit_logs` - Comprehensive audit trail
- `actions` - Proposed/executed actions (Phase 2)
- `integration_connections` - OAuth connection status

**Vector Collections:**
- `user_preferences` - User habits and preferences
- `conversation_context` - Semantic conversation search
- `search_embeddings` - Cached search results

## 🔄 Development Workflow

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Running Tests
```bash
# Backend
pytest tests/

# Frontend
npm test

# E2E
npx playwright test
```

## 📈 Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Global Search | <3s | Parallel queries, circuit breaker |
| Agent Response | <5s first token | Streaming LLM responses |
| API Latency (p95) | <500ms | Caching, indexes, async processing |
| Concurrent Users | 10,000+ | Horizontal scaling, connection pooling |

## 🚀 Deployment

### Production Architecture
- **Frontend**: Vercel (serverless Next.js)
- **Backend**: Railway/Render (containerized FastAPI)
- **Database**: Supabase/Neon (managed PostgreSQL)
- **Vector DB**: Zilliz Cloud (managed Milvus)
- **Cache**: Upstash Redis (serverless)

### Environment Variables
See `.env.example` files in backend/ and frontend/ directories.

### Docker Deployment
```bash
docker-compose up -d
```

## 📝 API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

## 🧪 Testing Strategy

1. **Unit Tests**: Individual functions and methods
2. **Integration Tests**: API endpoints with test database
3. **E2E Tests**: Complete user flows with Playwright
4. **Security Tests**: OWASP Top 10 vulnerability scanning
5. **Load Tests**: Performance under concurrent load

## 📞 Support & Contact

- **Technical Questions**: See implementation-guide.md
- **Security Issues**: security@aura.example.com
- **Architecture Decisions**: See architecture.md

## 📅 Development Timeline

### Phase 1 (6 weeks)
- Week 1-2: Foundation (Auth, DB, Core API)
- Week 3: BYOK Credentials
- Week 4: OAuth Integration
- Week 5: Global Search
- Week 6: Agent Orchestration & Audit Trail

### Phase 2 (4 weeks)
- Week 7-8: Review Drawer & Action Queue
- Week 9-10: Action Executors & Testing

## 🔍 Code Review Checklist

- [ ] Follows architecture patterns from documentation
- [ ] All API keys encrypted with AES-256-GCM
- [ ] Input validation using Pydantic schemas
- [ ] SQL queries parameterized (no injection risk)
- [ ] Error handling with proper status codes
- [ ] Audit logging for sensitive operations
- [ ] Rate limiting applied
- [ ] Unit tests written
- [ ] API documentation updated

## 📖 Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Next.js Documentation: https://nextjs.org/docs
- LangChain Documentation: https://python.langchain.com/
- Milvus Documentation: https://milvus.io/docs
- PostgreSQL Documentation: https://www.postgresql.org/docs/

## 🎓 Learning Path

1. **Understand the Problem**: Read project-details.md in root
2. **Learn the Architecture**: Read architecture.md
3. **Study Data Models**: Review database-schema.md
4. **Explore APIs**: Read api-contracts.md
5. **Learn Security**: Study security-architecture.md
6. **Start Building**: Follow implementation-guide.md

## ✅ Definition of Done

A feature is complete when:
- [ ] Code implemented per architecture specs
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] API documentation updated
- [ ] Security review completed
- [ ] Audit logging implemented
- [ ] Performance targets met
- [ ] Code reviewed and approved

---

**Last Updated**: 2024-02-18

**Architecture Version**: 1.0.0

**Status**: ✅ Ready for Implementation
