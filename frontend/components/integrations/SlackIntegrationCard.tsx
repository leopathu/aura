'use client'

import React, { useState, useEffect } from 'react'
import { FaSlack, FaCheck, FaTimes, FaSpinner, FaHashtag, FaLock } from 'react-icons/fa'
import { useAuthStore } from '@/store/authStore'

interface SlackConnectionStatus {
  provider: string
  is_connected: boolean
  expires_at: string | null
  scope: string | null
}

interface SlackWorkspaceInfo {
  team_id: string
  team_name: string
  team_url: string
}

export default function SlackIntegrationCard() {
  const { user, currentOrganization } = useAuthStore()
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [workspaceInfo, setWorkspaceInfo] = useState<SlackWorkspaceInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isDisconnecting, setIsDisconnecting] = useState(false)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

  // Check connection status on mount
  useEffect(() => {
    checkConnectionStatus()
  }, [currentOrganization])

  // Check for OAuth callback success/error
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const oauthStatus = params.get('oauth')
    
    if (oauthStatus === 'success') {
      checkConnectionStatus()
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname)
    } else if (oauthStatus === 'error') {
      setError('Failed to connect to Slack. Please try again.')
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  const checkConnectionStatus = async () => {
    if (!currentOrganization) return

    setIsLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${apiUrl}/api/v1/auth/oauth/slack/status?org_id=${currentOrganization.id}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data: SlackConnectionStatus = await response.json()
        setIsConnected(data.is_connected)

        // If connected, fetch workspace info
        if (data.is_connected) {
          await fetchWorkspaceInfo()
        }
      } else {
        throw new Error('Failed to check connection status')
      }
    } catch (err) {
      console.error('Error checking Slack status:', err)
      setError('Failed to check connection status')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchWorkspaceInfo = async () => {
    if (!currentOrganization) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${apiUrl}/api/v1/integrations/slack/workspace?org_id=${currentOrganization.id}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setWorkspaceInfo(data)
      }
    } catch (err) {
      console.error('Error fetching workspace info:', err)
      // Non-critical error - don't show to user
    }
  }

  const handleConnect = () => {
    if (!currentOrganization) return

    setIsConnecting(true)
    setError(null)

    // Redirect to OAuth flow
    const oauthUrl = `${apiUrl}/api/v1/auth/oauth/slack?org_id=${currentOrganization.id}`
    window.location.href = oauthUrl
  }

  const handleDisconnect = async () => {
    if (!currentOrganization) return

    setIsDisconnecting(true)
    setError(null)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${apiUrl}/api/v1/auth/oauth/slack/disconnect?org_id=${currentOrganization.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        setIsConnected(false)
        setWorkspaceInfo(null)
      } else {
        throw new Error('Failed to disconnect')
      }
    } catch (err) {
      console.error('Error disconnecting Slack:', err)
      setError('Failed to disconnect from Slack')
    } finally {
      setIsDisconnecting(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
            <FaSlack className="text-purple-600 text-2xl" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Slack</h3>
            <p className="text-sm text-gray-500">Team communication</p>
          </div>
        </div>

        {/* Connection Status Badge */}
        {!isLoading && (
          <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
            isConnected 
              ? 'bg-green-100 text-green-700' 
              : 'bg-gray-100 text-gray-600'
          }`}>
            {isConnected ? (
              <>
                <FaCheck className="text-xs" />
                Connected
              </>
            ) : (
              <>
                <FaTimes className="text-xs" />
                Not Connected
              </>
            )}
          </div>
        )}
      </div>

      {/* Description */}
      <p className="text-gray-600 text-sm mb-4">
        Send messages, read conversations, and manage channels directly from your AI agent.
      </p>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <FaSpinner className="animate-spin text-purple-600 text-2xl" />
        </div>
      )}

      {/* Connected State */}
      {!isLoading && isConnected && workspaceInfo && (
        <div className="space-y-4">
          {/* Workspace Info */}
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
            <div className="flex items-center gap-2 mb-2">
              <FaSlack className="text-purple-600" />
              <span className="font-medium text-gray-900">{workspaceInfo.team_name}</span>
            </div>
            <p className="text-sm text-gray-600">
              Team ID: <span className="font-mono text-xs">{workspaceInfo.team_id}</span>
            </p>
            <a 
              href={workspaceInfo.team_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-purple-600 hover:text-purple-700 hover:underline"
            >
              Open workspace →
            </a>
          </div>

          {/* AI Capabilities */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">AI Agent Capabilities</h4>
            <div className="space-y-2">
              <div className="flex items-start gap-2 text-sm text-gray-600">
                <FaCheck className="text-green-500 mt-0.5 flex-shrink-0" />
                <span>Send messages to channels and threads</span>
              </div>
              <div className="flex items-start gap-2 text-sm text-gray-600">
                <FaCheck className="text-green-500 mt-0.5 flex-shrink-0" />
                <span>Read message history from channels</span>
              </div>
              <div className="flex items-start gap-2 text-sm text-gray-600">
                <FaCheck className="text-green-500 mt-0.5 flex-shrink-0" />
                <span>List public and private channels</span>
              </div>
              <div className="flex items-start gap-2 text-sm text-gray-600">
                <FaCheck className="text-green-500 mt-0.5 flex-shrink-0" />
                <span>Get workspace information</span>
              </div>
            </div>
          </div>

          {/* Permissions Info */}
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <p className="text-xs text-gray-600 mb-2 font-medium">Granted Permissions:</p>
            <div className="flex flex-wrap gap-1.5">
              <span className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-700">
                channels:read
              </span>
              <span className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-700">
                chat:write
              </span>
              <span className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-700">
                channels:history
              </span>
              <span className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-700">
                team:read
              </span>
            </div>
          </div>

          {/* Disconnect Button */}
          <button
            onClick={handleDisconnect}
            disabled={isDisconnecting}
            className="w-full py-2.5 px-4 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isDisconnecting ? (
              <>
                <FaSpinner className="animate-spin" />
                Disconnecting...
              </>
            ) : (
              'Disconnect Slack'
            )}
          </button>
        </div>
      )}

      {/* Not Connected State */}
      {!isLoading && !isConnected && (
        <div className="space-y-4">
          {/* Features */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">What you can do:</h4>
            <div className="space-y-2">
              <div className="flex items-start gap-2 text-sm text-gray-600">
                <FaHashtag className="text-purple-500 mt-0.5 flex-shrink-0" />
                <span>Send and receive messages in channels</span>
              </div>
              <div className="flex items-start gap-2 text-sm text-gray-600">
                <FaHashtag className="text-purple-500 mt-0.5 flex-shrink-0" />
                <span>Reply to threads and conversations</span>
              </div>
              <div className="flex items-start gap-2 text-sm text-gray-600">
                <FaLock className="text-purple-500 mt-0.5 flex-shrink-0" />
                <span>Access both public and private channels</span>
              </div>
            </div>
          </div>

          {/* Security Note */}
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <p className="text-xs text-blue-800">
              <strong>Secure OAuth:</strong> Your Slack credentials are encrypted and never stored in plain text.
            </p>
          </div>

          {/* Connect Button */}
          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isConnecting ? (
              <>
                <FaSpinner className="animate-spin" />
                Connecting to Slack...
              </>
            ) : (
              <>
                <FaSlack />
                Connect with Slack
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}
