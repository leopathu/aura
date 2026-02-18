"""
Celery Configuration

TASK-316: Install Celery
TASK-317: Install Redis for message broker
TASK-318: Configure Celery workers
TASK-319: Create task queue initialization
TASK-320: Add task retry logic
TASK-321: Create task monitoring
"""

from celery import Celery
from celery.schedules import crontab
import os

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "aura",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.automation_tasks",
        "app.tasks.workflow_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution (TASK-320: retry logic)
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker settings (TASK-318)
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Monitoring (TASK-321)
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_track_started=True,
    
    # Beat scheduler settings
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="/tmp/celerybeat-schedule",
    
    # Task routes
    task_routes={
        "app.tasks.automation_tasks.*": {"queue": "automations"},
        "app.tasks.workflow_tasks.*": {"queue": "workflows"},
    },
    
    # Default queue
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
)

# Beat schedule (for periodic tasks)
celery_app.conf.beat_schedule = {
    "cleanup-old-runs": {
        "task": "app.tasks.automation_tasks.cleanup_old_runs",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "check-scheduled-automations": {
        "task": "app.tasks.automation_tasks.check_scheduled_automations",
        "schedule": 60.0,  # Every minute
    },
}


# Task base class with retry logic (TASK-320)
class BaseTask(celery_app.Task):
    """Base task with automatic retry logic"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler for task failure (TASK-321: monitoring)"""
        print(f"Task {task_id} failed: {exc}")
        # Can integrate with Sentry, logging, etc.
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handler for task retry (TASK-321: monitoring)"""
        print(f"Task {task_id} retrying: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handler for task success (TASK-321: monitoring)"""
        print(f"Task {task_id} succeeded")
        super().on_success(retval, task_id, args, kwargs)


# Export celery app
__all__ = ["celery_app", "BaseTask"]
