'use client'

import { useEffect, useState } from 'react'
import Sidebar from '@/components/Sidebar'
import ProtectedRoute from '@/components/ProtectedRoute'
import EmailVerificationBanner from '@/components/EmailVerificationBanner'
import { useOrganizationStore } from '@/store/organizationStore'
import api from '@/lib/api'

interface Organization {
  id: string
  name: string
  slug: string
  role: string
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { currentOrganization, setCurrentOrganization } = useOrganizationStore()
  const [isLoadingOrg, setIsLoadingOrg] = useState(true)

  useEffect(() => {
    loadDefaultOrganization()
  }, [])

  const loadDefaultOrganization = async () => {
    try {
      // If organization already set (from localStorage), just mark as loaded
      if (currentOrganization) {
        setIsLoadingOrg(false)
        return
      }

      // Otherwise, fetch organizations
      const response = await api.get('/organizations')
      if (response.data.length > 0) {
        setCurrentOrganization(response.data[0])
      }
    } catch (err) {
      console.error('Failed to load organization:', err)
    } finally {
      setIsLoadingOrg(false)
    }
  }

  return (
    <ProtectedRoute>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <EmailVerificationBanner />
          <main className="flex-1 overflow-y-auto bg-gray-50">
            {isLoadingOrg ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
              </div>
            ) : (
              children
            )}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
