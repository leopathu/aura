# Aura - Personal AI Assistant Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)

> **Open-source personal AI assistant platform** that enables you to connect your favorite applications, bring your own AI models, and automate workflows with intelligent agents powered by LangGraph.

## ✨ Features

- 🔗 **App Integrations** - Connect Gmail, Jira, Slack, Calendar, and more via OAuth
- 🤖 **Bring Your Own Models** - Use your API keys for OpenAI, Claude, Gemini, Grok
- 💬 **Intelligent Chat** - Conversational interface with context-aware AI agents
- ⚡ **Workflow Automation** - Schedule tasks and create event-driven workflows
- 🔒 **Privacy First** - Your data stays in your control, self-hostable
- 🎨 **Modern UI** - Clean, professional interface built with Next.js and Tailwind
- 📊 **Real-time Streaming** - See agent thinking process with live status updates
- 🌐 **Multi-tenant** - Organization-based workspaces with role management

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/leopathu/aura.git
cd aura
```

2. **Start the development environment**
```bash
./scripts/dev-start.sh
```

This will:
- Create necessary environment files
- Build Docker containers
- Start all services (Postgres, Redis, Backend, Frontend)
- Initialize the database with demo data

3. **Access the application**
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/api/docs

4. **Login with demo account**
- Email: `demo@aura.com`
- Password: `demo123`

## 📋 Project Structure

```
aura/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   ├── core/        # Configuration
│   │   └── db/          # Database setup
│   ├── alembic/         # Database migrations
│   ├── main.py          # Application entry point
│   └── requirements.txt # Python dependencies
│
├── frontend/            # Next.js frontend
│   ├── app/            # App Router pages
│   ├── components/     # React components
│   ├── lib/           # Utilities & API client
│   ├── store/         # Zustand state management
│   └── types/         # TypeScript types
│
├── database/           # Database scripts
│   ├── init.sql       # Schema initialization
│   ├── backup.sh      # Backup script
│   └── restore.sh     # Restore script
│
├── scripts/           # Development scripts
│   ├── dev-start.sh   # Start dev environment
│   ├── dev-stop.sh    # Stop dev environment
│   ├── migrate.sh     # Run migrations
│   └── logs.sh        # View logs
│
├── .github/           # GitHub Actions CI/CD
│   └── workflows/
│       ├── ci.yml     # Continuous Integration
│       └── deploy.yml # Deployment
│
├── docs/              # Documentation
│   ├── PRD.md         # Product Requirements
│   ├── TASKS.md       # Implementation tasks
│   └── DATABASE.md    # Database schema
│
└── docker-compose.yml # Development orchestration
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.109
- **Database**: PostgreSQL 16 with pgvector
- **ORM**: SQLAlchemy 2.0 (async)
- **AI/ML**: LangChain, LangGraph
- **Authentication**: JWT with bcrypt
- **Task Queue**: Celery with Redis
- **Models**: OpenAI, Anthropic, Google Gemini

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **State**: Zustand 4.4
- **HTTP**: Axios with interceptors

### Infrastructure
- **Container**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Database**: PostgreSQL + pgvector for embeddings
- **Cache**: Redis 7

## 📖 Documentation

- [Product Requirements Document](docs/PRD.md) - Complete feature specifications
- [Implementation Tasks](docs/TASKS.md) - 480+ development tasks breakdown
- [Database Schema](docs/DATABASE.md) - Full database documentation
- [GitHub Copilot Instructions](.github/copilot-instructions.md) - AI coding assistant guide

## 🔧 Development

### Start Development Environment
```bash
./scripts/dev-start.sh
```

### View Logs
```bash
# All services
./scripts/logs.sh

# Specific service
./scripts/logs.sh backend
./scripts/logs.sh frontend
```

### Run Database Migrations
```bash
./scripts/migrate.sh
```

### Create Database Backup
```bash
./scripts/backup.sh
```

### Stop Development Environment
```bash
./scripts/dev-stop.sh
```

### Run Tests
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## 🌐 Environment Variables

### Root `.env`
```bash
POSTGRES_USER=aura_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=aura_db
```

### Backend `.env`
```bash
SECRET_KEY=your-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key-32-bytes
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_secret
```

### Frontend `.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 🚢 Deployment

### Production Deployment

1. **Configure production environment**
```bash
cp .env.example .env
cp backend/.env.example backend/.env.production
# Update with production values
```

2. **Deploy with Docker Compose**
```bash
docker compose -f docker-compose.prod.yml up -d
```

3. **Or use GitHub Actions**
- Push to `main` branch triggers CI/CD
- Release creation triggers deployment

## 🔐 Security

- All passwords hashed with bcrypt
- API keys encrypted with Fernet (AES-256)
- JWT token authentication
- CORS configuration
- Rate limiting (planned)
- SQL injection prevention via ORM

## 🗺️ Roadmap

### Phase 1: MVP ✅ (In Progress)
- [x] Authentication & user management
- [x] Organization workspaces
- [x] Basic agent creation
- [x] LLM credential management
- [ ] Simple chat interface

### Phase 2: Integrations (Planned)
- [ ] Gmail integration
- [ ] Google Calendar integration
- [ ] Jira integration
- [ ] Slack integration
- [ ] OAuth2 flows

### Phase 3: Real-time Features (Planned)
- [ ] Streaming responses
- [ ] Agent thought traces
- [ ] Tool execution display
- [ ] Progress indicators

### Phase 4: Automation (Planned)
- [ ] Workflow builder
- [ ] Scheduled tasks
- [ ] Event triggers
- [ ] Template library

### Phase 5: Polish & Launch (Planned)
- [ ] Comprehensive testing
- [ ] Security audit
- [ ] Performance optimization
- [ ] Documentation
- [ ] Public launch

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [Next.js](https://nextjs.org/)
- AI orchestration with [LangGraph](https://langchain-ai.github.io/langgraph/)
- Vector search with [pgvector](https://github.com/pgvector/pgvector)

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/leopathu/aura/issues)
- **Discussions**: [GitHub Discussions](https://github.com/leopathu/aura/discussions)
- **Email**: support@aura.dev (coming soon)

## 🌟 Star History

If you find this project helpful, please consider giving it a star ⭐

---

**Made with ❤️ by the Aura team**
