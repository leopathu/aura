'use client'

/**
 * Activity Filters Component
 * 
 * TASK-306: Add filters for logs (date, type, agent, user)
 * Provides filtering controls for activity logs
 */

import { useState, useEffect } from 'react'
import { ActivityFilters as ActivityFiltersType, ACTION_CATEGORIES } from '@/types/activity'
import { useAuthStore } from '@/store/authStore'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ActivityFiltersProps {
  filters: ActivityFiltersType
  onFiltersChange: (filters: ActivityFiltersType) => void
}

export default function ActivityFilters({
  filters,
  onFiltersChange,
}: ActivityFiltersProps) {
  const { accessToken } = useAuthStore()
  const [agents, setAgents] = useState<any[]>([])
  const [users, setUsers] = useState<any[]>([])

  // Fetch agents and users for filter dropdowns
  useEffect(() => {
    const fetchData = async () => {
      if (!accessToken) return

      try {
        // Fetch agents
        const agentsRes = await axios.get(`${API_URL}/api/v1/agents`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        })
        setAgents(agentsRes.data || [])

        // Fetch organization users
        const usersRes = await axios.get(`${API_URL}/api/v1/users/org`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        })
        setUsers(usersRes.data || [])
      } catch (err) {
        console.error('Error fetching filter data:', err)
      }
    }

    fetchData()
  }, [accessToken])

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value ? new Date(e.target.value) : null
    onFiltersChange({ ...filters, startDate: date })
  }

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value ? new Date(e.target.value) : null
    onFiltersChange({ ...filters, endDate: date })
  }

  const handleActionTypeToggle = (actionType: string) => {
    const newActionTypes = filters.actionTypes.includes(actionType)
      ? filters.actionTypes.filter((t) => t !== actionType)
      : [...filters.actionTypes, actionType]
    onFiltersChange({ ...filters, actionTypes: newActionTypes })
  }

  const handleAgentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const agentId = e.target.value || null
    onFiltersChange({ ...filters, agentId })
  }

  const handleUserChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const userId = e.target.value || null
    onFiltersChange({ ...filters, userId })
  }

  const clearFilters = () => {
    onFiltersChange({
      startDate: null,
      endDate: null,
      actionTypes: [],
      agentId: null,
      userId: null,
    })
  }

  const hasFilters = Object.values(filters).some((v) => {
    if (Array.isArray(v)) return v.length > 0
    return v !== null
  })

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="text-xs text-purple-600 hover:text-purple-700 font-medium"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Date Range */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-2">
          Date Range
        </label>
        <div className="space-y-2">
          <input
            type="date"
            value={filters.startDate ? filters.startDate.toISOString().split('T')[0] : ''}
            onChange={handleStartDateChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="Start date"
          />
          <input
            type="date"
            value={filters.endDate ? filters.endDate.toISOString().split('T')[0] : ''}
            onChange={handleEndDateChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="End date"
          />
        </div>
      </div>

      {/* Action Types */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-2">
          Action Types
        </label>
        <div className="space-y-2">
          {Object.entries(ACTION_CATEGORIES).map(([key, label]) => (
            <label
              key={key}
              className="flex items-center gap-2 cursor-pointer group"
            >
              <input
                type="checkbox"
                checked={filters.actionTypes.includes(key)}
                onChange={() => handleActionTypeToggle(key)}
                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-700 group-hover:text-gray-900">
                {label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Agent Filter */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-2">
          Agent
        </label>
        <select
          value={filters.agentId || ''}
          onChange={handleAgentChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="">All agents</option>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name}
            </option>
          ))}
        </select>
      </div>

      {/* User Filter */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-2">
          User
        </label>
        <select
          value={filters.userId || ''}
          onChange={handleUserChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="">All users</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.name || user.email}
            </option>
          ))}
        </select>
      </div>

      {/* Quick Filters */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-2">
          Quick Filters
        </label>
        <div className="space-y-2">
          <button
            onClick={() => onFiltersChange({
              ...filters,
              startDate: new Date(Date.now() - 24 * 60 * 60 * 1000),
              endDate: new Date(),
            })}
            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
          >
            Last 24 hours
          </button>
          <button
            onClick={() => onFiltersChange({
              ...filters,
              startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
              endDate: new Date(),
            })}
            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
          >
            Last 7 days
          </button>
          <button
            onClick={() => onFiltersChange({
              ...filters,
              startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
              endDate: new Date(),
            })}
            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
          >
            Last 30 days
          </button>
        </div>
      </div>
    </div>
  )
}
