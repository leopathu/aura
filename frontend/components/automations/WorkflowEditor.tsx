/**
 * Workflow Editor Component
 * 
 * TASK-352: Create workflow step editor
 * TASK-355: Create action selector
 * TASK-356: Add condition builder
 */

'use client'

import { useState } from 'react'
import { WorkflowStep } from '@/types/automation'
import StepEditor from './StepEditor'

interface WorkflowEditorProps {
  workflow: WorkflowStep[]
  onChange: (workflow: WorkflowStep[]) => void
}

export default function WorkflowEditor({ workflow, onChange }: WorkflowEditorProps) {
  const [editingStep, setEditingStep] = useState<number | null>(null)

  const addStep = (type: WorkflowStep['type']) => {
    const newStep: WorkflowStep = {
      type,
      config: {}
    }
    onChange([...workflow, newStep])
    setEditingStep(workflow.length)
  }

  const updateStep = (index: number, step: WorkflowStep) => {
    const updated = [...workflow]
    updated[index] = step
    onChange(updated)
  }

  const deleteStep = (index: number) => {
    const updated = workflow.filter((_, i) => i !== index)
    onChange(updated)
    setEditingStep(null)
  }

  const moveStep = (index: number, direction: 'up' | 'down') => {
    if (direction === 'up' && index === 0) return
    if (direction === 'down' && index === workflow.length - 1) return

    const updated = [...workflow]
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    ;[updated[index], updated[targetIndex]] = [updated[targetIndex], updated[index]]
    onChange(updated)
  }

  const getStepIcon = (type: WorkflowStep['type']) => {
    switch (type) {
      case 'agent_task': return '🤖'
      case 'http_request': return '🌐'
      case 'condition': return '🔀'
      case 'delay': return '⏱️'
      case 'set_variable': return '💾'
      default: return '📋'
    }
  }

  const getStepLabel = (type: WorkflowStep['type']) => {
    switch (type) {
      case 'agent_task': return 'Agent Task'
      case 'http_request': return 'HTTP Request'
      case 'condition': return 'Condition'
      case 'delay': return 'Delay'
      case 'set_variable': return 'Set Variable'
      default: return type
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Workflow Steps
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Add and configure steps to build your automation workflow
        </p>
      </div>

      {/* Step List */}
      <div className="space-y-4">
        {workflow.map((step, index) => (
          <div
            key={index}
            className={`border rounded-lg ${
              editingStep === index
                ? 'border-purple-500 shadow-md'
                : 'border-gray-300'
            }`}
          >
            {/* Step Header */}
            <div
              className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
              onClick={() => setEditingStep(editingStep === index ? null : index)}
            >
              <div className="flex items-center gap-3">
                <div className="text-2xl">{getStepIcon(step.type)}</div>
                <div>
                  <div className="font-medium text-gray-900">
                    Step {index + 1}: {getStepLabel(step.type)}
                  </div>
                  {step.config.prompt && (
                    <div className="text-sm text-gray-600 mt-1">
                      {step.config.prompt.substring(0, 60)}
                      {step.config.prompt.length > 60 ? '...' : ''}
                    </div>
                  )}
                  {step.config.url && (
                    <div className="text-sm text-gray-600 mt-1">
                      {step.config.method || 'GET'} {step.config.url}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {/* Move Buttons */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    moveStep(index, 'up')
                  }}
                  disabled={index === 0}
                  className="p-2 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Move up"
                >
                  ↑
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    moveStep(index, 'down')
                  }}
                  disabled={index === workflow.length - 1}
                  className="p-2 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Move down"
                >
                  ↓
                </button>

                {/* Delete Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteStep(index)
                  }}
                  className="p-2 text-red-600 hover:bg-red-50 rounded"
                  title="Delete"
                >
                  🗑️
                </button>

                {/* Expand/Collapse */}
                <div className="text-gray-400 ml-2">
                  {editingStep === index ? '▼' : '▶'}
                </div>
              </div>
            </div>

            {/* Step Editor */}
            {editingStep === index && (
              <div className="border-t border-gray-200 p-4 bg-gray-50">
                <StepEditor
                  step={step}
                  onChange={(updated) => updateStep(index, updated)}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add Step Buttons - TASK-355 */}
      <div>
        <div className="text-sm font-medium text-gray-700 mb-3">Add Step:</div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <button
            onClick={() => addStep('agent_task')}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors text-left"
          >
            <div className="text-2xl mb-2">🤖</div>
            <div className="font-medium text-gray-900">Agent Task</div>
            <div className="text-xs text-gray-600">Run an AI agent</div>
          </button>

          <button
            onClick={() => addStep('http_request')}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors text-left"
          >
            <div className="text-2xl mb-2">🌐</div>
            <div className="font-medium text-gray-900">HTTP Request</div>
            <div className="text-xs text-gray-600">Call an API</div>
          </button>

          <button
            onClick={() => addStep('condition')}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors text-left"
          >
            <div className="text-2xl mb-2">🔀</div>
            <div className="font-medium text-gray-900">Condition</div>
            <div className="text-xs text-gray-600">If/then logic</div>
          </button>

          <button
            onClick={() => addStep('delay')}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors text-left"
          >
            <div className="text-2xl mb-2">⏱️</div>
            <div className="font-medium text-gray-900">Delay</div>
            <div className="text-xs text-gray-600">Wait for time</div>
          </button>

          <button
            onClick={() => addStep('set_variable')}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors text-left"
          >
            <div className="text-2xl mb-2">💾</div>
            <div className="font-medium text-gray-900">Set Variable</div>
            <div className="text-xs text-gray-600">Store a value</div>
          </button>
        </div>
      </div>

      {/* Help Text */}
      {workflow.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-4">👆</div>
          <div className="text-lg font-medium mb-2">No steps yet</div>
          <div className="text-sm">
            Add your first step to start building the workflow
          </div>
        </div>
      )}
    </div>
  )
}
