# Aura - AI Agent Platform

Aura is an outcome-centric AI Agent platform that allows users to connect their favorite apps and LLM models to perform tasks, analyze reports, and manage work from a single interface.

## Features

- 🔐 **Custom Authentication**: Secure user registration, login, and organization management
- 🤖 **Bring Your Own Model**: Connect OpenAI, Anthropic, or Gemini with your own API keys
- 🔗 **MCP Integration**: Model Context Protocol support for seamless app connections
- 🧠 **Smart Orchestration**: LangGraph-powered agent for intelligent task execution
- 💬 **Streaming UI**: Perplexity-style real-time thought trace
- ✅ **Human-in-the-Loop**: Approval drawer for safe action execution
- 🏢 **Multi-tenant**: Organization and team management
- 🧠 **Vector Memory**: Long-term context with pgvector

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript)
- **Database**: PostgreSQL with pgvector
- **AI**: LangGraph, LiteLLM
- **Protocol**: Model Context Protocol (MCP)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- Docker (optional)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
npm run dev
```

### Database Setup

```bash
# Create database and enable pgvector
psql -U postgres
CREATE DATABASE aura;
\c aura
CREATE EXTENSION vector;

# Run migrations
cd backend
alembic upgrade head
```

## Project Structure

```
aura/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Core configuration
│   │   ├── db/          # Database models
│   │   ├── services/    # Business logic
│   │   └── main.py      # FastAPI app
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── app/            # App router pages
│   ├── components/     # React components
│   ├── lib/            # Utilities
│   └── package.json
└── docker-compose.yml  # Docker setup
```

## License

MIT
