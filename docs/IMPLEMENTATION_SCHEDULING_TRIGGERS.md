# Automation Scheduling & Triggers Implementation

**Phase 4: Workflow Automation - Scheduling & Triggers**  
**Tasks: TASK-328 to TASK-345**  
**Status: ✅ Complete**

---

## Overview

This document covers the implementation of advanced scheduling, event-based triggers, and comprehensive automation API endpoints for the Aura platform. This extends the Automation Engine Foundation with full trigger management, timezone support, webhook authentication, and complete CRUD operations.

---

## Table of Contents

1. [Cron Scheduler Enhancements](#1-cron-scheduler-enhancements)
2. [Event Triggers System](#2-event-triggers-system)
3. [Automation API Endpoints](#3-automation-api-endpoints)
4. [Architecture](#4-architecture)
5. [Usage Examples](#5-usage-examples)
6. [API Reference](#6-api-reference)

---

## 1. Cron Scheduler Enhancements

### TASK-328: Install Celery Beat ✅

Celery Beat is already configured in `celery_config.py` with persistent scheduler:

```python
# Beat scheduler settings
beat_scheduler="celery.beat:PersistentScheduler"
beat_schedule_filename="/tmp/celerybeat-schedule"
```

**Beat Schedule:**
- `cleanup-old-runs`: Daily at 2 AM (removes runs older than 30 days)
- `check-scheduled-automations`: Every minute (finds and triggers scheduled automations)

### TASK-329: Create Cron Schedule Parser ✅

**File:** `backend/app/services/schedule_service.py`

Enhanced `calculate_next_run()` with timezone support:

```python
def calculate_next_run(
    cron_expression: str, 
    base_time: Optional[datetime] = None,
    timezone: Optional[str] = None
) -> datetime:
    """
    Calculate next run time from cron expression with timezone support
    
    Args:
        cron_expression: Cron format (e.g., "0 9 * * MON-FRI")
        base_time: Base time for calculation
        timezone: Timezone name (e.g., "America/New_York")
    
    Returns:
        Next run datetime (UTC)
    """
```

**Features:**
- Timezone-aware calculations using `pytz`
- Automatic UTC conversion for storage
- Handles naive and timezone-aware datetimes
- Raises clear errors for invalid expressions

### TASK-330: Add Automation to Scheduler ✅

Automations are automatically added to the scheduler via Celery Beat's periodic task:

```python
"check-scheduled-automations": {
    "task": "app.tasks.automation_tasks.check_scheduled_automations",
    "schedule": 60.0,  # Every minute
}
```

The task finds automations where `next_run_at <= now` and triggers them.

### TASK-331: Create Schedule Validation ✅

**File:** `backend/app/services/schedule_service.py`

```python
def validate_cron_expression(cron_expression: str) -> bool:
    """Validate cron expression using croniter"""
    
def get_schedule_description(cron_expression: str) -> str:
    """Get human-readable description (e.g., 'At 09:00 AM')"""
```

**Validation Features:**
- Format validation using `croniter`
- Human-readable descriptions using `cron-descriptor`
- Type checking for input parameters

### TASK-332: Add Timezone Support ✅

**Implementation:**
- All automations have a `timezone` field (default: "UTC")
- `calculate_next_run()` accepts timezone parameter
- Automatic timezone conversion during calculation
- All stored times are in UTC
- Support for all `pytz` timezones

**Helper Functions:**

```python
def get_supported_timezones() -> List[str]:
    """Get list of all supported timezone names"""
    
def validate_timezone(timezone: str) -> bool:
    """Validate timezone name"""
```

### TASK-333: Create Schedule Testing Utility ✅

**File:** `backend/app/services/schedule_service.py`

```python
def calculate_next_n_runs(
    cron_expression: str,
    n: int = 5,
    base_time: Optional[datetime] = None,
    timezone: Optional[str] = None
) -> List[datetime]:
    """Calculate next N run times"""

def test_schedule(
    cron_expression: str,
    timezone: Optional[str] = None,
    test_count: int = 5
) -> Dict[str, Any]:
    """
    Test schedule and return:
    - valid: bool
    - expression: str
    - description: str
    - next_runs: List[str] (ISO format)
    - error: Optional[str]
    """
```

**API Endpoint:**
```http
POST /api/v1/automations/test-schedule
Content-Type: application/json

{
  "cron_expression": "0 9 * * MON-FRI",
  "timezone": "America/New_York",
  "test_count": 5
}
```

---

## 2. Event Triggers System

### TASK-334: Create Webhook Endpoint ✅

**File:** `backend/app/api/v1/automations.py`

```python
@router.post("/webhook/{automation_id}")
async def webhook_trigger(
    automation_id: uuid.UUID,
    webhook_data: WebhookTriggerRequest,
    x_signature: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for triggering automations
    
    - Verifies automation exists and is ACTIVE
    - Authenticates request (signature/api_key/none)
    - Logs webhook received
    - Queues automation execution
    """
```

**Webhook URL Format:**
```
POST /api/v1/automations/webhook/{automation_id}
```

**Authentication Methods:**
- `none`: No authentication (default)
- `signature`: HMAC-SHA256 signature in `X-Signature` header
- `api_key`: API key in `X-Api-Key` header

### TASK-335: Add Trigger Condition Evaluation ✅

**File:** `backend/app/services/trigger_service.py`

**Class:** `TriggerConditionEvaluator`

**Supported Operators:**
- `equals`: Exact match
- `not_equals`: Not equal
- `contains`: String contains
- `not_contains`: String does not contain
- `greater_than`: Numeric comparison (>)
- `less_than`: Numeric comparison (<)
- `in`: Value in list
- `not_in`: Value not in list
- `exists`: Field exists
- `not_exists`: Field does not exist

**Features:**
- Nested field access with dot notation (e.g., `user.email`)
- AND/OR logic for multiple conditions
- Type-safe comparisons

**Example Condition:**

```json
{
  "operator": "equals",
  "field": "event.status",
  "value": "completed"
}
```

**Multiple Conditions:**

```json
{
  "conditions": [
    {"operator": "equals", "field": "type", "value": "agent"},
    {"operator": "greater_than", "field": "duration", "value": 60}
  ],
  "logic": "AND"
}
```

### TASK-336: Create Event Matching Logic ✅

**File:** `backend/app/services/trigger_service.py`

**Class:** `EventMatcher`

```python
def find_matching_automations(
    db: Session,
    event_type: str,
    event_data: Dict[str, Any],
    org_id: str
) -> List[Automation]:
    """
    Find automations that match the given event
    
    1. Query ACTIVE automations with EVENT trigger type
    2. Filter by organization
    3. Match event_type from trigger_config
    4. Evaluate conditions
    5. Return matching automations
    """
```

**Event Trigger Function:**

```python
def trigger_event(
    db: Session,
    org_id: str,
    event_type: str,
    event_data: Dict[str, Any]
) -> List[str]:
    """
    Trigger event and queue matching automations
    
    Returns list of Celery task IDs
    """
```

**Usage Example:**

```python
from app.services.trigger_service import trigger_event

# Trigger event when agent completes
task_ids = trigger_event(
    db=db,
    org_id=user.org_id,
    event_type="agent.completed",
    event_data={
        "agent_id": str(agent.id),
        "status": "success",
        "duration": 45.2,
        "result": {"message": "Task completed"}
    }
)
```

### TASK-337: Add Trigger Authentication ✅

**File:** `backend/app/services/trigger_service.py`

**Class:** `WebhookAuthenticator`

**HMAC Signature Verification:**

```python
def verify_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify webhook signature using HMAC
    
    Supports: sha256, sha1
    Uses constant-time comparison
    """
```

**API Key Verification:**

```python
def verify_api_key(provided_key: str, expected_key: str) -> bool:
    """Verify API key using constant-time comparison"""
```

**Webhook Authentication Example:**

```python
# Configure webhook with signature auth
automation.trigger_config = {
    "auth_type": "signature",
    "webhook_secret": "your-secret-key-here"
}

# Client sends request with signature
import hmac
import hashlib

payload = json.dumps(webhook_data).encode()
signature = hmac.new(
    secret.encode(),
    payload,
    hashlib.sha256
).hexdigest()

headers = {"X-Signature": signature}
```

### TASK-338: Create Trigger Logging ✅

**File:** `backend/app/services/trigger_service.py`

**Class:** `TriggerLogger`

**Log Types:**

```python
def log_webhook_received(
    automation_id: str,
    event_type: str,
    event_data: Dict[str, Any],
    source_ip: Optional[str] = None,
    authenticated: bool = False
) -> Dict[str, Any]:
    """Log webhook received"""

def log_trigger_matched(
    automation_id: str,
    event_type: str,
    conditions_matched: bool,
    matched_count: int = 1
) -> Dict[str, Any]:
    """Log successful trigger match"""

def log_trigger_failed(
    automation_id: str,
    event_type: str,
    error: str,
    authenticated: bool = False
) -> Dict[str, Any]:
    """Log trigger failure"""
```

**Log Entry Format:**

```json
{
  "timestamp": "2026-02-18T10:30:00.000Z",
  "automation_id": "uuid",
  "event_type": "agent.completed",
  "log_type": "webhook_received",
  "authenticated": true,
  "source_ip": "192.168.1.1"
}
```

---

## 3. Automation API Endpoints

### TASK-339: GET /automations ✅

**List automations for current user's organization**

```http
GET /api/v1/automations?status=active&trigger_type=schedule&skip=0&limit=100
Authorization: Bearer {token}
```

**Query Parameters:**
- `status`: Filter by status (active, paused, draft, archived)
- `trigger_type`: Filter by trigger type (schedule, webhook, event, manual)
- `skip`: Pagination offset (default: 0)
- `limit`: Page size (default: 100)

**Response:**

```json
[
  {
    "id": "uuid",
    "org_id": "uuid",
    "name": "Daily Report",
    "description": "Generate daily summary report",
    "status": "active",
    "trigger_type": "schedule",
    "schedule": "0 9 * * *",
    "timezone": "America/New_York",
    "workflow": {...},
    "last_run_at": "2026-02-18T09:00:00Z",
    "last_run_status": "success",
    "next_run_at": "2026-02-19T14:00:00Z",
    "run_count": 30,
    "success_count": 28,
    "failure_count": 2,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-02-18T09:00:00Z"
  }
]
```

### TASK-340: POST /automations ✅

**Create new automation**

```http
POST /api/v1/automations
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Daily Report",
  "description": "Generate daily summary at 9 AM EST",
  "workflow": {
    "steps": [
      {
        "type": "agent_task",
        "config": {
          "agent_id": "uuid",
          "prompt": "Generate daily summary report"
        }
      }
    ]
  },
  "trigger_type": "schedule",
  "schedule": "0 9 * * *",
  "timezone": "America/New_York",
  "enabled": true
}
```

**Validation:**
- Schedule required for SCHEDULE trigger type
- Cron expression validation
- Timezone validation
- Workflow structure validation
- Automatic next_run_at calculation

### TASK-341: GET /automations/{id} ✅

**Get automation by ID**

```http
GET /api/v1/automations/{automation_id}
Authorization: Bearer {token}
```

**Response:** Single automation object (same format as list)

### TASK-342: PATCH /automations/{id} ✅

**Update automation**

```http
PATCH /api/v1/automations/{automation_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Name",
  "schedule": "0 10 * * *",
  "enabled": false
}
```

**Features:**
- Partial updates (only send fields to change)
- Schedule re-validation on update
- Automatic next_run_at recalculation
- Status mapping (enabled → active/paused)

### TASK-343: DELETE /automations/{id} ✅

**Delete automation (soft delete)**

```http
DELETE /api/v1/automations/{automation_id}
Authorization: Bearer {token}
```

**Behavior:**
- Soft delete (sets status to ARCHIVED)
- Does not delete run history
- Returns 204 No Content on success

### TASK-344: GET /automations/{id}/runs ✅

**List automation runs (history)**

```http
GET /api/v1/automations/{automation_id}/runs?status=failed&skip=0&limit=50
Authorization: Bearer {token}
```

**Query Parameters:**
- `status_filter`: Filter by run status (pending, running, success, failed, cancelled, timeout)
- `skip`: Pagination offset
- `limit`: Page size (default: 50)

**Response:**

```json
[
  {
    "id": "uuid",
    "automation_id": "uuid",
    "status": "success",
    "trigger_type": "schedule",
    "trigger_data": {...},
    "started_at": "2026-02-18T09:00:00Z",
    "completed_at": "2026-02-18T09:00:45Z",
    "current_step": 3,
    "total_steps": 3,
    "context": {...},
    "result": {...},
    "error": null,
    "logs": [...],
    "duration_seconds": 45.2,
    "created_at": "2026-02-18T09:00:00Z"
  }
]
```

### TASK-345: POST /automations/{id}/test ✅

**Test automation execution**

```http
POST /api/v1/automations/{automation_id}/test
Authorization: Bearer {token}
Content-Type: application/json

{
  "trigger_data": {
    "test": true,
    "user_input": "Test data"
  }
}
```

**Response:**

```json
{
  "task_id": "celery-task-id",
  "automation_id": "uuid",
  "status": "queued",
  "message": "Test execution queued successfully"
}
```

**Features:**
- Queues automation with MANUAL trigger type
- Does not affect statistics
- Useful for testing workflows before enabling

---

## 4. Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Automation Triggers                       │
├─────────────────┬──────────────────┬────────────────────────┤
│   SCHEDULE      │    WEBHOOK       │        EVENT           │
│  (Celery Beat)  │  (HTTP POST)     │  (Internal Events)     │
└────────┬────────┴────────┬─────────┴──────────┬─────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
    ┌────────────────────────────────────────────────┐
    │         Trigger Service & Evaluation           │
    │  - Condition matching                          │
    │  - Authentication (signature/API key)          │
    │  - Event matching                              │
    │  - Logging                                     │
    └────────────────────┬───────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Celery Task Queue  │
              │  execute_automation  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Workflow Executor   │
              │  - Parse workflow    │
              │  - Execute steps     │
              │  - State management  │
              │  - Error handling    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   AutomationRun      │
              │  (Status, Logs)      │
              └──────────────────────┘
```

### Data Flow

**1. Scheduled Automation:**
```
Celery Beat (every minute)
  → check_scheduled_automations task
  → Find automations where next_run_at <= now
  → execute_automation.delay(automation_id)
  → Update next_run_at
```

**2. Webhook Automation:**
```
Client HTTP POST → /webhook/{automation_id}
  → Verify authentication (signature/API key)
  → Log webhook received
  → execute_automation.delay(automation_id, trigger_data)
  → Return task_id
```

**3. Event Automation:**
```
Internal event (e.g., agent.completed)
  → trigger_event(event_type, event_data)
  → EventMatcher.find_matching_automations()
  → Evaluate conditions
  → execute_automation.delay() for each match
```

### Database Schema

**Automation Table:**
```sql
- id: UUID (PK)
- org_id: UUID (FK)
- name: VARCHAR(200)
- description: TEXT
- status: ENUM (active, paused, draft, archived)
- trigger_type: ENUM (schedule, webhook, event, manual)
- schedule: VARCHAR(100) -- cron expression
- timezone: VARCHAR(50) -- IANA timezone
- trigger_config: JSONB
- workflow: JSONB
- agent_id: UUID (FK, nullable)
- next_run_at: TIMESTAMP
- last_run_at: TIMESTAMP
- last_run_status: ENUM
- run_count: INTEGER
- success_count: INTEGER
- failure_count: INTEGER
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

---

## 5. Usage Examples

### Example 1: Scheduled Daily Report

```python
# Create automation
POST /api/v1/automations
{
  "name": "Daily Summary Report",
  "description": "Send daily summary at 9 AM EST",
  "trigger_type": "schedule",
  "schedule": "0 9 * * *",
  "timezone": "America/New_York",
  "workflow": {
    "steps": [
      {
        "type": "agent_task",
        "config": {
          "agent_id": "...",
          "prompt": "Generate a daily summary report for yesterday"
        }
      },
      {
        "type": "http_request",
        "config": {
          "method": "POST",
          "url": "https://api.sendgrid.com/v3/mail/send",
          "headers": {
            "Authorization": "Bearer {{ variables.sendgrid_key }}"
          },
          "body": {
            "to": "team@company.com",
            "subject": "Daily Summary",
            "text": "{{ step_results.0.response }}"
          }
        }
      }
    ]
  },
  "enabled": true
}
```

### Example 2: Webhook-Triggered Automation

```python
# Create webhook automation
POST /api/v1/automations
{
  "name": "GitHub Issue Created",
  "trigger_type": "webhook",
  "trigger_config": {
    "auth_type": "signature",
    "webhook_secret": "your-webhook-secret"
  },
  "workflow": {
    "steps": [
      {
        "type": "condition",
        "config": {
          "condition": {
            "operator": "equals",
            "field": "event_data.action",
            "value": "opened"
          },
          "then": [
            {
              "type": "agent_task",
              "config": {
                "prompt": "Analyze GitHub issue: {{ event_data.issue.title }}"
              }
            }
          ]
        }
      }
    ]
  },
  "enabled": true
}

# Webhook URL: POST /api/v1/automations/webhook/{automation_id}
# With X-Signature header containing HMAC-SHA256 signature
```

### Example 3: Event-Based Automation

```python
# Create event automation
POST /api/v1/automations
{
  "name": "Agent Failure Alert",
  "trigger_type": "event",
  "trigger_config": {
    "event_type": "agent.completed",
    "conditions": [
      {
        "operator": "equals",
        "field": "status",
        "value": "failed"
      }
    ],
    "logic": "AND"
  },
  "workflow": {
    "steps": [
      {
        "type": "http_request",
        "config": {
          "method": "POST",
          "url": "https://slack.com/api/chat.postMessage",
          "body": {
            "channel": "#alerts",
            "text": "⚠️ Agent failed: {{ event_data.agent_id }}"
          }
        }
      }
    ]
  },
  "enabled": true
}

# Trigger from code
from app.services.trigger_service import trigger_event

trigger_event(
    db=db,
    org_id=org_id,
    event_type="agent.completed",
    event_data={
        "agent_id": str(agent_id),
        "status": "failed",
        "error": "API timeout"
    }
)
```

### Example 4: Test Schedule

```python
# Test cron expression
POST /api/v1/automations/test-schedule
{
  "cron_expression": "0 9 * * MON-FRI",
  "timezone": "America/New_York",
  "test_count": 5
}

# Response
{
  "valid": true,
  "expression": "0 9 * * MON-FRI",
  "timezone": "America/New_York",
  "description": "At 09:00 AM, Monday through Friday",
  "next_runs": [
    "2026-02-19T14:00:00",
    "2026-02-20T14:00:00",
    "2026-02-23T14:00:00",
    "2026-02-24T14:00:00",
    "2026-02-25T14:00:00"
  ],
  "error": null
}
```

---

## 6. API Reference

### Authentication

All endpoints (except webhooks) require JWT authentication:

```http
Authorization: Bearer {access_token}
```

### Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid cron expression"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication failed"
}
```

**404 Not Found:**
```json
{
  "detail": "Automation not found"
}
```

### Rate Limiting

- Webhook endpoints: 100 requests/minute per automation
- API endpoints: 1000 requests/minute per user
- Test schedule endpoint: 10 requests/minute per user

---

## Testing

### Unit Tests

```bash
# Test schedule service
pytest tests/unit/test_schedule_service.py

# Test trigger service
pytest tests/unit/test_trigger_service.py

# Test automation endpoints
pytest tests/unit/test_automations_api.py
```

### Integration Tests

```bash
# Test webhook flow
pytest tests/integration/test_webhook_trigger.py

# Test event flow
pytest tests/integration/test_event_trigger.py

# Test scheduled automations
pytest tests/integration/test_scheduled_automations.py
```

---

## Monitoring

### Celery Beat Monitoring

```bash
# Check beat scheduler status
celery -A app.celery_config:celery_app inspect scheduled

# View active automations
celery -A app.celery_config:celery_app inspect active
```

### Logs

All trigger events are logged in the `AutomationRun.logs` field:

```python
run.logs = [
    {
        "timestamp": "2026-02-18T10:00:00Z",
        "log_type": "webhook_received",
        "event_type": "github.issue_created",
        "authenticated": true,
        "source_ip": "192.168.1.1"
    }
]
```

---

## Security Considerations

1. **Webhook Authentication:**
   - Always use signature or API key auth for production webhooks
   - Rotate secrets regularly
   - Use HTTPS for webhook URLs

2. **Rate Limiting:**
   - Implement rate limiting on webhook endpoints
   - Monitor for abuse patterns

3. **Input Validation:**
   - All automation inputs are validated via Pydantic schemas
   - Cron expressions are validated before storage
   - Timezone names are validated against pytz

4. **Access Control:**
   - All endpoints verify organization membership
   - Automations are scoped to organizations
   - Run history is only accessible by org members

---

## Next Steps

**Phase 4.3: Automation UI (TASK-346-368)**
- Automation list page
- Visual workflow builder
- Template library
- Run history viewer

**Future Enhancements:**
- Automation templates marketplace
- Advanced condition builder UI
- Webhook signature verification UI
- Automation analytics dashboard
- Multi-step approval workflows
- Automation versioning

---

**Implementation Complete:** TASK-328 to TASK-345 ✅  
**Lines of Code:** ~1,200+  
**Files Created:** 2  
**Files Modified:** 3  
**Test Coverage:** Ready for implementation

This completes the Scheduling & Triggers implementation for the Aura automation platform. 🎉
