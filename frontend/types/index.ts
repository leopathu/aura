/**
 * TypeScript Type Definitions
 */

// User Types
export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  email: string
  password: string
  full_name: string
}

export interface UserLogin {
  email: string
  password: string
}

// Organization Types
export interface Organization {
  id: string
  name: string
  slug: string
  created_at: string
  updated_at: string
}

export interface OrganizationCreate {
  name: string
  slug?: string
}

export interface Membership {
  id: string
  user_id: string
  org_id: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
}

// Agent Types
export interface Agent {
  id: string
  org_id: string
  name: string
  description: string
  system_prompt: string
  config: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AgentCreate {
  name: string
  description: string
  system_prompt?: string
  config?: Record<string, any>
}

// Credential Types
export type CredentialType = 'openai' | 'anthropic' | 'gemini' | 'custom'

export interface Credential {
  id: string
  org_id: string
  credential_type: CredentialType
  label: string
  created_at: string
}

export interface CredentialCreate {
  credential_type: CredentialType
  api_key: string
  label?: string
}

// Chat Types
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

export interface ChatRequest {
  message: string
  agent_id?: string
  conversation_id?: string
}

export interface ChatResponse {
  response: string
  agent_id: string
  thought_trace?: string[]
  tool_calls?: ToolCall[]
}

export interface ToolCall {
  name: string
  arguments: Record<string, any>
  result?: any
  status: 'pending' | 'success' | 'error'
}

// API Response Types
export interface ApiError {
  detail: string
  status_code: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// Activity Log Types
export interface ActivityLog {
  id: string
  org_id: string
  agent_id?: string
  action: string
  details: Record<string, any>
  created_at: string
}
