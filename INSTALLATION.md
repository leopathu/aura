# Installation Guide - Aura RAG System

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Docker** (version 20.10+)
   - Download from: https://www.docker.com/products/docker-desktop
   
2. **Docker Compose** (version 2.0+)
   - Usually comes with Docker Desktop

3. **OpenAI API Key**
   - Sign up at: https://platform.openai.com/
   - Create an API key from: https://platform.openai.com/api-keys

## Installation Steps

### Option 1: Quick Start with Docker (Recommended)

1. **Clone or navigate to the project directory**
   ```bash
   cd /path/to/aura
   ```

2. **Make the setup script executable**
   ```bash
   chmod +x setup.sh
   ```

3. **Run the setup script**
   ```bash
   ./setup.sh
   ```

4. **Edit the backend .env file**
   ```bash
   nano backend/.env
   # or
   vim backend/.env
   ```

   **Required settings:**
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `SECRET_KEY` - Generate with: `openssl rand -hex 32`

   **Optional settings:**
   - Email configuration (for password reset)
   - Google Drive credentials (for Google Drive integration)

5. **Restart the backend to apply changes**
   ```bash
   docker-compose restart backend
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Manual Installation

#### Backend Setup

1. **Install Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

3. **Install Qdrant**
   ```bash
   docker run -p 6333:6333 -p 6334:6334 \
       -v $(pwd)/qdrant_storage:/qdrant/storage:z \
       qdrant/qdrant
   ```

4. **Install Redis**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   ```

5. **Setup Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

6. **Install system dependencies (for document processing)**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr libtesseract-dev poppler-utils
   
   # macOS
   brew install tesseract poppler
   ```

7. **Create and configure .env file**
   ```bash
   cp .env.example .env
   nano .env
   ```

8. **Create database**
   ```bash
   createdb aura_db
   ```

9. **Run migrations**
   ```bash
   alembic upgrade head
   ```

10. **Start the backend server**
    ```bash
    uvicorn app.main:app --reload
    ```

#### Frontend Setup

1. **Install Node.js 18+**
   ```bash
   node --version  # Should be 18 or higher
   ```

2. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Create environment file**
   ```bash
   cp .env.local .env.local
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

## Verification

1. **Check if all services are running:**
   ```bash
   docker-compose ps
   ```

   You should see:
   - aura_postgres (healthy)
   - aura_qdrant (healthy)
   - aura_redis (healthy)
   - aura_backend (running)
   - aura_frontend (running)

2. **Test the backend API:**
   ```bash
   curl http://localhost:8000/health
   ```

   Should return: `{"status":"healthy"}`

3. **Test the frontend:**
   Open http://localhost:3000 in your browser

## First-Time Usage

1. **Register an account:**
   - Go to http://localhost:3000
   - Click "Sign Up"
   - Fill in:
     - Email
     - Password (min 8 characters)
     - Full Name
     - Organization Name
   - Click "Create Account"

2. **The first user automatically becomes the organization administrator**

3. **Create your first brain:**
   - Navigate to "Brains"
   - Click "Create Brain"
   - Enter name and description
   - Choose visibility level
   - Click "Create"

4. **Upload documents:**
   - Select your brain
   - Click "Upload Documents"
   - Drag and drop files or click to browse
   - Wait for processing

5. **Start chatting:**
   - Go to "Chat"
   - Select your brain
   - Ask questions about your documents

## Troubleshooting

### Backend won't start

1. **Check logs:**
   ```bash
   docker-compose logs backend
   ```

2. **Common issues:**
   - Missing OPENAI_API_KEY in .env
   - Database connection failed (check PostgreSQL is running)
   - Port 8000 already in use

### Frontend won't start

1. **Check logs:**
   ```bash
   docker-compose logs frontend
   ```

2. **Common issues:**
   - node_modules not installed (run `npm install`)
   - Port 3000 already in use

### Documents not processing

1. **Check if tesseract is installed (for image OCR):**
   ```bash
   docker-compose exec backend tesseract --version
   ```

2. **Check processing logs:**
   ```bash
   docker-compose logs backend | grep "process"
   ```

### Can't connect to Qdrant

1. **Check if Qdrant is running:**
   ```bash
   curl http://localhost:6333/health
   ```

2. **Restart Qdrant:**
   ```bash
   docker-compose restart qdrant
   ```

## Updating

To update the application:

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

## Backup

### Database Backup

```bash
docker-compose exec postgres pg_dump -U postgres aura_db > backup.sql
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U postgres aura_db < backup.sql
```

### Qdrant Backup

The Qdrant data is stored in `qdrant_data` Docker volume. To backup:

```bash
docker run --rm -v aura_qdrant_data:/source -v $(pwd):/backup \
    alpine tar czf /backup/qdrant_backup.tar.gz -C /source .
```

## Production Deployment

For production deployment:

1. **Change SECRET_KEY** to a secure random value
2. **Set DEBUG=False** in backend/.env
3. **Use proper SSL certificates**
4. **Set up proper CORS origins**
5. **Use production database** (not localhost)
6. **Set up proper backup strategy**
7. **Configure monitoring and logging**
8. **Use environment-specific docker-compose files**

Example production docker-compose:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Getting Help

- Check the main README.md for more details
- View API documentation at http://localhost:8000/docs
- Check logs: `docker-compose logs -f`
- Open an issue on GitHub

## Next Steps

After installation:

1. Read the [User Guide](README.md#usage-guide)
2. Explore the [API Documentation](http://localhost:8000/docs)
3. Check out [Example Use Cases](README.md#architecture)
4. Configure [Google Drive Integration](README.md#roadmap) (optional)

---

Need help? Open an issue or check the documentation!
