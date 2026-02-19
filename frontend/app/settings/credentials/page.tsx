'use client'

import { useState, useEffect } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { useAuthStore } from '@/store/authStore'
import { useOrganizationStore } from '@/store/organizationStore'
import AddCredentialModal from '@/components/credentials/AddCredentialModal'
import EditCredentialModal from '@/components/credentials/EditCredentialModal'
import DeleteCredentialModal from '@/components/credentials/DeleteCredentialModal'

interface Credential {
  id: string
  org_id: string
  credential_type: string
  label: string | null
  is_active: boolean
  masked_key: string
  created_at: string
  updated_at: string
}

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google_gemini: 'Google Gemini',
  cohere: 'Cohere',
  huggingface: 'Hugging Face'
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: 'bg-green-100 text-green-800',
  anthropic: 'bg-orange-100 text-orange-800',
  google_gemini: 'bg-blue-100 text-blue-800',
  cohere: 'bg-purple-100 text-purple-800',
  huggingface: 'bg-yellow-100 text-yellow-800'
}

export default function CredentialsPage() {
  const currentOrganization = useOrganizationStore((state) => state.currentOrganization)
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingCredential, setEditingCredential] = useState<Credential | null>(null)
  const [deletingCredential, setDeletingCredential] = useState<Credential | null>(null)
  const [testingCredential, setTestingCredential] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({})

  useEffect(() => {
    if (currentOrganization) {
      loadCredentials()
    } else {
      setIsLoading(false)
    }
  }, [currentOrganization])

  const loadCredentials = async () => {
    if (!currentOrganization) return

    setIsLoading(true)
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials?org_id=${currentOrganization.id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setCredentials(data)
      }
    } catch (error) {
      console.error('Failed to load credentials:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddCredential = async (data: {
    credential_type: string
    api_key: string
    label: string
  }) => {
    if (!currentOrganization) {
      alert('No organization selected')
      return
    }

    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials?org_id=${currentOrganization.id}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(data)
        }
      )

      if (response.ok) {
        await loadCredentials()
        setShowAddModal(false)
      } else {
        const error = await response.json()
        console.error('API Error:', error)
        alert(error.detail || 'Failed to add credential')
      }
    } catch (error) {
      console.error('Failed to add credential:', error)
      alert('An error occurred while adding the credential')
    }
  }

  const handleUpdateCredential = async (credentialId: string, label: string) => {
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials/${credentialId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ label })
        }
      )

      if (response.ok) {
        loadCredentials()
        setEditingCredential(null)
      } else {
        const error = await response.json()
        alert(error.detail || 'Failed to update credential')
      }
    } catch (error) {
      console.error('Failed to update credential:', error)
      alert('An error occurred while updating the credential')
    }
  }

  const handleDeleteCredential = async (credentialId: string) => {
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials/${credentialId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        setCredentials((prev) => prev.filter((c) => c.id !== credentialId))
        setDeletingCredential(null)
      } else {
        const error = await response.json()
        alert(error.detail || 'Failed to delete credential')
      }
    } catch (error) {
      console.error('Failed to delete credential:', error)
      alert('An error occurred while deleting the credential')
    }
  }

  const handleTestCredential = async (credentialId: string) => {
    setTestingCredential(credentialId)
    setTestResults((prev) => ({ ...prev, [credentialId]: { success: false, message: 'Testing...' } }))

    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials/test`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ credential_id: credentialId })
        }
      )

      if (response.ok) {
        const result = await response.json()
        setTestResults((prev) => ({ ...prev, [credentialId]: result }))
      } else {
        setTestResults((prev) => ({
          ...prev,
          [credentialId]: { success: false, message: 'Failed to test credential' }
        }))
      }
    } catch (error) {
      console.error('Failed to test credential:', error)
      setTestResults((prev) => ({
        ...prev,
        [credentialId]: { success: false, message: 'Error testing credential' }
      }))
    } finally {
      setTestingCredential(null)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">LLM Credentials</h1>
              <p className="mt-2 text-gray-600">
                Manage your API keys for AI providers (OpenAI, Anthropic, etc.)
              </p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              <span className="font-medium">Add Credential</span>
            </button>
          </div>

          {/* Credentials List */}
          {isLoading ? (
            <div className="grid grid-cols-1 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
                  <div className="h-6 bg-gray-200 rounded w-1/3 mb-3" />
                  <div className="h-4 bg-gray-200 rounded w-2/3" />
                </div>
              ))}
            </div>
          ) : credentials.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                <svg className="h-8 w-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">No credentials yet</h2>
              <p className="text-gray-600 mb-6">Add your first API key to start using AI agents</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
                <span className="font-medium">Add Credential</span>
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {credentials.map((credential) => (
                <div
                  key={credential.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                            PROVIDER_COLORS[credential.credential_type] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {PROVIDER_LABELS[credential.credential_type] || credential.credential_type}
                        </span>
                        {credential.label && (
                          <span className="text-lg font-semibold text-gray-900">{credential.label}</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 font-mono">{credential.masked_key}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        Added {new Date(credential.created_at).toLocaleDateString()}
                      </p>

                      {/* Test Result */}
                      {testResults[credential.id] && (
                        <div
                          className={`mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${
                            testResults[credential.id].success
                              ? 'bg-green-50 text-green-700'
                              : 'bg-red-50 text-red-700'
                          }`}
                        >
                          {testResults[credential.id].success ? (
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                            </svg>
                          ) : (
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          )}
                          <span>{testResults[credential.id].message}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleTestCredential(credential.id)}
                        disabled={testingCredential === credential.id}
                        className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 disabled:bg-gray-100 disabled:cursor-not-allowed text-blue-600 disabled:text-gray-400 rounded-lg transition-colors text-sm font-medium"
                      >
                        {testingCredential === credential.id ? 'Testing...' : 'Test'}
                      </button>
                      <button
                        onClick={() => setEditingCredential(credential)}
                        className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => setDeletingCredential(credential)}
                        className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

        {/* Modals */}
        {showAddModal && (
          <AddCredentialModal onClose={() => setShowAddModal(false)} onSubmit={handleAddCredential} />
        )}

        {editingCredential && (
          <EditCredentialModal
            credential={editingCredential}
            onClose={() => setEditingCredential(null)}
            onSubmit={(label) => handleUpdateCredential(editingCredential.id, label)}
          />
        )}

        {deletingCredential && (
          <DeleteCredentialModal
            credential={deletingCredential}
            onClose={() => setDeletingCredential(null)}
            onConfirm={() => handleDeleteCredential(deletingCredential.id)}
          />
        )}
      </div>
    </DashboardLayout>
  )
}
