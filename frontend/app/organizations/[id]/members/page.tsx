'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import api from '@/lib/api'
import ProtectedRoute from '@/components/ProtectedRoute'
import LoadingSpinner from '@/components/LoadingSpinner'

interface Member {
  id: string
  user_id: string
  email: string
  full_name: string
  role: string
  joined_at: string
}

interface Organization {
  id: string
  name: string
  slug: string
  role: string
}

export default function OrganizationMembersPage() {
  const router = useRouter()
  const params = useParams()
  const orgId = params.id as string

  const [organization, setOrganization] = useState<Organization | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isInviting, setIsInviting] = useState(false)
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    fetchOrganization()
    fetchMembers()
  }, [orgId])

  const fetchOrganization = async () => {
    try {
      const response = await api.get(`/organizations/${orgId}`)
      setOrganization(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load organization')
    }
  }

  const fetchMembers = async () => {
    setIsLoading(true)
    setError('')
    
    try {
      const response = await api.get(`/organizations/${orgId}/members`)
      setMembers(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load members')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')

    if (!inviteEmail.trim()) {
      setError('Email is required')
      return
    }

    setIsInviting(true)

    try {
      await api.post(`/organizations/${orgId}/members`, {
        email: inviteEmail.trim(),
        role: inviteRole
      })
      
      setSuccessMessage('Member invited successfully')
      setShowInviteForm(false)
      setInviteEmail('')
      setInviteRole('member')
      
      // Refresh members list
      fetchMembers()
      
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to invite member')
    } finally {
      setIsInviting(false)
    }
  }

  const handleRemoveMember = async (userId: string) => {
    if (!confirm('Are you sure you want to remove this member?')) {
      return
    }

    try {
      await api.delete(`/organizations/${orgId}/members/${userId}`)
      setSuccessMessage('Member removed successfully')
      fetchMembers()
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove member')
    }
  }

  const getRoleBadge = (role: string) => {
    const colors = {
      owner: 'bg-purple-100 text-purple-700',
      admin: 'bg-blue-100 text-blue-700',
      member: 'bg-gray-100 text-gray-700'
    }
    
    return (
      <span className={`px-3 py-1 text-xs font-medium rounded-full ${colors[role as keyof typeof colors] || colors.member}`}>
        {role.charAt(0).toUpperCase() + role.slice(1)}
      </span>
    )
  }

  const canInvite = organization?.role === 'owner' || organization?.role === 'admin'
  const canRemove = organization?.role === 'owner' || organization?.role === 'admin'

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <LoadingSpinner size="lg" />
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
            <h1 className="text-3xl font-bold text-gray-900 mt-2">{organization?.name}</h1>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-gray-200 mb-8">
            <nav className="flex gap-8">
              <Link
                href={`/organizations/${orgId}/settings`}
                className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 py-4 px-1 text-sm font-medium"
              >
                Settings
              </Link>
              <Link
                href={`/organizations/${orgId}/members`}
                className="border-b-2 border-purple-600 text-purple-600 py-4 px-1 text-sm font-medium"
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

          {/* Invite Button */}
          {canInvite && !showInviteForm && (
            <div className="mb-6">
              <button
                onClick={() => setShowInviteForm(true)}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium"
              >
                Invite Member
              </button>
            </div>
          )}

          {/* Invite Form */}
          {showInviteForm && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Invite New Member</h2>
              
              <form onSubmit={handleInvite} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    placeholder="colleague@example.com"
                    disabled={isInviting}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-2">
                    Role
                  </label>
                  <select
                    id="role"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    disabled={isInviting}
                  >
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                    {organization?.role === 'owner' && <option value="owner">Owner</option>}
                  </select>
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowInviteForm(false)
                      setInviteEmail('')
                      setInviteRole('member')
                    }}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                    disabled={isInviting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isInviting}
                    className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {isInviting ? 'Inviting...' : 'Send Invite'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Members List */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Members ({members.length})
              </h2>
            </div>

            <div className="divide-y divide-gray-200">
              {members.map((member) => (
                <div key={member.id} className="px-6 py-4 flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-900">{member.full_name}</h3>
                    <p className="text-sm text-gray-500">{member.email}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Joined {new Date(member.joined_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    {getRoleBadge(member.role)}
                    
                    {canRemove && member.role !== 'owner' && (
                      <button
                        onClick={() => handleRemoveMember(member.user_id)}
                        className="text-red-600 hover:text-red-700 text-sm font-medium"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {members.length === 0 && (
                <div className="px-6 py-12 text-center text-gray-500">
                  No members yet
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
