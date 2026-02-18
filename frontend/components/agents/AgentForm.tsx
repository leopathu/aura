'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

interface AgentFormProps {
  initialData?: {
    name: string
    description: string
    system_prompt: string
    config: Record<string, any>
  }
  onSubmit: (data: {
    name: string
    description: string
    system_prompt: string
    config: Record<string, any>
  }) => void
  isSubmitting: boolean
}

export default function AgentForm({ initialData, onSubmit, isSubmitting }: AgentFormProps) {
  const router = useRouter()
  
  const [name, setName] = useState(initialData?.name || '')
  const [description, setDescription] = useState(initialData?.description || '')
  const [systemPrompt, setSystemPrompt] = useState(
    initialData?.system_prompt || 'You are a helpful AI assistant.'
  )
  const [configJson, setConfigJson] = useState(
    JSON.stringify(initialData?.config || {}, null, 2)
  )
  const [configError, setConfigError] = useState<string | null>(null)

  const handleConfigChange = (value: string) => {
    setConfigJson(value)
    setConfigError(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validate config JSON
    let config: Record<string, any>
    try {
      config = JSON.parse(configJson)
    } catch (error) {
      setConfigError('Invalid JSON format')
      return
    }

    onSubmit({
      name: name.trim(),
      description: description.trim(),
      system_prompt: systemPrompt.trim(),
      config
    })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {/* Name */}
      <div className="mb-6">
        <label htmlFor="name" className="block text-sm font-medium text-gray-900 mb-2">
          Agent Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          maxLength={255}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent"
          placeholder="My AI Assistant"
        />
      </div>

      {/* Description */}
      <div className="mb-6">
        <label htmlFor="description" className="block text-sm font-medium text-gray-900 mb-2">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent resize-none"
          placeholder="Describe what this agent does..."
        />
      </div>

      {/* System Prompt */}
      <div className="mb-6">
        <label htmlFor="systemPrompt" className="block text-sm font-medium text-gray-900 mb-2">
          System Prompt <span className="text-red-500">*</span>
        </label>
        <textarea
          id="systemPrompt"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          required
          rows={6}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent resize-none font-mono text-sm"
          placeholder="You are a helpful AI assistant that..."
        />
        <p className="mt-2 text-xs text-gray-500">
          Define how the agent should behave and respond to users
        </p>
      </div>

      {/* Config JSON */}
      <div className="mb-6">
        <label htmlFor="config" className="block text-sm font-medium text-gray-900 mb-2">
          Configuration (JSON)
        </label>
        <textarea
          id="config"
          value={configJson}
          onChange={(e) => handleConfigChange(e.target.value)}
          rows={8}
          className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent resize-none font-mono text-sm ${
            configError ? 'border-red-300' : 'border-gray-300'
          }`}
          placeholder='{\n  "temperature": 0.7,\n  "max_tokens": 2000\n}'
        />
        {configError && (
          <p className="mt-2 text-sm text-red-600">{configError}</p>
        )}
        <p className="mt-2 text-xs text-gray-500">
          Optional configuration parameters in JSON format
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-4 border-t border-gray-200">
        <button
          type="submit"
          disabled={isSubmitting || !name.trim() || !systemPrompt.trim()}
          className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Saving...
            </span>
          ) : initialData ? (
            'Update Agent'
          ) : (
            'Create Agent'
          )}
        </button>
        
        <button
          type="button"
          onClick={() => router.back()}
          disabled={isSubmitting}
          className="px-6 py-2.5 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:cursor-not-allowed text-gray-900 rounded-lg transition-colors font-medium"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
