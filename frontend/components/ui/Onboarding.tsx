'use client'

import React, { useState } from 'react'
import { Button } from './Button'
import { StepIndicator } from './Progress'

export interface OnboardingStep {
  title: string
  description: string
  content: React.ReactNode
  canSkip?: boolean
}

interface OnboardingFlowProps {
  steps: OnboardingStep[]
  onComplete: () => void
  onSkip?: () => void
}

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({
  steps,
  onComplete,
  onSkip,
}) => {
  const [currentStep, setCurrentStep] = useState(0)

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      onComplete()
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

  const step = steps[currentStep]
  const isLastStep = currentStep === steps.length - 1

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full overflow-hidden">
        {/* Progress */}
        <div className="px-6 pt-6">
          <StepIndicator
            steps={steps.map(s => s.title)}
            currentStep={currentStep}
          />
        </div>

        {/* Content */}
        <div className="px-6 py-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{step.title}</h2>
          <p className="text-gray-600 mb-6">{step.description}</p>
          <div className="min-h-[200px]">{step.content}</div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between">
          <div>
            {step.canSkip && (
              <Button variant="ghost" onClick={handleSkip}>
                Skip
              </Button>
            )}
          </div>
          <div className="flex space-x-2">
            {currentStep > 0 && (
              <Button variant="secondary" onClick={handleBack}>
                Back
              </Button>
            )}
            <Button onClick={handleNext}>
              {isLastStep ? 'Get Started' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Welcome onboarding for new users
export const WelcomeOnboarding: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  const steps: OnboardingStep[] = [
    {
      title: 'Welcome to Aura',
      description: 'Your personal AI assistant platform',
      content: (
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-primary-100 mb-4">
            <svg className="w-12 h-12 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Let's get you started!</h3>
          <p className="text-gray-600">
            Aura helps you automate tasks, connect your favorite apps, and build powerful AI agents.
          </p>
        </div>
      ),
      canSkip: true,
    },
    {
      title: 'Connect Your Apps',
      description: 'Link your favorite tools and services',
      content: (
        <div>
          <p className="text-gray-700 mb-4">
            Connect apps like Gmail, Slack, Jira, and more to give your AI agents access to your data.
          </p>
          <div className="grid grid-cols-3 gap-4">
            {['Gmail', 'Slack', 'Jira', 'Calendar', 'Notion', 'Drive'].map(app => (
              <div key={app} className="p-4 border border-gray-200 rounded-lg text-center hover:border-primary-500 transition-colors cursor-pointer">
                <div className="w-12 h-12 bg-gray-100 rounded-lg mx-auto mb-2"></div>
                <p className="text-sm font-medium text-gray-900">{app}</p>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    {
      title: 'Create Your First Agent',
      description: 'Build an AI assistant tailored to your needs',
      content: (
        <div>
          <p className="text-gray-700 mb-4">
            Agents can help you automate workflows, answer questions, and perform tasks across your connected apps.
          </p>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-2">Example Agents:</h4>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">•</span>
                <span>Email assistant that drafts and sends messages</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">•</span>
                <span>Calendar manager that schedules meetings</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">•</span>
                <span>Task tracker that updates Jira tickets</span>
              </li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      title: 'Set Up Automations',
      description: 'Schedule tasks to run automatically',
      content: (
        <div>
          <p className="text-gray-700 mb-4">
            Create automations that run on a schedule or triggered by events to save time on repetitive tasks.
          </p>
          <div className="space-y-3">
            <div className="flex items-start p-3 bg-blue-50 rounded-lg border border-blue-200">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-medium text-gray-900 text-sm">Daily standup summary</p>
                <p className="text-xs text-gray-600">Get a summary of your tasks every morning</p>
              </div>
            </div>
            <div className="flex items-start p-3 bg-green-50 rounded-lg border border-green-200">
              <svg className="w-5 h-5 text-green-600 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-medium text-gray-900 text-sm">Ticket triage</p>
                <p className="text-xs text-gray-600">Automatically categorize new support tickets</p>
              </div>
            </div>
          </div>
        </div>
      ),
    },
  ]

  return <OnboardingFlow steps={steps} onComplete={onComplete} />
}
