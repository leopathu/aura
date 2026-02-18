#!/bin/bash

# Celery Worker Startup Script
# TASK-318: Configure Celery workers

# Start Celery worker
echo "Starting Celery worker..."
celery -A app.celery_config:celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=default,automations,workflows \
    --hostname=worker@%h

# Worker will run in foreground
# Use Ctrl+C to stop
