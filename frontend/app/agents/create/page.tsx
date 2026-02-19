'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { useAuthStore } from '@/store/authStore'
import { useOrganizationStore } from '@/store/organizationStore'
import AgentForm from '@/components/agents/AgentForm'

export default function CreateAgentPage() {
  const router = useRouter()
  const currentOrganization = useOrganizationStore((state) => state.currentOrganization)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (data: {
    name: string
    description: string
    system_prompt: string
    config: Record<string, any>
  }) => {
    if (!currentOrganization) return

    setIsSubmitting(true)
    setError(null)

    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents?org_id=${currentOrganization.id}`,
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
        router.push('/agents')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Failed to create agent')
      }
    } catch (error) {
      console.error('Failed to create agent:', error)
      setError('An unexpected error occurred')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Create AI Agent</h1>
            <p className="mt-2 text-gray-600">
              Configure a new AI assistant for your organization
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
        <AgentForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
      </div>
    </DashboardLayout>
  )
}
