# SSE (Server-Sent Events) Streaming Implementation

## Overview
This document describes the complete implementation of Server-Sent Events (SSE) for real-time chat streaming in Aura AI Assistant platform (TASK-257 to TASK-273).

## Architecture

### Backend Components

#### 1. SSE Service (`backend/app/services/sse_service.py`)
**Purpose**: Core SSE protocol implementation with event formatting and connection management.

**Key Features**:
- **SSE Event Types**: 8 event types for comprehensive streaming
  - `thought`: Agent reasoning steps
  - `tool_call`: Tool execution initiation
  - `tool_result`: Tool execution results
  - `token`: Word-by-word response streaming
  - `completion`: Final response with metadata
  - `error`: Error events
  - `heartbeat`: Keep-alive events (15s interval)
  - `status`: Agent status updates

- **SSEFormatter Class**: Formats events into SSE protocol
  ```
  id: {uuid}
  event: {event_type}
  data: {json_data}
  
  ```
  - `format_event()`: Generic SSE formatting
  - `format_thought()`: Thought trace events
  - `format_tool_call()`: Tool call initiation
  - `format_tool_result()`: Tool execution results
  - `format_token()`: Token streaming
  - `format_completion()`: Final completion event
  - `format_heartbeat()`: Keep-alive events
  - `format_error()`: Error handling

- **SSEConnectionManager**: Connection lifecycle management
  - Register/unregister connections
  - Track active connections
  - Disconnection detection
  - Connection cleanup

- **Heartbeat Mechanism**: Prevents connection timeout
  - 15-second interval heartbeats
  - Graceful disconnection handling
  - Connection state tracking

#### 2. Streaming Agent Service (`backend/app/services/streaming_agent.py`)
**Purpose**: Stream agent execution with real-time event generation.

**Key Functions**:
- `stream_agent_execution()`: Main async generator
  - Orchestrates agent workflow streaming
  - Status updates at each phase:
    - `initializing` → `analyzing` → `planning` → `executing` → `synthesizing`
  - Streams thought trace in real-time
  - Streams tool calls and results
  - Token-by-token response (0.02s delay)
  - Completion event with full metadata

- `stream_execute_node()`: Tool execution streaming
  - Real-time tool call events
  - Tool result events with duration
  - Error handling

**Event Flow**:
```
1. STATUS: initializing
2. STATUS: analyzing → THOUGHT events
3. STATUS: planning → THOUGHT events
4. STATUS: executing → TOOL_CALL + TOOL_RESULT events
5. STATUS: synthesizing → THOUGHT events
6. TOKEN events (word-by-word)
7. COMPLETION event (final response + metadata)
```

#### 3. Chat Streaming Endpoint (`backend/app/api/v1/chat.py`)
**Endpoint**: `POST /api/v1/chat/stream`

**Features**:
- Accepts `ChatRequest` with agent_id, message, conversation_id
- Creates/retrieves conversation
- Saves user message
- Streams agent execution with SSE
- Collects metadata (thought trace, tool calls)
- Saves assistant message after completion
- Returns `StreamingResponse` with SSE events

**Headers**:
```python
{
  "Content-Type": "text/event-stream",
  "Cache-Control": "no-cache",
  "X-Accel-Buffering": "no"  # Disable nginx buffering
}
```

### Frontend Components

#### 1. SSE Client (`frontend/lib/sse-client.ts`)
**Purpose**: SSE client with event parsing, connection management, and auto-reconnection.

**Key Features**:
- **TypeScript Interfaces**: Type-safe event handling
  - `ThoughtEvent`, `ToolCallEvent`, `ToolResultEvent`, `TokenEvent`, `CompletionEvent`, etc.

- **SSEClient Class**: Main client for streaming
  - Connection state management: `connecting`, `connected`, `disconnected`, `error`
  - Event parsing and routing
  - Event handlers for each event type
  - Connection lifecycle management

- **Reconnection Logic**: Exponential backoff
  - Max 3 retry attempts
  - Delays: 1s, 2s, 4s, 8s...
  - Graceful error handling

- **Event Routing**:
  ```typescript
  onThought(data: ThoughtEvent)
  onToolCall(data: ToolCallEvent)
  onToolResult(data: ToolResultEvent)
  onToken(data: TokenEvent)
  onCompletion(data: CompletionEvent)
  onError(data: ErrorEvent)
  onStatus(data: StatusEvent)
  onHeartbeat(data: HeartbeatEvent)
  ```

#### 2. Chat Page (`frontend/app/chat/page.tsx`)
**Purpose**: Chat interface with SSE streaming support.

**Features**:
- Manual SSE handling (EventSource doesn't support POST)
- ReadableStream reader for chunked response
- Event parsing and state updates
- Real-time message rendering
- Thought trace and tool call tracking
- Connection state display

**State Management**:
```typescript
const [streamingContent, setStreamingContent] = useState('')
const [currentThoughts, setCurrentThoughts] = useState<ThoughtEvent[]>([])
const [currentToolCalls, setCurrentToolCalls] = useState<...>([])
const [agentStatus, setAgentStatus] = useState<string>('')
```

**Event Processing**:
1. Parse SSE events from stream
2. Route by event type
3. Update UI state in real-time
4. Accumulate tokens into message
5. Handle completion and save final message

#### 3. Message Components
**MessageList** (`frontend/components/chat/MessageList.tsx`):
- Renders messages with metadata support
- Passes metadata to AssistantMessage

**AssistantMessage** (`frontend/components/chat/AssistantMessage.tsx`):
- **Enhanced UI for Streaming**:
  - Streaming indicator (animated dots)
  - Collapsible thought trace viewer
  - Collapsible tool calls viewer
  - Markdown rendering with syntax highlighting
  - Copy code button

- **Thought Trace Display**:
  - Purple-themed cards
  - Step number and node name
  - Status badge (completed/in_progress)
  - Expandable/collapsible

- **Tool Call Display**:
  - Blue-themed cards
  - Tool name and duration
  - Arguments display (JSON)
  - Result display (JSON or text)
  - Error display (if failed)

## SSE Protocol Specification

### Event Format
```
id: {uuid4}
event: {event_type}
data: {json_data}

```

### Event Types

#### 1. Thought Event
```json
{
  "event": "thought",
  "data": {
    "step": 1,
    "node": "analyze",
    "content": "Analyzing user request...",
    "status": "in_progress",
    "metadata": {},
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 2. Tool Call Event
```json
{
  "event": "tool_call",
  "data": {
    "tool_name": "gmail_search",
    "arguments": {"query": "from:john@example.com"},
    "status": "running",
    "tool_id": "uuid",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 3. Tool Result Event
```json
{
  "event": "tool_result",
  "data": {
    "tool_name": "gmail_search",
    "result": {...},
    "error": null,
    "duration_ms": 1234,
    "tool_id": "uuid",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 4. Token Event
```json
{
  "event": "token",
  "data": {
    "token": "Hello",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 5. Completion Event
```json
{
  "event": "completion",
  "data": {
    "final_response": "Complete response text",
    "metadata": {
      "total_tokens": 150,
      "thought_trace": [...],
      "tool_calls": [...],
      "execution_time_ms": 5000
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 6. Status Event
```json
{
  "event": "status",
  "data": {
    "status": "analyzing",
    "message": "Analyzing your request",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 7. Heartbeat Event
```json
{
  "event": "heartbeat",
  "data": {
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 8. Error Event
```json
{
  "event": "error",
  "data": {
    "message": "Tool execution failed",
    "code": "TOOL_ERROR",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## User Experience Flow

1. **User sends message**
   - User types message and clicks send
   - Optimistic UI update (add user message immediately)
   - Initiate SSE connection

2. **Connection established**
   - Receive conversation_id
   - Connection state: `connected`

3. **Agent execution starts**
   - Status: `initializing`
   - Display loading indicator

4. **Thought streaming**
   - Status: `analyzing`, `planning`, `synthesizing`
   - Receive thought events in real-time
   - Display in collapsible thought trace viewer

5. **Tool execution**
   - Status: `executing`
   - Receive tool_call events (show tool name, arguments)
   - Receive tool_result events (show results, duration)
   - Display in collapsible tool calls viewer

6. **Response streaming**
   - Receive token events word-by-word
   - Accumulate tokens into message
   - Display with typing effect (0.02s delay)
   - Show streaming indicator

7. **Completion**
   - Receive completion event
   - Save final message with metadata
   - Update conversation sidebar
   - Reset streaming state

8. **Heartbeat**
   - Receive heartbeat every 15s
   - Keeps connection alive
   - Prevents timeout

9. **Error handling**
   - Receive error event
   - Display user-friendly error message
   - Remove optimistic message
   - Reset streaming state

## Benefits

### Transparency
- Users see agent thinking process
- Tool execution visible in real-time
- Clear status updates

### Responsiveness
- Immediate feedback vs waiting 10+ seconds
- Progressive response rendering
- No "black box" waiting

### User Engagement
- Users stay engaged during long operations
- See progress in real-time
- Like ChatGPT streaming experience

### Debugging
- Developers see agent workflow
- Tool calls and results visible
- Thought trace for debugging

### Performance
- Perceived performance improvement
- Progressive rendering
- Connection keepalive prevents timeout

## Technical Considerations

### Connection Management
- Track active connections to prevent leaks
- Graceful disconnection handling
- Reconnection with exponential backoff
- Max 3 retry attempts

### Error Handling
- Try-catch around event parsing
- Error events for user feedback
- Fallback to non-streaming on failure
- Connection state tracking

### Performance Optimization
- Heartbeat interval: 15s (balance between keepalive and overhead)
- Token delay: 0.02s (natural typing speed)
- Buffer management for incomplete events
- Event batching where appropriate

### Browser Compatibility
- EventSource doesn't support POST (using fetch + ReadableStream)
- Manual SSE parsing on frontend
- Compatible with all modern browsers
- Fallback to non-streaming if needed

## Testing

### Backend Testing
```bash
# Test SSE endpoint
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"agent_id": "...", "message": "Hello", "conversation_id": null}'
```

### Frontend Testing
1. Open chat interface
2. Send message
3. Verify events appear in real-time:
   - Status updates
   - Thought trace
   - Tool calls
   - Token streaming
   - Completion
4. Check for memory leaks (disconnect on unmount)
5. Test reconnection (disconnect network, reconnect)

## Future Enhancements

1. **Message Editing**
   - Edit streaming responses on-the-fly
   - Stop generation button

2. **Advanced Thought Visualization**
   - Graph view of agent reasoning
   - Timeline of execution

3. **Tool Call Approval**
   - Pause before tool execution
   - User approval for sensitive tools

4. **Performance Metrics**
   - Token/sec display
   - Execution time breakdown
   - Cost estimation

5. **Multiplayer Chat**
   - Multiple users see same stream
   - Broadcast to all connected clients

6. **Stream Resumption**
   - Resume interrupted streams
   - Event replay from checkpoint

## Files Created/Modified

### Backend
- ✅ `backend/app/services/sse_service.py` (458 lines) - CREATED
- ✅ `backend/app/services/streaming_agent.py` (315 lines) - CREATED
- ✅ `backend/app/api/v1/chat.py` - MODIFIED (streaming endpoint)

### Frontend
- ✅ `frontend/lib/sse-client.ts` (358 lines) - CREATED
- ✅ `frontend/app/chat/page.tsx` - MODIFIED (SSE integration)
- ✅ `frontend/components/chat/MessageList.tsx` - MODIFIED (metadata support)
- ✅ `frontend/components/chat/AssistantMessage.tsx` - MODIFIED (thought/tool display)

## Completion Status

**TASK-257 to TASK-273: ✅ COMPLETE**

- ✅ TASK-257: SSE dependencies (built-in FastAPI support)
- ✅ TASK-258: SSE response generator
- ✅ TASK-259: Event formatting
- ✅ TASK-260: Heartbeat mechanism
- ✅ TASK-261: Connection management
- ✅ TASK-262: Error handling
- ✅ TASK-263: Streaming agent execution
- ✅ TASK-264: Thought trace streaming
- ✅ TASK-265: Tool call streaming
- ✅ TASK-266: Token streaming
- ✅ TASK-267: Completion events
- ✅ TASK-268: Client disconnection handling
- ✅ TASK-269: Frontend SSE client class
- ✅ TASK-270: Event parsing and routing
- ✅ TASK-271: Connection state management
- ✅ TASK-272: Reconnection logic
- ✅ TASK-273: Error handling and retry limits

**Total: 17 tasks completed**

## Summary

The SSE streaming implementation provides a production-ready real-time chat experience with:
- Complete SSE protocol compliance
- Real-time agent execution streaming
- Thought trace and tool call visibility
- Token-by-token response rendering
- Robust error handling and reconnection
- Clean, professional UI with collapsible sections
- Type-safe TypeScript implementation
- Comprehensive event types for all scenarios

This completes Phase 3 (Real-time Features) of the Aura AI Assistant platform, enabling transparent, responsive, and engaging AI agent interactions.
