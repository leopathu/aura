/**
 * Automation Templates Page
 * 
 * TASK-359: Create template gallery page
 * TASK-360: Add pre-built automation templates
 * TASK-361: Create template preview modal
 * TASK-362: Add "Use Template" button
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { AutomationTemplate, TriggerType } from '@/types/automation'

export default function TemplatesPage() {
  const router = useRouter()
  const [selectedTemplate, setSelectedTemplate] = useState<AutomationTemplate | null>(null)
  const [showPreview, setShowPreview] = useState(false)

  // TASK-360: Pre-built automation templates
  const templates: AutomationTemplate[] = [
    {
      id: 'daily-standup',
      name: 'Daily Standup Report',
      description: 'Generate a daily standup summary from your tasks and send via email',
      category: 'productivity',
      trigger_type: TriggerType.SCHEDULE,
      workflow: [
        {
          type: 'agent_task',
          config: {
            prompt: 'Generate a standup report summarizing tasks completed yesterday, tasks planned for today, and any blockers'
          }
        },
        {
          type: 'http_request',
          config: {
            method: 'POST',
            url: 'https://api.sendgrid.com/v3/mail/send',
            headers: {
              'Authorization': 'Bearer {{ env.SENDGRID_API_KEY }}',
              'Content-Type': 'application/json'
            },
            body: {
              personalizations: [{ to: [{ email: '{{ user.email }}' }] }],
              from: { email: 'bot@example.com' },
              subject: 'Daily Standup - {{ now }}',
              content: [{ type: 'text/plain', value: '{{ steps.0.result }}' }]
            }
          }
        }
      ],
      config: {
        schedule: '0 9 * * MON-FRI',
        timezone: 'America/New_York'
      }
    },
    {
      id: 'github-issue-triage',
      name: 'GitHub Issue Triage',
      description: 'Automatically triage new GitHub issues with AI and post to Slack',
      category: 'development',
      trigger_type: TriggerType.WEBHOOK,
      workflow: [
        {
          type: 'agent_task',
          config: {
            prompt: 'Analyze this GitHub issue and provide: 1) Priority (high/medium/low), 2) Suggested labels, 3) Recommended assignee. Issue: {{ trigger.data.issue }}'
          }
        },
        {
          type: 'http_request',
          config: {
            method: 'POST',
            url: 'https://slack.com/api/chat.postMessage',
            headers: {
              'Authorization': 'Bearer {{ env.SLACK_TOKEN }}',
              'Content-Type': 'application/json'
            },
            body: {
              channel: '#dev-triage',
              text: 'New issue triaged: {{ trigger.data.issue.title }}',
              blocks: [
                {
                  type: 'section',
                  text: { type: 'mrkdwn', text: '{{ steps.0.result }}' }
                }
              ]
            }
          }
        }
      ],
      config: {}
    },
    {
      id: 'service-monitoring',
      name: 'Service Health Monitor',
      description: 'Check service health every 5 minutes and create Jira ticket on failure',
      category: 'devops',
      trigger_type: TriggerType.SCHEDULE,
      workflow: [
        {
          type: 'http_request',
          config: {
            method: 'GET',
            url: 'https://api.example.com/health'
          }
        },
        {
          type: 'condition',
          config: {
            field: 'steps.0.status_code',
            operator: 'not_equals',
            value: '200'
          }
        },
        {
          type: 'http_request',
          config: {
            method: 'POST',
            url: 'https://your-domain.atlassian.net/rest/api/3/issue',
            headers: {
              'Authorization': 'Basic {{ env.JIRA_TOKEN }}',
              'Content-Type': 'application/json'
            },
            body: {
              fields: {
                project: { key: 'OPS' },
                summary: 'Service Health Check Failed',
                description: 'Health check returned status {{ steps.0.status_code }}',
                issuetype: { name: 'Bug' },
                priority: { name: 'High' }
              }
            }
          }
        }
      ],
      config: {
        schedule: '*/5 * * * *',
        timezone: 'UTC'
      }
    },
    {
      id: 'weekly-summary',
      name: 'Weekly Summary Email',
      description: 'Generate a weekly summary of activities and send via email',
      category: 'productivity',
      trigger_type: TriggerType.SCHEDULE,
      workflow: [
        {
          type: 'agent_task',
          config: {
            prompt: 'Generate a weekly summary report for the past 7 days including: 1) Key accomplishments, 2) Metrics and statistics, 3) Areas for improvement, 4) Goals for next week'
          }
        },
        {
          type: 'http_request',
          config: {
            method: 'POST',
            url: 'https://api.sendgrid.com/v3/mail/send',
            headers: {
              'Authorization': 'Bearer {{ env.SENDGRID_API_KEY }}',
              'Content-Type': 'application/json'
            },
            body: {
              personalizations: [{ to: [{ email: '{{ user.email }}' }] }],
              from: { email: 'bot@example.com' },
              subject: 'Weekly Summary - Week of {{ now }}',
              content: [{ type: 'text/html', value: '<pre>{{ steps.0.result }}</pre>' }]
            }
          }
        }
      ],
      config: {
        schedule: '0 17 * * FRI',
        timezone: 'America/New_York'
      }
    },
    {
      id: 'customer-onboarding',
      name: 'Customer Onboarding Flow',
      description: 'Multi-step onboarding workflow with emails, Slack, and Jira',
      category: 'sales',
      trigger_type: TriggerType.EVENT,
      workflow: [
        {
          type: 'http_request',
          config: {
            method: 'POST',
            url: 'https://api.sendgrid.com/v3/mail/send',
            headers: {
              'Authorization': 'Bearer {{ env.SENDGRID_API_KEY }}',
              'Content-Type': 'application/json'
            },
            body: {
              personalizations: [{ to: [{ email: '{{ trigger.data.customer_email }}' }] }],
              from: { email: 'welcome@example.com' },
              subject: 'Welcome to Our Platform!',
              content: [{ type: 'text/html', value: '<h1>Welcome {{ trigger.data.customer_name }}!</h1>' }]
            }
          }
        },
        {
          type: 'http_request',
          config: {
            method: 'POST',
            url: 'https://slack.com/api/chat.postMessage',
            headers: {
              'Authorization': 'Bearer {{ env.SLACK_TOKEN }}',
              'Content-Type': 'application/json'
            },
            body: {
              channel: '#sales',
              text: 'New customer onboarded: {{ trigger.data.customer_name }}'
            }
          }
        },
        {
          type: 'delay',
          config: {
            seconds: 86400 // 24 hours
          }
        },
        {
          type: 'agent_task',
          config: {
            prompt: 'Generate a personalized follow-up email for {{ trigger.data.customer_name }} checking on their onboarding experience'
          }
        },
        {
          type: 'http_request',
          config: {
            method: 'POST',
            url: 'https://api.sendgrid.com/v3/mail/send',
            headers: {
              'Authorization': 'Bearer {{ env.SENDGRID_API_KEY }}',
              'Content-Type': 'application/json'
            },
            body: {
              personalizations: [{ to: [{ email: '{{ trigger.data.customer_email }}' }] }],
              from: { email: 'success@example.com' },
              subject: 'How is your experience so far?',
              content: [{ type: 'text/plain', value: '{{ steps.3.result }}' }]
            }
          }
        }
      ],
      config: {
        event_type: 'customer.created'
      }
    },
    {
      id: 'data-pipeline',
      name: 'Daily Data Pipeline',
      description: 'Fetch data from API, process with AI, and send to webhook',
      category: 'data',
      trigger_type: TriggerType.SCHEDULE,
      workflow: [
        {
          type: 'http_request',
          config: {
            method: 'GET',
            url: 'https://api.example.com/data'
          }
        },
        {
          type: 'agent_task',
          config: {
            prompt: 'Analyze this data and provide insights: {{ steps.0.data }}'
          }
        },
        {
          type: 'http_request',
          config: {
            method: 'POST',
            url: 'https://webhook.site/your-unique-url',
            headers: {
              'Content-Type': 'application/json'
            },
            body: {
              timestamp: '{{ now }}',
              insights: '{{ steps.1.result }}'
            }
          }
        }
      ],
      config: {
        schedule: '0 0 * * *',
        timezone: 'UTC'
      }
    }
  ]

  const categories = [
    { id: 'all', label: 'All Templates', icon: '📋' },
    { id: 'productivity', label: 'Productivity', icon: '📈' },
    { id: 'development', label: 'Development', icon: '💻' },
    { id: 'devops', label: 'DevOps', icon: '🛠️' },
    { id: 'sales', label: 'Sales', icon: '💼' },
    { id: 'data', label: 'Data', icon: '📊' }
  ]

  const [selectedCategory, setSelectedCategory] = useState('all')

  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(t => t.category === selectedCategory)

  const getTriggerIcon = (triggerType: TriggerType) => {
    switch (triggerType) {
      case TriggerType.SCHEDULE: return '⏰'
      case TriggerType.WEBHOOK: return '🔗'
      case TriggerType.EVENT: return '⚡'
      case TriggerType.MANUAL: return '👆'
      default: return '❓'
    }
  }

  const getTriggerLabel = (triggerType: TriggerType) => {
    switch (triggerType) {
      case TriggerType.SCHEDULE: return 'Schedule'
      case TriggerType.WEBHOOK: return 'Webhook'
      case TriggerType.EVENT: return 'Event'
      case TriggerType.MANUAL: return 'Manual'
      default: return triggerType
    }
  }

  const handleUseTemplate = (template: AutomationTemplate) => {
    // TASK-362: Use template by navigating to create page with template data
    localStorage.setItem('automation_template', JSON.stringify(template))
    router.push('/automations/create')
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Automation Templates
        </h1>
        <p className="text-gray-600">
          Get started quickly with pre-built automation templates
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap ${
              selectedCategory === category.id
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <span className="mr-2">{category.icon}</span>
            {category.label}
          </button>
        ))}
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((template) => (
          <div
            key={template.id}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-900">
                  {template.name}
                </h3>
                <span className="text-2xl">
                  {getTriggerIcon(template.trigger_type)}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                {template.description}
              </p>
              <div className="flex items-center text-xs text-gray-500">
                <span className="mr-1">{getTriggerIcon(template.trigger_type)}</span>
                {getTriggerLabel(template.trigger_type)}
                <span className="mx-2">•</span>
                <span>{template.workflow.length} steps</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleUseTemplate(template)}
                className="flex-1 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 font-medium"
              >
                Use Template
              </button>
              <button
                onClick={() => {
                  setSelectedTemplate(template)
                  setShowPreview(true)
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Preview
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No templates in this category
          </h3>
          <p className="text-gray-600">
            Try selecting a different category
          </p>
        </div>
      )}

      {/* TASK-361: Template Preview Modal */}
      {showPreview && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {selectedTemplate.name}
              </h2>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Description</h3>
                <p className="text-gray-600">{selectedTemplate.description}</p>
              </div>

              <div>
                <h3 className="font-medium text-gray-900 mb-2">Trigger</h3>
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <span className="text-2xl mr-2">
                      {getTriggerIcon(selectedTemplate.trigger_type)}
                    </span>
                    <span className="font-medium">
                      {getTriggerLabel(selectedTemplate.trigger_type)}
                    </span>
                  </div>
                  {selectedTemplate.config.schedule && (
                    <div className="text-sm text-gray-600 mt-2">
                      Schedule: {selectedTemplate.config.schedule}
                      {selectedTemplate.config.timezone && ` (${selectedTemplate.config.timezone})`}
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-900 mb-2">
                  Workflow ({selectedTemplate.workflow.length} steps)
                </h3>
                <div className="space-y-3">
                  {selectedTemplate.workflow.map((step, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-medium">
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{step.type}</div>
                          <div className="text-sm text-gray-600 mt-1">
                            {JSON.stringify(step.config, null, 2)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  handleUseTemplate(selectedTemplate)
                  setShowPreview(false)
                }}
                className="flex-1 bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 font-medium"
              >
                Use This Template
              </button>
              <button
                onClick={() => setShowPreview(false)}
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
