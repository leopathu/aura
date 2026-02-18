// Calendar-specific integration component
'use client'

import { useState, useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'

interface CalendarEvent {
  id: string
  summary: string
  start: string
  end: string
  location?: string
}

interface CalendarIntegrationCardProps {
  isConnected: boolean
  scope?: string | null
  orgId: string
  onConnect: () => void
  onDisconnect: () => void
}

export default function CalendarIntegrationCard({
  isConnected,
  scope,
  orgId,
  onConnect,
  onDisconnect
}: CalendarIntegrationCardProps) {
  const [upcomingEvents, setUpcomingEvents] = useState<CalendarEvent[]>([])
  const [loadingEvents, setLoadingEvents] = useState(false)

  const calendarScopes = [
    { name: 'Read events', included: scope?.includes('calendar.readonly') },
    { name: 'Create events', included: scope?.includes('calendar.events') },
    { name: 'Manage calendar', included: scope?.includes('calendar') && !scope?.includes('calendar.readonly') }
  ]

  useEffect(() => {
    if (isConnected) {
      loadUpcomingEvents()
    }
  }, [isConnected])

  const loadUpcomingEvents = async () => {
    setLoadingEvents(true)
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/tools/calendar?org_id=${orgId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        // This would call the actual calendar API in production
        // For now, just set empty array
        setUpcomingEvents([])
      }
    } catch (error) {
      console.error('Failed to load calendar events:', error)
    } finally {
      setLoadingEvents(false)
    }
  }

  const formatEventTime = (dateTime: string) => {
    try {
      const date = new Date(dateTime)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      })
    } catch {
      return dateTime
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Google Calendar</h3>
            <p className="text-sm text-gray-600">Event management</p>
          </div>
        </div>
        {isConnected && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Connected
          </span>
        )}
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Connect Google Calendar to allow AI agents to view, create, and manage your calendar events.
      </p>

      {isConnected ? (
        <div className="space-y-4">
          {/* Permissions Display */}
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-gray-700 mb-2">Permissions</h4>
            <div className="space-y-1.5">
              {calendarScopes.map((scopeItem) => (
                <div key={scopeItem.name} className="flex items-center gap-2 text-xs">
                  {scopeItem.included ? (
                    <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  <span className={scopeItem.included ? 'text-gray-700' : 'text-gray-400'}>
                    {scopeItem.name}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Agent Capabilities */}
          <div className="bg-purple-50 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-purple-700 mb-2">AI Agent Capabilities</h4>
            <ul className="space-y-1 text-xs text-purple-600">
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>View upcoming events and schedules</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>Create new calendar events and meetings</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>Update existing event details and times</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>Check availability and schedule conflicts</span>
              </li>
            </ul>
          </div>

          {/* Upcoming Events Preview */}
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-blue-700">Upcoming Events</h4>
              <button
                onClick={loadUpcomingEvents}
                disabled={loadingEvents}
                className="text-xs text-blue-600 hover:text-blue-700 disabled:opacity-50"
              >
                {loadingEvents ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            {loadingEvents ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-3 bg-blue-200 rounded w-3/4 mb-1" />
                    <div className="h-2 bg-blue-100 rounded w-1/2" />
                  </div>
                ))}
              </div>
            ) : upcomingEvents.length > 0 ? (
              <div className="space-y-2">
                {upcomingEvents.slice(0, 3).map((event) => (
                  <div key={event.id} className="border-l-2 border-blue-400 pl-2">
                    <p className="text-xs font-medium text-gray-800">{event.summary}</p>
                    <p className="text-xs text-gray-600">{formatEventTime(event.start)}</p>
                    {event.location && (
                      <p className="text-xs text-gray-500">📍 {event.location}</p>
                    )}
                  </div>
                ))}
                {upcomingEvents.length > 3 && (
                  <p className="text-xs text-blue-600">+{upcomingEvents.length - 3} more events</p>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-500">No upcoming events in the next 7 days</p>
            )}
          </div>

          {/* Disconnect Button */}
          <button
            onClick={onDisconnect}
            className="w-full px-4 py-2.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors font-medium"
          >
            Disconnect Calendar
          </button>
        </div>
      ) : (
        <button
          onClick={onConnect}
          className="w-full px-4 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg transition-all font-medium shadow-sm"
        >
          Connect Calendar
        </button>
      )}
    </div>
  )
}
