'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import api from '@/lib/api'
import ProtectedRoute from '@/components/ProtectedRoute'

export default function CreateOrganizationPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!name.trim()) {
      setError('Organization name is required')
      return
    }

    if (name.trim().length < 2) {
      setError('Organization name must be at least 2 characters')
      return
    }

    setIsLoading(true)

    try {
      const response = await api.post('/organizations', { name: name.trim() })
      const org = response.data
      
      // Redirect to organization settings
      router.push(`/organizations/${org.id}/settings`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create organization')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Create Organization
            </h1>
            <p className="text-gray-600">
              Start collaborating with your team
            </p>
          </div>

          {/* Form */}
          <div className="bg-white rounded-xl shadow-md p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Organization Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Organization Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Acme Inc."
                  disabled={isLoading}
                  required
                />
                <p className="mt-2 text-xs text-gray-500">
                  This will be the name of your workspace
                </p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Buttons */}
              <div className="flex gap-3">
                <Link
                  href="/organizations"
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium text-center"
                >
                  Cancel
                </Link>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 bg-purple-600 text-white py-3 rounded-lg font-medium hover:bg-purple-700 focus:ring-4 focus:ring-purple-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Creating...
                    </span>
                  ) : (
                    'Create Organization'
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Info */}
          <div className="mt-6 text-center text-sm text-gray-500">
            <p>You'll be the owner of this organization</p>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
