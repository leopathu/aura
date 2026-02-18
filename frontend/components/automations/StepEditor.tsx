/**
 * Step Editor Component
 * 
 * Edits individual workflow step configuration
 */

'use client'

import { WorkflowStep } from '@/types/automation'

interface StepEditorProps {
  step: WorkflowStep
  onChange: (step: WorkflowStep) => void
}

export default function StepEditor({ step, onChange }: StepEditorProps) {
  const updateConfig = (key: string, value: any) => {
    onChange({
      ...step,
      config: {
        ...step.config,
        [key]: value
      }
    })
  }

  if (step.type === 'agent_task') {
    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Prompt *
          </label>
          <textarea
            value={step.config.prompt || ''}
            onChange={(e) => updateConfig('prompt', e.target.value)}
            placeholder="What should the agent do?"
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
          />
          <div className="text-xs text-gray-500 mt-1">
            Use {`{{ variables.name }}`} to insert variables
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Agent ID (optional)
          </label>
          <input
            type="text"
            value={step.config.agent_id || ''}
            onChange={(e) => updateConfig('agent_id', e.target.value)}
            placeholder="Leave empty to use default agent"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
      </div>
    )
  }

  if (step.type === 'http_request') {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-4 gap-4">
          <div className="col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Method *
            </label>
            <select
              value={step.config.method || 'GET'}
              onChange={(e) => updateConfig('method', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
          <div className="col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              URL *
            </label>
            <input
              type="text"
              value={step.config.url || ''}
              onChange={(e) => updateConfig('url', e.target.value)}
              placeholder="https://api.example.com/endpoint"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Headers (JSON)
          </label>
          <textarea
            value={step.config.headers ? JSON.stringify(step.config.headers, null, 2) : ''}
            onChange={(e) => {
              try {
                updateConfig('headers', JSON.parse(e.target.value))
              } catch {
                // Invalid JSON, ignore
              }
            }}
            placeholder='{"Authorization": "Bearer token"}'
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg font-mono text-sm"
          />
        </div>

        {(step.config.method === 'POST' || step.config.method === 'PUT' || step.config.method === 'PATCH') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Body (JSON)
            </label>
            <textarea
              value={step.config.body ? JSON.stringify(step.config.body, null, 2) : ''}
              onChange={(e) => {
                try {
                  updateConfig('body', JSON.parse(e.target.value))
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              placeholder='{"key": "value"}'
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg font-mono text-sm"
            />
          </div>
        )}
      </div>
    )
  }

  if (step.type === 'condition') {
    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Condition
          </label>
          <div className="grid grid-cols-3 gap-2">
            <input
              type="text"
              value={step.config.field || ''}
              onChange={(e) => updateConfig('field', e.target.value)}
              placeholder="Field"
              className="px-4 py-2 border border-gray-300 rounded-lg"
            />
            <select
              value={step.config.operator || 'equals'}
              onChange={(e) => updateConfig('operator', e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="equals">Equals</option>
              <option value="not_equals">Not Equals</option>
              <option value="contains">Contains</option>
              <option value="greater_than">Greater Than</option>
              <option value="less_than">Less Than</option>
            </select>
            <input
              type="text"
              value={step.config.value || ''}
              onChange={(e) => updateConfig('value', e.target.value)}
              placeholder="Value"
              className="px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
          Note: Condition branches (then/else steps) are configured in the workflow JSON for advanced use
        </div>
      </div>
    )
  }

  if (step.type === 'delay') {
    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Delay Duration (seconds) *
          </label>
          <input
            type="number"
            value={step.config.seconds || 0}
            onChange={(e) => updateConfig('seconds', parseInt(e.target.value))}
            min={1}
            placeholder="60"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
      </div>
    )
  }

  if (step.type === 'set_variable') {
    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Variable Name *
          </label>
          <input
            type="text"
            value={step.config.name || ''}
            onChange={(e) => updateConfig('name', e.target.value)}
            placeholder="my_variable"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Value *
          </label>
          <input
            type="text"
            value={step.config.value || ''}
            onChange={(e) => updateConfig('value', e.target.value)}
            placeholder="value or {{ context.field }}"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="text-gray-500">
      Unknown step type: {step.type}
    </div>
  )
}
