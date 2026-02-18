/**
 * Tool Call Card Component
 * 
 * Displays tool execution information including name, parameters,
 * execution status, results, and error handling.
 * 
 * TASK-279 to TASK-283: Tool call display components
 */

'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'

export interface ToolCall {
  tool_id: string
  tool_name: string
  arguments: Record<string, any>
  status: 'initiating' | 'running' | 'completed' | 'failed'
  result?: any
  error?: string
  duration_ms?: number
  timestamp: string
}

interface ToolCallCardProps {
  toolCall: ToolCall
  showDetails?: boolean
  className?: string
}

/**
 * Get tool icon based on tool name
 */
function getToolIcon(toolName: string) {
  const iconMap: Record<string, JSX.Element> = {
    gmail_search: (
      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
        <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
      </svg>
    ),
    gmail_send: (
      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
      </svg>
    ),
    calendar_list: (
      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
      </svg>
    ),
    calendar_create: (
      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm4.5 7.5a.5.5 0 00-1 0v2h-2a.5.5 0 000 1h2v2a.5.5 0 001 0v-2h2a.5.5 0 000-1h-2v-2z" clipRule="evenodd" />
      </svg>
    ),
    jira_search: (
      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
      </svg>
    ),
    slack_send: (
      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
      </svg>
    ),
    default: (
      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
      </svg>
    )
  }

  return iconMap[toolName] || iconMap.default
}

/**
 * Status badge component
 */
function StatusBadge({ status }: { status: ToolCall['status'] }) {
  const statusConfig = {
    initiating: { 
      bg: 'bg-blue-100', 
      text: 'text-blue-800', 
      label: 'Initiating',
      icon: '⏳'
    },
    running: { 
      bg: 'bg-yellow-100', 
      text: 'text-yellow-800', 
      label: 'Running',
      icon: '⚡'
    },
    completed: { 
      bg: 'bg-green-100', 
      text: 'text-green-800', 
      label: 'Completed',
      icon: '✓'
    },
    failed: { 
      bg: 'bg-red-100', 
      text: 'text-red-800', 
      label: 'Failed',
      icon: '✗'
    }
  }

  const config = statusConfig[status]

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </span>
  )
}

/**
 * Tool Call Card
 * TASK-279: Tool call card component
 * TASK-280: Show tool name and parameters
 * TASK-281: Display tool execution status
 * TASK-282: Show tool results
 * TASK-283: Add tool error display
 */
export default function ToolCallCard({ toolCall, showDetails = true, className = '' }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false)

  const statusColors = {
    initiating: 'border-blue-200 bg-blue-50',
    running: 'border-yellow-200 bg-yellow-50',
    completed: 'border-green-200 bg-green-50',
    failed: 'border-red-200 bg-red-50'
  }

  const toolDisplayName = toolCall.tool_name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`border-2 rounded-lg overflow-hidden ${statusColors[toolCall.status]} ${className}`}
    >
      {/* Header */}
      <div className="p-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {/* Tool icon */}
            <div className={`flex-shrink-0 p-2 rounded-lg ${
              toolCall.status === 'completed' ? 'bg-green-200 text-green-700' :
              toolCall.status === 'failed' ? 'bg-red-200 text-red-700' :
              toolCall.status === 'running' ? 'bg-yellow-200 text-yellow-700' :
              'bg-blue-200 text-blue-700'
            }`}>
              {getToolIcon(toolCall.tool_name)}
            </div>

            {/* Tool info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-semibold text-gray-900 text-sm">
                  {toolDisplayName}
                </h4>
                <StatusBadge status={toolCall.status} />
              </div>

              {/* Duration (if available) */}
              {toolCall.duration_ms !== undefined && (
                <p className="text-xs text-gray-600">
                  Execution time: {toolCall.duration_ms}ms ({(toolCall.duration_ms / 1000).toFixed(2)}s)
                </p>
              )}

              {/* Running animation */}
              {toolCall.status === 'running' && (
                <div className="flex items-center gap-2 mt-2">
                  <motion.div
                    className="flex gap-1"
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
                  >
                    <div className="w-1.5 h-1.5 bg-yellow-600 rounded-full" />
                    <div className="w-1.5 h-1.5 bg-yellow-600 rounded-full" style={{ animationDelay: '200ms' }} />
                    <div className="w-1.5 h-1.5 bg-yellow-600 rounded-full" style={{ animationDelay: '400ms' }} />
                  </motion.div>
                  <span className="text-xs text-yellow-700 font-medium">Executing...</span>
                </div>
              )}
            </div>
          </div>

          {/* Expand button */}
          {showDetails && (Object.keys(toolCall.arguments).length > 0 || toolCall.result || toolCall.error) && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex-shrink-0 p-1 hover:bg-black hover:bg-opacity-5 rounded transition-colors"
            >
              <motion.svg
                animate={{ rotate: expanded ? 180 : 0 }}
                transition={{ duration: 0.2 }}
                className="h-4 w-4 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </motion.svg>
            </button>
          )}
        </div>

        {/* Error message (always visible if present) */}
        {toolCall.error && (
          <div className="mt-3 p-2 bg-red-100 border border-red-300 rounded text-sm text-red-800">
            <div className="flex items-start gap-2">
              <svg className="h-4 w-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <p className="font-medium mb-1">Error</p>
                <p className="text-xs">{toolCall.error}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Expandable details */}
      {expanded && showDetails && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="border-t border-gray-200 bg-white bg-opacity-50"
        >
          {/* Parameters */}
          {Object.keys(toolCall.arguments).length > 0 && (
            <div className="p-3 border-b border-gray-200">
              <h5 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
                Parameters
              </h5>
              <pre className="text-xs bg-gray-100 rounded p-2 overflow-x-auto">
                {JSON.stringify(toolCall.arguments, null, 2)}
              </pre>
            </div>
          )}

          {/* Result */}
          {toolCall.result && !toolCall.error && (
            <div className="p-3">
              <h5 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Result
              </h5>
              <div className="text-xs bg-gray-100 rounded p-2 overflow-x-auto">
                {typeof toolCall.result === 'string' ? (
                  <p className="whitespace-pre-wrap">{toolCall.result}</p>
                ) : (
                  <pre>{JSON.stringify(toolCall.result, null, 2)}</pre>
                )}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  )
}

/**
 * Compact tool call list for multiple tools
 */
export function ToolCallList({ toolCalls, className = '' }: { toolCalls: ToolCall[]; className?: string }) {
  if (!toolCalls || toolCalls.length === 0) return null

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
        </svg>
        <span>Tool Calls ({toolCalls.length})</span>
      </div>
      {toolCalls.map((toolCall) => (
        <ToolCallCard key={toolCall.tool_id} toolCall={toolCall} />
      ))}
    </div>
  )
}
