/**
 * Schedule Config Component
 * 
 * TASK-354: Add schedule configuration UI
 */

'use client'

import { useState, useEffect } from 'react'

interface ScheduleConfigProps {
  schedule: string
  timezone: string
  onScheduleChange: (schedule: string) => void
  onTimezoneChange: (timezone: string) => void
}

export default function ScheduleConfig({ 
  schedule, 
  timezone, 
  onScheduleChange, 
  onTimezoneChange 
}: ScheduleConfigProps) {
  const [usePreset, setUsePreset] = useState(true)
  const [preview, setPreview] = useState<string | null>(null)

  const presets = [
    { label: 'Every minute', value: '* * * * *' },
    { label: 'Every 5 minutes', value: '*/5 * * * *' },
    { label: 'Every 15 minutes', value: '*/15 * * * *' },
    { label: 'Every hour', value: '0 * * * *' },
    { label: 'Every day at 9 AM', value: '0 9 * * *' },
    { label: 'Every day at midnight', value: '0 0 * * *' },
    { label: 'Weekdays at 9 AM', value: '0 9 * * MON-FRI' },
    { label: 'Weekdays at 5 PM', value: '0 17 * * MON-FRI' },
    { label: 'First day of month', value: '0 0 1 * *' }
  ]

  const commonTimezones = [
    'UTC',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Australia/Sydney'
  ]

  useEffect(() => {
    // Fetch schedule preview
    const fetchPreview = async () => {
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/automations/test-schedule`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              cron_expression: schedule,
              timezone,
              test_count: 3
            })
          }
        )

        if (response.ok) {
          const data = await response.json()
          if (data.valid) {
            setPreview(data.description)
          } else {
            setPreview('Invalid schedule')
          }
        }
      } catch (err) {
        console.error('Failed to fetch schedule preview:', err)
      }
    }

    if (schedule) {
      fetchPreview()
    }
  }, [schedule, timezone])

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <button
          onClick={() => setUsePreset(true)}
          className={`px-4 py-2 rounded-lg font-medium ${
            usePreset
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-700'
          }`}
        >
          Preset Schedule
        </button>
        <button
          onClick={() => setUsePreset(false)}
          className={`px-4 py-2 rounded-lg font-medium ${
            !usePreset
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-700'
          }`}
        >
          Custom Cron
        </button>
      </div>

      {usePreset ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Choose Schedule
          </label>
          <select
            value={schedule}
            onChange={(e) => onScheduleChange(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
          >
            {presets.map((preset) => (
              <option key={preset.value} value={preset.value}>
                {preset.label}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Cron Expression
          </label>
          <input
            type="text"
            value={schedule}
            onChange={(e) => onScheduleChange(e.target.value)}
            placeholder="0 9 * * *"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 font-mono"
          />
          <div className="text-xs text-gray-500 mt-1">
            Format: minute hour day month weekday (e.g., "0 9 * * *" = daily at 9 AM)
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Timezone
        </label>
        <select
          value={timezone}
          onChange={(e) => onTimezoneChange(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
        >
          {commonTimezones.map((tz) => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </select>
      </div>

      {preview && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm font-medium text-blue-900 mb-1">Schedule Preview</div>
          <div className="text-sm text-blue-700">{preview}</div>
        </div>
      )}
    </div>
  )
}
