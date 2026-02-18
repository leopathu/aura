// Jira-specific integration component
'use client'

import { useState, useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'

interface JiraProject {
  key: string
  name: string
  id: string
}

interface JiraIntegrationCardProps {
  orgId: string
  onRefresh?: () => void
}

export default function JiraIntegrationCard({
  orgId,
  onRefresh
}: JiraIntegrationCardProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [projects, setProjects] = useState<JiraProject[]>([])
  const [loadingProjects, setLoadingProjects] = useState(false)
  const [showSetupModal, setShowSetupModal] = useState(false)
  const [jiraServer, setJiraServer] = useState('')
  const [jiraEmail, setJiraEmail] = useState('')
  const [jiraToken, setJiraToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    checkConnection()
  }, [orgId])

  const checkConnection = async () => {
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials?org_id=${orgId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        const jiraCred = data.find((c: any) => c.credential_type === 'jira')
        setIsConnected(!!jiraCred)
        
        if (jiraCred) {
          loadProjects()
        }
      }
    } catch (error) {
      console.error('Failed to check Jira connection:', error)
    }
  }

  const loadProjects = async () => {
    setLoadingProjects(true)
    try {
      // In production, this would call the Jira service to get projects
      // For now, just set empty array
      setProjects([])
    } catch (error) {
      console.error('Failed to load Jira projects:', error)
    } finally {
      setLoadingProjects(false)
    }
  }

  const handleConnect = async () => {
    setLoading(true)
    setError('')
    
    try {
      // Format: server|email|token
      const apiKey = `${jiraServer}|${jiraEmail}|${jiraToken}`
      
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials?org_id=${orgId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            credential_type: 'jira',
            api_key: apiKey,
            label: 'Jira API Token'
          })
        }
      )

      if (response.ok) {
        setShowSetupModal(false)
        setJiraServer('')
        setJiraEmail('')
        setJiraToken('')
        checkConnection()
        if (onRefresh) onRefresh()
      } else {
        const data = await response.json()
        setError(data.detail || 'Failed to save Jira credentials')
      }
    } catch (error) {
      console.error('Failed to connect Jira:', error)
      setError('An error occurred while connecting Jira')
    } finally {
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect Jira?')) return

    try {
      const token = useAuthStore.getState().accessToken
      const credResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials?org_id=${orgId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (credResponse.ok) {
        const credentials = await credResponse.json()
        const jiraCred = credentials.find((c: any) => c.credential_type === 'jira')
        
        if (jiraCred) {
          const deleteResponse = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/api/v1/credentials/${jiraCred.id}?org_id=${orgId}`,
            {
              method: 'DELETE',
              headers: {
                Authorization: `Bearer ${token}`
              }
            }
          )

          if (deleteResponse.ok) {
            checkConnection()
            if (onRefresh) onRefresh()
          } else {
            alert('Failed to disconnect Jira')
          }
        }
      }
    } catch (error) {
      console.error('Failed to disconnect Jira:', error)
      alert('An error occurred while disconnecting Jira')
    }
  }

  return (
    <>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg flex items-center justify-center">
              <svg className="h-7 w-7 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.571 11.513H0a5.218 5.218 0 0 0 5.232 5.215h2.13v2.057A5.215 5.215 0 0 0 12.575 24V12.518a1.005 1.005 0 0 0-1.004-1.005zm5.723-5.756H5.736a5.215 5.215 0 0 0 5.215 5.214h2.129v2.058a5.218 5.218 0 0 0 5.215 5.214V6.758a1.001 1.001 0 0 0-1.001-1.001zM23.013 0H11.455a5.215 5.215 0 0 0 5.215 5.215h2.129v2.057A5.215 5.215 0 0 0 24 12.483V1.005A1.001 1.001 0 0 0 23.013 0z"/>
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Jira</h3>
              <p className="text-sm text-gray-600">Issue tracking</p>
            </div>
          </div>
          {isConnected && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Connected
            </span>
          )}
        </div>

        <p className="text-sm text-gray-600 mb-4">
          Connect Jira to allow AI agents to search, create, and update issues and projects.
        </p>

        {isConnected ? (
          <div className="space-y-4">
            {/* AI Agent Capabilities */}
            <div className="bg-purple-50 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-purple-700 mb-2">AI Agent Capabilities</h4>
              <ul className="space-y-1 text-xs text-purple-600">
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">•</span>
                  <span>Search and filter issues using JQL</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">•</span>
                  <span>View detailed issue information and comments</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">•</span>
                  <span>Create new tasks, bugs, and stories</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">•</span>
                  <span>Update issue status and assignments</span>
                </li>
              </ul>
            </div>

            {/* Connected Projects */}
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-semibold text-blue-700">Connected Projects</h4>
                <button
                  onClick={loadProjects}
                  disabled={loadingProjects}
                  className="text-xs text-blue-600 hover:text-blue-700 disabled:opacity-50"
                >
                  {loadingProjects ? 'Loading...' : 'Refresh'}
                </button>
              </div>

              {loadingProjects ? (
                <div className="space-y-2">
                  {[1, 2].map((i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-3 bg-blue-200 rounded w-2/3" />
                    </div>
                  ))}
                </div>
              ) : projects.length > 0 ? (
                <div className="space-y-1.5">
                  {projects.slice(0, 5).map((project) => (
                    <div key={project.key} className="flex items-center gap-2">
                      <span className="text-xs font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                        {project.key}
                      </span>
                      <span className="text-xs text-gray-700">{project.name}</span>
                    </div>
                  ))}
                  {projects.length > 5 && (
                    <p className="text-xs text-blue-600">+{projects.length - 5} more projects</p>
                  )}
                </div>
              ) : (
                <p className="text-xs text-gray-500">Connect to see your Jira projects</p>
              )}
            </div>

            {/* Disconnect Button */}
            <button
              onClick={handleDisconnect}
              className="w-full px-4 py-2.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors font-medium"
            >
              Disconnect Jira
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowSetupModal(true)}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg transition-all font-medium shadow-sm"
          >
            Connect Jira
          </button>
        )}
      </div>

      {/* Setup Modal */}
      {showSetupModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Connect Jira</h3>
              <button
                onClick={() => setShowSetupModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Jira Server URL
                </label>
                <input
                  type="url"
                  value={jiraServer}
                  onChange={(e) => setJiraServer(e.target.value)}
                  placeholder="https://your-domain.atlassian.net"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">Your Jira Cloud instance URL</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={jiraEmail}
                  onChange={(e) => setJiraEmail(e.target.value)}
                  placeholder="your-email@example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">Your Jira account email</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Token
                </label>
                <input
                  type="password"
                  value={jiraToken}
                  onChange={(e) => setJiraToken(e.target.value)}
                  placeholder="Your Jira API token"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Generate at{' '}
                  <a
                    href="https://id.atlassian.com/manage-profile/security/api-tokens"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-600 hover:text-purple-700"
                  >
                    Atlassian Account Settings
                  </a>
                </p>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => setShowSetupModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConnect}
                  disabled={loading || !jiraServer || !jiraEmail || !jiraToken}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Connecting...' : 'Connect'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
