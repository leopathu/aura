'use client'

import { useAuthStore } from '@/store/authStore'
import Link from 'next/link'

export default function EmailVerificationBanner() {
  const user = useAuthStore((state) => state.user)

  if (!user || user.is_verified) {
    return null
  }

  return (
    <div className="bg-yellow-50 border-b border-yellow-200">
      <div className="max-w-7xl mx-auto py-3 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between flex-wrap">
          <div className="w-0 flex-1 flex items-center">
            <span className="flex p-2 rounded-lg bg-yellow-100">
              <svg className="h-5 w-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </span>
            <p className="ml-3 font-medium text-yellow-800">
              <span className="md:hidden">Please verify your email address</span>
              <span className="hidden md:inline">
                Please verify your email address to access all features
              </span>
            </p>
          </div>
          <div className="order-3 mt-2 flex-shrink-0 w-full sm:order-2 sm:mt-0 sm:w-auto">
            <Link
              href="/resend-verification"
              className="flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-yellow-800 bg-yellow-100 hover:bg-yellow-200 transition-colors"
            >
              Resend verification email
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
