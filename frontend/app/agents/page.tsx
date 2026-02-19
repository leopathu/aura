'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import DashboardLayout from '@/components/DashboardLayout'
import { useAuthStore } from '@/store/authStore'
import { useOrganizationStore } from '@/store/organizationStore'
import DeleteAgentModal from '@/components/agents/DeleteAgentModal'

interface Agent {
  id: string
  name: string
  description: string
  system_prompt: string
  config: Record<string, any>
  is_active: boolean
  created_at: string
}

export default function AgentsPage() {
  const currentOrganization = useOrganizationStore((state) => state.currentOrganization)
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [deleteModalAgent, setDeleteModalAgent] = useState<Agent | null>(null)

  useEffect(() => {
    if (currentOrganization) {
      loadAgents()
    }
  }, [currentOrganization])

  const loadAgents = async () => {
    if (!currentOrganization) return

    setIsLoading(true)
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents?org_id=${currentOrganization.id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setAgents(data)
      }
    } catch (error) {
      console.error('Failed to load agents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteAgent = async (agentId: string) => {
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents/${agentId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        setAgents((prev) => prev.filter((a) => a.id !== agentId))
        setDeleteModalAgent(null)
      }
    } catch (error) {
      console.error('Failed to delete agent:', error)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8 flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Agents</h1>
              <p className="mt-2 text-gray-600">
                Manage your AI assistants and their configurations
              </p>
            </div>
            <Link
              href="/agents/create"
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              <span className="font-medium">Create Agent</span>
            </Link>
          </div>

          {/* Agents List */}
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-3" />
                  <div className="h-4 bg-gray-200 rounded w-full mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-5/6" />
                </div>
              ))}
            </div>
          ) : agents.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                <svg className="h-8 w-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">No agents yet</h2>
              <p className="text-gray-600 mb-6">Create your first AI agent to get started</p>
              <Link
                href="/agents/create"
                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
                <span className="font-medium">Create Agent</span>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">{agent.name}</h3>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          agent.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {agent.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>

                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {agent.description || 'No description'}
                  </p>

                  <div className="flex items-center gap-2">
                    <Link
                      href={`/agents/${agent.id}`}
                      className="flex-1 text-center px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg transition-colors text-sm font-medium"
                    >
                      View Details
                    </Link>
                    <button
                      onClick={() => setDeleteModalAgent(agent)}
                      className="px-4 py-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors text-sm font-medium"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Delete Modal */}
        {deleteModalAgent && (
          <DeleteAgentModal
            agent={deleteModalAgent}
            onConfirm={() => handleDeleteAgent(deleteModalAgent.id)}
            onCancel={() => setDeleteModalAgent(null)}
          />
        )}
      </div>
    </DashboardLayout>
  )
}
