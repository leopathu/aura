'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import api from '@/lib/api'
import ProtectedRoute from '@/components/ProtectedRoute'
import LoadingSpinner from '@/components/LoadingSpinner'

interface Organization {
  id: string
  name: string
  slug: string
  role: string
  created_at: string
  updated_at: string
}

export default function OrganizationsPage() {
  const router = useRouter()
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchOrganizations()
  }, [])

  const fetchOrganizations = async () => {
    setIsLoading(true)
    setError('')
    
    try {
      const response = await api.get('/organizations')
      setOrganizations(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load organizations')
    } finally {
      setIsLoading(false)
    }
  }

  const getRoleBadge = (role: string) => {
    const colors = {
      owner: 'bg-purple-100 text-purple-700',
      admin: 'bg-blue-100 text-blue-700',
      member: 'bg-gray-100 text-gray-700'
    }
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${colors[role as keyof typeof colors] || colors.member}`}>
        {role.charAt(0).toUpperCase() + role.slice(1)}
      </span>
    )
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Organizations</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage your organizations and team workspaces
              </p>
            </div>
            
            <Link
              href="/organizations/create"
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              Create Organization
            </Link>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex justify-center items-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {/* Organizations List */}
          {!isLoading && organizations.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {organizations.map((org) => (
                <div
                  key={org.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => router.push(`/organizations/${org.id}/settings`)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {org.name}
                      </h3>
                      <p className="text-sm text-gray-500">/{org.slug}</p>
                    </div>
                    {getRoleBadge(org.role)}
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>Created {new Date(org.created_at).toLocaleDateString()}</span>
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && organizations.length === 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="text-6xl mb-4">🏢</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No organizations yet
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Organizations help you collaborate with your team. Create your first organization to get started.
              </p>
              <Link
                href="/organizations/create"
                className="inline-block bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium"
              >
                Create Your First Organization
              </Link>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}
