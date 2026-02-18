/**
 * Workflow Preview Component
 * 
 * TASK-357: Create workflow preview
 */

'use client'

import { TriggerType, WorkflowStep } from '@/types/automation'

interface WorkflowPreviewProps {
  name: string
  description?: string
  triggerType: TriggerType
  schedule?: string
  timezone: string
  workflow: WorkflowStep[]
}

export default function WorkflowPreview({
  name,
  description,
  triggerType,
  schedule,
  timezone,
  workflow
}: WorkflowPreviewProps) {
  const getTriggerLabel = () => {
    switch (triggerType) {
      case TriggerType.SCHEDULE:
        return `Scheduled: ${schedule} (${timezone})`
      case TriggerType.WEBHOOK:
        return 'Webhook Trigger'
      case TriggerType.EVENT:
        return 'Event-based Trigger'
      case TriggerType.MANUAL:
        return 'Manual Trigger Only'
      default:
        return triggerType
    }
  }

  const getStepLabel = (step: WorkflowStep) => {
    switch (step.type) {
      case 'agent_task':
        return `Agent Task: ${step.config.prompt?.substring(0, 50)}...`
      case 'http_request':
        return `HTTP ${step.config.method} ${step.config.url}`
      case 'condition':
        return `If ${step.config.field} ${step.config.operator} ${step.config.value}`
      case 'delay':
        return `Wait ${step.config.seconds} seconds`
      case 'set_variable':
        return `Set ${step.config.name} = ${step.config.value}`
      default:
        return step.type
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Review Your Automation
        </h3>
        <p className="text-sm text-gray-600">
          Please review the automation configuration before creating
        </p>
      </div>

      {/* Basic Info */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-3">Basic Information</h4>
        <div className="space-y-2">
          <div>
            <span className="text-sm text-gray-600">Name:</span>
            <span className="ml-2 text-sm font-medium text-gray-900">{name}</span>
          </div>
          {description && (
            <div>
              <span className="text-sm text-gray-600">Description:</span>
              <span className="ml-2 text-sm text-gray-700">{description}</span>
            </div>
          )}
        </div>
      </div>

      {/* Trigger */}
      <div className="bg-purple-50 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-3">Trigger</h4>
        <div className="text-sm text-gray-700">{getTriggerLabel()}</div>
      </div>

      {/* Workflow */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Workflow ({workflow.length} steps)</h4>
        <div className="space-y-3">
          {workflow.map((step, index) => (
            <div key={index} className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-medium">
                {index + 1}
              </div>
              <div className="flex-1 bg-white rounded-lg p-3">
                <div className="text-sm font-medium text-gray-900">{step.type}</div>
                <div className="text-xs text-gray-600 mt-1">{getStepLabel(step)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Warning if no steps */}
      {workflow.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg">
          ⚠️ No workflow steps defined. Please go back and add at least one step.
        </div>
      )}
    </div>
  )
}
