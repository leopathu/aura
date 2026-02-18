# GitHub Copilot Instructions for Aura

## Project Overview
Aura is an open-source Personal AI Assistant platform that enables users to connect their favorite applications (Gmail, Jira, Slack, etc.) and execute tasks through intelligent AI agents.

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with pgvector extension
- **AI/ML**: LangGraph for agent orchestration, LangChain for model connectivity
- **Authentication**: JWT-based auth with bcrypt password hashing
- **Security**: Fernet AES-256 encryption for API keys
- **API Protocols**: REST API + Model Context Protocol (MCP)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **UI/UX**: Professional, clean design with smooth loading states

### Infrastructure
- **Container**: Docker & Docker Compose
- **Vector Database**: pgvector for semantic search
- **Multi-tenancy**: Organization-based data isolation

## Architecture Principles

### Agent System
- Use **LangGraph** for agent state machines and workflow orchestration
- Support multiple LLM providers (OpenAI, Anthropic, Google Gemini)
- Implement "Bring Your Own API Key" model - users provide their own LLM credentials
- Store encrypted API keys per organization using Fernet encryption
- Each agent should have configurable system prompts and behavior

### App Integrations
- Support both **REST API** and **MCP (Model Context Protocol)** for app connections
- OAuth2/API key authentication - store encrypted credentials securely
- Simple one-click app connection flow: Login → Authorize → Store credentials
- MCP client for universal app integrations
- Support for: Gmail, Slack, Jira, Notion, Calendar, and custom integrations

### Database Design
- Multi-tenant architecture with organization-level isolation
- Tables: users, organizations, memberships, credentials, agents, agent_memory, activity_logs
- Use pgvector for storing embeddings (1536 dimensions for OpenAI compatibility)
- All sensitive data (API keys, tokens) must be encrypted before storage

### API Design
- RESTful endpoints under `/api/v1/`
- Proper HTTP status codes and error handling
- JWT bearer token authentication
- Request/response validation with Pydantic schemas
- Support for both synchronous and streaming responses

## Code Style & Patterns

### Backend (FastAPI)
```python
# Use async/await for all database operations
async def create_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    pass

# Proper dependency injection
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    pass

# Encrypt sensitive data before storage
encrypted_key = encryption_service.encrypt(api_key)

# Use LangGraph for agent workflows
from langgraph.graph import StateGraph
graph = StateGraph(AgentState)
graph.add_node("analyze", analyze_node)
```

### Frontend (Next.js)
```typescript
// Use 'use client' for interactive components
'use client'

// Proper TypeScript interfaces
interface Agent {
  id: string
  name: string
  description: string
}

// Tailwind CSS for styling - professional, clean design
<div className="flex items-center justify-between p-6 bg-white rounded-xl shadow-sm">

// Loading states with skeleton screens or spinners
{loading ? <Spinner /> : <Content />}

// Error boundaries and user-friendly error messages
{error && <ErrorMessage message={error} />}
```

## Feature Implementation Guidelines

### Authentication Flow
1. User registers → Create user + default organization
2. User logs in → Return JWT access & refresh tokens
3. Protected routes check JWT validity
4. Support organization switching for multi-org users

### Agent Creation
1. User creates agent with name, description, system prompt
2. Agent linked to organization
3. User can assign LLM credentials to agent
4. Agent config stored as JSON for flexibility

### App Connection
1. Display available apps with logos and descriptions
2. One-click "Connect" button initiates OAuth/API key flow
3. Store encrypted credentials in database
4. Show connection status (connected/disconnected)
5. Allow credential refresh/disconnect

### Chat Interface
1. Real-time chat UI with message history
2. Streaming responses for better UX
3. Show agent "thinking" indicators
4. Display tool usage and thought traces
5. Support for rich content (markdown, code blocks, tables)

### LLM Integration
1. Support multiple providers in parallel
2. User selects preferred model per agent
3. Graceful fallback if model unavailable
4. Cost tracking per organization (future)

## Security Requirements

### Always Encrypt
- API keys and tokens (Fernet encryption)
- OAuth refresh tokens
- Any user-provided credentials

### Never Expose
- Encrypted data in API responses
- Internal system prompts or logic
- Database connection strings
- Encryption keys

### Input Validation
- Validate all user inputs with Pydantic
- Sanitize data before database insertion
- Rate limiting on auth endpoints
- CORS properly configured

## UI/UX Guidelines

### Design System
- **Colors**: Purple primary (#7C3AED), Blue accent (#3B82F6)
- **Spacing**: Consistent 4px/8px grid system
- **Typography**: Clean, readable fonts (system fonts)
- **Shadows**: Subtle shadows for depth (shadow-sm, shadow-md)
- **Transitions**: Smooth 200-300ms transitions

### Loading States
```tsx
// Skeleton screens for content loading
<div className="animate-pulse bg-gray-200 h-8 w-full rounded" />

// Spinners for actions
<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />

// Progress indicators for multi-step flows
<ProgressBar current={2} total={4} />
```

### Error Handling
- User-friendly error messages (no technical jargon)
- Actionable error states with retry buttons
- Toast notifications for success/error feedback
- Form validation with inline errors

## Testing Approach

### Backend
- Unit tests for services and utilities
- Integration tests for API endpoints
- Test encryption/decryption flows
- Mock external API calls

### Frontend
- Component testing with React Testing Library
- E2E tests for critical user flows
- Accessibility testing (WCAG compliance)

## Documentation Standards

### Code Comments
- Document complex LangGraph workflows
- Explain security-critical sections
- API endpoint docstrings with examples
- Type hints for all Python functions

### API Documentation
- Auto-generated OpenAPI/Swagger docs
- Example requests/responses
- Authentication requirements
- Error codes and meanings

## Performance Considerations

### Backend
- Database query optimization (proper indexes)
- Connection pooling for PostgreSQL
- Caching for frequently accessed data
- Async operations for I/O bound tasks

### Frontend
- Code splitting and lazy loading
- Image optimization (Next.js Image component)
- Debounced search inputs
- Virtualized lists for large datasets

## Environment Variables

### Required Backend Variables
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=<jwt-secret>
ENCRYPTION_KEY=<32-byte-key>
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Required Frontend Variables
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Common Patterns to Use

### Database Operations
```python
# Always use sessions properly
async def get_agents(org_id: UUID, db: Session):
    agents = db.query(Agent).filter(
        Agent.org_id == org_id,
        Agent.is_active == True
    ).all()
    return agents
```

### LangGraph Agent Pattern
```python
class AgentState(TypedDict):
    messages: list[dict]
    thought_trace: list[str]
    tool_calls: list[dict]

async def analyze_node(state: AgentState) -> AgentState:
    # Process user input
    state["thought_trace"].append("Analyzing request...")
    return state
```

### Frontend API Calls
```typescript
// Centralized API client with interceptors
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL + '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

// Automatic token injection
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

## What NOT to Do

❌ Don't store unencrypted API keys or credentials
❌ Don't expose internal error details to users
❌ Don't use synchronous database operations
❌ Don't hardcode API URLs or credentials
❌ Don't skip input validation
❌ Don't use inline styles (use Tailwind classes)
❌ Don't make API calls in React render functions
❌ Don't commit .env files
❌ Don't use deprecated LangChain/LangGraph APIs

## Key Focus Areas

When generating code for this project:

1. **Security First**: Always encrypt sensitive data, validate inputs, use proper authentication
2. **Professional UI**: Clean, modern design with smooth loading states and transitions
3. **Type Safety**: Use TypeScript interfaces and Pydantic models consistently
4. **Error Handling**: Graceful degradation with user-friendly messages
5. **Performance**: Optimize queries, use async operations, implement caching
6. **Scalability**: Multi-tenant design, organization-level isolation
7. **Developer Experience**: Clear code structure, comprehensive comments, proper typing

## Integration Examples

### Adding a New LLM Provider
1. Add credential type to `CredentialType` enum
2. Update encryption service if needed
3. Add provider to LangChain model mapping
4. Update frontend credential form
5. Test end-to-end flow

### Adding a New App Integration
1. Create MCP server or REST client
2. Add OAuth flow or API key input
3. Store encrypted credentials
4. Implement tool functions for agent use
5. Add to UI with icon and description

## Version Control

- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Branch naming: `feature/`, `bugfix/`, `hotfix/`
- PR descriptions should reference issues
- Keep commits atomic and focused

---

**Remember**: Aura is about making AI agents accessible and powerful while keeping user data secure and giving users control over their tools and models.
