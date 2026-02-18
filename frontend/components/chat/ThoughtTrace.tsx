/**
 * Thought Trace Component
 * 
 * Displays the agent's reasoning process step-by-step with animations,
 * collapsible sections, and visual indicators for completed/in-progress steps.
 * 
 * TASK-274 to TASK-278: Thought trace display with animations and styling
 */

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export interface ThoughtStep {
  step: number
  node: string
  content: string
  status: 'in_progress' | 'completed' | 'pending'
  metadata?: Record<string, any>
  timestamp: string
}

interface ThoughtTraceProps {
  steps: ThoughtStep[]
  isExpanded?: boolean
  showAnimation?: boolean
  className?: string
}

/**
 * Individual thought step component with status indicator
 */
function ThoughtStepItem({ step, isLatest }: { step: ThoughtStep; isLatest: boolean }) {
  const statusColors = {
    completed: 'bg-green-100 border-green-300 text-green-800',
    in_progress: 'bg-purple-100 border-purple-300 text-purple-800',
    pending: 'bg-gray-100 border-gray-300 text-gray-600'
  }

  const statusIcons = {
    completed: (
      <svg className="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    ),
    in_progress: (
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      >
        <svg className="h-4 w-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </motion.div>
    ),
    pending: (
      <svg className="h-4 w-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
      </svg>
    )
  }

  const nodeDisplayNames: Record<string, string> = {
    analyze: 'Analyzing',
    plan: 'Planning',
    execute: 'Executing',
    synthesize: 'Synthesizing',
    reflect: 'Reflecting'
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className={`relative pl-6 pb-4 ${isLatest ? '' : 'border-l-2 border-gray-200'}`}
    >
      {/* Status icon */}
      <div className="absolute left-0 top-0 -ml-2 flex items-center justify-center w-4 h-4 rounded-full bg-white">
        {statusIcons[step.status]}
      </div>

      {/* Content */}
      <div className={`border rounded-lg p-3 ${statusColors[step.status]}`}>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wide">
              {nodeDisplayNames[step.node] || step.node}
            </span>
            <span className="text-xs opacity-75">
              Step {step.step}
            </span>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            step.status === 'completed' 
              ? 'bg-green-200 text-green-800' 
              : step.status === 'in_progress'
              ? 'bg-purple-200 text-purple-800'
              : 'bg-gray-200 text-gray-600'
          }`}>
            {step.status === 'in_progress' ? 'In Progress' : step.status === 'completed' ? 'Done' : 'Pending'}
          </span>
        </div>
        
        <p className="text-sm leading-relaxed">
          {step.content}
        </p>

        {/* Metadata (if any) */}
        {step.metadata && Object.keys(step.metadata).length > 0 && (
          <details className="mt-2">
            <summary className="text-xs font-medium cursor-pointer hover:underline">
              View details
            </summary>
            <pre className="text-xs mt-1 bg-white bg-opacity-50 rounded p-2 overflow-x-auto">
              {JSON.stringify(step.metadata, null, 2)}
            </pre>
          </details>
        )}
      </div>

      {/* Thinking animation for in-progress steps */}
      {step.status === 'in_progress' && (
        <motion.div
          className="mt-2 flex items-center gap-2 text-xs text-purple-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="flex gap-1"
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <div className="w-1.5 h-1.5 bg-purple-600 rounded-full" style={{ animationDelay: '0ms' }} />
            <div className="w-1.5 h-1.5 bg-purple-600 rounded-full" style={{ animationDelay: '200ms' }} />
            <div className="w-1.5 h-1.5 bg-purple-600 rounded-full" style={{ animationDelay: '400ms' }} />
          </motion.div>
          <span className="font-medium">Thinking...</span>
        </motion.div>
      )}
    </motion.div>
  )
}

/**
 * Main thought trace component with collapsible sections
 * TASK-274: Thought trace component
 * TASK-275: Step-by-step indicators
 * TASK-276: Thinking animation
 * TASK-277: Collapsible trace sections
 * TASK-278: Completed vs in-progress styling
 */
export default function ThoughtTrace({ 
  steps, 
  isExpanded = false, 
  showAnimation = true,
  className = ''
}: ThoughtTraceProps) {
  const [expanded, setExpanded] = useState(isExpanded)

  if (!steps || steps.length === 0) {
    return null
  }

  const completedCount = steps.filter(s => s.status === 'completed').length
  const inProgressCount = steps.filter(s => s.status === 'in_progress').length
  const totalSteps = steps.length

  return (
    <div className={`mb-3 ${className}`}>
      {/* Header with toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full text-left p-3 rounded-lg bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 hover:border-purple-300 transition-all group"
      >
        <div className="flex items-center gap-3">
          {/* Expand/collapse icon */}
          <motion.svg
            animate={{ rotate: expanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
            className="h-4 w-4 text-purple-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
          </motion.svg>

          {/* Title with icon */}
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span className="font-semibold text-gray-900">
              Thought Process
            </span>
          </div>

          {/* Step counter */}
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-1 bg-purple-200 text-purple-800 rounded-full font-medium">
              {completedCount}/{totalSteps} steps
            </span>
            {inProgressCount > 0 && (
              <motion.span
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="px-2 py-1 bg-yellow-200 text-yellow-800 rounded-full font-medium"
              >
                {inProgressCount} in progress
              </motion.span>
            )}
          </div>
        </div>

        {/* Expand hint */}
        <span className="text-xs text-gray-500 group-hover:text-gray-700 transition-colors">
          {expanded ? 'Hide details' : 'Show details'}
        </span>
      </button>

      {/* Collapsible content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="mt-3 space-y-0">
              {steps.map((step, index) => (
                <ThoughtStepItem 
                  key={`${step.step}-${step.timestamp}`} 
                  step={step} 
                  isLatest={index === steps.length - 1}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/**
 * Compact thought trace for inline display
 */
export function CompactThoughtTrace({ steps }: { steps: ThoughtStep[] }) {
  if (!steps || steps.length === 0) return null

  const latestStep = steps[steps.length - 1]
  const completedCount = steps.filter(s => s.status === 'completed').length

  return (
    <div className="flex items-center gap-2 text-xs text-purple-600 bg-purple-50 rounded-lg px-3 py-2 mb-2">
      {latestStep.status === 'in_progress' ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </motion.div>
      ) : (
        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      )}
      <span className="font-medium">
        {latestStep.content}
      </span>
      <span className="text-purple-500">
        ({completedCount}/{steps.length})
      </span>
    </div>
  )
}
