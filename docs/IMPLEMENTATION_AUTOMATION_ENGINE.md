# Automation Engine Implementation

**Status**: ✅ COMPLETE  
**Tasks**: TASK-310 to TASK-327 (18 tasks)  
**Date**: February 2026

## Overview

Implemented comprehensive workflow automation engine with Celery task queue, cron scheduling, and flexible workflow execution supporting conditional logic, agent tasks, HTTP requests, and error handling with rollback capabilities.

---

## Architecture

### Components

1. **Automation Models** - PostgreSQL models for storing automation definitions and runs
2. **Celery Task Queue** - Distributed task execution with Redis broker
3. **Workflow Executor** - Flexible workflow parser and step executor with state management
4. **Schedule Service** - Cron parsing and next run calculation
5. **Celery Beat** - Periodic task scheduler

---

## Backend Implementation

### 1. Automation Models (`backend/app/models/automation.py`)

**TASK-310 to TASK-315**: Automation and AutomationRun models

#### Automation Model

```python
class Automation(Base):
    id = UUID (primary key)
    org_id = UUID (ForeignKey to organizations)
    name = String(255)
    description = Text
    status = Enum(ACTIVE, PAUSED, DRAFT, ARCHIVED)
    
    # Workflow definition (TASK-311)
    workflow = JSONB  # { "steps": [...] }
    
    # Trigger configuration (TASK-313)
    trigger_type = Enum(SCHEDULE, WEBHOOK, EVENT, MANUAL)
    schedule = String(255)  # Cron format (TASK-312)
    trigger_config = JSONB
    
    # Agent assignment
    agent_id = UUID (optional)
    
    # Metadata
    created_at, updated_at
    last_run_at, next_run_at
    
    # Statistics
    total_runs, success_runs, failed_runs
```

**Trigger Types**:
- `SCHEDULE` - Cron-based scheduling
- `WEBHOOK` - External webhook triggers
- `EVENT` - Internal events (agent completion, etc.)
- `MANUAL` - User-triggered execution

**Automation Status**:
- `ACTIVE` - Running and accepting triggers
- `PAUSED` - Temporarily disabled
- `DRAFT` - Not yet activated
- `ARCHIVED` - Disabled and hidden

#### AutomationRun Model

```python
class AutomationRun(Base):
    id = UUID (primary key)
    automation_id = UUID (ForeignKey)
    
    # Run status (TASK-315)
    status = Enum(PENDING, RUNNING, SUCCESS, FAILED, CANCELLED, TIMEOUT)
    
    # Trigger information
    trigger_type = String(50)
    trigger_data = JSONB
    
    # Execution timeline
    started_at, completed_at
    
    # Workflow progress
    current_step = Integer
    total_steps = Integer
    
    # State and results
    context = JSONB  # Workflow state
    result = JSONB   # Final result
    error = Text     # Error message if failed
    logs = JSONB     # Execution logs
    
    # Celery task tracking
    task_id = String(255)
```

**Run Statuses**:
- `PENDING` - Queued for execution
- `RUNNING` - Currently executing
- `SUCCESS` - Completed successfully
- `FAILED` - Failed with error
- `CANCELLED` - Manually cancelled
- `TIMEOUT` - Exceeded time limit

**Helper Methods**:
- `add_log(level, message, data)` - Add log entry
- `duration_seconds` - Calculate run duration
- `is_running` - Check if currently running
- `is_complete` - Check if finished

---

### 2. Celery Configuration (`backend/app/celery_config.py`)

**TASK-316 to TASK-321**: Task queue setup

#### Celery App Configuration

```python
celery_app = Celery(
    "aura",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
```

**Configuration** (TASK-318, TASK-320):
```python
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    
    # Retry logic (TASK-320)
    task_acks_late=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Worker settings (TASK-318)
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Monitoring (TASK-321)
    worker_send_task_events=True,
    task_track_started=True,
    
    # Task routes
    task_routes={
        "app.tasks.automation_tasks.*": {"queue": "automations"},
        "app.tasks.workflow_tasks.*": {"queue": "workflows"},
    }
)
```

**Beat Schedule**:
```python
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
```

**Base Task Class** (TASK-320, TASK-321):
```python
class BaseTask(celery_app.Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Monitoring hook
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        # Retry logging
        
    def on_success(self, retval, task_id, args, kwargs):
        # Success tracking
```

---

### 3. Automation Tasks (`backend/app/tasks/automation_tasks.py`)

**TASK-316 to TASK-321**: Celery task implementations

#### Core Tasks

**1. Execute Automation**
```python
@celery_app.task(base=BaseTask, bind=True)
def execute_automation(self, automation_id, trigger_type, trigger_data):
    """
    Execute automation workflow
    
    1. Get automation
    2. Create run record
    3. Execute workflow via WorkflowExecutor
    4. Update run status and statistics
    5. Handle errors with rollback
    """
```

**2. Check Scheduled Automations**
```python
@celery_app.task
def check_scheduled_automations():
    """
    Runs every minute via Celery Beat
    
    1. Find automations where next_run_at <= now
    2. Trigger execution
    3. Calculate and update next_run_at
    """
```

**3. Cleanup Old Runs**
```python
@celery_app.task
def cleanup_old_runs(days_to_keep=30):
    """
    Delete old automation runs (daily at 2 AM)
    
    Removes completed runs older than 30 days
    """
```

**4. Cancel Automation Run**
```python
@celery_app.task(base=BaseTask, bind=True)
def cancel_automation_run(self, run_id):
    """
    Cancel running automation
    
    1. Revoke Celery task
    2. Update run status to CANCELLED
    3. Log cancellation
    """
```

---

### 4. Workflow Executor (`backend/app/services/workflow_executor.py`)

**TASK-322 to TASK-327**: Workflow parsing and execution

#### WorkflowParser (TASK-322)

Parses JSON workflow definitions into executable steps.

**Workflow Format**:
```json
{
  "steps": [
    {
      "type": "agent_task",
      "agent_id": "uuid",
      "prompt": "Analyze {{ variables.data }}",
      "save_to": "analysis_result"
    },
    {
      "type": "condition",
      "condition": "{{ variables.status == 'success' }}",
      "then": [
        { "type": "http_request", "url": "...", "method": "POST" }
      ],
      "else": [
        { "type": "delay", "seconds": 60 }
      ]
    },
    {
      "type": "set_variable",
      "name": "final_status",
      "value": "{{ variables.analysis_result }}"
    }
  ]
}
```

**Supported Step Types**:
- `agent_task` - Execute AI agent with prompt
- `http_request` - Make HTTP API call
- `condition` - Conditional branching (TASK-324)
- `delay` - Wait for specified seconds
- `set_variable` - Set workflow variable

#### WorkflowState (TASK-325)

Manages workflow execution state:
```python
class WorkflowState:
    context = {}       # Trigger data
    variables = {}     # Workflow variables
    step_results = []  # Step execution results
    rollback_stack = [] # Rollback actions
```

**Methods**:
- `set_variable(name, value)` - Store variable
- `get_variable(name, default)` - Retrieve variable
- `add_step_result(index, result)` - Save step result
- `add_rollback_action(action)` - Queue rollback action

#### StepExecutor (TASK-323)

Executes individual workflow steps:

**1. Agent Task Execution**
```python
async def execute_agent_task(step, state):
    """
    Execute AI agent with prompt
    
    1. Get agent from database
    2. Replace variables in prompt ({{ variables.x }})
    3. Execute agent via StreamingAgentOrchestrator
    4. Return response
    """
```

**2. HTTP Request Execution**
```python
async def execute_http_request(step, state):
    """
    Make HTTP API call
    
    Supports: GET, POST, PUT, DELETE, PATCH
    Variable replacement in URL and body
    """
```

**3. Variable Operations**
```python
async def execute_set_variable(step, state):
    """Set workflow variable with value"""
```

**4. Delay Execution**
```python
async def execute_delay(step, state):
    """Sleep for specified seconds"""
```

**Variable Replacement**:
```python
def _replace_variables(text, state):
    """
    Replace {{ variable_name }} in text
    
    Supports:
    - {{ variables.name }}
    - {{ context.field }}
    - {{ variables.nested.path }}
    """
```

#### WorkflowExecutor (TASK-327)

Main execution orchestrator:

**Execution Flow**:
```python
def execute(workflow_definition, trigger_data):
    """
    1. Parse workflow (TASK-322)
    2. Initialize state with trigger data
    3. Execute steps sequentially
    4. Handle errors with rollback (TASK-326)
    5. Return final result
    """
```

**Conditional Logic** (TASK-324):
```python
async def _execute_condition(step):
    """
    Evaluate condition and execute branch
    
    1. Parse condition: {{ variables.x == 'value' }}
    2. Evaluate using restricted eval
    3. Execute 'then' or 'else' steps
    4. Return branch result
    """
```

**Error Handling & Rollback** (TASK-326):
```python
def _rollback():
    """
    Rollback workflow changes
    
    Executes rollback actions in reverse order:
    - Delete created records
    - Restore previous values
    - Revert state changes
    """
```

---

### 5. Schedule Service (`backend/app/services/schedule_service.py`)

Cron schedule parsing and management.

**Functions**:
```python
def calculate_next_run(cron_expression, base_time=None) -> datetime:
    """Calculate next run time from cron"""

def validate_cron_expression(cron_expression) -> bool:
    """Validate cron format"""

def get_cron_description(cron_expression) -> str:
    """Human-readable cron description"""
```

**Common Patterns**:
```python
CRON_PATTERNS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_hour": "0 * * * *",
    "every_day_9am": "0 9 * * *",
    "weekdays_9am": "0 9 * * MON-FRI",
    "first_of_month": "0 0 1 * *",
}
```

---

## Workflow Examples

### Example 1: Daily Summary Email

```json
{
  "steps": [
    {
      "type": "agent_task",
      "agent_id": "uuid-of-summary-agent",
      "prompt": "Generate a daily summary report",
      "save_to": "summary"
    },
    {
      "type": "http_request",
      "method": "POST",
      "url": "https://api.sendgrid.com/v3/mail/send",
      "body": {
        "to": "user@example.com",
        "subject": "Daily Summary",
        "body": "{{ variables.summary }}"
      }
    }
  ]
}
```

**Schedule**: `0 9 * * MON-FRI` (Weekdays at 9 AM)

### Example 2: Conditional Notification

```json
{
  "steps": [
    {
      "type": "http_request",
      "method": "GET",
      "url": "https://api.example.com/status",
      "save_to": "status"
    },
    {
      "type": "condition",
      "condition": "{{ variables.status.status_code == 200 }}",
      "then": [
        {
          "type": "set_variable",
          "name": "message",
          "value": "Service is healthy"
        }
      ],
      "else": [
        {
          "type": "agent_task",
          "agent_id": "uuid",
          "prompt": "Service is down. Create incident report.",
          "save_to": "incident"
        },
        {
          "type": "http_request",
          "method": "POST",
          "url": "https://hooks.slack.com/...",
          "body": {
            "text": "🚨 Service down: {{ variables.incident }}"
          }
        }
      ]
    }
  ]
}
```

### Example 3: Data Pipeline

```json
{
  "steps": [
    {
      "type": "http_request",
      "method": "GET",
      "url": "https://api.example.com/data",
      "save_to": "raw_data"
    },
    {
      "type": "agent_task",
      "agent_id": "data-processor-agent",
      "prompt": "Process this data: {{ variables.raw_data }}",
      "save_to": "processed"
    },
    {
      "type": "http_request",
      "method": "POST",
      "url": "https://api.example.com/results",
      "body": {
        "data": "{{ variables.processed }}"
      }
    },
    {
      "type": "delay",
      "seconds": 5
    },
    {
      "type": "set_variable",
      "name": "pipeline_complete",
      "value": true
    }
  ]
}
```

---

## Docker Services

### Redis Service

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
```

### Celery Worker

```yaml
celery-worker:
  build: ./backend
  command: >
    celery -A app.celery_config:celery_app worker
    --loglevel=info
    --concurrency=4
    --queues=default,automations,workflows
  depends_on:
    - postgres
    - redis
```

### Celery Beat

```yaml
celery-beat:
  build: ./backend
  command: >
    celery -A app.celery_config:celery_app beat
    --loglevel=info
  depends_on:
    - postgres
    - redis
```

**Start automation services**:
```bash
docker-compose --profile automation up
```

---

## Dependencies Added

```txt
# Task Queue
redis==5.0.1
celery==5.3.4
croniter==2.0.1
cron-descriptor==1.4.0
aiohttp==3.9.1
```

---

## Usage Examples

### Creating an Automation

```python
from app.models.automation import Automation, TriggerType, AutomationStatus

automation = Automation(
    org_id=org.id,
    name="Daily Report Generator",
    description="Generates and emails daily reports",
    status=AutomationStatus.ACTIVE,
    trigger_type=TriggerType.SCHEDULE,
    schedule="0 9 * * MON-FRI",  # Weekdays at 9 AM
    workflow={
        "steps": [
            {
                "type": "agent_task",
                "agent_id": str(agent.id),
                "prompt": "Generate daily report",
                "save_to": "report"
            },
            {
                "type": "http_request",
                "method": "POST",
                "url": "https://api.sendgrid.com/v3/mail/send",
                "body": {
                    "to": "user@example.com",
                    "subject": "Daily Report",
                    "body": "{{ variables.report }}"
                }
            }
        ]
    },
    agent_id=agent.id
)

db.add(automation)
db.commit()

# Calculate next run
from app.services.schedule_service import calculate_next_run
automation.next_run_at = calculate_next_run(automation.schedule)
db.commit()
```

### Triggering Manual Execution

```python
from app.tasks.automation_tasks import execute_automation

# Trigger execution
task = execute_automation.delay(
    str(automation.id),
    "manual",
    {"triggered_by": "user@example.com"}
)

# Get task result
result = task.get(timeout=300)  # 5 minutes
print(f"Run ID: {result}")
```

### Monitoring Runs

```python
from app.models.automation import AutomationRun, RunStatus

# Get recent runs
runs = db.query(AutomationRun).filter(
    AutomationRun.automation_id == automation.id
).order_by(AutomationRun.created_at.desc()).limit(10).all()

for run in runs:
    print(f"Run {run.id}: {run.status}")
    print(f"  Started: {run.started_at}")
    print(f"  Duration: {run.duration_seconds}s")
    print(f"  Steps: {run.current_step}/{run.total_steps}")
    
    # View logs
    for log in run.logs:
        print(f"  [{log['level']}] {log['message']}")
```

### Cancelling a Run

```python
from app.tasks.automation_tasks import cancel_automation_run

cancel_automation_run.delay(str(run.id))
```

---

## Monitoring & Debugging

### View Celery Tasks

```bash
# List active tasks
celery -A app.celery_config:celery_app inspect active

# List scheduled tasks
celery -A app.celery_config:celery_app inspect scheduled

# List registered tasks
celery -A app.celery_config:celery_app inspect registered
```

### Monitor Workers

```bash
# Worker stats
celery -A app.celery_config:celery_app inspect stats

# Ping workers
celery -A app.celery_config:celery_app inspect ping
```

### View Logs

```bash
# Worker logs
docker-compose logs -f celery-worker

# Beat logs
docker-compose logs -f celery-beat

# Redis logs
docker-compose logs -f redis
```

---

## Error Handling

### Automatic Retries

Tasks automatically retry up to 3 times with exponential backoff:
```python
class BaseTask(celery_app.Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_jitter = True
```

### Workflow Rollback

On error, workflows execute rollback actions in reverse order:
```python
# During execution, add rollback actions
state.add_rollback_action({
    "type": "delete_record",
    "record_id": created_id
})

# On error, rollback is triggered automatically
executor._rollback()
```

### Failed Run Handling

```python
# Failed runs have error details
if run.status == RunStatus.FAILED:
    print(f"Error: {run.error}")
    
    # View error logs
    error_logs = [log for log in run.logs if log['level'] == 'error']
```

---

## Performance Considerations

### Concurrency

- Workers: 4 concurrent tasks per worker
- Queues: Separate queues for automations and workflows
- Prefetch: 1 task per worker to prevent blocking

### Scaling

```bash
# Scale workers horizontally
docker-compose --profile automation up --scale celery-worker=4

# Increase worker concurrency
celery worker --concurrency=8
```

### Resource Limits

```python
# Task timeout
@celery_app.task(time_limit=300, soft_time_limit=270)
def execute_automation(...):
    pass

# Result expiration
celery_app.conf.result_expires = 3600  # 1 hour
```

---

## Future Enhancements

1. **Parallel Step Execution** - Execute independent steps concurrently
2. **Workflow Templates** - Pre-built automation templates
3. **Visual Workflow Builder** - Drag-and-drop UI for workflow creation
4. **Webhook Triggers** - External webhook endpoint support
5. **Event-based Triggers** - React to internal events
6. **Error Recovery** - Automatic error recovery strategies
7. **Workflow Versioning** - Version control for workflow definitions
8. **A/B Testing** - Test different workflow variations
9. **Performance Analytics** - Execution time analysis and optimization
10. **SLA Monitoring** - Track and alert on SLA violations

---

## Completion Summary

✅ **TASK-310**: Automation model  
✅ **TASK-311**: Workflow definition field (JSON)  
✅ **TASK-312**: Schedule field (cron format)  
✅ **TASK-313**: Trigger configuration  
✅ **TASK-314**: AutomationRun model  
✅ **TASK-315**: Run status tracking  
✅ **TASK-316**: Install Celery  
✅ **TASK-317**: Install Redis  
✅ **TASK-318**: Configure Celery workers  
✅ **TASK-319**: Task queue initialization  
✅ **TASK-320**: Task retry logic  
✅ **TASK-321**: Task monitoring  
✅ **TASK-322**: Workflow parser  
✅ **TASK-323**: Step executor  
✅ **TASK-324**: Conditional logic support  
✅ **TASK-325**: Workflow state management  
✅ **TASK-326**: Error handling and rollback  
✅ **TASK-327**: Workflow completion handler  

**Total Tasks**: 18/18 ✅

---

## Files Created

### Backend
1. `backend/app/models/automation.py` (200+ lines)
2. `backend/app/celery_config.py` (120+ lines)
3. `backend/app/tasks/__init__.py`
4. `backend/app/tasks/automation_tasks.py` (200+ lines)
5. `backend/app/services/workflow_executor.py` (600+ lines)
6. `backend/app/services/schedule_service.py` (100+ lines)

### Scripts
7. `backend/start_worker.sh`
8. `backend/start_beat.sh`

### Modified
9. `backend/requirements.txt` - Added Celery dependencies
10. `docker-compose.yml` - Updated Celery commands
11. `backend/app/models/organization.py` - Added automations relationship
12. `backend/app/models/agent.py` - Added automations relationship

**Total Lines**: ~1,220+ lines of production code

---

This implementation provides a robust, scalable automation engine supporting:
- Scheduled cron jobs
- Flexible workflow definitions with conditional logic
- AI agent integration
- HTTP API calls
- Error handling with automatic retries
- Rollback capabilities
- Distributed task execution via Celery
- Real-time monitoring and logging
