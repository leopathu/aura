/**
 * API Client Configuration
 * Axios instance with interceptors for authentication
 */

import axios, { AxiosError } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

// Create axios instance
export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
})

// Request interceptor - Add auth token
api.interceptors.request.use(
  (config) => {
    // Get token from Zustand persisted storage
    if (typeof window !== 'undefined') {
      const authStorage = localStorage.getItem('auth-storage')
      if (authStorage) {
        try {
          const parsed = JSON.parse(authStorage)
          const token = parsed.state?.accessToken
          if (token) {
            config.headers.Authorization = `Bearer ${token}`
          }
        } catch (error) {
          console.error('Error parsing auth storage:', error)
        }
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any

    // If 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh token from Zustand storage
        if (typeof window !== 'undefined') {
          const authStorage = localStorage.getItem('auth-storage')
          if (authStorage) {
            const parsed = JSON.parse(authStorage)
            const refreshToken = parsed.state?.refreshToken

            if (refreshToken) {
              const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
                refresh_token: refreshToken,
              })

              const { access_token } = response.data
              
              // Update token in Zustand storage
              parsed.state.accessToken = access_token
              localStorage.setItem('auth-storage', JSON.stringify(parsed))

              // Retry original request with new token
              originalRequest.headers.Authorization = `Bearer ${access_token}`
              return api(originalRequest)
            }
          }
        }
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth-storage')
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api
