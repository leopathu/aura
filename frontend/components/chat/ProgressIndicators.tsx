/**
 * Progress Indicators Components
 * 
 * Collection of loading and progress indicators for chat UI
 * including spinners, progress bars, pulse animations, step counters,
 * and estimated time displays.
 * 
 * TASK-284 to TASK-288: Progress indicator components
 */

'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

/**
 * Loading Spinner Component
 * TASK-284: Create loading spinner component
 */
export function LoadingSpinner({ 
  size = 'md', 
  color = 'purple',
  className = '' 
}: { 
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'purple' | 'blue' | 'green' | 'gray'
  className?: string 
}) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  }

  const colorClasses = {
    purple: 'border-purple-600',
    blue: 'border-blue-600',
    green: 'border-green-600',
    gray: 'border-gray-600'
  }

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      className={`${sizeClasses[size]} border-2 border-t-transparent ${colorClasses[color]} rounded-full ${className}`}
    />
  )
}

/**
 * Progress Bar Component
 * TASK-285: Create progress bar component
 */
export function ProgressBar({ 
  progress, 
  showPercentage = true,
  color = 'purple',
  height = 'md',
  animated = true,
  className = '' 
}: { 
  progress: number // 0-100
  showPercentage?: boolean
  color?: 'purple' | 'blue' | 'green' | 'gradient'
  height?: 'sm' | 'md' | 'lg'
  animated?: boolean
  className?: string 
}) {
  const heightClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  const colorClasses = {
    purple: 'bg-purple-600',
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    gradient: 'bg-gradient-to-r from-purple-600 to-blue-600'
  }

  const clampedProgress = Math.min(100, Math.max(0, progress))

  return (
    <div className={className}>
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${heightClasses[height]}`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${clampedProgress}%` }}
          transition={{ duration: animated ? 0.5 : 0, ease: 'easeOut' }}
          className={`${heightClasses[height]} ${colorClasses[color]} rounded-full`}
        />
      </div>
      {showPercentage && (
        <div className="text-xs text-gray-600 mt-1 text-right">
          {Math.round(clampedProgress)}%
        </div>
      )}
    </div>
  )
}

/**
 * Pulse Animation Component
 * TASK-286: Add pulse animation for thinking
 */
export function PulseAnimation({ 
  color = 'purple',
  size = 'md',
  className = '' 
}: { 
  color?: 'purple' | 'blue' | 'green'
  size?: 'sm' | 'md' | 'lg'
  className?: string 
}) {
  const sizeClasses = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3'
  }

  const colorClasses = {
    purple: 'bg-purple-600',
    blue: 'bg-blue-600',
    green: 'bg-green-600'
  }

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <motion.div
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity, delay: 0 }}
        className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full`}
      />
      <motion.div
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
        className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full`}
      />
      <motion.div
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
        className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full`}
      />
    </div>
  )
}

/**
 * Step Counter Component
 * TASK-287: Create step counter component
 */
export function StepCounter({ 
  currentStep, 
  totalSteps,
  showLabels = true,
  size = 'md',
  className = '' 
}: { 
  currentStep: number
  totalSteps: number
  showLabels?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string 
}) {
  const sizeClasses = {
    sm: { container: 'text-xs', circle: 'h-6 w-6', text: 'text-xs' },
    md: { container: 'text-sm', circle: 'h-8 w-8', text: 'text-sm' },
    lg: { container: 'text-base', circle: 'h-10 w-10', text: 'text-base' }
  }

  const sizes = sizeClasses[size]

  return (
    <div className={`flex items-center gap-2 ${sizes.container} ${className}`}>
      {showLabels && (
        <span className="text-gray-600 font-medium">
          Step
        </span>
      )}
      <div className="flex items-center gap-1">
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
          <motion.div
            key={step}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: step * 0.1 }}
            className={`${sizes.circle} rounded-full flex items-center justify-center font-semibold transition-all ${
              step < currentStep
                ? 'bg-green-600 text-white'
                : step === currentStep
                ? 'bg-purple-600 text-white ring-2 ring-purple-300 ring-offset-2'
                : 'bg-gray-200 text-gray-500'
            }`}
          >
            {step < currentStep ? (
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            ) : (
              <span className={sizes.text}>{step}</span>
            )}
          </motion.div>
        ))}
      </div>
      {showLabels && (
        <span className="text-gray-600">
          of {totalSteps}
        </span>
      )}
    </div>
  )
}

/**
 * Linear Step Counter (alternative style)
 */
export function LinearStepCounter({ 
  currentStep, 
  totalSteps,
  stepLabels,
  className = '' 
}: { 
  currentStep: number
  totalSteps: number
  stepLabels?: string[]
  className?: string 
}) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => {
        const isCompleted = step < currentStep
        const isCurrent = step === currentStep
        const label = stepLabels?.[step - 1] || `Step ${step}`

        return (
          <div key={step} className="flex items-center gap-3">
            <div className={`flex-shrink-0 h-6 w-6 rounded-full flex items-center justify-center text-xs font-semibold ${
              isCompleted ? 'bg-green-600 text-white' :
              isCurrent ? 'bg-purple-600 text-white' :
              'bg-gray-200 text-gray-500'
            }`}>
              {isCompleted ? '✓' : step}
            </div>
            <div className="flex-1">
              <div className={`text-sm font-medium ${
                isCurrent ? 'text-purple-700' : isCompleted ? 'text-green-700' : 'text-gray-500'
              }`}>
                {label}
              </div>
            </div>
            {isCurrent && <PulseAnimation size="sm" />}
          </div>
        )
      })}
    </div>
  )
}

/**
 * Estimated Time Display Component
 * TASK-288: Add estimated time display
 */
export function EstimatedTime({ 
  startTime,
  estimatedDurationMs,
  showElapsed = true,
  showRemaining = true,
  className = '' 
}: { 
  startTime: Date | string
  estimatedDurationMs?: number
  showElapsed?: boolean
  showRemaining?: boolean
  className?: string 
}) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const start = new Date(startTime).getTime()
    const interval = setInterval(() => {
      setElapsed(Date.now() - start)
    }, 100)

    return () => clearInterval(interval)
  }, [startTime])

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`
    } else {
      return `${seconds}s`
    }
  }

  const remaining = estimatedDurationMs ? Math.max(0, estimatedDurationMs - elapsed) : 0
  const progress = estimatedDurationMs ? Math.min(100, (elapsed / estimatedDurationMs) * 100) : 0

  return (
    <div className={`space-y-2 ${className}`}>
      {estimatedDurationMs && (
        <ProgressBar 
          progress={progress} 
          color="gradient" 
          height="sm"
          showPercentage={false}
        />
      )}
      <div className="flex items-center justify-between text-xs text-gray-600">
        {showElapsed && (
          <div className="flex items-center gap-1">
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            <span>Elapsed: {formatTime(elapsed)}</span>
          </div>
        )}
        {showRemaining && estimatedDurationMs && remaining > 0 && (
          <div className="flex items-center gap-1">
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
            </svg>
            <span>~{formatTime(remaining)} remaining</span>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Composite Agent Activity Indicator
 * Combines multiple progress indicators for agent execution
 */
export function AgentActivityIndicator({ 
  status,
  currentStep,
  totalSteps,
  startTime,
  estimatedDuration,
  className = '' 
}: { 
  status: string
  currentStep?: number
  totalSteps?: number
  startTime?: Date | string
  estimatedDuration?: number
  className?: string 
}) {
  const statusLabels: Record<string, { label: string; color: 'purple' | 'blue' | 'green' }> = {
    initializing: { label: 'Initializing...', color: 'blue' },
    analyzing: { label: 'Analyzing request...', color: 'purple' },
    planning: { label: 'Planning approach...', color: 'purple' },
    executing: { label: 'Executing actions...', color: 'blue' },
    synthesizing: { label: 'Synthesizing response...', color: 'green' },
    completed: { label: 'Completed', color: 'green' }
  }

  const config = statusLabels[status] || { label: status, color: 'purple' as const }

  return (
    <div className={`bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <PulseAnimation color={config.color} />
          <span className="font-medium text-gray-900">{config.label}</span>
        </div>
        {status !== 'completed' && <LoadingSpinner size="sm" color={config.color} />}
      </div>

      {currentStep !== undefined && totalSteps !== undefined && (
        <div className="mb-3">
          <StepCounter 
            currentStep={currentStep} 
            totalSteps={totalSteps}
            showLabels={false}
            size="sm"
          />
        </div>
      )}

      {startTime && (
        <EstimatedTime 
          startTime={startTime}
          estimatedDurationMs={estimatedDuration}
          showElapsed={true}
          showRemaining={!!estimatedDuration}
        />
      )}
    </div>
  )
}

/**
 * Simple typing indicator (for minimal UI)
 */
export function TypingIndicator({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 text-gray-600 ${className}`}>
      <PulseAnimation size="sm" color="purple" />
      <span className="text-sm">AI is typing...</span>
    </div>
  )
}
