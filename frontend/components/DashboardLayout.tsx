'use client'

import Sidebar from '@/components/Sidebar'
import ProtectedRoute from '@/components/ProtectedRoute'
import EmailVerificationBanner from '@/components/EmailVerificationBanner'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <EmailVerificationBanner />
          <main className="flex-1 overflow-y-auto bg-gray-50">
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
