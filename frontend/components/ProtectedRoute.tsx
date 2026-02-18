'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { user, isLoading } = useAuthStore()

  useEffect(() => {
    if (!isLoading && !user) {
      // Redirect to login with return URL
      const currentPath = window.location.pathname
      router.push(`/login?redirect=${encodeURIComponent(currentPath)}`)
    }
  }, [user, isLoading, router])

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  // Show nothing while redirecting
  if (!user) {
    return null
  }

  // Render children if authenticated
  return <>{children}</>
}
