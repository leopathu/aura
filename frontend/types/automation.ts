/**
 * Automation Types
 * 
 * TypeScript interfaces for automation system
 */

export enum TriggerType {
  SCHEDULE = 'schedule',
  WEBHOOK = 'webhook',
  EVENT = 'event',
  MANUAL = 'manual'
}

export enum AutomationStatus {
  ACTIVE = 'active',
  PAUSED = 'paused',
  DRAFT = 'draft',
  ARCHIVED = 'archived'
}

export enum RunStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  SUCCESS = 'success',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  TIMEOUT = 'timeout'
}

export interface WorkflowStep {
  type: 'agent_task' | 'http_request' | 'condition' | 'delay' | 'set_variable'
  config: Record<string, any>
}

export interface TriggerConfig {
  event_type?: string
  conditions?: Array<{
    operator: string
    field: string
    value: any
  }>
  logic?: 'AND' | 'OR'
  webhook_secret?: string
  auth_type?: 'none' | 'signature' | 'api_key'
}

export interface Automation {
  id: string
  org_id: string
  name: string
  description?: string
  status: AutomationStatus
  trigger_type: TriggerType
  schedule?: string
  timezone: string
  workflow: {
    steps: WorkflowStep[]
  }
  trigger_config?: TriggerConfig
  agent_id?: string
  last_run_at?: string
  last_run_status?: RunStatus
  next_run_at?: string
  run_count: number
  success_count: number
  failure_count: number
  created_at: string
  updated_at: string
}

export interface AutomationRun {
  id: string
  automation_id: string
  status: RunStatus
  trigger_type: TriggerType
  trigger_data?: Record<string, any>
  started_at?: string
  completed_at?: string
  current_step: number
  total_steps: number
  context?: Record<string, any>
  result?: Record<string, any>
  error?: string
  logs: Array<{
    timestamp: string
    message: string
    level: string
  }>
  duration_seconds?: number
  created_at: string
}

export interface AutomationTemplate {
  id: string
  name: string
  description: string
  category: string
  icon: string
  trigger_type: TriggerType
  schedule?: string
  workflow: {
    steps: WorkflowStep[]
  }
  trigger_config?: TriggerConfig
  variables?: string[]
}

export interface CreateAutomationRequest {
  name: string
  description?: string
  workflow: {
    steps: WorkflowStep[]
  }
  trigger_type: TriggerType
  schedule?: string
  trigger_config?: TriggerConfig
  timezone?: string
  agent_id?: string
  enabled?: boolean
}

export interface UpdateAutomationRequest {
  name?: string
  description?: string
  workflow?: {
    steps: WorkflowStep[]
  }
  schedule?: string
  trigger_config?: TriggerConfig
  timezone?: string
  enabled?: boolean
  status?: AutomationStatus
}
