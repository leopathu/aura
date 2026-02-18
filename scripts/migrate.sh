#!/bin/bash
# Database migration script

set -e

echo "🔄 Running database migrations..."

# Check if backend container is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "❌ Backend container is not running!"
    echo "Start it with: docker compose up -d backend"
    exit 1
fi

# Run migrations
docker compose exec backend alembic upgrade head

echo "✅ Migrations completed!"
