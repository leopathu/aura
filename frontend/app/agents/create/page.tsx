'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'

export default function CreateAgentPage() {
  const router = useRouter()
  const { currentOrg } = useAuthStore()
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: '',
    config: {},
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!currentOrg) {
      setError('No organization selected')
      return
    }

    setError('')
    setLoading(true)

    try {
      await api.post(`/organizations/${currentOrg.id}/agents/`, formData)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create agent')
    } finally {
      setLoading(false)
    }
  }

  if (!currentOrg) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-blue-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">No Organization Selected</h1>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-purple-600 hover:text-purple-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Create AI Agent</h1>
            <p className="text-gray-600 mt-2">Set up your intelligent assistant</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Agent Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                placeholder="Marketing Assistant"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                placeholder="Helps with marketing tasks and content creation"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                System Prompt
              </label>
              <textarea
                value={formData.system_prompt}
                onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                placeholder="You are a helpful marketing assistant. You help with content creation, social media strategy, and campaign planning."
                rows={6}
              />
              <p className="text-xs text-gray-500 mt-1">
                Define the agent's personality, expertise, and behavior
              </p>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">💡 Tips</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Be specific about the agent's role and capabilities</li>
                <li>• Include any constraints or guidelines for behavior</li>
                <li>• You can add app integrations and LLM credentials later</li>
              </ul>
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating...' : 'Create Agent'}
              </button>

              <button
                type="button"
                onClick={() => router.push('/dashboard')}
                className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
