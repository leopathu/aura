'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
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

export default function OrganizationSettingsPage() {
  const router = useRouter()
  const params = useParams()
  const orgId = params.id as string

  const [organization, setOrganization] = useState<Organization | null>(null)
  const [name, setName] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    fetchOrganization()
  }, [orgId])

  const fetchOrganization = async () => {
    setIsLoading(true)
    setError('')
    
    try {
      const response = await api.get(`/organizations/${orgId}`)
      setOrganization(response.data)
      setName(response.data.name)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load organization')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdateName = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')

    if (!name.trim()) {
      setError('Organization name is required')
      return
    }

    setIsSaving(true)

    try {
      const response = await api.patch(`/organizations/${orgId}`, { name: name.trim() })
      setOrganization(response.data)
      setSuccessMessage('Organization name updated successfully')
      
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update organization')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    setError('')

    try {
      await api.delete(`/organizations/${orgId}`)
      router.push('/organizations')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete organization')
      setIsDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  const canEdit = organization?.role === 'owner' || organization?.role === 'admin'
  const canDelete = organization?.role === 'owner'

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </ProtectedRoute>
    )
  }

  if (!organization) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Organization not found</h2>
            <Link href="/organizations" className="text-purple-600 hover:text-purple-700">
              Back to organizations
            </Link>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <Link
              href="/organizations"
              className="text-sm text-purple-600 hover:text-purple-700 mb-2 inline-flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to organizations
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mt-2">{organization.name}</h1>
            <p className="text-sm text-gray-500 mt-1">/{organization.slug}</p>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-gray-200 mb-8">
            <nav className="flex gap-8">
              <Link
                href={`/organizations/${orgId}/settings`}
                className="border-b-2 border-purple-600 text-purple-600 py-4 px-1 text-sm font-medium"
              >
                Settings
              </Link>
              <Link
                href={`/organizations/${orgId}/members`}
                className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 py-4 px-1 text-sm font-medium"
              >
                Members
              </Link>
            </nav>
          </div>

          {/* Messages */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {successMessage && (
            <div className="mb-6 bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-lg">
              {successMessage}
            </div>
          )}

          {/* General Settings */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">General Settings</h2>
            
            <form onSubmit={handleUpdateName} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Organization Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                  disabled={!canEdit || isSaving}
                  required
                />
              </div>

              {canEdit && (
                <button
                  type="submit"
                  disabled={isSaving || name.trim() === organization.name}
                  className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              )}

              {!canEdit && (
                <p className="text-sm text-gray-500">
                  Only admins and owners can edit organization settings
                </p>
              )}
            </form>
          </div>

          {/* Danger Zone */}
          {canDelete && (
            <div className="bg-white rounded-xl shadow-sm border border-red-200 p-6">
              <h2 className="text-xl font-semibold text-red-600 mb-4">Danger Zone</h2>
              
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-900 mb-1">
                    Delete Organization
                  </h3>
                  <p className="text-sm text-gray-500">
                    Permanently delete this organization and all its data. This action cannot be undone.
                  </p>
                </div>

                {!showDeleteConfirm ? (
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="ml-4 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors font-medium whitespace-nowrap"
                  >
                    Delete Organization
                  </button>
                ) : (
                  <div className="ml-4 flex gap-2">
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                      disabled={isDeleting}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleDelete}
                      disabled={isDeleting}
                      className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors font-medium disabled:opacity-50"
                    >
                      {isDeleting ? 'Deleting...' : 'Confirm Delete'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}
