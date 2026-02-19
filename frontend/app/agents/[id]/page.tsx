'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { useAuthStore } from '@/store/authStore'
import AgentForm from '@/components/agents/AgentForm'

interface Agent {
  id: string
  name: string
  description: string
  system_prompt: string
  config: Record<string, any>
  is_active: boolean
  created_at: string
}

export default function AgentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const agentId = params.id as string

  const [agent, setAgent] = useState<Agent | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAgent()
  }, [agentId])

  const loadAgent = async () => {
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents/${agentId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setAgent(data)
      } else {
        setError('Agent not found')
      }
    } catch (error) {
      console.error('Failed to load agent:', error)
      setError('Failed to load agent')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (data: {
    name: string
    description: string
    system_prompt: string
    config: Record<string, any>
  }) => {
    setIsSubmitting(true)
    setError(null)

    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents/${agentId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(data)
        }
      )

      if (response.ok) {
        router.push('/agents')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Failed to update agent')
      }
    } catch (error) {
      console.error('Failed to update agent:', error)
      setError('An unexpected error occurred')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600" />
        </div>
      </DashboardLayout>
    )
  }

  if (error && !agent) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">{error}</h2>
            <button
              onClick={() => router.push('/agents')}
              className="text-purple-600 hover:text-purple-700"
            >
              Back to Agents
            </button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Edit Agent</h1>
            <p className="mt-2 text-gray-600">
              Update your AI assistant configuration
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Form */}
          {agent && (
            <AgentForm
              initialData={agent}
              onSubmit={handleSubmit}
              isSubmitting={isSubmitting}
            />
          )}
        </div>
      </DashboardLayout>
    )
  }
