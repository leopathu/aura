'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useOrganizationStore } from '@/store/organizationStore'
import api from '@/lib/api'

interface Organization {
  id: string
  name: string
  slug: string
  role: string
}

export default function OrganizationSwitcher() {
  const router = useRouter()
  const { currentOrganization, setCurrentOrganization } = useOrganizationStore()
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetchOrganizations()
  }, [])

  const fetchOrganizations = async () => {
    setIsLoading(true)
    
    try {
      const response = await api.get('/organizations')
      setOrganizations(response.data)
      
      // Set first org as current if none selected
      if (response.data.length > 0 && !currentOrganization) {
        setCurrentOrganization(response.data[0])
      }
    } catch (err) {
      console.error('Failed to load organizations:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectOrganization = (org: Organization) => {
    setCurrentOrganization(org)
    setIsOpen(false)
  }

  const handleCreateNew = () => {
    setIsOpen(false)
    router.push('/organizations/create')
  }

  if (isLoading || organizations.length === 0) {
    return null
  }

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="flex-shrink-0 w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
            <span className="text-purple-600 font-semibold text-sm">
              {currentOrganization?.name?.charAt(0).toUpperCase() || 'O'}
            </span>
          </div>
          <span className="font-medium text-gray-900 truncate">
            {currentOrganization?.name || 'Select Organization'}
          </span>
        </div>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ml-2 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <div className="absolute z-20 mt-2 w-full bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
            <div className="py-1 max-h-64 overflow-y-auto">
              {organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => handleSelectOrganization(org)}
                  className={`w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors ${
                    currentOrganization?.id === org.id ? 'bg-purple-50' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                      <span className="text-purple-600 font-semibold text-sm">
                        {org.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 truncate">{org.name}</div>
                      <div className="text-xs text-gray-500 truncate">/{org.slug}</div>
                    </div>
                    {currentOrganization?.id === org.id && (
                      <svg className="w-5 h-5 text-purple-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>

            {/* Divider */}
            <div className="border-t border-gray-200" />

            {/* Create New Organization */}
            <button
              onClick={handleCreateNew}
              className="w-full px-4 py-2 text-left text-purple-600 hover:bg-purple-50 transition-colors font-medium text-sm"
            >
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create New Organization
              </div>
            </button>
          </div>
        </>
      )}
    </div>
  )
}
