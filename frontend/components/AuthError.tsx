'use client'

interface AuthErrorProps {
  error: string | null
  className?: string
}

export default function AuthError({ error, className = '' }: AuthErrorProps) {
  if (!error) return null

  return (
    <div className={`bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg flex items-start ${className}`}>
      <svg
        className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5"
        fill="currentColor"
        viewBox="0 0 20 20"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
          clipRule="evenodd"
        />
      </svg>
      <div className="flex-1">
        <p className="text-sm font-medium">{error}</p>
      </div>
    </div>
  )
}
