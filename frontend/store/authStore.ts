/**
 * Authentication Store (Zustand)
 * Manages user authentication state
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '@/lib/api'
import { useOrganizationStore } from './organizationStore'

interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isLoading: boolean
  
  // Actions
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; full_name: string; password: string }) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<void>
  fetchCurrentUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/auth/login', { email, password })
          const { access_token, refresh_token, user_id, email: userEmail, full_name } = response.data
          
          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            user: {
              id: user_id,
              email: userEmail,
              full_name,
              is_active: true,
              is_verified: false,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          })

          // Fetch full user details
          await get().fetchCurrentUser()
        } finally {
          set({ isLoading: false })
        }
      },

      register: async (data: { email: string; full_name: string; password: string }) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/auth/register', data)
          const { access_token, refresh_token, user_id, email, full_name } = response.data
          
          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            user: {
              id: user_id,
              email,
              full_name,
              is_active: true,
              is_verified: false,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          })

          // Fetch full user details
          await get().fetchCurrentUser()
        } finally {
          set({ isLoading: false })
        }
      },

      logout: () => {
        // Clear organization context on logout
        useOrganizationStore.getState().clearOrganization()
        
        set({
          user: null,
          accessToken: null,
          refreshToken: null
        })
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get()
        if (!refreshToken) {
          throw new Error('No refresh token available')
        }

        try {
          const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
          set({ accessToken: response.data.access_token })
        } catch (error) {
          // If refresh fails, logout
          get().logout()
          throw error
        }
      },

      fetchCurrentUser: async () => {
        try {
          const response = await api.get('/auth/me')
          set({ user: response.data })
        } catch (error) {
          console.error('Failed to fetch current user:', error)
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken
      })
    }
  )
)
