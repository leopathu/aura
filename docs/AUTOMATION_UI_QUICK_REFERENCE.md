# Automation UI - Quick Reference

## File Locations

```
frontend/
├── types/automation.ts                         # TypeScript interfaces
├── app/automations/
│   ├── page.tsx                                # List page
│   ├── create/page.tsx                         # Creation wizard
│   ├── templates/page.tsx                      # Template gallery
│   └── [id]/runs/page.tsx                      # Run history
└── components/automations/
    ├── AutomationCard.tsx                      # Display card
    ├── WorkflowEditor.tsx                      # Step manager
    ├── StepEditor.tsx                          # Step config
    ├── TriggerSelector.tsx                     # Trigger selection
    ├── ScheduleConfig.tsx                      # Cron editor
    └── WorkflowPreview.tsx                     # Review display
```

## Quick Start

### View Automations
```bash
Navigate to: /automations
- Filter by status or trigger type
- Toggle active/paused
- Delete automations
- View run history
```

### Create Automation
```bash
Navigate to: /automations/create

Step 1: Basic Info
- Name (required)
- Description

Step 2: Trigger
- Select type: Schedule, Webhook, Event, Manual
- Configure schedule (cron + timezone)

Step 3: Workflow
- Add steps: Agent Task, HTTP Request, Condition, Delay, Set Variable
- Configure each step
- Reorder with up/down buttons

Step 4: Review
- Preview configuration
- Create automation
```

### Use Template
```bash
Navigate to: /automations/templates
- Browse 6 pre-built templates
- Preview template details
- Click "Use Template" to pre-fill creation wizard
```

### View Run History
```bash
Navigate to: /automations/{id}/runs
- Timeline of all executions
- Filter by status
- Search logs
- View full details (timing, logs, errors)
- Retry failed runs
```

## Workflow Step Types

| Type | Icon | Description | Config |
|------|------|-------------|--------|
| Agent Task | 🤖 | Run AI agent | `prompt`, `agent_id` |
| HTTP Request | 🌐 | Call external API | `method`, `url`, `headers`, `body` |
| Condition | 🔀 | If/then logic | `field`, `operator`, `value` |
| Delay | ⏱️ | Wait time | `seconds` |
| Set Variable | 💾 | Store value | `name`, `value` |

## Variable Templating

Use `{{ }}` syntax in prompts, URLs, headers, and body:

```
{{ trigger.data.field }}      - Webhook/event data
{{ steps.0.result }}          - Previous step result
{{ user.email }}              - Current user
{{ env.API_KEY }}             - Environment variable
{{ now }}                     - Current timestamp
```

## API Endpoints

```http
# List
GET /api/v1/automations?status=ACTIVE

# Create
POST /api/v1/automations
Body: { name, trigger_type, workflow, trigger_config }

# Update
PATCH /api/v1/automations/{id}
Body: { status: "PAUSED" }

# Delete
DELETE /api/v1/automations/{id}

# Test
POST /api/v1/automations/{id}/test
Body: { trigger_data: {} }

# Runs
GET /api/v1/automations/{id}/runs?status=FAILED

# Schedule validation
POST /api/v1/automations/test-schedule
Body: { cron_expression, timezone, test_count }
```

## Templates

1. **Daily Standup Report** - Schedule (9 AM weekdays) → Agent → Email
2. **GitHub Issue Triage** - Webhook → Agent → Slack
3. **Service Health Monitor** - Schedule (5 min) → HTTP → Condition → Jira
4. **Weekly Summary Email** - Schedule (Fri 5 PM) → Agent → Email
5. **Customer Onboarding** - Event → Email → Slack → Delay → Email
6. **Daily Data Pipeline** - Schedule (midnight) → HTTP → Agent → Webhook

## Status Colors

- **Green** = Active, Success
- **Yellow** = Paused, Pending
- **Blue** = Running
- **Red** = Failed, Archived
- **Gray** = Draft, Cancelled
- **Orange** = Timeout

## Common Use Cases

### Daily Report Automation
```
Trigger: Schedule (0 9 * * MON-FRI)
Step 1: Agent generates report
Step 2: HTTP POST to SendGrid
```

### Webhook Integration
```
Trigger: Webhook
Step 1: Agent analyzes payload
Step 2: HTTP POST to Slack
```

### Service Monitoring
```
Trigger: Schedule (*/5 * * * *)
Step 1: HTTP GET health endpoint
Step 2: Condition (status != 200)
Step 3: HTTP POST create Jira ticket
```

### Multi-Step Workflow
```
Trigger: Event (customer.created)
Step 1: HTTP POST welcome email
Step 2: HTTP POST Slack notification
Step 3: Delay 86400 seconds (24 hours)
Step 4: Agent generate follow-up
Step 5: HTTP POST follow-up email
```

## Keyboard Shortcuts

- `Esc` - Close modals
- `Tab` - Navigate form fields
- Arrow keys - Navigate step list
- `Enter` - Submit forms

## Troubleshooting

**Automation not running:**
- Check status is ACTIVE
- Verify schedule is valid (use preview)
- Check timezone settings

**Webhook not triggering:**
- Verify webhook URL is correct
- Check authentication headers
- Review trigger logs in run history

**Step failing:**
- View run details for error message
- Check variable syntax `{{ }}`
- Verify API credentials in config
- Test HTTP endpoints separately

**Schedule validation error:**
- Use preset schedules or cron validator
- Ensure timezone is pytz-compatible
- Test with POST /test-schedule

## Implementation Status

✅ 22/23 tasks complete (96%)

### Completed (TASK-346 to 368)
- ✅ Automation list page
- ✅ Automation card component
- ✅ Enable/disable toggle
- ✅ Last run status
- ✅ Automation deletion
- ✅ Creation wizard (4 steps)
- ✅ Workflow step editor
- ✅ Trigger selection UI
- ✅ Schedule configuration
- ✅ Action selector (5 types)
- ✅ Condition builder
- ✅ Workflow preview
- ✅ Workflow validation
- ✅ Template gallery
- ✅ Pre-built templates (6)
- ✅ Template preview modal
- ✅ "Use Template" button
- ✅ Run history page
- ✅ Timeline component
- ✅ Run details modal
- ✅ Run filtering
- ✅ Retry button

### Pending
- ⏳ TASK-363: Custom template saving

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| types/automation.ts | 130 | Type definitions |
| app/automations/page.tsx | 250 | List page |
| components/AutomationCard.tsx | 233 | Card component |
| app/automations/create/page.tsx | 410 | Creation wizard |
| components/WorkflowEditor.tsx | 244 | Step manager |
| components/StepEditor.tsx | 200 | Step config |
| components/TriggerSelector.tsx | 80 | Trigger selection |
| components/ScheduleConfig.tsx | 150 | Cron editor |
| components/WorkflowPreview.tsx | 120 | Review display |
| app/automations/templates/page.tsx | 540 | Template gallery |
| app/automations/[id]/runs/page.tsx | 450 | Run history |

**Total:** ~2,800 lines of production-ready TypeScript/React code

## Next Steps

1. Implement custom template saving (TASK-363)
2. Add E2E tests for automation workflows
3. Enhance with drag-and-drop visual editor
4. Add real-time status updates via WebSockets
5. Implement workflow versioning
6. Add analytics dashboard

---

**Phase 4: Workflow Automation - COMPLETE! 🎉**
