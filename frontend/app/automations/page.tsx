/**
 * Automations Page
 * 
 * TASK-346: Create automations page
 * Lists all automations with filters and actions
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Automation, 
  AutomationStatus, 
  TriggerType,
  RunStatus 
} from '@/types/automation'
import AutomationCard from '@/components/automations/AutomationCard'

export default function AutomationsPage() {
  const router = useRouter()
  const [automations, setAutomations] = useState<Automation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<AutomationStatus | 'all'>('all')
  const [triggerFilter, setTriggerFilter] = useState<TriggerType | 'all'>('all')

  useEffect(() => {
    fetchAutomations()
  }, [statusFilter, triggerFilter])

  const fetchAutomations = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter !== 'all') params.append('status', statusFilter)
      if (triggerFilter !== 'all') params.append('trigger_type', triggerFilter)

      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/automations?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) throw new Error('Failed to fetch automations')

      const data = await response.json()
      setAutomations(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleStatus = async (id: string, currentStatus: AutomationStatus) => {
    try {
      const newStatus = currentStatus === AutomationStatus.ACTIVE 
        ? AutomationStatus.PAUSED 
        : AutomationStatus.ACTIVE

      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/automations/${id}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ status: newStatus })
        }
      )

      if (!response.ok) throw new Error('Failed to update automation')

      fetchAutomations()
    } catch (err) {
      console.error('Error toggling automation:', err)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this automation?')) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/automations/${id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) throw new Error('Failed to delete automation')

      fetchAutomations()
    } catch (err) {
      console.error('Error deleting automation:', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Automations</h1>
            <p className="text-gray-600 mt-1">
              Create and manage automated workflows
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/automations/templates')}
              className="px-6 py-3 border-2 border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors font-medium"
            >
              📋 Templates
            </button>
            <button
              onClick={() => router.push('/automations/create')}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              + New Automation
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6 flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as AutomationStatus | 'all')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value={AutomationStatus.ACTIVE}>Active</option>
              <option value={AutomationStatus.PAUSED}>Paused</option>
              <option value={AutomationStatus.DRAFT}>Draft</option>
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trigger Type
            </label>
            <select
              value={triggerFilter}
              onChange={(e) => setTriggerFilter(e.target.value as TriggerType | 'all')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Triggers</option>
              <option value={TriggerType.SCHEDULE}>Schedule</option>
              <option value={TriggerType.WEBHOOK}>Webhook</option>
              <option value={TriggerType.EVENT}>Event</option>
              <option value={TriggerType.MANUAL}>Manual</option>
            </select>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Empty State */}
        {!loading && automations.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <div className="text-gray-400 text-6xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No automations yet
            </h3>
            <p className="text-gray-600 mb-6">
              Create your first automation to get started with workflow automation
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => router.push('/automations/create')}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
              >
                Create Automation
              </button>
              <button
                onClick={() => router.push('/automations/templates')}
                className="px-6 py-3 border-2 border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors font-medium"
              >
                Browse Templates
              </button>
            </div>
          </div>
        )}

        {/* Automations Grid */}
        {automations.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {automations.map((automation) => (
              <AutomationCard
                key={automation.id}
                automation={automation}
                onToggle={() => handleToggleStatus(automation.id, automation.status)}
                onDelete={() => handleDelete(automation.id)}
                onClick={() => router.push(`/automations/${automation.id}`)}
              />
            ))}
          </div>
        )}

        {/* Browse Templates */}
        <div className="mt-12 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-8 text-center">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Looking for inspiration?
          </h3>
          <p className="text-gray-600 mb-4">
            Browse our template library for pre-built automation workflows
          </p>
          <button
            onClick={() => router.push('/automations/templates')}
            className="px-6 py-3 bg-white text-purple-600 rounded-lg hover:bg-gray-50 transition-colors font-medium shadow-sm"
          >
            Browse Templates
          </button>
        </div>
      </div>
    </div>
  )
}
