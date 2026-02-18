# Aura Backend

FastAPI backend for the Aura Personal AI Assistant Platform.

## Project Structure

```
backend/
├── app/
│   ├── api/                 # API routes
│   │   └── v1/
│   │       ├── endpoints/   # API endpoint modules
│   │       └── __init__.py  # API router
│   ├── core/                # Core configuration
│   │   └── config.py        # Settings management
│   ├── db/                  # Database
│   │   ├── base.py          # Base model imports
│   │   └── session.py       # Database session
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
└── .env.example            # Environment variables template
```

## Technology Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL with pgvector extension
- **ORM**: SQLAlchemy 2.0 (async)
- **AI/ML**: LangChain, LangGraph, Google Gemini
- **Authentication**: JWT with bcrypt
- **Security**: Fernet encryption for API keys
- **Task Queue**: Celery with Redis (future)

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 16 with pgvector
- Redis (optional, for task queue)

### Installation

1. **Clone the repository**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your values
```

5. **Run the application**
```bash
uvicorn main:app --reload --port 8001
```

The API will be available at `http://localhost:8001`

## Environment Variables

Key environment variables (see `.env.example` for full list):

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (32+ characters)
- `ENCRYPTION_KEY`: Fernet key for encrypting API keys
- `ALLOWED_ORIGINS`: CORS allowed origins
- `GEMINI_API_KEY`: Google Gemini API key (optional)

## API Documentation

- **Swagger UI**: `http://localhost:8001/api/docs`
- **ReDoc**: `http://localhost:8001/api/redoc`
- **OpenAPI JSON**: `http://localhost:8001/api/openapi.json`

## Development

### Running with Docker

```bash
# From the root directory
docker compose up backend
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Style

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Use async/await for all I/O operations

## Features

### Current
- ✅ FastAPI application structure
- ✅ CORS configuration
- ✅ Environment-based settings
- ✅ Async database setup
- ✅ Project structure organized

### Planned
- Authentication endpoints
- Organization management
- Agent creation and chat
- App integrations (Gmail, Jira, Slack, etc.)
- LangGraph agent orchestration
- Streaming responses with SSE
- Workflow automation

## Contributing

1. Create a new branch for your feature
2. Follow the project structure
3. Write tests for new features
4. Update documentation
5. Submit a pull request

## License

Open source - see LICENSE file
