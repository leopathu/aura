/**
 * Organization Store (Zustand)
 * Manages current organization context
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Organization {
  id: string
  name: string
  slug: string
  role: string
  created_at?: string
  updated_at?: string
}

interface OrganizationState {
  currentOrganization: Organization | null
  setCurrentOrganization: (organization: Organization | null) => void
  clearOrganization: () => void
}

export const useOrganizationStore = create<OrganizationState>()(
  persist(
    (set) => ({
      currentOrganization: null,

      setCurrentOrganization: (organization) => {
        set({ currentOrganization: organization })
      },

      clearOrganization: () => {
        set({ currentOrganization: null })
      }
    }),
    {
      name: 'organization-storage',
      partialize: (state) => ({
        currentOrganization: state.currentOrganization
      })
    }
  )
)
