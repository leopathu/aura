#!/bin/bash

# Celery Beat Startup Script
# For scheduled tasks

echo "Starting Celery Beat scheduler..."
celery -A app.celery_config:celery_app beat \
    --loglevel=info \
    --schedule=/tmp/celerybeat-schedule

# Beat will run in foreground
# Use Ctrl+C to stop
