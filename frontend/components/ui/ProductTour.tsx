'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from './Button'

export interface TourStep {
  target: string // CSS selector
  title: string
  content: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  disableBeacon?: boolean
}

interface ProductTourProps {
  steps: TourStep[]
  isOpen: boolean
  onComplete: () => void
  onSkip?: () => void
}

export const ProductTour: React.FC<ProductTourProps> = ({
  steps,
  isOpen,
  onComplete,
  onSkip,
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen || !steps[currentStep]) return

    const updatePosition = () => {
      const targetElement = document.querySelector(steps[currentStep].target)
      if (!targetElement || !tooltipRef.current) return

      const targetRect = targetElement.getBoundingClientRect()
      const tooltipRect = tooltipRef.current.getBoundingClientRect()
      const placement = steps[currentStep].placement || 'bottom'

      let top = 0
      let left = 0

      switch (placement) {
        case 'top':
          top = targetRect.top - tooltipRect.height - 12
          left = targetRect.left + targetRect.width / 2 - tooltipRect.width / 2
          break
        case 'bottom':
          top = targetRect.bottom + 12
          left = targetRect.left + targetRect.width / 2 - tooltipRect.width / 2
          break
        case 'left':
          top = targetRect.top + targetRect.height / 2 - tooltipRect.height / 2
          left = targetRect.left - tooltipRect.width - 12
          break
        case 'right':
          top = targetRect.top + targetRect.height / 2 - tooltipRect.height / 2
          left = targetRect.right + 12
          break
      }

      setPosition({ top, left })

      // Highlight target element
      targetElement.classList.add('tour-highlight')
    }

    updatePosition()
    window.addEventListener('resize', updatePosition)
    window.addEventListener('scroll', updatePosition)

    return () => {
      const targetElement = document.querySelector(steps[currentStep].target)
      if (targetElement) {
        targetElement.classList.remove('tour-highlight')
      }
      window.removeEventListener('resize', updatePosition)
      window.removeEventListener('scroll', updatePosition)
    }
  }, [currentStep, isOpen, steps])

  if (!isOpen) return null

  const step = steps[currentStep]
  const isLastStep = currentStep === steps.length - 1

  const handleNext = () => {
    if (isLastStep) {
      onComplete()
    } else {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    if (onSkip) {
      onSkip()
    } else {
      onComplete()
    }
  }

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-40 pointer-events-none" />

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-4 max-w-sm animate-scale-in"
        style={{ top: `${position.top}px`, left: `${position.left}px` }}
      >
        <div className="mb-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
            <button
              onClick={handleSkip}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close tour"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-sm text-gray-600">{step.content}</p>
        </div>

        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">
            {currentStep + 1} of {steps.length}
          </div>
          <div className="flex space-x-2">
            {currentStep > 0 && (
              <Button size="sm" variant="secondary" onClick={handleBack}>
                Back
              </Button>
            )}
            <Button size="sm" onClick={handleNext}>
              {isLastStep ? 'Done' : 'Next'}
            </Button>
          </div>
        </div>
      </div>

      {/* Add CSS for tour-highlight */}
      <style jsx global>{`
        .tour-highlight {
          position: relative;
          z-index: 45;
          box-shadow: 0 0 0 4px rgba(147, 51, 234, 0.4);
          border-radius: 0.5rem;
        }
      `}</style>
    </>
  )
}

// Example product tour for Aura
export const AuraProductTour: React.FC<{ isOpen: boolean; onComplete: () => void }> = ({
  isOpen,
  onComplete,
}) => {
  const steps: TourStep[] = [
    {
      target: '[data-tour="agents"]',
      title: 'Agents',
      content: 'Create and manage your AI agents here. Each agent can have different capabilities and tools.',
      placement: 'right',
    },
    {
      target: '[data-tour="chat"]',
      title: 'Chat',
      content: 'Interact with your agents in real-time. Ask questions, give commands, and get instant responses.',
      placement: 'right',
    },
    {
      target: '[data-tour="automations"]',
      title: 'Automations',
      content: 'Set up workflows that run automatically on a schedule or when triggered by events.',
      placement: 'right',
    },
    {
      target: '[data-tour="apps"]',
      title: 'Connected Apps',
      content: 'Connect your favorite apps to give your agents access to your data and services.',
      placement: 'bottom',
    },
    {
      target: '[data-tour="settings"]',
      title: 'Settings',
      content: 'Manage your account, credentials, and organization settings here.',
      placement: 'left',
    },
  ]

  return <ProductTour steps={steps} isOpen={isOpen} onComplete={onComplete} />
}
