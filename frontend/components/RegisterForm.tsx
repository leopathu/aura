'use client'

import { useState } from 'react'
import PasswordStrengthIndicator from './PasswordStrengthIndicator'

interface RegisterFormProps {
  onSubmit: (data: { email: string; full_name: string; password: string }) => Promise<void>
  error?: string
  isLoading?: boolean
}

export default function RegisterForm({ onSubmit, error, isLoading = false }: RegisterFormProps) {
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [validationError, setValidationError] = useState('')

  const validateForm = () => {
    // Email validation
    if (!email.trim()) {
      setValidationError('Email is required')
      return false
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      setValidationError('Please enter a valid email address')
      return false
    }

    // Full name validation
    if (!fullName.trim()) {
      setValidationError('Full name is required')
      return false
    }

    if (fullName.trim().length < 2) {
      setValidationError('Full name must be at least 2 characters')
      return false
    }

    // Password validation
    if (!password) {
      setValidationError('Password is required')
      return false
    }

    if (password.length < 8) {
      setValidationError('Password must be at least 8 characters long')
      return false
    }

    if (!/[A-Z]/.test(password)) {
      setValidationError('Password must contain at least one uppercase letter')
      return false
    }

    if (!/[a-z]/.test(password)) {
      setValidationError('Password must contain at least one lowercase letter')
      return false
    }

    if (!/[0-9]/.test(password)) {
      setValidationError('Password must contain at least one number')
      return false
    }

    // Confirm password validation
    if (password !== confirmPassword) {
      setValidationError('Passwords do not match')
      return false
    }

    setValidationError('')
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    try {
      await onSubmit({ email, full_name: fullName, password })
    } catch (err) {
      // Error handling is done by parent component
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Email Field */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
          Email Address
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          placeholder="you@example.com"
          disabled={isLoading}
          required
        />
      </div>

      {/* Full Name Field */}
      <div>
        <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-2">
          Full Name
        </label>
        <input
          id="fullName"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          placeholder="John Doe"
          disabled={isLoading}
          required
        />
      </div>

      {/* Password Field */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          placeholder="••••••••"
          disabled={isLoading}
          required
        />
        {password && <PasswordStrengthIndicator password={password} />}
      </div>

      {/* Confirm Password Field */}
      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
          Confirm Password
        </label>
        <input
          id="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          placeholder="••••••••"
          disabled={isLoading}
          required
        />
      </div>

      {/* Validation Error */}
      {validationError && (
        <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm">
          {validationError}
        </div>
      )}

      {/* Server Error */}
      {error && (
        <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-purple-600 text-white py-3 rounded-lg font-medium hover:bg-purple-700 focus:ring-4 focus:ring-purple-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Creating account...
          </span>
        ) : (
          'Create Account'
        )}
      </button>
    </form>
  )
}
