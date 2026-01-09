# Aura MVP - Setup Instructions

## Prerequisites

- Docker and Docker Compose
- OR:
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL 15+ with pgvector extension

## Quick Start with Docker

1. **Clone and navigate to the project:**
   ```bash
   cd /home/leopathu/Public/aura
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs

## Manual Setup

### Backend Setup

1. **Create Python virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Generate encryption key:**
   ```python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Add this to `.env` as `ENCRYPTION_KEY`

5. **Setup database:**
   ```bash
   # Create database
   createdb aura
   
   # Enable pgvector extension
   psql aura -c "CREATE EXTENSION vector;"
   ```

6. **Start the backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. **Navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API URL
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

## First Steps

1. **Register an account** at http://localhost:3000/auth/register

2. **Create an organization** (you'll be prompted on first login)

3. **Add API credentials:**
   - Go to Settings → Credentials
   - Add your OpenAI, Anthropic, or Gemini API key

4. **Create your first agent:**
   - Go to Dashboard → Create Agent
   - Give it a name and description

5. **Start chatting:**
   - Click "Chat with Agent"
   - Ask Aura to help you with tasks

## MVP Features Included

✅ **Authentication**
- User registration and login
- JWT-based authentication
- Secure password hashing

✅ **Organization Management**
- Create organizations
- Invite team members
- Role-based access control (Owner, Admin, Member)

✅ **BYO LLM Keys**
- Encrypted storage of API keys
- Support for OpenAI, Anthropic, and Gemini
- Secure key management

✅ **Agent System**
- Create multiple agents per organization
- Configure agent behavior
- Activity logging

✅ **Chat Interface**
- Perplexity-style streaming UI
- Thought trace visualization
- Message history

✅ **MCP Integration Framework**
- MCP client implementation
- Tool discovery and execution
- Multi-server support

✅ **LangGraph Orchestration**
- State machine for agent logic
- Planning and execution nodes
- Human-in-the-loop support

## Next Steps for Production

- [ ] Implement actual MCP server connections
- [ ] Add OAuth for app integrations (Gmail, Slack, etc.)
- [ ] Implement vector memory with embeddings
- [ ] Add approval drawer for write operations
- [ ] Set up scheduled background tasks
- [ ] Add comprehensive error handling
- [ ] Implement rate limiting
- [ ] Add monitoring and logging
- [ ] Set up CI/CD pipeline
- [ ] Security audit and SOC2 compliance

## Troubleshooting

**Database connection errors:**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify pgvector extension is installed

**Frontend can't reach backend:**
- Check NEXT_PUBLIC_API_URL in .env.local
- Ensure backend is running on correct port
- Check CORS settings in backend

**Authentication issues:**
- Clear browser localStorage
- Check JWT secret configuration
- Verify token expiration settings

## Support

For issues or questions:
- Check the README.md
- Review API docs at /api/docs
- Check backend logs for errors

## License

MIT License - See LICENSE file for details
