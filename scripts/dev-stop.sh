#!/bin/bash
# Development environment shutdown script

set -e

echo "🛑 Stopping Aura development environment..."

# Stop all services
docker compose down

echo "✅ All services stopped!"
echo ""
echo "💡 To remove volumes (database data), run:"
echo "   docker compose down -v"
