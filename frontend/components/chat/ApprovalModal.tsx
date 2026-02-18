/**
 * Approval Modal Component
 * 
 * Modal dialog for requesting user approval before executing sensitive
 * agent actions. Shows action preview, approve/reject buttons, and
 * handles timeout scenarios.
 * 
 * TASK-289 to TASK-293: Approval prompt components
 */

'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export interface ApprovalRequest {
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

export interface ApprovalResponse {
  approval_id: string
  approved: boolean
  user_note?: string
}

interface ApprovalModalProps {
  request: ApprovalRequest
  onApprove: (response: ApprovalResponse) => void
  onReject: (response: ApprovalResponse) => void
  onTimeout?: () => void
}

/**
 * Risk level indicator
 */
function RiskBadge({ level }: { level: ApprovalRequest['risk_level'] }) {
  const config = {
    low: { bg: 'bg-green-100', text: 'text-green-800', icon: '✓', label: 'Low Risk' },
    medium: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '⚠', label: 'Medium Risk' },
    high: { bg: 'bg-red-100', text: 'text-red-800', icon: '⚠', label: 'High Risk' }
  }

  const { bg, text, icon, label } = config[level]

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${bg} ${text}`}>
      <span>{icon}</span>
      <span>{label}</span>
    </span>
  )
}

/**
 * Countdown timer
 */
function CountdownTimer({ 
  timeoutMs, 
  startTime,
  onTimeout 
}: { 
  timeoutMs: number
  startTime: Date
  onTimeout: () => void 
}) {
  const [remaining, setRemaining] = useState(timeoutMs)

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime.getTime()
      const left = Math.max(0, timeoutMs - elapsed)
      setRemaining(left)

      if (left === 0) {
        clearInterval(interval)
        onTimeout()
      }
    }, 100)

    return () => clearInterval(interval)
  }, [timeoutMs, startTime, onTimeout])

  const seconds = Math.ceil(remaining / 1000)
  const progress = (remaining / timeoutMs) * 100

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">Time to respond:</span>
        <span className={`font-semibold ${
          seconds <= 5 ? 'text-red-600' : seconds <= 10 ? 'text-yellow-600' : 'text-gray-900'
        }`}>
          {seconds}s
        </span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: '100%' }}
          animate={{ width: `${progress}%` }}
          className={`h-full rounded-full transition-colors ${
            seconds <= 5 ? 'bg-red-600' : seconds <= 10 ? 'bg-yellow-600' : 'bg-green-600'
          }`}
        />
      </div>
    </div>
  )
}

/**
 * Approval Modal
 * TASK-289: Create approval modal component
 * TASK-290: Show action preview before execution
 * TASK-291: Add approve/reject buttons
 * TASK-292: Send approval response to backend
 * TASK-293: Handle approval timeout
 */
export default function ApprovalModal({ 
  request, 
  onApprove, 
  onReject,
  onTimeout 
}: ApprovalModalProps) {
  const [userNote, setUserNote] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [startTime] = useState(new Date(request.timestamp))

  const handleApprove = () => {
    setIsProcessing(true)
    onApprove({
      approval_id: request.id,
      approved: true,
      user_note: userNote || undefined
    })
  }

  const handleReject = () => {
    setIsProcessing(true)
    onReject({
      approval_id: request.id,
      approved: false,
      user_note: userNote || undefined
    })
  }

  const handleTimeout = () => {
    onTimeout?.()
    // Auto-reject on timeout
    onReject({
      approval_id: request.id,
      approved: false,
      user_note: 'Approval timeout'
    })
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ duration: 0.2 }}
          className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white bg-opacity-20 rounded-lg">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold">Approval Required</h2>
                  <p className="text-sm text-purple-100">Please review and approve this action</p>
                </div>
              </div>
              <RiskBadge level={request.risk_level} />
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
            {/* Countdown timer */}
            <CountdownTimer 
              timeoutMs={request.timeout_ms}
              startTime={startTime}
              onTimeout={handleTimeout}
            />

            {/* Action preview */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900">Action Preview</h3>
              </div>
              <div className="p-4 space-y-3">
                {/* Action type */}
                <div>
                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    Action Type
                  </label>
                  <p className="text-sm font-medium text-gray-900 mt-1">
                    {request.action_type}
                  </p>
                </div>

                {/* Action name */}
                <div>
                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    Action
                  </label>
                  <p className="text-sm font-medium text-gray-900 mt-1">
                    {request.action_name}
                  </p>
                </div>

                {/* Description */}
                <div>
                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    Description
                  </label>
                  <p className="text-sm text-gray-700 mt-1 leading-relaxed">
                    {request.description}
                  </p>
                </div>

                {/* Parameters */}
                {Object.keys(request.parameters).length > 0 && (
                  <div>
                    <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Parameters
                    </label>
                    <div className="mt-1 bg-gray-100 rounded-lg p-3">
                      <pre className="text-xs text-gray-800 overflow-x-auto">
                        {JSON.stringify(request.parameters, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Estimated duration */}
                {request.estimated_duration_ms && (
                  <div>
                    <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Estimated Duration
                    </label>
                    <p className="text-sm text-gray-700 mt-1">
                      ~{(request.estimated_duration_ms / 1000).toFixed(1)} seconds
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Risk warning */}
            {request.risk_level !== 'low' && (
              <div className={`border rounded-lg p-4 ${
                request.risk_level === 'high' 
                  ? 'bg-red-50 border-red-200' 
                  : 'bg-yellow-50 border-yellow-200'
              }`}>
                <div className="flex items-start gap-3">
                  <svg 
                    className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
                      request.risk_level === 'high' ? 'text-red-600' : 'text-yellow-600'
                    }`}
                    fill="currentColor" 
                    viewBox="0 0 20 20"
                  >
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <h4 className={`font-semibold ${
                      request.risk_level === 'high' ? 'text-red-900' : 'text-yellow-900'
                    }`}>
                      {request.risk_level === 'high' ? 'High Risk Action' : 'Medium Risk Action'}
                    </h4>
                    <p className={`text-sm mt-1 ${
                      request.risk_level === 'high' ? 'text-red-800' : 'text-yellow-800'
                    }`}>
                      {request.risk_level === 'high' 
                        ? 'This action may make significant changes or access sensitive data. Please review carefully before approving.'
                        : 'This action requires your approval. Please review the details before proceeding.'
                      }
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Optional note */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Add a note (optional)
              </label>
              <textarea
                value={userNote}
                onChange={(e) => setUserNote(e.target.value)}
                placeholder="Add any notes or conditions..."
                rows={3}
                disabled={isProcessing}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          {/* Footer with action buttons */}
          <div className="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3 border-t border-gray-200">
            <button
              onClick={handleReject}
              disabled={isProcessing}
              className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              Reject
            </button>
            <button
              onClick={handleApprove}
              disabled={isProcessing}
              className="px-6 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isProcessing ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="h-4 w-4 border-2 border-white border-t-transparent rounded-full"
                  />
                  Processing...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Approve & Continue
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

/**
 * Compact approval notification (for non-blocking approval requests)
 */
export function ApprovalNotification({ 
  request,
  onApprove,
  onReject,
  onViewDetails 
}: {
  request: ApprovalRequest
  onApprove: () => void
  onReject: () => void
  onViewDetails?: () => void
}) {
  const [timeRemaining, setTimeRemaining] = useState(request.timeout_ms)

  useEffect(() => {
    const start = new Date(request.timestamp).getTime()
    const interval = setInterval(() => {
      const elapsed = Date.now() - start
      const remaining = Math.max(0, request.timeout_ms - elapsed)
      setTimeRemaining(remaining)
    }, 100)

    return () => clearInterval(interval)
  }, [request.timeout_ms, request.timestamp])

  const seconds = Math.ceil(timeRemaining / 1000)

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="bg-white border-2 border-purple-300 rounded-lg shadow-lg p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          <div className="p-2 bg-purple-100 rounded-lg">
            <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900">{request.action_name}</h4>
            <p className="text-sm text-gray-600 mt-1">{request.description}</p>
            <div className="flex items-center gap-2 mt-2">
              <RiskBadge level={request.risk_level} />
              <span className="text-xs text-gray-500">{seconds}s remaining</span>
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <button
            onClick={onApprove}
            className="px-4 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 transition-colors"
          >
            Approve
          </button>
          <button
            onClick={onReject}
            className="px-4 py-1.5 border border-gray-300 text-gray-700 rounded text-sm font-medium hover:bg-gray-100 transition-colors"
          >
            Reject
          </button>
          {onViewDetails && (
            <button
              onClick={onViewDetails}
              className="text-xs text-purple-600 hover:underline"
            >
              Details
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}
