'use client'

import { useMemo } from 'react'

interface PasswordStrengthIndicatorProps {
  password: string
  className?: string
}

interface StrengthResult {
  score: number // 0-4
  label: string
  color: string
  bgColor: string
  requirements: {
    length: boolean
    uppercase: boolean
    lowercase: boolean
    number: boolean
    special: boolean
  }
}

export default function PasswordStrengthIndicator({ password, className = '' }: PasswordStrengthIndicatorProps) {
  const strength = useMemo((): StrengthResult => {
    const requirements = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[^A-Za-z0-9]/.test(password),
    }

    const passed = Object.values(requirements).filter(Boolean).length

    if (passed === 0 || password.length === 0) {
      return {
        score: 0,
        label: 'No password',
        color: 'text-gray-500',
        bgColor: 'bg-gray-300',
        requirements,
      }
    } else if (passed <= 2) {
      return {
        score: 1,
        label: 'Weak',
        color: 'text-red-600',
        bgColor: 'bg-red-500',
        requirements,
      }
    } else if (passed === 3) {
      return {
        score: 2,
        label: 'Fair',
        color: 'text-orange-600',
        bgColor: 'bg-orange-500',
        requirements,
      }
    } else if (passed === 4) {
      return {
        score: 3,
        label: 'Good',
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-500',
        requirements,
      }
    } else {
      return {
        score: 4,
        label: 'Strong',
        color: 'text-green-600',
        bgColor: 'bg-green-500',
        requirements,
      }
    }
  }, [password])

  if (!password) return null

  return (
    <div className={`mt-3 ${className}`}>
      {/* Strength Bar */}
      <div className="flex gap-1 mb-2">
        {[1, 2, 3, 4].map((level) => (
          <div
            key={level}
            className={`h-1 flex-1 rounded-full transition-all ${
              level <= strength.score ? strength.bgColor : 'bg-gray-200'
            }`}
          />
        ))}
      </div>

      {/* Strength Label */}
      <p className={`text-sm font-medium ${strength.color} mb-2`}>
        Password strength: {strength.label}
      </p>

      {/* Requirements Checklist */}
      <div className="space-y-1 text-xs">
        <RequirementItem met={strength.requirements.length}>
          At least 8 characters
        </RequirementItem>
        <RequirementItem met={strength.requirements.uppercase}>
          One uppercase letter
        </RequirementItem>
        <RequirementItem met={strength.requirements.lowercase}>
          One lowercase letter
        </RequirementItem>
        <RequirementItem met={strength.requirements.number}>
          One number
        </RequirementItem>
        <RequirementItem met={strength.requirements.special}>
          One special character (optional)
        </RequirementItem>
      </div>
    </div>
  )
}

function RequirementItem({ met, children }: { met: boolean; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      {met ? (
        <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      ) : (
        <svg className="w-4 h-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clipRule="evenodd"
          />
        </svg>
      )}
      <span className={met ? 'text-gray-700' : 'text-gray-400'}>{children}</span>
    </div>
  )
}
