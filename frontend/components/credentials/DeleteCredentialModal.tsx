'use client'

interface DeleteCredentialModalProps {
  credential: {
    id: string
    label: string | null
    credential_type: string
  }
  onClose: () => void
  onConfirm: () => void
}

export default function DeleteCredentialModal({ credential, onClose, onConfirm }: DeleteCredentialModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        {/* Icon */}
        <div className="flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mb-4">
          <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        {/* Content */}
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Delete Credential</h2>
        <p className="text-gray-600 mb-6">
          Are you sure you want to delete this <span className="font-semibold">{credential.credential_type}</span> credential
          {credential.label && <> (<span className="font-semibold">{credential.label}</span>)</>}?
          This action cannot be undone and may affect agents using this credential.
        </p>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
          >
            Delete Credential
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg transition-colors font-medium"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
