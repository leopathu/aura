#!/bin/bash
# Development environment startup script

set -e

echo "🚀 Starting Aura development environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration!"
fi

# Check if backend/.env exists
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please update backend/.env with your configuration!"
fi

# Check if frontend/.env.local exists
if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend/.env.local file..."
    cp frontend/.env.local.example frontend/.env.local
fi

# Create backup directory
mkdir -p database/backups

# Pull latest images
echo "📦 Pulling Docker images..."
docker compose pull

# Build containers
echo "🔨 Building containers..."
docker compose build

# Start services
echo "▶️  Starting services..."
docker compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Start backend
echo "▶️  Starting backend..."
docker compose up -d backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Start frontend
echo "▶️  Starting frontend..."
docker compose up -d frontend

# Show status
echo ""
echo "✅ Aura is running!"
echo ""
echo "📊 Service URLs:"
echo "   Frontend:  http://localhost:3001"
echo "   Backend:   http://localhost:8001"
echo "   API Docs:  http://localhost:8001/api/docs"
echo "   Database:  localhost:5432"
echo "   Redis:     localhost:6379"
echo ""
echo "🔍 View logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 Stop all services:"
echo "   docker compose down"
echo ""
echo "🗑️  Clean up (removes volumes):"
echo "   docker compose down -v"
echo ""

# Show container status
docker compose ps
