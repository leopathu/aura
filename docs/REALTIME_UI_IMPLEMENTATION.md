# Real-time UI Updates Implementation

## Overview
This document describes the implementation of real-time UI components for displaying agent execution details including thought traces, tool calls, progress indicators, and approval prompts (TASK-274 to TASK-293).

## Architecture

### Frontend Components

#### 1. Thought Trace Component (`frontend/components/chat/ThoughtTrace.tsx`)
**Purpose**: Display agent reasoning process step-by-step with animations and visual indicators.

**Features (TASK-274 to TASK-278)**:
- **Step-by-step indicators**: Each thought step shows with numbered indicators
- **Thinking animations**: Rotating spinner for in-progress steps, checkmark for completed
- **Collapsible sections**: Expand/collapse to show/hide thought details
- **Status-based styling**: 
  - `completed`: Green background with checkmark
  - `in_progress`: Purple background with spinner animation
  - `pending`: Gray background with clock icon
- **Timeline view**: Visual connection between steps with border line
- **Metadata expansion**: Collapsible details for additional step metadata

**Key Components**:
```typescript
// Main component
<ThoughtTrace 
  steps={thoughtSteps} 
  isExpanded={false} 
  showAnimation={true}
/>

// Compact inline version
<CompactThoughtTrace steps={thoughtSteps} />
```

**Props**:
- `steps`: Array of ThoughtStep objects
- `isExpanded`: Initial expanded state (default: false)
- `showAnimation`: Enable/disable animations (default: true)

**ThoughtStep Interface**:
```typescript
interface ThoughtStep {
  step: number
  node: string  // analyze, plan, execute, synthesize, reflect
  content: string
  status: 'in_progress' | 'completed' | 'pending'
  metadata?: Record<string, any>
  timestamp: string
}
```

#### 2. Tool Call Card Component (`frontend/components/chat/ToolCallCard.tsx`)
**Purpose**: Display tool execution information with detailed parameters and results.

**Features (TASK-279 to TASK-283)**:
- **Tool card display**: Cards with tool icons and names
- **Parameter display**: JSON-formatted parameters with syntax highlighting
- **Execution status**: Visual badges (initiating, running, completed, failed)
- **Result display**: Formatted results with JSON or text display
- **Error handling**: Error messages with red styling and error icon
- **Duration tracking**: Execution time in milliseconds
- **Expandable details**: Click to expand/collapse parameters and results

**Key Components**:
```typescript
// Single tool call
<ToolCallCard 
  toolCall={toolCall} 
  showDetails={true}
/>

// Multiple tool calls
<ToolCallList toolCalls={toolCalls} />
```

**ToolCall Interface**:
```typescript
interface ToolCall {
  tool_id: string
  tool_name: string
  arguments: Record<string, any>
  status: 'initiating' | 'running' | 'completed' | 'failed'
  result?: any
  error?: string
  duration_ms?: number
  timestamp: string
}
```

**Tool Icons**: Custom icons for Gmail, Calendar, Jira, Slack, and generic tools.

**Status Colors**:
- `initiating`: Blue (⏳)
- `running`: Yellow (⚡) with pulsing animation
- `completed`: Green (✓)
- `failed`: Red (✗)

#### 3. Progress Indicators (`frontend/components/chat/ProgressIndicators.tsx`)
**Purpose**: Collection of loading and progress visualization components.

**Components (TASK-284 to TASK-288)**:

**a) LoadingSpinner**:
```typescript
<LoadingSpinner size="md" color="purple" />
```
- Sizes: sm, md, lg, xl
- Colors: purple, blue, green, gray
- Rotating border animation

**b) ProgressBar**:
```typescript
<ProgressBar 
  progress={75} 
  showPercentage={true}
  color="gradient"
  height="md"
  animated={true}
/>
```
- Progress from 0-100
- Optional percentage display
- Colors: purple, blue, green, gradient
- Heights: sm (h-1), md (h-2), lg (h-3)
- Smooth animation

**c) PulseAnimation**:
```typescript
<PulseAnimation color="purple" size="md" />
```
- Three dots pulsing in sequence
- Used for "thinking" indicators
- Sizes: sm, md, lg
- Colors: purple, blue, green

**d) StepCounter**:
```typescript
<StepCounter 
  currentStep={3} 
  totalSteps={5}
  showLabels={true}
  size="md"
/>
```
- Visual step progression
- Checkmarks for completed steps
- Highlighted current step with ring
- Gray for pending steps

**e) LinearStepCounter**:
```typescript
<LinearStepCounter 
  currentStep={2}
  totalSteps={4}
  stepLabels={['Analyze', 'Plan', 'Execute', 'Synthesize']}
/>
```
- Vertical list of steps
- Labels for each step
- Pulse animation on current step

**f) EstimatedTime**:
```typescript
<EstimatedTime 
  startTime={new Date()}
  estimatedDurationMs={10000}
  showElapsed={true}
  showRemaining={true}
/>
```
- Elapsed time counter (updates every 100ms)
- Remaining time estimate
- Progress bar visualization
- Formatted time display (Xh Ym Zs)

**g) AgentActivityIndicator** (Composite):
```typescript
<AgentActivityIndicator 
  status="analyzing"
  currentStep={2}
  totalSteps={5}
  startTime={new Date()}
  estimatedDuration={15000}
/>
```
- Combines multiple indicators
- Status-based colors and labels
- Step counter integration
- Time tracking

**h) TypingIndicator**:
```typescript
<TypingIndicator />
```
- Simple "AI is typing..." indicator
- Pulse animation
- Minimal UI

#### 4. Approval Modal Component (`frontend/components/chat/ApprovalModal.tsx`)
**Purpose**: Modal dialog for user approval of sensitive agent actions.

**Features (TASK-289 to TASK-293)**:
- **Approval modal**: Full-screen overlay with backdrop blur
- **Action preview**: Detailed display of action type, name, description, parameters
- **Approve/reject buttons**: Clear action buttons with icons
- **Timeout handling**: Countdown timer with visual progress bar
- **Risk level indicator**: Badges for low/medium/high risk
- **User notes**: Optional textarea for approval notes
- **Auto-reject on timeout**: Automatically rejects if time expires

**Key Components**:
```typescript
// Full modal
<ApprovalModal 
  request={approvalRequest}
  onApprove={(response) => handleApprove(response)}
  onReject={(response) => handleReject(response)}
  onTimeout={() => handleTimeout()}
/>

// Compact notification
<ApprovalNotification 
  request={approvalRequest}
  onApprove={() => approve()}
  onReject={() => reject()}
  onViewDetails={() => showModal()}
/>
```

**ApprovalRequest Interface**:
```typescript
interface ApprovalRequest {
  id: string
  action_type: string
  action_name: string
  description: string
  parameters: Record<string, any>
  risk_level: 'low' | 'medium' | 'high'
  estimated_duration_ms?: number
  timeout_ms: number
  timestamp: string
}
```

**ApprovalResponse Interface**:
```typescript
interface ApprovalResponse {
  approval_id: string
  approved: boolean
  user_note?: string
}
```

**Risk Levels**:
- **Low**: Green badge, minimal warning
- **Medium**: Yellow badge, cautionary message
- **High**: Red badge, strong warning with detailed caution

**Countdown Timer**:
- Updates every 100ms
- Color changes: Green → Yellow (≤10s) → Red (≤5s)
- Progress bar visualization
- Auto-timeout calls onTimeout callback

### Backend Components

#### 1. Approvals API (`backend/app/api/v1/approvals.py`)
**Purpose**: Backend API for managing approval requests and responses.

**Features (TASK-292 to TASK-293)**:
- **Approval request creation**: Generate unique approval IDs
- **Response handling**: Process approve/reject decisions
- **Status tracking**: Check approval status with timeout detection
- **Async waiting**: Wait for approval response in agent execution
- **Cleanup**: Remove old approval records

**API Endpoints**:

**POST /api/v1/approvals/respond**:
```json
{
  "approval_id": "uuid",
  "approved": true,
  "user_note": "Optional note"
}
```
Response: `ApprovalStatus`

**GET /api/v1/approvals/{approval_id}/status**:
Response: `ApprovalStatus` with timeout check

**POST /api/v1/approvals/cleanup**:
Query param: `max_age_hours` (default: 1)

**Key Classes**:

**ApprovalManager**:
- `create_approval_request()`: Create new approval
- `submit_approval_response()`: Handle user response
- `check_approval_status()`: Get status with timeout check
- `wait_for_approval()`: Async wait for response
- `cleanup_old_approvals()`: Remove stale records

**Helper Functions**:
```python
# Request approval in agent code
request, approved = await request_user_approval(
    action_type="gmail_send",
    action_name="Send Email",
    description="Send email to john@example.com",
    parameters={"to": "john@example.com", "subject": "Hello"},
    risk_level="medium",
    timeout_ms=30000
)

if not approved:
    return {"error": "User rejected action"}
```

```python
# Determine risk level
risk = determine_risk_level("gmail_send", arguments)
# Returns: "low", "medium", or "high"
```

**Risk Level Determination**:
- **High**: Delete operations, sending emails, destructive actions
- **Medium**: Create/update operations, messaging
- **Low**: Read-only operations, search queries

**Storage**: In-memory dictionary (for MVP). Production should use Redis or database.

## Integration with Existing Components

### Updated AssistantMessage Component
The `AssistantMessage` component now uses the new components:

```typescript
<AssistantMessage 
  content="Response text"
  timestamp="2024-01-01T12:00:00Z"
  metadata={{
    thought_trace: [...],
    tool_calls: [...],
    streaming: true
  }}
/>
```

**Changes**:
- Imports `ThoughtTrace` and `ToolCallList`
- Removed inline thought/tool display
- Uses dedicated components for cleaner UI
- Increased max-width to accommodate wider content

### Updated Chat Page
The chat page handles streaming with the new components:

```typescript
// Streaming state
const [currentThoughts, setCurrentThoughts] = useState<ThoughtEvent[]>([])
const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([])
const [streamingContent, setStreamingContent] = useState('')

// Update on SSE events
onThought: (data) => setCurrentThoughts([...currentThoughts, data])
onToolCall: (data) => setCurrentToolCalls([...currentToolCalls, data])
```

## UI/UX Design Patterns

### Color Scheme
- **Purple**: Primary color for agent/AI elements
- **Blue**: Secondary color for tools and actions
- **Green**: Success, completed states
- **Yellow**: Warning, in-progress states
- **Red**: Errors, high-risk actions
- **Gray**: Neutral, pending states

### Animation Principles
- **Smooth transitions**: 200-300ms for state changes
- **Meaningful motion**: Animations indicate state (rotating = loading, pulse = thinking)
- **Performance**: CSS transforms for smooth 60fps
- **Framer Motion**: Used for complex animations and layout changes

### Accessibility
- **Clear labels**: All buttons have descriptive text
- **Icon + text**: Icons paired with text labels
- **Color + shape**: Don't rely solely on color for state
- **Keyboard navigation**: All interactive elements focusable
- **Screen readers**: Semantic HTML and ARIA labels

### Responsive Design
- **Flexible layouts**: Components adapt to container width
- **Mobile-friendly**: Touch-friendly tap targets (min 44x44px)
- **Readable text**: Minimum 12px font size
- **Spacing**: Adequate whitespace for readability

## Performance Considerations

### Component Optimization
- **Lazy rendering**: Collapse details by default
- **Memoization**: React.memo for expensive components
- **Virtual scrolling**: For long lists (future enhancement)
- **Debounced updates**: Throttle rapid state changes

### Animation Performance
- **CSS transforms**: Use translate3d for GPU acceleration
- **will-change**: Hint browser for upcoming animations
- **Reduced motion**: Respect user preferences
- **Conditional rendering**: Don't animate off-screen elements

### Data Management
- **Efficient state**: Only store necessary data
- **Cleanup**: Remove old approval records
- **Pagination**: Limit displayed items (future)

## Usage Examples

### Basic Thought Trace
```tsx
const thoughts = [
  {
    step: 1,
    node: 'analyze',
    content: 'Analyzing user request...',
    status: 'completed',
    timestamp: new Date().toISOString()
  },
  {
    step: 2,
    node: 'plan',
    content: 'Planning approach...',
    status: 'in_progress',
    timestamp: new Date().toISOString()
  }
]

<ThoughtTrace steps={thoughts} />
```

### Tool Call Display
```tsx
const toolCalls = [
  {
    tool_id: 'uuid-1',
    tool_name: 'gmail_search',
    arguments: { query: 'from:john@example.com' },
    status: 'completed',
    result: '5 emails found',
    duration_ms: 1234,
    timestamp: new Date().toISOString()
  }
]

<ToolCallList toolCalls={toolCalls} />
```

### Progress Tracking
```tsx
<AgentActivityIndicator 
  status="executing"
  currentStep={3}
  totalSteps={5}
  startTime={executionStart}
  estimatedDuration={15000}
/>
```

### Approval Request
```tsx
const approvalRequest = {
  id: 'approval-uuid',
  action_type: 'gmail_send',
  action_name: 'Send Email',
  description: 'Send email to john@example.com with subject "Hello"',
  parameters: { to: 'john@example.com', subject: 'Hello', body: 'Hi there!' },
  risk_level: 'medium',
  timeout_ms: 30000,
  timestamp: new Date().toISOString()
}

<ApprovalModal 
  request={approvalRequest}
  onApprove={async (response) => {
    await fetch('/api/v1/approvals/respond', {
      method: 'POST',
      body: JSON.stringify(response)
    })
  }}
  onReject={async (response) => {
    await fetch('/api/v1/approvals/respond', {
      method: 'POST',
      body: JSON.stringify(response)
    })
  }}
  onTimeout={() => {
    console.log('Approval timed out')
  }}
/>
```

## Testing

### Component Testing
```bash
# Test thought trace rendering
- Verify step indicators display correctly
- Check animation on status changes
- Test expand/collapse functionality
- Validate metadata display

# Test tool call cards
- Verify icon selection logic
- Check parameter formatting
- Test result/error display
- Validate status badge colors

# Test progress indicators
- Verify spinner rotation
- Check progress bar animation
- Test step counter logic
- Validate time formatting

# Test approval modal
- Verify countdown timer
- Check timeout behavior
- Test approve/reject flow
- Validate risk level display
```

### Integration Testing
```bash
# Test with real SSE stream
- Send message with agent execution
- Verify thought events display in real-time
- Check tool calls appear as executed
- Validate approval modal triggers

# Test approval workflow
- Trigger high-risk action
- Verify modal appears
- Test approval response
- Check timeout handling
```

## Future Enhancements

### Thought Trace
- **Graph visualization**: Show thought process as flowchart
- **Branching paths**: Display alternative reasoning paths
- **Confidence scores**: Show certainty for each step
- **Replay mode**: Step through thought process

### Tool Calls
- **Live output**: Stream tool results as they arrive
- **Retry button**: Re-execute failed tools
- **Tool chaining**: Show dependencies between tools
- **Performance metrics**: Track tool execution statistics

### Progress Indicators
- **Adaptive estimates**: Learn from past executions
- **Resource usage**: Show CPU/memory/token consumption
- **Cost tracking**: Display LLM API costs
- **Bottleneck detection**: Highlight slow operations

### Approval System
- **Approval templates**: Pre-configured approval rules
- **Delegation**: Allow approval by other team members
- **Audit log**: Track all approval decisions
- **Conditional approval**: Approve with constraints
- **Batch approval**: Approve multiple actions at once

## Files Created/Modified

### Frontend Components
- ✅ `frontend/components/chat/ThoughtTrace.tsx` (350 lines) - CREATED
- ✅ `frontend/components/chat/ToolCallCard.tsx` (430 lines) - CREATED
- ✅ `frontend/components/chat/ProgressIndicators.tsx` (520 lines) - CREATED
- ✅ `frontend/components/chat/ApprovalModal.tsx` (450 lines) - CREATED
- ✅ `frontend/components/chat/AssistantMessage.tsx` - MODIFIED (integrated new components)
- ✅ `frontend/package.json` - MODIFIED (added framer-motion)

### Backend API
- ✅ `backend/app/api/v1/approvals.py` (350 lines) - CREATED
- ✅ `backend/app/api/v1/__init__.py` - MODIFIED (registered approvals router)

## Completion Status

**TASK-274 to TASK-293: ✅ COMPLETE (20 tasks)**

**Thought Trace (TASK-274-278)**:
- ✅ TASK-274: Thought trace component
- ✅ TASK-275: Step-by-step indicators
- ✅ TASK-276: Thinking animation
- ✅ TASK-277: Collapsible trace sections
- ✅ TASK-278: Completed vs in-progress styling

**Tool Call Display (TASK-279-283)**:
- ✅ TASK-279: Tool call card component
- ✅ TASK-280: Tool name and parameters display
- ✅ TASK-281: Execution status display
- ✅ TASK-282: Tool results display
- ✅ TASK-283: Tool error display

**Progress Indicators (TASK-284-288)**:
- ✅ TASK-284: Loading spinner component
- ✅ TASK-285: Progress bar component
- ✅ TASK-286: Pulse animation for thinking
- ✅ TASK-287: Step counter component
- ✅ TASK-288: Estimated time display

**Approval Prompts (TASK-289-293)**:
- ✅ TASK-289: Approval modal component
- ✅ TASK-290: Action preview display
- ✅ TASK-291: Approve/reject buttons
- ✅ TASK-292: Backend approval response handling
- ✅ TASK-293: Approval timeout handling

**Total Progress**: ~293 tasks completed out of 480+ overall

## Summary

The Real-time UI Updates implementation provides a comprehensive, professional interface for displaying agent execution details with:

- **Transparent reasoning**: Users see how the agent thinks through problems
- **Tool visibility**: All tool executions displayed with parameters and results
- **Progress feedback**: Multiple indicators for different types of progress
- **User control**: Approval system for sensitive actions
- **Professional animations**: Smooth, meaningful motion with Framer Motion
- **Type-safe**: Full TypeScript implementation
- **Accessible**: Keyboard navigation, screen readers, color contrast
- **Responsive**: Works on all screen sizes

This completes Phase 3.3 (Real-time UI Updates) of the Aura AI Assistant platform, enabling transparent, interactive, and controlled AI agent interactions.
