/**
 * Create Automation Page
 * 
 * TASK-351: Create automation creation page
 * TASK-352: Create workflow step editor
 * TASK-353: Add trigger selection UI
 * TASK-354: Add schedule configuration UI
 * TASK-355: Create action selector
 * TASK-356: Add condition builder
 * TASK-357: Create workflow preview
 * TASK-358: Add workflow validation
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  TriggerType, 
  WorkflowStep,
  CreateAutomationRequest,
  TriggerConfig
} from '@/types/automation'
import WorkflowEditor from '@/components/automations/WorkflowEditor'
import TriggerSelector from '@/components/automations/TriggerSelector'
import ScheduleConfig from '@/components/automations/ScheduleConfig'
import WorkflowPreview from '@/components/automations/WorkflowPreview'

export default function CreateAutomationPage() {
  const router = useRouter()
  const [step, setStep] = useState(1) // 1: Basic Info, 2: Trigger, 3: Workflow, 4: Review
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Basic Info
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  // Trigger Config
  const [triggerType, setTriggerType] = useState<TriggerType>(TriggerType.SCHEDULE)
  const [schedule, setSchedule] = useState('0 9 * * *') // Default: 9 AM daily
  const [timezone, setTimezone] = useState('UTC')
  const [triggerConfig, setTriggerConfig] = useState<TriggerConfig>({})

  // Workflow
  const [workflow, setWorkflow] = useState<WorkflowStep[]>([])

  // Validation
  const [validationErrors, setValidationErrors] = useState<string[]>([])

  // TASK-362: Load template from localStorage if available
  useEffect(() => {
    const templateData = localStorage.getItem('automation_template')
    if (templateData) {
      try {
        const template = JSON.parse(templateData)
        setName(template.name)
        setDescription(template.description || '')
        setTriggerType(template.trigger_type)
        setWorkflow(template.workflow || [])
        
        if (template.config?.schedule) {
          setSchedule(template.config.schedule)
        }
        if (template.config?.timezone) {
          setTimezone(template.config.timezone)
        }
        if (template.config) {
          setTriggerConfig(template.config)
        }

        // Clear template from storage
        localStorage.removeItem('automation_template')
      } catch (err) {
        console.error('Failed to load template:', err)
      }
    }
  }, [])

  const validateStep1 = () => {
    const errors: string[] = []
    if (!name.trim()) errors.push('Name is required')
    if (name.length > 200) errors.push('Name must be less than 200 characters')
    setValidationErrors(errors)
    return errors.length === 0
  }

  const validateStep2 = () => {
    const errors: string[] = []
    if (triggerType === TriggerType.SCHEDULE && !schedule) {
      errors.push('Schedule is required for scheduled automations')
    }
    setValidationErrors(errors)
    return errors.length === 0
  }

  const validateStep3 = () => {
    const errors: string[] = []
    if (workflow.length === 0) {
      errors.push('At least one workflow step is required')
    }
    // Validate each step
    workflow.forEach((step, index) => {
      if (!step.type) {
        errors.push(`Step ${index + 1}: Type is required`)
      }
      if (!step.config || Object.keys(step.config).length === 0) {
        errors.push(`Step ${index + 1}: Configuration is required`)
      }
    })
    setValidationErrors(errors)
    return errors.length === 0
  }

  const handleNext = () => {
    if (step === 1 && !validateStep1()) return
    if (step === 2 && !validateStep2()) return
    if (step === 3 && !validateStep3()) return
    setStep(step + 1)
    setValidationErrors([])
  }

  const handleBack = () => {
    setStep(step - 1)
    setValidationErrors([])
  }

  const handleCreate = async () => {
    if (!validateStep3()) return

    try {
      setLoading(true)
      setError(null)

      const payload: CreateAutomationRequest = {
        name,
        description: description || undefined,
        workflow: { steps: workflow },
        trigger_type: triggerType,
        schedule: triggerType === TriggerType.SCHEDULE ? schedule : undefined,
        trigger_config: Object.keys(triggerConfig).length > 0 ? triggerConfig : undefined,
        timezone,
        enabled: true
      }

      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/automations`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create automation')
      }

      const automation = await response.json()
      router.push(`/automations/${automation.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Create Automation
          </h1>
          <p className="text-gray-600">
            Build automated workflows in a few simple steps
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[
              { num: 1, label: 'Basic Info' },
              { num: 2, label: 'Trigger' },
              { num: 3, label: 'Workflow' },
              { num: 4, label: 'Review' }
            ].map((s, idx) => (
              <div key={s.num} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    step >= s.num
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {s.num}
                  </div>
                  <div className="text-sm mt-2 font-medium text-gray-700">
                    {s.label}
                  </div>
                </div>
                {idx < 3 && (
                  <div className={`h-1 flex-1 mx-4 ${
                    step > s.num ? 'bg-purple-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg mb-6">
            <div className="font-medium mb-2">Please fix the following errors:</div>
            <ul className="list-disc list-inside space-y-1">
              {validationErrors.map((err, idx) => (
                <li key={idx} className="text-sm">{err}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Step Content */}
        <div className="bg-white rounded-xl shadow-sm p-8">
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Daily Report Automation"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  maxLength={200}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What does this automation do?"
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
          )}

          {/* Step 2: Trigger - TASK-353, 354 */}
          {step === 2 && (
            <div className="space-y-6">
              <TriggerSelector
                triggerType={triggerType}
                onTriggerTypeChange={setTriggerType}
              />

              {triggerType === TriggerType.SCHEDULE && (
                <ScheduleConfig
                  schedule={schedule}
                  timezone={timezone}
                  onScheduleChange={setSchedule}
                  onTimezoneChange={setTimezone}
                />
              )}

              {triggerType === TriggerType.WEBHOOK && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="font-medium text-blue-900 mb-2">Webhook Configuration</div>
                  <p className="text-sm text-blue-700 mb-4">
                    After creating the automation, you'll receive a webhook URL to trigger this automation.
                  </p>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Authentication Type
                    </label>
                    <select
                      value={triggerConfig.auth_type || 'none'}
                      onChange={(e) => setTriggerConfig({
                        ...triggerConfig,
                        auth_type: e.target.value as 'none' | 'signature' | 'api_key'
                      })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="none">No Authentication</option>
                      <option value="signature">HMAC Signature</option>
                      <option value="api_key">API Key</option>
                    </select>
                  </div>
                </div>
              )}

              {triggerType === TriggerType.EVENT && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <div className="font-medium text-purple-900 mb-2">Event Configuration</div>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Event Type
                      </label>
                      <input
                        type="text"
                        placeholder="e.g., agent.completed"
                        value={triggerConfig.event_type || ''}
                        onChange={(e) => setTriggerConfig({
                          ...triggerConfig,
                          event_type: e.target.value
                        })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Workflow - TASK-352, 355, 356 */}
          {step === 3 && (
            <WorkflowEditor
              workflow={workflow}
              onChange={setWorkflow}
            />
          )}

          {/* Step 4: Review - TASK-357 */}
          {step === 4 && (
            <WorkflowPreview
              name={name}
              description={description}
              triggerType={triggerType}
              schedule={schedule}
              timezone={timezone}
              workflow={workflow}
            />
          )}
        </div>

        {/* Navigation */}
        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={() => router.push('/automations')}
            className="px-6 py-3 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>

          <div className="flex gap-4">
            {step > 1 && (
              <button
                onClick={handleBack}
                className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Back
              </button>
            )}

            {step < 4 ? (
              <button
                onClick={handleNext}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleCreate}
                disabled={loading}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating...' : 'Create Automation'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
