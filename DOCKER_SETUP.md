# Docker Compose Setup for Aura

This document describes the Docker Compose setup for the Aura application.

## Architecture

The Docker Compose configuration includes:

- **Backend**: FastAPI application (Python 3.11) on port 8000
- **Frontend**: Next.js application (Node 18) on port 3000
- **Database**: PostgreSQL 16 with PgVector extension on port 5432

## Features

### PostgreSQL with PgVector
- Uses the official `pgvector/pgvector:pg16` image
- Automatically installs and enables the vector extension
- Configured with database initialization scripts

### Backend API
- FastAPI with hot-reload for development
- Includes PgVector Python client (`pgvector`)
- Database connectivity testing endpoint
- CORS configured for frontend communication

### Frontend (Next.js)
- Next.js 15 with TypeScript and Tailwind CSS
- Hot-reload development mode
- Environment variables configured

## Quick Start

1. **Start all services:**
```bash
docker compose up -d
```

2. **Check service status:**
```bash
docker compose ps
```

3. **Test the setup:**
```bash
# Backend health check
curl http://localhost:8000/health

# Database and PgVector status
curl http://localhost:8000/api/db-status

# Frontend (when running)
curl http://localhost:3000
```

## Environment Files

The setup includes pre-configured environment files:

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@db:5432/aura_db
API_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Aura
NEXT_PUBLIC_APP_DESCRIPTION=Augmented Understanding & Retrieval Assistant
```

## Database Features

The database includes:
- PostgreSQL 16
- PgVector extension for vector operations
- Persistent data storage with named volumes
- Initialization scripts for extension setup

### Testing Vector Operations

```sql
-- Connect to database
docker exec -it aura-db psql -U user -d aura_db

-- Test vector extension
SELECT '[1,2,3]'::vector(3) AS sample_vector;

-- Create a table with vectors (example)
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

The backend provides several endpoints:

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /api/test` - Test endpoint
- `GET /api/db-status` - Database and PgVector status

## Troubleshooting

### Check logs
```bash
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs frontend
docker compose logs db
```

### Rebuild services
```bash
docker compose down
docker compose up --build -d
```

### Database connection
```bash
docker exec -it aura-db psql -U user -d aura_db
```