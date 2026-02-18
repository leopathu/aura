/**
 * Automation Card Component
 * 
 * TASK-347: Create automation card component
 * TASK-348: Add enable/disable toggle
 * TASK-349: Show last run status
 * TASK-350: Add automation deletion
 */

'use client'

import { Automation, AutomationStatus, TriggerType, RunStatus } from '@/types/automation'
import { formatDistanceToNow } from 'date-fns'

interface AutomationCardProps {
  automation: Automation
  onToggle: () => void
  onDelete: () => void
  onClick: () => void
}

export default function AutomationCard({ 
  automation, 
  onToggle, 
  onDelete, 
  onClick 
}: AutomationCardProps) {
  const getStatusColor = (status: AutomationStatus) => {
    switch (status) {
      case AutomationStatus.ACTIVE:
        return 'bg-green-100 text-green-700'
      case AutomationStatus.PAUSED:
        return 'bg-yellow-100 text-yellow-700'
      case AutomationStatus.DRAFT:
        return 'bg-gray-100 text-gray-700'
      case AutomationStatus.ARCHIVED:
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getRunStatusColor = (status?: RunStatus) => {
    if (!status) return 'bg-gray-100 text-gray-700'
    
    switch (status) {
      case RunStatus.SUCCESS:
        return 'bg-green-100 text-green-700'
      case RunStatus.FAILED:
        return 'bg-red-100 text-red-700'
      case RunStatus.RUNNING:
        return 'bg-blue-100 text-blue-700'
      case RunStatus.PENDING:
        return 'bg-yellow-100 text-yellow-700'
      case RunStatus.CANCELLED:
        return 'bg-gray-100 text-gray-700'
      case RunStatus.TIMEOUT:
        return 'bg-orange-100 text-orange-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getTriggerIcon = (type: TriggerType) => {
    switch (type) {
      case TriggerType.SCHEDULE:
        return '⏰'
      case TriggerType.WEBHOOK:
        return '🔗'
      case TriggerType.EVENT:
        return '⚡'
      case TriggerType.MANUAL:
        return '👆'
      default:
        return '📋'
    }
  }

  const getTriggerLabel = (type: TriggerType) => {
    switch (type) {
      case TriggerType.SCHEDULE:
        return automation.schedule || 'Scheduled'
      case TriggerType.WEBHOOK:
        return 'Webhook'
      case TriggerType.EVENT:
        return 'Event-based'
      case TriggerType.MANUAL:
        return 'Manual'
      default:
        return type
    }
  }

  const successRate = automation.run_count > 0
    ? Math.round((automation.success_count / automation.run_count) * 100)
    : 0

  return (
    <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow border border-gray-200">
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div 
            className="flex-1 cursor-pointer" 
            onClick={onClick}
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-1 hover:text-purple-600 transition-colors">
              {automation.name}
            </h3>
            {automation.description && (
              <p className="text-sm text-gray-600 line-clamp-2">
                {automation.description}
              </p>
            )}
          </div>

          {/* TASK-348: Enable/Disable Toggle */}
          <div className="ml-4">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onToggle()
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                automation.status === AutomationStatus.ACTIVE
                  ? 'bg-green-600'
                  : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  automation.status === AutomationStatus.ACTIVE
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Status and Trigger */}
        <div className="flex items-center gap-2 mb-4">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(automation.status)}`}>
            {automation.status}
          </span>
          <span className="text-xs text-gray-500">
            {getTriggerIcon(automation.trigger_type)} {getTriggerLabel(automation.trigger_type)}
          </span>
        </div>

        {/* TASK-349: Last Run Status */}
        {automation.last_run_at && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Last run:</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRunStatusColor(automation.last_run_status)}`}>
                {automation.last_run_status || 'Unknown'}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {formatDistanceToNow(new Date(automation.last_run_at), { addSuffix: true })}
            </div>
          </div>
        )}

        {/* Next Run (for scheduled automations) */}
        {automation.trigger_type === TriggerType.SCHEDULE && automation.next_run_at && automation.status === AutomationStatus.ACTIVE && (
          <div className="text-sm text-gray-600 mb-4">
            <span className="font-medium">Next run:</span>{' '}
            {formatDistanceToNow(new Date(automation.next_run_at), { addSuffix: true })}
          </div>
        )}

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <div className="text-2xl font-bold text-gray-900">{automation.run_count}</div>
            <div className="text-xs text-gray-600">Total Runs</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">{automation.success_count}</div>
            <div className="text-xs text-gray-600">Success</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">{automation.failure_count}</div>
            <div className="text-xs text-gray-600">Failed</div>
          </div>
        </div>

        {/* Success Rate */}
        {automation.run_count > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">Success Rate</span>
              <span className="font-medium text-gray-900">{successRate}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-600 h-2 rounded-full transition-all" 
                style={{ width: `${successRate}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="border-t border-gray-200 px-6 py-3 flex items-center justify-between bg-gray-50 rounded-b-xl">
        <button
          onClick={(e) => {
            e.stopPropagation()
            window.location.href = `/automations/${automation.id}/runs`
          }}
          className="text-sm text-purple-600 hover:text-purple-700 font-medium"
        >
          View Runs
        </button>

        {/* TASK-350: Delete Button */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="text-sm text-red-600 hover:text-red-700 font-medium"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
