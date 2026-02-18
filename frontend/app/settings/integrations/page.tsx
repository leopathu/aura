'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/ProtectedRoute'
import { useAuthStore } from '@/store/authStore'
import { useOrganizationStore } from '@/store/organizationStore'
import GoogleOAuthButton from '@/components/oauth/GoogleOAuthButton'
import GmailIntegrationCard from '@/components/integrations/GmailIntegrationCard'
import CalendarIntegrationCard from '@/components/integrations/CalendarIntegrationCard'
import JiraIntegrationCard from '@/components/integrations/JiraIntegrationCard'
import SlackIntegrationCard from '@/components/integrations/SlackIntegrationCard'

interface OAuthConnection {
  provider: string
  is_connected: boolean
  expires_at: string | null
  scope: string | null
}

export default function IntegrationsPage() {
  const currentOrganization = useOrganizationStore((state) => state.currentOrganization)
  const [googleConnection, setGoogleConnection] = useState<OAuthConnection | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (currentOrganization) {
      loadConnections()
    }
  }, [currentOrganization])

  // Check for OAuth callback status
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const oauthStatus = params.get('oauth')
    
    if (oauthStatus === 'success') {
      // Reload connections after successful OAuth
      loadConnections()
      // Clear URL params
      window.history.replaceState({}, '', '/settings/integrations')
    } else if (oauthStatus === 'error') {
      alert('OAuth connection failed. Please try again.')
      window.history.replaceState({}, '', '/settings/integrations')
    }
  }, [])

  const loadConnections = async () => {
    if (!currentOrganization) return

    setIsLoading(true)
    try {
      const token = useAuthStore.getState().accessToken
      
      // Load Google connection status
      const googleResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/oauth/google/status?org_id=${currentOrganization.id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (googleResponse.ok) {
        const googleData = await googleResponse.json()
        setGoogleConnection(googleData)
      }
    } catch (error) {
      console.error('Failed to load connections:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDisconnect = async (provider: string) => {
    if (!currentOrganization) return
    if (!confirm(`Are you sure you want to disconnect ${provider}?`)) return

    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/oauth/${provider}/disconnect?org_id=${currentOrganization.id}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        loadConnections()
      } else {
        alert('Failed to disconnect. Please try again.')
      }
    } catch (error) {
      console.error('Failed to disconnect:', error)
      alert('An error occurred while disconnecting.')
    }
  }

  const handleGoogleConnect = () => {
    if (!currentOrganization) return
    // Trigger OAuth flow - GoogleOAuthButton handles this
    const oauthUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/oauth/google?org_id=${currentOrganization.id}`
    const width = 600
    const height = 700
    const left = window.screen.width / 2 - width / 2
    const top = window.screen.height / 2 - height / 2
    
    window.open(
      oauthUrl,
      'oauth',
      `width=${width},height=${height},left=${left},top=${top}`
    )
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
            <p className="mt-2 text-gray-600">
              Connect your favorite apps and services to use with AI agents
            </p>
          </div>

          {/* Integration Cards */}
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2].map((i) => (
                <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
                  <div className="h-12 w-12 bg-gray-200 rounded-lg mb-4" />
                  <div className="h-6 bg-gray-200 rounded w-1/3 mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-2/3" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Gmail Integration Card */}
              <GmailIntegrationCard
                isConnected={googleConnection?.is_connected || false}
                scope={googleConnection?.scope}
                onConnect={handleGoogleConnect}
                onDisconnect={() => handleDisconnect('google')}
              />

              {/* Calendar Integration Card */}
              <CalendarIntegrationCard
                isConnected={googleConnection?.is_connected || false}
                scope={googleConnection?.scope}
                orgId={currentOrganization?.id || ''}
                onConnect={handleGoogleConnect}
                onDisconnect={() => handleDisconnect('google')}
              />

              {/* Jira Integration Card */}
              <JiraIntegrationCard
                orgId={currentOrganization?.id || ''}
                onRefresh={loadConnections}
              />

              {/* Slack Integration Card */}
              <SlackIntegrationCard />

              {/* Placeholder for future integrations */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 opacity-50">
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                    <svg className="h-7 w-7 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">More Coming Soon</h3>
                    <p className="text-sm text-gray-600">Notion, Trello, and more</p>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  Additional integrations will be available soon.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}
