'use client'

import DashboardLayout from '@/components/DashboardLayout'
import OrganizationSwitcher from '@/components/OrganizationSwitcher'
import { useAuthStore } from '@/store/authStore'

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user)

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome back, {user?.full_name}!
            </h1>
            <p className="mt-2 text-gray-600">
              Here's what's happening with your AI assistants
            </p>
          </div>
          
          <div className="w-64 ml-4">
            <OrganizationSwitcher />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Agents</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">0</p>
                </div>
                <div className="bg-purple-100 p-3 rounded-lg">
                  <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Connected Apps</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">0</p>
                </div>
                <div className="bg-blue-100 p-3 rounded-lg">
                  <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Tasks Completed</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">0</p>
                </div>
                <div className="bg-green-100 p-3 rounded-lg">
                  <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No agents yet</h3>
            <p className="mt-2 text-sm text-gray-500">
              Get started by creating your first AI agent
            </p>
            <div className="mt-6">
              <a
                href="/agents/create"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                Create Agent
              </a>
            </div>
          </div>
        </div>
      </DashboardLayout>
    )
  }
