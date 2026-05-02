# Aura — RAG System

A full-stack **Retrieval-Augmented Generation (RAG)** application. Upload documents into topic-based "Brains", then chat with them using an LLM of your choice. Conversations are persisted and answers stream in real time with source citations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python 3.11), SQLAlchemy 2.0 async, Alembic |
| **Database** | PostgreSQL 16 + pgvector |
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| **LLM / Embeddings** | Ollama (local), OpenAI, Anthropic, Google |
| **Containerisation** | Docker + Docker Compose |

---

## Prerequisites

| Requirement | Version |
|---|---|
| Docker | 24+ |
| Docker Compose | v2 (bundled with Docker Desktop) |
| Ollama *(for local models)* | Latest — [ollama.com](https://ollama.com) |

> **No Python or Node.js installation is required** — everything runs inside Docker.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/leopathu/aura.git
cd aura
```

### 2. Create environment files

**`backend/.env`** (copy and edit):

```bash
cp backend/.env.example backend/.env   # if the example exists, otherwise create it manually
```

Minimum required contents:

```env
# Auth
SECRET_KEY=change-me-to-a-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database (leave as-is for Docker Compose)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/aura

# AI provider — see "AI Provider Setup" section below
OPENAI_API_KEY=sk-replace-me
EMBEDDING_MODEL=mxbai-embed-large
LLM_MODEL=llama3.2
VECTOR_DIMENSIONS=1024

# RAG settings
CHUNK_SIZE=512
CHUNK_OVERLAP=64
RETRIEVAL_TOP_K=5

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:3001"]
DEBUG=false
```

**`frontend/.env.local`**:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. (Optional) Pull Ollama models for local inference

If you want to run models locally, install [Ollama](https://ollama.com) and pull the models before starting:

```bash
# Embedding model (1024-dim — required if using Ollama embeddings)
ollama pull mxbai-embed-large

# LLM
ollama pull llama3.2
```

Then make Ollama listen on all interfaces so Docker can reach it:

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

> On **macOS / Windows** Ollama already listens on `0.0.0.0` by default. On **Linux** you may need to set `OLLAMA_HOST=0.0.0.0` in `/etc/systemd/system/ollama.service` and restart the service.

### 4. Build and start all services

```bash
docker compose up -d --build
```

This starts three containers:

| Container | URL |
|---|---|
| Frontend (Next.js) | http://localhost:3001 |
| Backend (FastAPI) | http://localhost:8000 |
| Database (PostgreSQL + pgvector) | `localhost:5432` |

The backend automatically runs all Alembic migrations on startup.

### 5. Open the app

Navigate to **http://localhost:3001** and register a new account.

---

## AI Provider Setup

You can configure which provider is used for embeddings and LLM generation — **per user** — from the **Settings** page in the app.

### Ollama (local, recommended for privacy)

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull the models: `ollama pull mxbai-embed-large && ollama pull llama3.2`
3. In the app → **Settings**:
   - **Embedding provider**: Ollama | Model: `mxbai-embed-large:latest`
   - **LLM provider**: Ollama | Model: `llama3.2`
   - **Ollama base URL**: `http://localhost:11434`
4. Set `VECTOR_DIMENSIONS=1024` in `backend/.env`

### OpenAI

1. Get an API key from [platform.openai.com](https://platform.openai.com)
2. In the app → **Settings**:
   - **Embedding provider**: OpenAI | Model: `text-embedding-3-small` (1536-dim) or `text-embedding-3-large`
   - **LLM provider**: OpenAI | Model: `gpt-4o`
   - Enter your API key
3. Set `VECTOR_DIMENSIONS=1536` in `backend/.env`

> ⚠️ If you switch between providers that use different embedding dimensions, you must delete all existing documents and re-upload them, and update `VECTOR_DIMENSIONS` to match.

### Anthropic

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. In the app → **Settings**: select **Anthropic**, enter API key, set model (e.g. `claude-3-5-sonnet-20241022`)
3. Use **OpenAI** for embeddings (Anthropic doesn't provide an embedding API)

### Google Gemini

1. Get an API key from [aistudio.google.com](https://aistudio.google.com)
2. In the app → **Settings**: select **Google**, enter API key, set model (e.g. `gemini-1.5-pro`)

---

## Using the App

### Brains

A **Brain** is a knowledge base scoped to a topic. You can create multiple Brains and upload different documents to each.

1. Click **New Brain** in the left sidebar
2. Give it a name (e.g. "Product Docs", "Research Papers")

### Uploading Documents

1. Select a Brain from the sidebar
2. Go to the **Sources** tab
3. Click **Upload** and choose a file

**Supported formats**: PDF, DOCX, XLSX/XLS, CSV, TXT  
**Maximum file size**: 10 MB

After upload the document shows a status badge:
- 🟡 **Pending** — queued for embedding
- 🔵 **Embedding…** — chunks are being vectorised (may take 10–60 s with Ollama)
- 🟢 **Ready** — document is searchable
- 🔴 **Failed** — hover the badge for the error message

### Chatting

1. Select a Brain and go to the **Chat** tab
2. Type a question and press **Enter** (or **Shift+Enter** for a new line)
3. The answer streams in real time with source citations at the bottom of each message
4. Past conversations appear in the left sidebar — click to reload them
5. Click **+ New Chat** to start a fresh conversation
6. Click the **■ Stop** button to abort a stream mid-way

### Conversation History

Conversations are saved to the database. They persist across page refreshes and browser sessions. You can delete individual conversations using the trash icon that appears on hover.

---

## API Reference

Interactive docs are available at **http://localhost:8000/docs** (Swagger UI) and **http://localhost:8000/redoc**.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Get JWT token |
| `GET` | `/api/v1/brains` | List brains |
| `POST` | `/api/v1/brains` | Create brain |
| `POST` | `/api/v1/documents/upload` | Upload & embed a file |
| `GET` | `/api/v1/brains/{id}/documents` | List documents in brain |
| `POST` | `/api/v1/chat/stream` | Chat with SSE streaming |
| `GET` | `/api/v1/chat/conversations` | List conversations |
| `GET` | `/api/v1/settings` | Get AI settings |
| `PUT` | `/api/v1/settings` | Update AI settings |

---

## Development

### Backend — live reload (no container rebuild needed)

The backend directory is volume-mounted into the container. Any Python file change triggers an automatic uvicorn reload.

```bash
# View live backend logs
docker compose logs -f backend

# Run a one-off command inside the container
docker compose exec backend python3 -c "..."

# Create a new Alembic migration
docker compose exec backend alembic revision --autogenerate -m "describe_change"

# Apply migrations
docker compose exec backend alembic upgrade head
```

### Frontend — requires rebuild on code changes

```bash
docker compose build frontend && docker compose up -d frontend
```

### Database

```bash
# Open a psql shell
docker exec aura-db-1 psql -U postgres -d aura

# Reset the database (destructive!)
docker compose down -v && docker compose up -d --build
```

---

## Stopping & Resetting

```bash
# Stop all containers (data preserved)
docker compose down

# Stop and delete all data (full reset)
docker compose down -v
```

---

## Environment Variable Reference

### `backend/.env`

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-…` | JWT signing secret — **change in production** |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime (24 h) |
| `DATABASE_URL` | `postgresql+asyncpg://…` | Async PostgreSQL connection string |
| `OPENAI_API_KEY` | `sk-replace-me` | Fallback OpenAI key (overridden by per-user settings) |
| `EMBEDDING_MODEL` | `mxbai-embed-large` | Default embedding model |
| `LLM_MODEL` | `llama3.2` | Default LLM model |
| `VECTOR_DIMENSIONS` | `1024` | Embedding vector size — **must match your model** |
| `CHUNK_SIZE` | `512` | Characters per document chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between consecutive chunks |
| `RETRIEVAL_TOP_K` | `5` | Number of chunks retrieved per query |
| `ALLOWED_ORIGINS` | `["http://localhost:3001"]` | CORS allowed origins |
| `DEBUG` | `false` | Enable SQLAlchemy query logging |

### `frontend/.env.local`

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI backend base URL |

---

## Troubleshooting

**Embedding stays at "Pending" after upload**
- Check that Ollama is running: `curl http://localhost:11434/api/tags`
- Check backend logs: `docker compose logs -f backend`
- Verify `VECTOR_DIMENSIONS` in `backend/.env` matches your embedding model (1024 for `mxbai-embed-large`, 1536 for OpenAI `text-embedding-3-small`)

**`expected 1536 dimensions, not 1024` error**
- Your `VECTOR_DIMENSIONS` env var doesn't match the DB column. Update `backend/.env` and restart: `docker compose up -d --force-recreate backend`

**Ollama not reachable from Docker**
- Start Ollama with `OLLAMA_HOST=0.0.0.0 ollama serve`
- The backend resolves `localhost` to `host.docker.internal` automatically

**Frontend shows stale data after code changes**
- The frontend requires a full rebuild: `docker compose build frontend && docker compose up -d frontend`

**Port conflicts**
- Frontend uses `3001`, backend uses `8000`, database uses `5432`. Edit `docker-compose.yml` to change host ports if needed.
