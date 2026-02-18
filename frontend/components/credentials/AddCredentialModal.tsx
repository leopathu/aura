'use client'

import { useState } from 'react'

interface AddCredentialModalProps {
  onClose: () => void
  onSubmit: (data: { credential_type: string; api_key: string; label: string }) => void
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', placeholder: 'sk-...' },
  { value: 'anthropic', label: 'Anthropic', placeholder: 'sk-ant-...' },
  { value: 'google_gemini', label: 'Google Gemini', placeholder: 'AIza...' },
  { value: 'cohere', label: 'Cohere', placeholder: 'co-...' },
  { value: 'huggingface', label: 'Hugging Face', placeholder: 'hf_...' }
]

export default function AddCredentialModal({ onClose, onSubmit }: AddCredentialModalProps) {
  const [credentialType, setCredentialType] = useState('openai')
  const [apiKey, setApiKey] = useState('')
  const [label, setLabel] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await onSubmit({
        credential_type: credentialType,
        api_key: apiKey.trim(),
        label: label.trim()
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const selectedProvider = PROVIDERS.find((p) => p.value === credentialType)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Add LLM Credential</h2>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Provider Selection */}
          <div className="mb-4">
            <label htmlFor="provider" className="block text-sm font-medium text-gray-900 mb-2">
              Provider <span className="text-red-500">*</span>
            </label>
            <select
              id="provider"
              value={credentialType}
              onChange={(e) => setCredentialType(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent"
            >
              {PROVIDERS.map((provider) => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </div>

          {/* API Key */}
          <div className="mb-4">
            <label htmlFor="apiKey" className="block text-sm font-medium text-gray-900 mb-2">
              API Key <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              id="apiKey"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={selectedProvider?.placeholder}
              required
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent font-mono text-sm"
            />
            <p className="mt-2 text-xs text-gray-500">
              Your API key will be encrypted before storage
            </p>
          </div>

          {/* Label */}
          <div className="mb-6">
            <label htmlFor="label" className="block text-sm font-medium text-gray-900 mb-2">
              Label (optional)
            </label>
            <input
              type="text"
              id="label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g., Production Key, Testing Key"
              maxLength={255}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={!apiKey.trim() || isSubmitting}
              className="flex-1 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
            >
              {isSubmitting ? 'Adding...' : 'Add Credential'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:cursor-not-allowed text-gray-900 rounded-lg transition-colors font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
