# Aura - Enterprise RAG System

A complete Retrieval-Augmented Generation (RAG) system built with FastAPI, Next.js, PostgreSQL, and Qdrant vector database.

## Features

### 🏢 Organization Management
- Organization setup on registration
- Multi-user support within organizations
- Role-based access control (RBAC)
- Department and team management

### 👥 User Management
- User registration and authentication
- JWT-based authentication with refresh tokens
- Password reset functionality
- User roles, departments, and teams assignment

### 🧠 Brain Management
- Create multiple "brains" (knowledge bases)
- Assign brains to roles, departments, or teams
- Different visibility levels: Private, Organization, Role, Department, Team
- Personal brains for individual users

### 📄 Document Management
- Upload documents (PDF, DOCX, TXT, Images)
- OCR support for images
- Automatic document processing and vectorization
- Google Drive integration (coming soon)

### 💬 AI Chat Interface
- Chat with your documents using RAG
- Context-aware responses
- Source attribution for answers
- Chat history and session management

### 🔍 Search Functionality
- Semantic search across documents
- Get document locations and metadata
- Relevance scoring

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database management
- **PostgreSQL** - Main database
- **Qdrant** - Vector database for embeddings
- **OpenAI** - LLM and embeddings
- **Redis** - Caching and background tasks
- **Alembic** - Database migrations

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Zustand** - State management
- **React Query** - Server state management
- **Axios** - API client

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- OpenAI API key

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd aura
```

### 2. Setup Environment Variables

#### Backend

```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your API keys:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - Generate a secure random string
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` - For Google Drive integration (optional)
- `MAIL_USERNAME` and `MAIL_PASSWORD` - For email notifications (optional)

#### Frontend

```bash
cd frontend
cp .env.local .env.local
```

The default API URL should work with Docker setup.

### 3. Run with Docker

From the root directory:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL on port 5432
- Qdrant on ports 6333 (API) and 6334 (gRPC)
- Redis on port 6379
- Backend API on port 8000
- Frontend on port 3000

### 4. Run Database Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

## Manual Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.local .env.local

# Start development server
npm run dev
```

### Start Required Services

You'll need to manually start:
- PostgreSQL
- Qdrant
- Redis

## Usage Guide

### 1. Registration

1. Visit http://localhost:3000
2. Click "Sign Up"
3. Enter your email, password, name, and organization name
4. The first user becomes the organization administrator

### 2. Create a Brain

1. Navigate to "Brains" in the dashboard
2. Click "Create Brain"
3. Set name, description, and visibility
4. Assign to roles, departments, or teams if needed

### 3. Upload Documents

1. Select a brain
2. Click "Upload Documents"
3. Choose files (PDF, DOCX, TXT, or images)
4. Wait for processing to complete

### 4. Chat with Your Documents

1. Go to "Chat"
2. Select a brain
3. Start asking questions
4. View sources for each answer

### 5. Search Documents

1. Use the search feature
2. Enter your query
3. Get relevant document chunks with scores and locations

## API Documentation

Full API documentation is available at http://localhost:8000/docs when the backend is running.

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/password-reset` - Request password reset

#### Brains
- `GET /api/v1/brains` - List accessible brains
- `POST /api/v1/brains` - Create brain
- `GET /api/v1/brains/{id}` - Get brain details
- `PUT /api/v1/brains/{id}` - Update brain
- `DELETE /api/v1/brains/{id}` - Delete brain

#### Documents
- `POST /api/v1/brains/{id}/documents` - Upload document
- `GET /api/v1/brains/{id}/documents` - List documents
- `DELETE /api/v1/brains/{id}/documents/{doc_id}` - Delete document

#### Chat
- `POST /api/v1/chat` - Send message
- `GET /api/v1/sessions` - List chat sessions
- `POST /api/v1/search` - Search documents

## Architecture

### Data Flow

1. **Document Upload**
   - User uploads document
   - Backend saves file to disk
   - Background task processes document
   - Text extracted and chunked
   - Chunks embedded using OpenAI
   - Vectors stored in Qdrant

2. **Chat Query**
   - User sends message
   - Message embedded
   - Similar vectors retrieved from Qdrant
   - Context + query sent to LLM
   - Response generated and returned

### Access Control

Brains can have different visibility levels:
- **Private**: Only owner can access
- **Organization**: All organization members
- **Role**: Members with assigned roles
- **Department**: Members in assigned departments
- **Team**: Members in assigned teams

## Development

### Backend Structure

```
backend/
├── app/
│   ├── api/          # API routes
│   ├── core/         # Core functionality (config, security)
│   ├── db/           # Database session
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   └── services/     # Business logic
├── alembic/          # Database migrations
└── tests/            # Tests
```

### Frontend Structure

```
frontend/
├── app/              # Next.js app directory
├── components/       # React components
├── lib/              # Utilities (API, store)
└── public/           # Static assets
```

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env

2. **Qdrant Connection Error**
   - Ensure Qdrant is running
   - Check QDRANT_HOST and QDRANT_PORT

3. **OpenAI API Error**
   - Verify OPENAI_API_KEY is set correctly
   - Check API usage limits

4. **Document Processing Fails**
   - For PDFs: Ensure pypdf can read the file
   - For Images: Ensure tesseract-ocr is installed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

## Roadmap

- [ ] Google Drive integration
- [ ] SharePoint connector
- [ ] Multiple LLM support (Anthropic, Llama)
- [ ] Advanced analytics dashboard
- [ ] Mobile app
- [ ] Slack/Teams integration
- [ ] Custom embedding models
- [ ] Multi-language support

---

Built with ❤️ using FastAPI and Next.js
