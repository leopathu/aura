#!/bin/bash
# Database backup script wrapper

set -e

echo "💾 Creating database backup..."

# Check if postgres container is running
if ! docker compose ps postgres | grep -q "Up"; then
    echo "❌ Postgres container is not running!"
    echo "Start it with: docker compose up -d postgres"
    exit 1
fi

# Run backup inside container
docker compose exec postgres /backups/backup.sh

echo "✅ Backup completed!"
