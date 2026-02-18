#!/bin/bash
# View logs for all services or specific service

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "📋 Viewing logs for all services (Ctrl+C to exit)..."
    docker compose logs -f
else
    echo "📋 Viewing logs for $SERVICE (Ctrl+C to exit)..."
    docker compose logs -f "$SERVICE"
fi
