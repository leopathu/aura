/**
 * Activity Types
 * 
 * Type definitions for activity logging system
 */

export interface Activity {
  id: string
  org_id: string
  agent_id: string | null
  user_id: string | null
  action: string
  details: Record<string, any>
  created_at: string
}

export interface ActivityFilters {
  startDate: Date | null
  endDate: Date | null
  actionTypes: string[]
  agentId: string | null
  userId: string | null
}

export interface ActivityStatistics {
  total: number
  by_type: Record<string, number>
  by_agent: Record<string, number>
  by_user: Record<string, number>
}

export const ACTION_CATEGORIES = {
  agent: 'Agent',
  message: 'Message',
  tool: 'Tool',
  credential: 'Credential',
  integration: 'Integration',
  user: 'User',
  org: 'Organization',
  approval: 'Approval',
} as const

export const ACTION_COLORS = {
  agent: 'purple',
  message: 'blue',
  tool: 'green',
  credential: 'yellow',
  integration: 'pink',
  user: 'indigo',
  org: 'gray',
  approval: 'orange',
} as const
