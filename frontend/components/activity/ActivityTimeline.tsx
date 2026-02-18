'use client'

/**
 * Activity Timeline Component
 * 
 * TASK-307: Timeline view for activities
 * Displays activities in a chronological timeline with grouping by date
 */

import { Activity, ACTION_CATEGORIES, ACTION_COLORS } from '@/types/activity'
import { format, isToday, isYesterday, formatDistanceToNow } from 'date-fns'

interface ActivityTimelineProps {
  activities: Activity[]
  loading: boolean
  onActivityClick: (activity: Activity) => void
}

export default function ActivityTimeline({
  activities,
  loading,
  onActivityClick,
}: ActivityTimelineProps) {
  // Group activities by date
  const groupedActivities = activities.reduce((groups, activity) => {
    const date = new Date(activity.created_at)
    const dateKey = format(date, 'yyyy-MM-dd')

    if (!groups[dateKey]) {
      groups[dateKey] = []
    }
    groups[dateKey].push(activity)

    return groups
  }, {} as Record<string, Activity[]>)

  const dateKeys = Object.keys(groupedActivities).sort((a, b) => b.localeCompare(a))

  // Format date header
  const formatDateHeader = (dateKey: string) => {
    const date = new Date(dateKey)
    if (isToday(date)) return 'Today'
    if (isYesterday(date)) return 'Yesterday'
    return format(date, 'MMMM d, yyyy')
  }

  // Get action category
  const getActionCategory = (action: string): string => {
    const prefix = action.split('.')[0]
    return ACTION_CATEGORIES[prefix as keyof typeof ACTION_CATEGORIES] || 'Other'
  }

  // Get color for action
  const getActionColor = (action: string): string => {
    const prefix = action.split('.')[0]
    return ACTION_COLORS[prefix as keyof typeof ACTION_COLORS] || 'gray'
  }

  // Get icon for action
  const getActionIcon = (action: string): JSX.Element => {
    const category = action.split('.')[0]
    const iconClass = "h-5 w-5"

    switch (category) {
      case 'agent':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        )
      case 'message':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )
      case 'tool':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        )
      case 'credential':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
        )
      case 'integration':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
        )
      case 'user':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        )
      case 'approval':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      default:
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  // Format action text
  const formatActionText = (action: string): string => {
    return action
      .split('.')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' - ')
  }

  if (loading && activities.length === 0) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {dateKeys.map((dateKey) => (
        <div key={dateKey}>
          {/* Date Header */}
          <div className="sticky top-0 z-10 bg-gray-50 py-2 mb-4">
            <h3 className="text-sm font-semibold text-gray-900">
              {formatDateHeader(dateKey)}
            </h3>
          </div>

          {/* Activities for this date */}
          <div className="space-y-3">
            {groupedActivities[dateKey].map((activity, index) => {
              const color = getActionColor(activity.action)
              const bgColors = {
                purple: 'bg-purple-100 text-purple-600',
                blue: 'bg-blue-100 text-blue-600',
                green: 'bg-green-100 text-green-600',
                yellow: 'bg-yellow-100 text-yellow-600',
                pink: 'bg-pink-100 text-pink-600',
                indigo: 'bg-indigo-100 text-indigo-600',
                gray: 'bg-gray-100 text-gray-600',
                orange: 'bg-orange-100 text-orange-600',
              }

              return (
                <div
                  key={activity.id}
                  onClick={() => onActivityClick(activity)}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer border border-gray-200 hover:border-gray-300"
                >
                  <div className="p-4">
                    <div className="flex items-start gap-3">
                      {/* Icon */}
                      <div className={`flex-shrink-0 rounded-lg p-2 ${bgColors[color as keyof typeof bgColors]}`}>
                        {getActionIcon(activity.action)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {formatActionText(activity.action)}
                          </h4>
                          <span className="text-xs text-gray-500 whitespace-nowrap">
                            {format(new Date(activity.created_at), 'h:mm a')}
                          </span>
                        </div>

                        {/* Details Preview */}
                        {activity.details && Object.keys(activity.details).length > 0 && (
                          <div className="mt-1 text-sm text-gray-600">
                            {activity.details.message || activity.details.description || (
                              <span className="text-gray-400 italic">
                                {Object.keys(activity.details).length} detail{Object.keys(activity.details).length !== 1 ? 's' : ''}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Metadata */}
                        <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                          {activity.agent_id && (
                            <span className="inline-flex items-center gap-1">
                              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                              </svg>
                              {activity.details.agent_name || 'Agent'}
                            </span>
                          )}
                          {activity.user_id && (
                            <span className="inline-flex items-center gap-1">
                              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                              {activity.details.user_name || 'User'}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
