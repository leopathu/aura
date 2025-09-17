# Aura - Augmented Understanding & Retrieval Assistant

Aura is a project template for building an AI-powered assistant with a Python backend and Node.js frontend, orchestrated using Docker Compose.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Current Repository State
- This is a **project template** - the backend and frontend directories referenced in docker-compose.yml do NOT exist yet
- The repository contains only: README.md, docker-compose.yml, .gitignore, and this instructions file
- No source code, build scripts, or CI/CD pipelines exist currently
- The project is designed to have a microservices architecture with PostgreSQL database

## Working Effectively

### Prerequisites
Before attempting to work with this project:
- Docker must be installed and running
- Docker Compose v2 must be available (use `docker compose` not `docker-compose`)
- The backend and frontend directories must be created with proper structure

### Current Build Status
- **CRITICAL**: DO NOT attempt to run `docker compose up` until backend and frontend directories are created
- Running docker compose currently fails with: "env file /home/runner/work/aura/aura/backend/.env not found"
- The docker-compose.yml expects:
  - `./backend/` directory with a Dockerfile
  - `./frontend/` directory with a Dockerfile  
  - `./backend/.env` environment file
  - `./frontend/.env` environment file

### Expected Project Structure
Based on docker-compose.yml analysis, the complete project should have:
```
.
├── README.md
├── docker-compose.yml
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── .env
│   ├── main.py (FastAPI application)
│   └── requirements.txt
└── frontend/
    ├── Dockerfile
    ├── .env
    ├── package.json
    └── src/
```

### Docker Compose Configuration
The docker-compose.yml defines:
- **backend**: Python/FastAPI service on port 8000 with `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- **frontend**: Node.js service on port 3000 with `npm run dev -- --host`
- **db**: PostgreSQL 16 database on port 5432
  - Database: aura_db
  - User: user
  - Password: password

### Commands That Work Currently
- `docker --version` - Check Docker installation
- `docker compose version` - Check Docker Compose availability
- `docker compose up db --no-deps -d` - Start database service independently (WORKS!)
- `docker exec -it aura-db psql -U user -d aura_db -c "SELECT version();"` - Test database connection
- `ls -la` - View repository contents
- `git status` - Check git repository status

### Commands That DO NOT Work Currently
- `docker compose ps` - Fails due to missing .env files even when containers are running
- `docker compose config` - Shows warning about obsolete version and fails due to missing .env files
- `docker compose up` - Fails because backend/frontend directories don't exist
- `docker compose build` - Fails because Dockerfiles don't exist
- Any build, test, or run commands - No source code exists yet

## Development Setup (When Code Exists)

### Initial Setup (After Creating Backend/Frontend)
```bash
# Clone and enter repository
cd /path/to/aura

# Create environment files
touch backend/.env
touch frontend/.env

# Build and start services - NEVER CANCEL: Initial build may take 10-15 minutes
docker compose up --build
# Set timeout to 30+ minutes for first build
```

### Development Workflow (Future)
```bash
# Start services in development mode
docker compose up

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop services
docker compose down

# Rebuild after code changes - NEVER CANCEL: Rebuild takes 5-10 minutes
docker compose up --build
# Set timeout to 20+ minutes for rebuilds
```

### Database Access (When Available)
```bash
# Connect to PostgreSQL
docker exec -it aura-db psql -U user -d aura_db

# Database connection details:
# Host: localhost (or db from within containers)
# Port: 5432
# Database: aura_db
# Username: user
# Password: password
```

## Validation Steps

### Current State Validation
Run these commands to verify the current template state:
```bash
# Verify repository structure
ls -la
# Should show: README.md, docker-compose.yml, .gitignore, .github/

# Verify Docker availability
docker --version
docker compose version

# Test that database service works independently - NEVER CANCEL: Takes 2-3 minutes to pull PostgreSQL image
docker compose up db --no-deps -d
# Set timeout to 10+ minutes for initial PostgreSQL image pull

# Verify database is running and accessible
docker exec -it aura-db psql -U user -d aura_db -c "SELECT version();"
# Should return PostgreSQL version information

# Clean up database test
docker compose down

# Verify docker-compose configuration syntax
docker compose config
# Should show version warning and fail due to missing .env files

# Confirm expected failure when trying to build full stack
docker compose up --build --no-start
# Should fail with env file not found error
```

### Future Validation (When Code Exists)
After backend and frontend are implemented:
```bash
# Test complete application startup - NEVER CANCEL: Takes 10-15 minutes
docker compose up --build -d
# Set timeout to 30+ minutes

# Verify all services are running
docker compose ps
# Should show backend, frontend, and db as "running"

# Test backend API (when implemented)
curl http://localhost:8000/
# Should return API response

# Test frontend (when implemented)
curl http://localhost:3000/
# Should return frontend page

# Test database connection
docker exec -it aura-db psql -U user -d aura_db -c "SELECT version();"
# Should return PostgreSQL version

# Clean up
docker compose down
```

## Important Notes

- **CRITICAL**: This is a template repository - most functionality doesn't exist yet
- **NEVER** attempt to cancel Docker builds - they may take 15+ minutes on first run
- Always use `docker compose` (with space) not `docker-compose` (with hyphen)
- The .gitignore is configured for Python development with extensive exclusions
- All services use volume mounts for hot-reload development
- Database data persists in named volume `postgres_data`

## Creating the Missing Components

To make this project functional, you need to create:

1. **backend/** directory with:
   - Dockerfile (Python-based)
   - main.py (FastAPI application)
   - requirements.txt
   - .env file

2. **frontend/** directory with:
   - Dockerfile (Node.js-based)
   - package.json
   - src/ directory with application code
   - .env file

3. Optionally add:
   - GitHub Actions workflows in .github/workflows/
   - Additional documentation
   - Tests and test configuration

## Common Issues

- **"env file not found"**: Create .env files in backend/ and frontend/ directories
- **"build context does not exist"**: Create backend/ and frontend/ directories with Dockerfiles
- **Docker compose version warning**: Remove the `version: '3.8'` line from docker-compose.yml (obsolete in Compose v2)