/**
 * Trigger Selector Component
 * 
 * TASK-353: Add trigger selection UI
 */

'use client'

import { TriggerType } from '@/types/automation'

interface TriggerSelectorProps {
  triggerType: TriggerType
  onTriggerTypeChange: (type: TriggerType) => void
}

export default function TriggerSelector({ triggerType, onTriggerTypeChange }: TriggerSelectorProps) {
  const triggers = [
    {
      type: TriggerType.SCHEDULE,
      icon: '⏰',
      label: 'Schedule',
      description: 'Run on a cron schedule'
    },
    {
      type: TriggerType.WEBHOOK,
      icon: '🔗',
      label: 'Webhook',
      description: 'Trigger via HTTP webhook'
    },
    {
      type: TriggerType.EVENT,
      icon: '⚡',
      label: 'Event',
      description: 'Trigger on internal events'
    },
    {
      type: TriggerType.MANUAL,
      icon: '👆',
      label: 'Manual',
      description: 'Trigger manually only'
    }
  ]

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-3">
        How should this automation be triggered?
      </label>
      <div className="grid grid-cols-2 gap-4">
        {triggers.map((trigger) => (
          <button
            key={trigger.type}
            onClick={() => onTriggerTypeChange(trigger.type)}
            className={`p-4 border-2 rounded-lg text-left transition-all ${
              triggerType === trigger.type
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-300 hover:border-purple-300'
            }`}
          >
            <div className="text-3xl mb-2">{trigger.icon}</div>
            <div className="font-medium text-gray-900">{trigger.label}</div>
            <div className="text-sm text-gray-600 mt-1">{trigger.description}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
