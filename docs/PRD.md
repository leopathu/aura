# Product Requirements Document (PRD)
# Aura - Personal AI Assistant Platform

**Version:** 1.0  
**Date:** February 18, 2026  
**Project Manager:** AI Product Manager  
**Status:** Planning Phase

---

## Executive Summary

Aura is an open-source personal AI assistant platform that enables users to connect their favorite productivity applications and AI models to automate tasks, generate insights, and streamline workflows through intelligent agents. Users can interact through a conversational interface while agents work in the background with real-time status updates.

---

## Product Vision

**Mission Statement:**  
Empower users to accomplish more by connecting their tools and AI models into one intelligent assistant that understands context, executes tasks, and provides actionable insights.

**Target Audience:**
- Knowledge workers (developers, project managers, analysts)
- Professionals managing multiple SaaS tools
- Teams seeking workflow automation
- Power users comfortable with AI tools

---

## Core Features

### 1. User Authentication & Onboarding

**Feature Description:**  
Secure user registration and login system with organization management.

**User Stories:**
- As a new user, I want to register with my email and password so I can start using Aura
- As a returning user, I want to log in securely so I can access my agents and connections
- As a user, I want to create an organization workspace so I can manage my apps and agents
- As a user, I want to switch between multiple organizations so I can separate work and personal projects

**Acceptance Criteria:**
- ✅ Email/password registration with validation
- ✅ Secure password hashing (bcrypt)
- ✅ JWT-based authentication with refresh tokens
- ✅ Organization creation and management
- ✅ Multi-organization support per user
- ✅ Email verification (optional for MVP)
- ✅ Password reset flow (optional for MVP)

**Technical Requirements:**
- FastAPI endpoints: `/auth/register`, `/auth/login`, `/auth/me`
- PostgreSQL tables: users, organizations, memberships
- JWT tokens with 30-minute expiry, refresh tokens with 7-day expiry
- Role-based access: Owner, Admin, Member
- Next.js auth pages with form validation
- Protected routes using middleware

---

### 2. App Connections (OAuth & API Key Integration)

**Feature Description:**  
One-click connection to popular productivity applications with secure credential storage.

**User Stories:**
- As a user, I want to connect Gmail so I can read and send emails through Aura
- As a user, I want to connect Jira so I can create and update tickets via chat
- As a user, I want to connect Google Drive so I can search and retrieve documents
- As a user, I want to connect Google Calendar so I can schedule and manage events
- As a user, I want to see all my connected apps in one place so I can manage them easily
- As a user, I want to disconnect an app so I can revoke access when needed

**Supported Apps (Phase 1):**
1. **Gmail** - OAuth2, read/send emails
2. **Google Calendar** - OAuth2, create/read events
3. **Google Drive** - OAuth2, search/read files
4. **Jira** - OAuth2/API Key, create/update issues
5. **Slack** - OAuth2, send messages, read channels
6. **Notion** - API Key, read/write pages

**App Connection Flow:**
1. User clicks "Connect [App Name]"
2. OAuth popup opens (or API key input form)
3. User authorizes access
4. Aura receives OAuth tokens/API key
5. Credentials encrypted and stored in database
6. Connection status shown as "Connected"
7. User can disconnect anytime

**Acceptance Criteria:**
- ✅ OAuth2 flow implementation for Google apps
- ✅ OAuth2 flow for Jira and Slack
- ✅ API key input for Notion and other apps
- ✅ AES-256 encryption for all credentials
- ✅ Connection status indicators
- ✅ Disconnect/refresh functionality
- ✅ Connection health checks
- ✅ Support for both REST API and MCP protocol

**Technical Requirements:**
- FastAPI OAuth callbacks: `/auth/callback/{provider}`
- Database table: app_credentials (encrypted tokens)
- MCP client implementation for universal app support
- REST API clients for each app
- Next.js app connection UI with icons
- Encryption service using Fernet
- Token refresh logic for OAuth

---

### 3. LLM Model Connections (BYOK - Bring Your Own Key)

**Feature Description:**  
Allow users to add their own API keys for multiple AI model providers.

**User Stories:**
- As a user, I want to add my OpenAI API key so I can use GPT models
- As a user, I want to add my Anthropic key so I can use Claude models
- As a user, I want to add my Google AI key so I can use Gemini models
- As a user, I want to add my xAI key so I can use Grok models
- As a user, I want to label my API keys so I can organize production vs testing keys
- As a user, I want to delete API keys so I can remove them when needed

**Supported Models (Phase 1):**
1. **OpenAI** - GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
2. **Anthropic** - Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
3. **Google** - Gemini 1.5 Pro, Gemini 1.5 Flash
4. **xAI** - Grok (when available)
5. **Custom** - Any OpenAI-compatible endpoint

**API Key Management Flow:**
1. User navigates to Settings → Credentials
2. Clicks "Add API Key"
3. Selects provider (OpenAI, Anthropic, etc.)
4. Enters API key and optional label
5. System validates key format
6. Key encrypted and stored
7. User sees masked key in UI (never displayed again)

**Acceptance Criteria:**
- ✅ Support for 5+ LLM providers
- ✅ API key validation before storage
- ✅ AES-256 encryption for all keys
- ✅ Optional labels for keys
- ✅ Never display keys after storage
- ✅ Delete functionality
- ✅ Active/inactive status toggle
- ✅ Cost tracking per key (future enhancement)

**Technical Requirements:**
- Database table: credentials (type: openai, anthropic, gemini, etc.)
- LangChain model adapters for each provider
- Password input fields for API keys
- Validation endpoints for key testing
- Encryption before database storage
- Next.js credentials management page

---

### 4. Chat Interface with AI Agents

**Feature Description:**  
Conversational interface where users interact with AI agents to get information, generate reports, and execute tasks across connected apps.

**User Stories:**
- As a user, I want to chat with my agent so I can ask questions naturally
- As a user, I want to see my agent's thinking process so I understand what it's doing
- As a user, I want to see which tools the agent is using so I can trust its actions
- As a user, I want to create multiple agents so I can specialize them for different tasks
- As a user, I want to customize agent personality so it matches my preferences
- As a user, I want to see chat history so I can reference previous conversations

**Example Interactions:**
```
User: "Show me all high-priority Jira tickets assigned to me"
Agent: [Searches Jira] "You have 3 high-priority tickets:
1. AUTH-123: Fix login issue
2. API-456: Implement rate limiting
3. DB-789: Optimize query performance"

User: "Email the team about the standup meeting tomorrow at 10am"
Agent: [Creates calendar event, drafts email, shows preview]
"I've created a calendar event and drafted this email: [preview]
Should I send it?"

User: "Generate a summary of all my meetings this week"
Agent: [Reads calendar, fetches meeting notes from Drive]
"Here's your weekly summary: [detailed report with bullet points]"
```

**Acceptance Criteria:**
- ✅ Real-time chat interface
- ✅ Message history persistence
- ✅ Agent "thinking" indicators
- ✅ Tool usage transparency
- ✅ Support for rich content (markdown, code blocks, tables)
- ✅ Multiple agents per organization
- ✅ Agent configuration (name, description, system prompt)
- ✅ Conversation threading
- ✅ Copy/share conversations

**Technical Requirements:**
- LangGraph agent orchestration
- LangChain for model connectivity
- Database table: agent_memory (with pgvector embeddings)
- Activity logs for audit trail
- Next.js chat UI with message bubbles
- Markdown rendering
- WebSocket or SSE for streaming responses

---

### 5. Background Agents with Real-time Streaming Status

**Feature Description:**  
Agents work autonomously in the background with real-time status updates similar to Perplexity's search interface, showing each step of their thought process and tool execution.

**User Stories:**
- As a user, I want to see what my agent is thinking so I understand its reasoning
- As a user, I want to see which tools the agent is calling so I can monitor its actions
- As a user, I want to see progress indicators so I know the agent is working
- As a user, I want to approve dangerous actions so I maintain control
- As a user, I want to see sources and citations so I can verify information
- As a user, I want to cancel long-running tasks so I can stop unwanted actions

**Real-time Status Display:**
```
🤔 Analyzing request...
📊 Searching Jira for tickets...
✓ Found 15 tickets
🔍 Filtering by priority and assignee...
✓ 3 high-priority tickets match
📝 Generating summary...
✓ Summary complete
```

**Agent Thought Process (LangGraph Nodes):**
1. **Analyze** - Understand user request
2. **Plan** - Decide which tools to use
3. **Execute** - Call APIs/tools
4. **Wait for Approval** - Ask user before dangerous actions
5. **Synthesize** - Generate final response
6. **Reflect** - Learn from the interaction (future)

**Acceptance Criteria:**
- ✅ Real-time status streaming (SSE or WebSocket)
- ✅ Display thought trace steps
- ✅ Show tool calls with parameters
- ✅ Progress indicators for long operations
- ✅ Approval prompts for destructive actions
- ✅ Cancellation support
- ✅ Source citations and links
- ✅ Error handling with retry options
- ✅ Background task queue

**Technical Requirements:**
- LangGraph StateGraph implementation
- Server-Sent Events (SSE) for streaming
- FastAPI streaming responses
- Next.js real-time UI updates
- Task queue (Redis/Celery for background jobs)
- Database: activity_logs table
- Status indicators with animations

---

### 6. Workflow Automation & Configuration

**Feature Description:**  
Allow users to create automated workflows that run on schedules or triggers without manual intervention.

**User Stories:**
- As a user, I want to create a daily standup report so it's generated automatically every morning
- As a user, I want to set up email notifications so I'm alerted about important events
- As a user, I want to schedule recurring tasks so they run without my input
- As a user, I want to create triggers so actions happen based on conditions
- As a user, I want to see automation history so I can audit what happened
- As a user, I want to pause/resume automations so I can control when they run

**Automation Examples:**

**Daily Standup Report:**
```yaml
name: "Daily Standup Report"
schedule: "0 9 * * 1-5"  # 9 AM Mon-Fri
steps:
  - Get Jira tickets updated in last 24h
  - Get calendar events for today
  - Get unread high-priority emails
  - Generate summary with AI
  - Send to Slack #standup channel
```

**High-Priority Ticket Alert:**
```yaml
name: "High Priority Alert"
trigger: "jira.issue.created"
conditions:
  - priority: "High" or "Critical"
  - assignee: "@me"
steps:
  - Send Slack DM
  - Add to calendar
  - Email notification
```

**Weekly Report:**
```yaml
name: "Weekly Metrics Report"
schedule: "0 17 * * 5"  # 5 PM Friday
steps:
  - Count completed Jira tickets
  - Calculate meeting hours
  - Analyze email response times
  - Generate charts and insights
  - Email to manager
```

**Acceptance Criteria:**
- ✅ Cron-based scheduling
- ✅ Event-based triggers (webhooks)
- ✅ Conditional logic (if/then)
- ✅ Multi-step workflows
- ✅ Workflow templates
- ✅ Visual workflow builder (future)
- ✅ Test/preview mode
- ✅ Automation history logs
- ✅ Enable/disable toggle
- ✅ Error notifications

**Technical Requirements:**
- Database table: automations, automation_runs
- Celery + Redis for task scheduling
- Webhook endpoints for triggers
- YAML/JSON workflow definitions
- Workflow execution engine
- Next.js automation builder UI
- Monitoring and logging

---

## User Experience Flow

### Complete User Journey

**Day 1 - Onboarding:**
1. User discovers Aura via GitHub/Product Hunt
2. User registers with email/password
3. Creates first organization "Personal Workspace"
4. Guided tour shows key features
5. Connects first app (Gmail) via OAuth
6. Adds OpenAI API key
7. Creates first agent "Email Assistant"
8. Sends first message: "Summarize my unread emails"

**Day 7 - Power User:**
1. User has 5 apps connected (Gmail, Calendar, Jira, Slack, Drive)
2. Has 3 agents: Email Assistant, Project Manager, Report Generator
3. Chats daily for quick tasks
4. Sets up first automation: Daily standup report
5. Shares Aura with team members

**Day 30 - Team Collaboration:**
1. User invites team to organization
2. Team shares agents and automations
3. Background agents handle routine tasks
4. User focuses on high-value work
5. Reports generated automatically

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐   │
│  │  Auth   │  │  Chat   │  │ Apps    │  │ Automations  │   │
│  │  Pages  │  │   UI    │  │Settings │  │    Builder   │   │
│  └─────────┘  └─────────┘  └─────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕ REST API
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │     Auth     │  │     Chat     │  │   Automations    │  │
│  │   Service    │  │   Service    │  │     Service      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          LangGraph Agent Orchestrator                 │  │
│  │   ┌─────────┐  ┌─────────┐  ┌──────────┐            │  │
│  │   │ Analyze │→ │  Plan   │→ │ Execute  │→ Synthesize│  │
│  │   └─────────┘  └─────────┘  └──────────┘            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Integration Layer                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│  │
│  │  │  MCP    │  │  Gmail  │  │  Jira   │  │  Slack  ││  │
│  │  │ Client  │  │ Client  │  │ Client  │  │ Client  ││  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘│  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL + pgvector)                │
│  ┌──────┐ ┌──────────┐ ┌────────────┐ ┌────────────────┐  │
│  │Users │ │ Agents   │ │ Credentials│ │  Agent Memory  │  │
│  └──────┘ └──────────┘ └────────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

**Core Tables:**
1. `users` - User accounts
2. `organizations` - Workspaces
3. `memberships` - User-org relationships
4. `credentials` - Encrypted API keys
5. `agents` - AI agent configurations
6. `agent_memory` - Vector embeddings
7. `activity_logs` - Audit trail
8. `automations` - Workflow definitions
9. `automation_runs` - Execution history

---

## Implementation Roadmap

### Phase 1: MVP Foundation (Weeks 1-4)
**Goal:** Core authentication and basic chat functionality

**Week 1-2: Authentication & Database**
- [ ] Set up project structure
- [ ] PostgreSQL + pgvector setup
- [ ] User registration/login
- [ ] Organization management
- [ ] JWT authentication
- [ ] Basic frontend layout

**Week 3-4: Chat & Agents**
- [ ] LangGraph agent setup
- [ ] Basic chat interface
- [ ] LangChain model integration
- [ ] Simple agent creation
- [ ] Message history

### Phase 2: App Integrations (Weeks 5-8)
**Goal:** Connect 3-5 popular apps

**Week 5-6: OAuth & Credentials**
- [ ] OAuth2 implementation
- [ ] Credential encryption
- [ ] Gmail integration
- [ ] Google Calendar integration
- [ ] App connection UI

**Week 7-8: More Apps**
- [ ] Jira integration
- [ ] Slack integration
- [ ] MCP client implementation
- [ ] App management UI
- [ ] Connection health checks

### Phase 3: Real-time Features (Weeks 9-12)
**Goal:** Background agents with streaming

**Week 9-10: Agent Orchestration**
- [ ] LangGraph state machine
- [ ] Thought trace streaming
- [ ] Tool execution display
- [ ] Approval mechanisms
- [ ] SSE implementation

**Week 11-12: Polish**
- [ ] Real-time UI updates
- [ ] Progress indicators
- [ ] Error handling
- [ ] Performance optimization
- [ ] User testing

### Phase 4: Automations (Weeks 13-16)
**Goal:** Workflow automation

**Week 13-14: Automation Engine**
- [ ] Celery + Redis setup
- [ ] Cron scheduling
- [ ] Webhook triggers
- [ ] Workflow execution
- [ ] Automation database

**Week 15-16: Automation UI**
- [ ] Builder interface
- [ ] Template library
- [ ] History logs
- [ ] Testing tools
- [ ] Documentation

### Phase 5: Polish & Launch (Weeks 17-20)
**Goal:** Production-ready platform

**Week 17-18: Testing & Security**
- [ ] Security audit
- [ ] Performance testing
- [ ] Bug fixes
- [ ] Documentation
- [ ] API documentation

**Week 19-20: Launch Prep**
- [ ] Demo videos
- [ ] Landing page
- [ ] GitHub README
- [ ] Blog post
- [ ] Product Hunt launch

---

## Success Metrics

### User Metrics
- **Week 1:** 100 registered users
- **Month 1:** 500 active users
- **Month 3:** 2,000 active users
- **Month 6:** 10,000+ users

### Engagement Metrics
- Daily active users: >30%
- Average apps connected: 3+
- Average agents per user: 2+
- Chat messages per day: 10+
- Automations created: 1+ per user

### Technical Metrics
- API response time: <200ms
- Agent response time: <3s
- Uptime: >99.5%
- Error rate: <1%

---

## Risk Assessment

### Technical Risks
1. **OAuth Complexity** - Mitigation: Use proven libraries, extensive testing
2. **LLM Rate Limits** - Mitigation: User brings own keys, implement queuing
3. **Data Security** - Mitigation: Encryption, security audits, penetration testing
4. **Scalability** - Mitigation: Horizontal scaling, caching, CDN

### Business Risks
1. **User Adoption** - Mitigation: Focus on UX, clear value proposition
2. **API Key Costs** - Mitigation: BYOK model shifts cost to users
3. **Competition** - Mitigation: Open-source advantage, community building

---

## Future Enhancements (Post-MVP)

### Advanced Features
- [ ] Voice interface
- [ ] Mobile apps (iOS/Android)
- [ ] Team collaboration features
- [ ] Visual workflow builder (drag-and-drop)
- [ ] Agent marketplace
- [ ] Custom tool creation
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Cost tracking and optimization
- [ ] Agent-to-agent communication

### Enterprise Features
- [ ] SSO integration (SAML, LDAP)
- [ ] Advanced permissions
- [ ] Audit logs and compliance
- [ ] On-premise deployment
- [ ] White-labeling
- [ ] SLA guarantees

---

## Appendix

### Glossary
- **Agent:** AI-powered assistant that can execute tasks
- **MCP:** Model Context Protocol - universal app integration standard
- **BYOK:** Bring Your Own Key - user provides their own API keys
- **LangGraph:** Framework for building agent workflows
- **pgvector:** PostgreSQL extension for vector embeddings
- **SSE:** Server-Sent Events - real-time streaming protocol

### References
- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- MCP Specification: https://modelcontextprotocol.io/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Next.js Documentation: https://nextjs.org/docs

---

**Document Owner:** Project Manager  
**Last Updated:** February 18, 2026  
**Next Review:** March 18, 2026
