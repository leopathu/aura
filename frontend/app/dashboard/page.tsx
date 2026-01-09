'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import api from '@/lib/api'

export default function DashboardPage() {
  const router = useRouter()
  const { user, currentOrg, organizations, logout } = useAuthStore()
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      router.push('/auth/login')
      return
    }

    if (!currentOrg && organizations.length === 0) {
      // No organizations, redirect to create one
      router.push('/organizations/create')
      return
    }

    loadAgents()
  }, [user, currentOrg])

  const loadAgents = async () => {
    if (!currentOrg) return
    
    try {
      const response = await api.get(`/organizations/${currentOrg.id}/agents`)
      setAgents(response.data)
    } catch (error) {
      console.error('Failed to load agents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  if (!user || !currentOrg) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-purple-600">Aura</h1>
            <p className="text-sm text-gray-600">{currentOrg.name}</p>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/settings')}
              className="px-4 py-2 text-gray-700 hover:text-purple-600"
            >
              Settings
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h2>
          <p className="text-gray-600">Manage your AI agents and tasks</p>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <button
            onClick={() => router.push('/chat')}
            className="p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow border-2 border-purple-200 hover:border-purple-400"
          >
            <div className="text-4xl mb-3">💬</div>
            <h3 className="text-xl font-semibold mb-2">Chat with Agent</h3>
            <p className="text-gray-600">Start a conversation with your AI agent</p>
          </button>

          <button
            onClick={() => router.push('/agents/create')}
            className="p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="text-4xl mb-3">🤖</div>
            <h3 className="text-xl font-semibold mb-2">Create Agent</h3>
            <p className="text-gray-600">Set up a new AI agent</p>
          </button>

          <button
            onClick={() => router.push('/settings/credentials')}
            className="p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="text-4xl mb-3">🔑</div>
            <h3 className="text-xl font-semibold mb-2">Add API Keys</h3>
            <p className="text-gray-600">Connect your LLM providers</p>
          </button>
        </div>

        {/* Agents List */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-xl font-semibold mb-4">Your Agents</h3>
          
          {loading ? (
            <p className="text-gray-600">Loading agents...</p>
          ) : agents.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">No agents yet. Create your first one!</p>
              <button
                onClick={() => router.push('/agents/create')}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                Create Agent
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {agents.map((agent: any) => (
                <div
                  key={agent.id}
                  className="p-4 border border-gray-200 rounded-lg hover:border-purple-400 cursor-pointer"
                  onClick={() => router.push(`/agents/${agent.id}`)}
                >
                  <h4 className="font-semibold text-lg">{agent.name}</h4>
                  {agent.description && (
                    <p className="text-gray-600 mt-1">{agent.description}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
