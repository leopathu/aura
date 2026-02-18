'use client'

/**
 * Activity Logs Page
 * 
 * TASK-305: Create activity log viewer UI
 * TASK-306: Add filters for logs (date, type, agent, user)
 * TASK-307: Timeline view for activities
 * TASK-308: Activity details modal
 * TASK-309: Export activity logs (CSV/JSON)
 */

import { useState, useEffect } from 'react'
import { useAuthStore } from '@/store/auth'
import ActivityTimeline from '@/components/activity/ActivityTimeline'
import ActivityFilters from '@/components/activity/ActivityFilters'
import ActivityDetailsModal from '@/components/activity/ActivityDetailsModal'
import ActivityExport from '@/components/activity/ActivityExport'
import { Activity, ActivityFilters as ActivityFiltersType } from '@/types/activity'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ActivityPage() {
  const { accessToken, user } = useAuthStore()
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null)
  const [filters, setFilters] = useState<ActivityFiltersType>({
    startDate: null,
    endDate: null,
    actionTypes: [],
    agentId: null,
    userId: null,
  })
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [totalCount, setTotalCount] = useState(0)

  const limit = 50

  // Fetch activities
  const fetchActivities = async (reset: boolean = false) => {
    if (!accessToken || !user?.org_id) return

    try {
      setLoading(true)
      setError(null)

      const offset = reset ? 0 : (page - 1) * limit

      // Build query params
      const params: any = {
        limit,
        offset,
      }

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
        `${API_URL}/api/v1/activity/logs`,
        {
          params,
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      )

      const newActivities = response.data.logs || []
      const count = response.data.total || 0

      if (reset) {
        setActivities(newActivities)
      } else {
        setActivities((prev) => [...prev, ...newActivities])
      }

      setTotalCount(count)
      setHasMore(newActivities.length === limit)
    } catch (err: any) {
      console.error('Error fetching activities:', err)
      setError(err.response?.data?.detail || 'Failed to load activities')
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchActivities(true)
  }, [accessToken, user?.org_id, filters])

  // Load more
  const loadMore = () => {
    if (!loading && hasMore) {
      setPage((p) => p + 1)
      fetchActivities(false)
    }
  }

  // Handle filter change
  const handleFiltersChange = (newFilters: ActivityFiltersType) => {
    setFilters(newFilters)
    setPage(1)
  }

  // Handle activity click
  const handleActivityClick = (activity: Activity) => {
    setSelectedActivity(activity)
  }

  // Close modal
  const closeModal = () => {
    setSelectedActivity(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Activity Logs
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                View and track all agent activities in your organization
              </p>
            </div>

            {/* Export Button */}
            <ActivityExport
              filters={filters}
              totalCount={totalCount}
            />
          </div>

          {/* Stats */}
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg px-4 py-3">
              <div className="text-sm font-medium text-purple-600">
                Total Activities
              </div>
              <div className="mt-1 text-2xl font-semibold text-purple-900">
                {totalCount.toLocaleString()}
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg px-4 py-3">
              <div className="text-sm font-medium text-blue-600">
                Filtered Results
              </div>
              <div className="mt-1 text-2xl font-semibold text-blue-900">
                {activities.length.toLocaleString()}
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg px-4 py-3">
              <div className="text-sm font-medium text-green-600">
                Active Filters
              </div>
              <div className="mt-1 text-2xl font-semibold text-green-900">
                {Object.values(filters).filter(Boolean).length}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <ActivityFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
            />
          </div>

          {/* Timeline */}
          <div className="lg:col-span-3">
            {error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <div className="mt-2 text-sm text-red-700">{error}</div>
                  </div>
                </div>
              </div>
            ) : (
              <>
                <ActivityTimeline
                  activities={activities}
                  loading={loading}
                  onActivityClick={handleActivityClick}
                />

                {/* Load More */}
                {hasMore && !loading && (
                  <div className="mt-6 text-center">
                    <button
                      onClick={loadMore}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-colors"
                    >
                      Load More
                    </button>
                  </div>
                )}

                {/* End of Results */}
                {!hasMore && activities.length > 0 && (
                  <div className="mt-6 text-center">
                    <p className="text-sm text-gray-500">
                      No more activities to load
                    </p>
                  </div>
                )}

                {/* Empty State */}
                {!loading && activities.length === 0 && (
                  <div className="text-center py-12">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">
                      No activities found
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Try adjusting your filters or check back later
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Activity Details Modal */}
      {selectedActivity && (
        <ActivityDetailsModal
          activity={selectedActivity}
          onClose={closeModal}
        />
      )}
    </div>
  )
}
