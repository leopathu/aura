'use client'

/**
 * Activity Export Component
 * 
 * TASK-309: Export activity logs (CSV/JSON)
 * Allows exporting activity logs in CSV or JSON format
 */

import { useState } from 'react'
import { ActivityFilters } from '@/types/activity'
import { useAuthStore } from '@/store/authStore'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ActivityExportProps {
  filters: ActivityFilters
  totalCount: number
}

export default function ActivityExport({
  filters,
  totalCount,
}: ActivityExportProps) {
  const { accessToken } = useAuthStore()
  const [exporting, setExporting] = useState(false)
  const [format, setFormat] = useState<'json' | 'csv'>('json')

  const handleExport = async () => {
    if (!accessToken) return

    try {
      setExporting(true)

      // Build query params
      const params: any = { format }

      if (filters.startDate) {
        params.start_date = filters.startDate.toISOString()
      }
      if (filters.endDate) {
        params.end_date = filters.endDate.toISOString()
      }
      if (filters.actionTypes && filters.actionTypes.length > 0) {
        params.action_types = filters.actionTypes.join(',')
      }
      if (filters.agentId) {
        params.agent_id = filters.agentId
      }
      if (filters.userId) {
        params.user_id = filters.userId
      }

      const response = await axios.get(
        `${API_URL}/api/v1/activity/export`,
        {
          params,
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
          responseType: format === 'csv' ? 'blob' : 'json',
        }
      )

      // Download file
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json',
        })
        downloadBlob(blob, `activity-logs-${Date.now()}.json`)
      } else {
        downloadBlob(response.data, `activity-logs-${Date.now()}.csv`)
      }
    } catch (err) {
      console.error('Export error:', err)
      alert('Failed to export activity logs')
    } finally {
      setExporting(false)
    }
  }

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  return (
    <div className="flex items-center gap-3">
      {/* Format Selector */}
      <select
        value={format}
        onChange={(e) => setFormat(e.target.value as 'json' | 'csv')}
        disabled={exporting}
        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50"
      >
        <option value="json">JSON</option>
        <option value="csv">CSV</option>
      </select>

      {/* Export Button */}
      <button
        onClick={handleExport}
        disabled={exporting || totalCount === 0}
        className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {exporting ? (
          <>
            <svg
              className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Exporting...
          </>
        ) : (
          <>
            <svg
              className="-ml-1 mr-2 h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            Export
          </>
        )}
      </button>
    </div>
  )
}
