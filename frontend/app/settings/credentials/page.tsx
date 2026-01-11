'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'

interface Credential {
  id: string
  credential_type: string
  label: string
  is_active: boolean
  created_at: string
}

const CREDENTIAL_TYPES = [
  { value: 'openai', label: 'OpenAI', icon: '🤖' },
  { value: 'anthropic', label: 'Anthropic (Claude)', icon: '🧠' },
  { value: 'gemini', label: 'Google Gemini', icon: '✨' },
  { value: 'custom', label: 'Custom LLM', icon: '🔧' },
]

export default function CredentialsPage() {
  const router = useRouter()
  const { currentOrg } = useAuthStore()
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    credential_type: 'openai',
    label: '',
    api_key: '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (currentOrg) {
      loadCredentials()
    }
  }, [currentOrg])

  const loadCredentials = async () => {
    if (!currentOrg) return
    
    try {
      const response = await api.get(`/organizations/${currentOrg.id}/credentials/`)
      setCredentials(response.data)
    } catch (err) {
      console.error('Failed to load credentials:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!currentOrg) return

    setError('')
    setSaving(true)

    try {
      await api.post(`/organizations/${currentOrg.id}/credentials/`, formData)
      await loadCredentials()
      setShowForm(false)
      setFormData({ credential_type: 'openai', label: '', api_key: '' })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save credential')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!currentOrg) return
    if (!confirm('Are you sure you want to delete this credential?')) return

    try {
      await api.delete(`/organizations/${currentOrg.id}/credentials/${id}`)
      await loadCredentials()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete credential')
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
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-gray-600 hover:text-gray-800 mb-4 text-sm"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900">LLM API Credentials</h1>
          <p className="text-gray-600 mt-2">
            Bring Your Own Key - Add your LLM provider API keys
          </p>
        </div>

        {/* Add New Credential Form */}
        {showForm ? (
          <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Add New Credential</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Provider *
                </label>
                <select
                  value={formData.credential_type}
                  onChange={(e) => setFormData({ ...formData, credential_type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                >
                  {CREDENTIAL_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.icon} {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Label (Optional)
                </label>
                <input
                  type="text"
                  value={formData.label}
                  onChange={(e) => setFormData({ ...formData, label: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                  placeholder="e.g., Production Key, Test Key"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key *
                </label>
                <input
                  type="password"
                  required
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                  placeholder="sk-..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  🔒 Your API key is encrypted and never shown again
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Credential'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false)
                    setError('')
                    setFormData({ credential_type: 'openai', label: '', api_key: '' })
                  }}
                  className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        ) : (
          <button
            onClick={() => setShowForm(true)}
            className="mb-6 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
          >
            + Add API Key
          </button>
        )}

        {/* Credentials List */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading credentials...</p>
            </div>
          ) : credentials.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">🔑</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No API Keys Yet</h3>
              <p className="text-gray-600">
                Add your LLM provider API keys to start using Aura agents
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {credentials.map((cred) => {
                const type = CREDENTIAL_TYPES.find(t => t.value === cred.credential_type)
                return (
                  <div key={cred.id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-3xl">{type?.icon || '🔧'}</div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {cred.label || type?.label || cred.credential_type}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {type?.label} • Added {new Date(cred.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          cred.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {cred.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <button
                          onClick={() => handleDelete(cred.id)}
                          className="text-red-600 hover:text-red-700 font-medium text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 p-6 rounded-xl">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">💡 About API Keys</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>• Your API keys are encrypted using AES-256 encryption</li>
            <li>• Keys are never displayed after saving for security</li>
            <li>• Each agent can use different API keys for different models</li>
            <li>• You only pay for what you use - no Aura markup on API costs</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
