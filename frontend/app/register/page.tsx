'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/store/authStore'
import RegisterForm from '@/components/RegisterForm'

export default function RegisterPage() {
  const router = useRouter()
  const register = useAuthStore((state) => state.register)
  
  const [serverError, setServerError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (data: { email: string; full_name: string; password: string }) => {
    setServerError('')
    setIsLoading(true)

    try {
      await register(data)

      // Redirect to dashboard on success
      router.push('/dashboard')
    } catch (error: any) {
      setServerError(error.response?.data?.detail || 'Registration failed. Please try again.')
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
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link href="/login" className="font-medium text-purple-600 hover:text-purple-500">
              Sign in
            </Link>
          </p>
        </div>

        <div className="bg-white p-8 rounded-xl shadow-md">
          <RegisterForm 
            onSubmit={handleSubmit}
            error={serverError}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  )
}
