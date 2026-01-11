'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'

export default function CreateOrganizationPage() {
  const router = useRouter()
  const { user } = useAuthStore()
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSlugChange = (name: string) => {
    // Auto-generate slug from name
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
    setFormData(prev => ({ ...prev, slug }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await api.post('/organizations/', formData)
      
      // Refresh user's organizations list
      const orgsResponse = await api.get('/organizations/')
      useAuthStore.getState().setOrganizations(orgsResponse.data)
      useAuthStore.getState().setCurrentOrg(response.data)
      
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create organization')
    } finally {
      setLoading(false)
    }
  }

  if (!user) {
    router.push('/auth/login')
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-blue-50 px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Create Organization</h1>
          <p className="text-gray-600 mt-2">Set up your workspace to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Organization Name
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => {
                setFormData({ ...formData, name: e.target.value })
                handleSlugChange(e.target.value)
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
              placeholder="Acme Inc"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Slug (URL identifier)
            </label>
            <input
              type="text"
              required
              value={formData.slug}
              onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
              placeholder="acme-inc"
              pattern="[a-z0-9-]+"
            />
            <p className="text-xs text-gray-500 mt-1">
              Only lowercase letters, numbers, and hyphens
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
              placeholder="What does your organization do?"
              rows={3}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating...' : 'Create Organization'}
          </button>

          <button
            type="button"
            onClick={() => router.back()}
            className="w-full text-gray-600 py-2 text-sm hover:text-gray-800"
          >
            Back
          </button>
        </form>
      </div>
    </div>
  )
}
