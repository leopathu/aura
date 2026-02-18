/**
 * SSE Client for Real-time Chat Streaming
 * 
 * Handles Server-Sent Events connection for streaming chat responses
 * with automatic reconnection, error handling, and event routing.
 */

// Event types from backend SSE service
export type SSEEventType = 
  | 'thought'
  | 'tool_call'
  | 'tool_result'
  | 'token'
  | 'completion'
  | 'error'
  | 'heartbeat'
  | 'status'

// Event data interfaces
export interface ThoughtEvent {
  step: number
  node: string
  content: string
  status: 'in_progress' | 'completed'
  metadata?: Record<string, any>
  timestamp: string
}

export interface ToolCallEvent {
  tool_name: string
  arguments: Record<string, any>
  status: 'initiating' | 'running' | 'completed' | 'failed'
  tool_id: string
  timestamp: string
}

export interface ToolResultEvent {
  tool_name: string
  result?: any
  error?: string
  duration_ms: number
  tool_id: string
  timestamp: string
}

export interface TokenEvent {
  token: string
  timestamp: string
}

export interface CompletionEvent {
  final_response: string
  metadata: {
    total_tokens?: number
    thought_trace: any[]
    tool_calls: any[]
    execution_time_ms: number
  }
  timestamp: string
}

export interface ErrorEvent {
  message: string
  code: string
  timestamp: string
}

export interface StatusEvent {
  status: string
  message?: string
  timestamp: string
}

export interface HeartbeatEvent {
  timestamp: string
}

// Union type for all event data
export type SSEEventData = 
  | ThoughtEvent
  | ToolCallEvent
  | ToolResultEvent
  | TokenEvent
  | CompletionEvent
  | ErrorEvent
  | StatusEvent
  | HeartbeatEvent

// Parsed SSE event
export interface ParsedSSEEvent {
  id?: string
  event: SSEEventType
  data: SSEEventData
}

// Connection state
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

// Event handlers
export type EventHandler<T = SSEEventData> = (data: T) => void

export interface SSEClientOptions {
  url: string
  token: string
  onThought?: EventHandler<ThoughtEvent>
  onToolCall?: EventHandler<ToolCallEvent>
  onToolResult?: EventHandler<ToolResultEvent>
  onToken?: EventHandler<TokenEvent>
  onCompletion?: EventHandler<CompletionEvent>
  onError?: EventHandler<ErrorEvent>
  onStatus?: EventHandler<StatusEvent>
  onHeartbeat?: EventHandler<HeartbeatEvent>
  onConnectionChange?: (state: ConnectionState) => void
  maxRetries?: number
  retryDelay?: number
}

/**
 * SSE Client for streaming chat responses
 * 
 * Features:
 * - EventSource wrapper with event parsing
 * - Connection state management
 * - Automatic reconnection with exponential backoff
 * - Event type routing to specific handlers
 * - Error handling and retry limits
 */
export class SSEClient {
  private eventSource: EventSource | null = null
  private connectionState: ConnectionState = 'disconnected'
  private options: SSEClientOptions
  private retryCount = 0
  private reconnectTimeout?: NodeJS.Timeout
  private conversationId?: string

  constructor(options: SSEClientOptions) {
    this.options = {
      maxRetries: 3,
      retryDelay: 1000,
      ...options
    }
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.connectionState
  }

  /**
   * Get conversation ID from stream
   */
  getConversationId(): string | undefined {
    return this.conversationId
  }

  /**
   * Update connection state and notify listeners
   */
  private setState(state: ConnectionState): void {
    this.connectionState = state
    this.options.onConnectionChange?.(state)
  }

  /**
   * Parse SSE event data
   */
  private parseEvent(eventType: string, data: string): ParsedSSEEvent | null {
    try {
      const parsedData = JSON.parse(data)
      
      // Handle conversation_id (initial event)
      if (parsedData.conversation_id) {
        this.conversationId = parsedData.conversation_id
        return null
      }
      
      return {
        event: eventType as SSEEventType,
        data: parsedData
      }
    } catch (error) {
      console.error('Failed to parse SSE event:', error)
      return null
    }
  }

  /**
   * Route event to appropriate handler
   */
  private routeEvent(event: ParsedSSEEvent): void {
    switch (event.event) {
      case 'thought':
        this.options.onThought?.(event.data as ThoughtEvent)
        break
      case 'tool_call':
        this.options.onToolCall?.(event.data as ToolCallEvent)
        break
      case 'tool_result':
        this.options.onToolResult?.(event.data as ToolResultEvent)
        break
      case 'token':
        this.options.onToken?.(event.data as TokenEvent)
        break
      case 'completion':
        this.options.onCompletion?.(event.data as CompletionEvent)
        break
      case 'error':
        this.options.onError?.(event.data as ErrorEvent)
        break
      case 'status':
        this.options.onStatus?.(event.data as StatusEvent)
        break
      case 'heartbeat':
        this.options.onHeartbeat?.(event.data as HeartbeatEvent)
        break
      default:
        console.warn('Unknown SSE event type:', event.event)
    }
  }

  /**
   * Connect to SSE stream
   */
  connect(): void {
    if (this.eventSource) {
      console.warn('SSE connection already exists')
      return
    }

    this.setState('connecting')

    // Create EventSource with authorization
    const url = new URL(this.options.url)
    this.eventSource = new EventSource(url.toString())

    // Handle open event
    this.eventSource.onopen = () => {
      console.log('SSE connection established')
      this.setState('connected')
      this.retryCount = 0 // Reset retry count on successful connection
    }

    // Handle message event (default)
    this.eventSource.onmessage = (event) => {
      const parsedEvent = this.parseEvent('message', event.data)
      if (parsedEvent) {
        this.routeEvent(parsedEvent)
      }
    }

    // Handle error event
    this.eventSource.onerror = (error) => {
      console.error('SSE connection error:', error)
      this.setState('error')
      
      // Close and attempt reconnection
      this.disconnect()
      this.attemptReconnect()
    }

    // Register custom event listeners for all event types
    const eventTypes: SSEEventType[] = [
      'thought', 'tool_call', 'tool_result', 'token', 
      'completion', 'error', 'status', 'heartbeat'
    ]

    eventTypes.forEach(eventType => {
      this.eventSource!.addEventListener(eventType, (event: any) => {
        const parsedEvent = this.parseEvent(eventType, event.data)
        if (parsedEvent) {
          this.routeEvent(parsedEvent)
        }
      })
    })
  }

  /**
   * Attempt reconnection with exponential backoff
   */
  private attemptReconnect(): void {
    const maxRetries = this.options.maxRetries || 3
    
    if (this.retryCount >= maxRetries) {
      console.error(`Max reconnection attempts (${maxRetries}) reached`)
      this.setState('disconnected')
      this.options.onError?.({
        message: 'Connection failed after maximum retry attempts',
        code: 'MAX_RETRIES_EXCEEDED',
        timestamp: new Date().toISOString()
      })
      return
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, ...
    const delay = (this.options.retryDelay || 1000) * Math.pow(2, this.retryCount)
    this.retryCount++

    console.log(`Attempting reconnection in ${delay}ms (attempt ${this.retryCount}/${maxRetries})`)

    this.reconnectTimeout = setTimeout(() => {
      this.connect()
    }, delay)
  }

  /**
   * Disconnect from SSE stream
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = undefined
    }

    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }

    this.setState('disconnected')
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState === 'connected'
  }

  /**
   * Reset retry count (useful for manual reconnection)
   */
  resetRetries(): void {
    this.retryCount = 0
  }
}

/**
 * Create SSE client with simplified API
 */
export function createSSEClient(
  url: string,
  token: string,
  handlers: Omit<SSEClientOptions, 'url' | 'token'>
): SSEClient {
  return new SSEClient({
    url,
    token,
    ...handlers
  })
}

/**
 * Hook-friendly SSE client factory
 */
export function useSSEConnection(
  url: string,
  token: string,
  options?: Partial<SSEClientOptions>
): SSEClient {
  const client = new SSEClient({
    url,
    token,
    ...options
  })
  
  return client
}
