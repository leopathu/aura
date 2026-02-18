'use client'

/**
 * Activity Details Modal
 * 
 * TASK-308: Activity details modal
 * Shows detailed information about a single activity log entry
 */

import { Activity } from '@/types/activity'
import { format } from 'date-fns'
import { motion, AnimatePresence } from 'framer-motion'

interface ActivityDetailsModalProps {
  activity: Activity
  onClose: () => void
}

export default function ActivityDetailsModal({
  activity,
  onClose,
}: ActivityDetailsModalProps) {
  // Format JSON details for display
  const formatDetails = (details: Record<string, any>): string => {
    return JSON.stringify(details, null, 2)
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-y-auto">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        />

        {/* Modal */}
        <div className="flex min-h-full items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white">Activity Details</h2>
                <button
                  onClick={onClose}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Activity ID
                  </label>
                  <div className="text-sm font-mono text-gray-900 bg-gray-50 px-3 py-2 rounded-lg">
                    {activity.id}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Timestamp
                  </label>
                  <div className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-lg">
                    {format(new Date(activity.created_at), 'MMM d, yyyy h:mm:ss a')}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Action
                  </label>
                  <div className="text-sm font-medium text-gray-900 bg-purple-50 px-3 py-2 rounded-lg">
                    {activity.action}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Organization ID
                  </label>
                  <div className="text-sm font-mono text-gray-900 bg-gray-50 px-3 py-2 rounded-lg truncate">
                    {activity.org_id}
                  </div>
                </div>

                {activity.agent_id && (
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Agent ID
                    </label>
                    <div className="text-sm font-mono text-gray-900 bg-blue-50 px-3 py-2 rounded-lg truncate">
                      {activity.agent_id}
                    </div>
                  </div>
                )}

                {activity.user_id && (
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      User ID
                    </label>
                    <div className="text-sm font-mono text-gray-900 bg-green-50 px-3 py-2 rounded-lg truncate">
                      {activity.user_id}
                    </div>
                  </div>
                )}
              </div>

              {/* Details */}
              {activity.details && Object.keys(activity.details).length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-2">
                    Details
                  </label>
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-xs text-green-400 font-mono">
                      {formatDetails(activity.details)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Metadata Table */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-2">
                  Summary
                </label>
                <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg overflow-hidden">
                  <tbody className="divide-y divide-gray-200">
                    {activity.details.message && (
                      <tr>
                        <td className="px-4 py-3 text-xs font-medium text-gray-500 bg-gray-50 w-1/3">
                          Message
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {activity.details.message}
                        </td>
                      </tr>
                    )}
                    {activity.details.description && (
                      <tr>
                        <td className="px-4 py-3 text-xs font-medium text-gray-500 bg-gray-50">
                          Description
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {activity.details.description}
                        </td>
                      </tr>
                    )}
                    {activity.details.agent_name && (
                      <tr>
                        <td className="px-4 py-3 text-xs font-medium text-gray-500 bg-gray-50">
                          Agent Name
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {activity.details.agent_name}
                        </td>
                      </tr>
                    )}
                    {activity.details.user_name && (
                      <tr>
                        <td className="px-4 py-3 text-xs font-medium text-gray-500 bg-gray-50">
                          User Name
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {activity.details.user_name}
                        </td>
                      </tr>
                    )}
                    {activity.details.status && (
                      <tr>
                        <td className="px-4 py-3 text-xs font-medium text-gray-500 bg-gray-50">
                          Status
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              activity.details.status === 'success'
                                ? 'bg-green-100 text-green-800'
                                : activity.details.status === 'error'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {activity.details.status}
                          </span>
                        </td>
                      </tr>
                    )}
                    {activity.details.duration && (
                      <tr>
                        <td className="px-4 py-3 text-xs font-medium text-gray-500 bg-gray-50">
                          Duration
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {activity.details.duration}ms
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 flex justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-colors"
              >
                Close
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </AnimatePresence>
  )
}
