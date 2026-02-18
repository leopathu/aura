/**
 * Automation Run History Page
 * 
 * TASK-364: Create run history page
 * TASK-365: Create timeline component for runs
 * TASK-366: Show run details modal
 * TASK-367: Add run filtering
 * TASK-368: Add retry button
 */

'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { AutomationRun, RunStatus, Automation } from '@/types/automation'
import { formatDistanceToNow } from 'date-fns'

export default function AutomationRunsPage() {
  const params = useParams()
  const router = useRouter()
  const automationId = params.id as string

  const [automation, setAutomation] = useState<Automation | null>(null)
  const [runs, setRuns] = useState<AutomationRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedRun, setSelectedRun] = useState<AutomationRun | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  // TASK-367: Filtering state
  const [statusFilter, setStatusFilter] = useState<RunStatus | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchAutomation()
    fetchRuns()
  }, [automationId, statusFilter])

  const fetchAutomation = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/automations/${automationId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setAutomation(data)
      }
    } catch (err) {
      console.error('Failed to fetch automation:', err)
    }
  }

  const fetchRuns = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const params = new URLSearchParams()
      if (statusFilter !== 'all') {
        params.append('status', statusFilter)
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/automations/${automationId}/runs?${params}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setRuns(data)
      } else {
        setError('Failed to load runs')
      }
    } catch (err) {
      setError('Failed to load runs')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  // TASK-368: Retry automation
  const handleRetry = async (run: AutomationRun) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/automations/${automationId}/test`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            trigger_data: run.trigger_data || {}
          })
        }
      )

      if (response.ok) {
        fetchRuns() // Refresh runs
        alert('Automation queued for retry')
      } else {
        alert('Failed to retry automation')
      }
    } catch (err) {
      alert('Failed to retry automation')
    }
  }

  const getStatusColor = (status: RunStatus) => {
    switch (status) {
      case RunStatus.SUCCESS:
        return 'bg-green-100 text-green-800 border-green-200'
      case RunStatus.FAILED:
        return 'bg-red-100 text-red-800 border-red-200'
      case RunStatus.RUNNING:
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case RunStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case RunStatus.CANCELLED:
        return 'bg-gray-100 text-gray-800 border-gray-200'
      case RunStatus.TIMEOUT:
        return 'bg-orange-100 text-orange-800 border-orange-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusIcon = (status: RunStatus) => {
    switch (status) {
      case RunStatus.SUCCESS: return '✅'
      case RunStatus.FAILED: return '❌'
      case RunStatus.RUNNING: return '⏳'
      case RunStatus.PENDING: return '⏰'
      case RunStatus.CANCELLED: return '🚫'
      case RunStatus.TIMEOUT: return '⏱️'
      default: return '❓'
    }
  }

  const filteredRuns = runs.filter(run => {
    if (searchQuery) {
      return JSON.stringify(run).toLowerCase().includes(searchQuery.toLowerCase())
    }
    return true
  })

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => router.push('/automations')}
          className="text-purple-600 hover:text-purple-700 mb-4"
        >
          ← Back to Automations
        </button>
        
        {automation && (
          <>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {automation.name}
            </h1>
            <p className="text-gray-600">Run History</p>
          </>
        )}
      </div>

      {/* TASK-367: Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as RunStatus | 'all')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="all">All Statuses</option>
              <option value={RunStatus.SUCCESS}>Success</option>
              <option value={RunStatus.FAILED}>Failed</option>
              <option value={RunStatus.RUNNING}>Running</option>
              <option value={RunStatus.PENDING}>Pending</option>
              <option value={RunStatus.CANCELLED}>Cancelled</option>
              <option value={RunStatus.TIMEOUT}>Timeout</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Logs
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search in logs..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading runs...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* TASK-365: Timeline Component */}
      {!loading && !error && (
        <div className="space-y-4">
          {filteredRuns.map((run) => (
            <div
              key={run.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">{getStatusIcon(run.status)}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(run.status)}`}>
                          {run.status}
                        </span>
                        <span className="text-sm text-gray-500">
                          {formatDistanceToNow(new Date(run.started_at), { addSuffix: true })}
                        </span>
                      </div>
                      {run.completed_at && (
                        <div className="text-xs text-gray-500 mt-1">
                          Duration: {Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s
                        </div>
                      )}
                    </div>
                  </div>

                  {run.error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                      <div className="text-sm font-medium text-red-900">Error</div>
                      <div className="text-xs text-red-700 mt-1">{run.error}</div>
                    </div>
                  )}

                  {run.logs && run.logs.length > 0 && (
                    <div className="text-sm text-gray-600">
                      {run.logs.slice(0, 2).map((log, idx) => (
                        <div key={idx} className="font-mono text-xs py-1">
                          {log}
                        </div>
                      ))}
                      {run.logs.length > 2 && (
                        <div className="text-xs text-gray-500">
                          +{run.logs.length - 2} more logs
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setSelectedRun(run)
                      setShowDetails(true)
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    View Details
                  </button>
                  {(run.status === RunStatus.FAILED || run.status === RunStatus.TIMEOUT) && (
                    <button
                      onClick={() => handleRetry(run)}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                    >
                      Retry
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredRuns.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📊</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No runs found
          </h3>
          <p className="text-gray-600">
            {statusFilter !== 'all' 
              ? 'Try changing the filter'
              : 'This automation hasn\'t run yet'}
          </p>
        </div>
      )}

      {/* TASK-366: Run Details Modal */}
      {showDetails && selectedRun && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Run Details</h2>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Status */}
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Status</h3>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(selectedRun.status)}`}>
                  {getStatusIcon(selectedRun.status)} {selectedRun.status}
                </span>
              </div>

              {/* Timing */}
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Timing</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                  <div><span className="text-gray-600">Started:</span> {new Date(selectedRun.started_at).toLocaleString()}</div>
                  {selectedRun.completed_at && (
                    <div><span className="text-gray-600">Completed:</span> {new Date(selectedRun.completed_at).toLocaleString()}</div>
                  )}
                  {selectedRun.completed_at && (
                    <div><span className="text-gray-600">Duration:</span> {Math.round((new Date(selectedRun.completed_at).getTime() - new Date(selectedRun.started_at).getTime()) / 1000)}s</div>
                  )}
                </div>
              </div>

              {/* Trigger Data */}
              {selectedRun.trigger_data && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Trigger Data</h3>
                  <pre className="bg-gray-50 rounded-lg p-4 text-xs font-mono overflow-x-auto">
                    {JSON.stringify(selectedRun.trigger_data, null, 2)}
                  </pre>
                </div>
              )}

              {/* Context */}
              {selectedRun.context && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Context & Variables</h3>
                  <pre className="bg-gray-50 rounded-lg p-4 text-xs font-mono overflow-x-auto">
                    {JSON.stringify(selectedRun.context, null, 2)}
                  </pre>
                </div>
              )}

              {/* Result */}
              {selectedRun.result && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Result</h3>
                  <pre className="bg-green-50 rounded-lg p-4 text-xs font-mono overflow-x-auto">
                    {JSON.stringify(selectedRun.result, null, 2)}
                  </pre>
                </div>
              )}

              {/* Error */}
              {selectedRun.error && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Error</h3>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="text-sm text-red-900">{selectedRun.error}</div>
                  </div>
                </div>
              )}

              {/* Logs */}
              {selectedRun.logs && selectedRun.logs.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Execution Logs</h3>
                  <div className="bg-gray-900 text-green-400 rounded-lg p-4 font-mono text-xs space-y-1 max-h-96 overflow-y-auto">
                    {selectedRun.logs.map((log, idx) => (
                      <div key={idx}>{log}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-3 mt-6">
              {(selectedRun.status === RunStatus.FAILED || selectedRun.status === RunStatus.TIMEOUT) && (
                <button
                  onClick={() => {
                    handleRetry(selectedRun)
                    setShowDetails(false)
                  }}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
                >
                  Retry This Run
                </button>
              )}
              <button
                onClick={() => setShowDetails(false)}
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
