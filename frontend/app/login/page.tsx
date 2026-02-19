'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/store/authStore'
import LoginForm from '@/components/LoginForm'

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const login = useAuthStore((state) => state.login)
  
  const [serverError, setServerError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (email: string, password: string) => {
    setServerError('')
    setIsLoading(true)

    try {
      await login(email, password)

      // Get redirect URL from query params or default to dashboard
      const redirectTo = searchParams.get('redirect') || '/dashboard'
      router.push(redirectTo)
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed. Please try again.'
      setServerError(errorMessage)
      throw error // Re-throw to let form component know
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-4xl font-bold text-gray-900">
            Welcome back
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <Link href="/register" className="font-medium text-purple-600 hover:text-purple-500">
              Sign up for free
            </Link>
          </p>
        </div>

        <div className="bg-white p-8 rounded-xl shadow-md">
          <LoginForm 
            onSubmit={handleSubmit}
            error={serverError}
            isLoading={isLoading}
          />

          <div className="mt-6 text-center">
            <Link
              href="/forgot-password"
              className="text-sm font-medium text-purple-600 hover:text-purple-500"
            >
              Forgot your password?
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
