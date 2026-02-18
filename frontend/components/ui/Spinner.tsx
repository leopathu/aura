'use client'

import React from 'react'

export type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

interface SpinnerProps {
  size?: SpinnerSize
  className?: string
  color?: string
}

const sizeStyles: Record<SpinnerSize, string> = {
  xs: 'h-4 w-4 border-2',
  sm: 'h-6 w-6 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
  xl: 'h-16 w-16 border-4',
}

export const LoadingSpinner: React.FC<SpinnerProps> = ({
  size = 'md',
  className = '',
  color = 'border-gray-300 border-t-primary-600',
}) => {
  return (
    <div
      className={`animate-spin rounded-full ${sizeStyles[size]} ${color} ${className}`}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}

interface LoadingProps {
  text?: string
  fullScreen?: boolean
  size?: SpinnerSize
}

export const Loading: React.FC<LoadingProps> = ({
  text = 'Loading...',
  fullScreen = false,
  size = 'md',
}) => {
  const containerClass = fullScreen
    ? 'fixed inset-0 flex items-center justify-center bg-white bg-opacity-90 z-50'
    : 'flex items-center justify-center py-12'

  return (
    <div className={containerClass}>
      <div className="flex flex-col items-center space-y-4">
        <LoadingSpinner size={size} />
        {text && <p className="text-sm text-gray-600">{text}</p>}
      </div>
    </div>
  )
}

interface DotsSpinnerProps {
  className?: string
}

export const DotsSpinner: React.FC<DotsSpinnerProps> = ({ className = '' }) => {
  return (
    <div className={`flex space-x-1 ${className}`}>
      <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
      <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
      <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
    </div>
  )
}

interface PulseLoaderProps {
  className?: string
}

export const PulseLoader: React.FC<PulseLoaderProps> = ({ className = '' }) => {
  return (
    <div className={`flex space-x-2 ${className}`}>
      <div className="w-3 h-3 bg-primary-600 rounded-full animate-pulse"></div>
      <div className="w-3 h-3 bg-primary-600 rounded-full animate-pulse" style={{ animationDelay: '75ms' }}></div>
      <div className="w-3 h-3 bg-primary-600 rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></div>
    </div>
  )
}
