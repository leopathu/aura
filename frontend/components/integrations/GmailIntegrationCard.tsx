// Gmail-specific integration component
'use client'

interface GmailIntegrationCardProps {
  isConnected: boolean
  scope?: string | null
  onConnect: () => void
  onDisconnect: () => void
}

export default function GmailIntegrationCard({
  isConnected,
  scope,
  onConnect,
  onDisconnect
}: GmailIntegrationCardProps) {
  const gmailScopes = [
    { name: 'Read emails', included: scope?.includes('gmail.readonly') },
    { name: 'Send emails', included: scope?.includes('gmail.send') },
    { name: 'Compose emails', included: scope?.includes('gmail.compose') },
    { name: 'Modify emails', included: scope?.includes('gmail.modify') }
  ]

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-yellow-500 rounded-lg flex items-center justify-center">
            <svg className="h-7 w-7 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Gmail</h3>
            <p className="text-sm text-gray-600">Email management</p>
          </div>
        </div>
        {isConnected && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Connected
          </span>
        )}
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Connect Gmail to allow AI agents to read, search, and send emails on your behalf.
      </p>

      {isConnected ? (
        <div className="space-y-4">
          {/* Permissions Display */}
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-gray-700 mb-2">Permissions</h4>
            <div className="space-y-1.5">
              {gmailScopes.map((scopeItem) => (
                <div key={scopeItem.name} className="flex items-center gap-2 text-xs">
                  {scopeItem.included ? (
                    <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  <span className={scopeItem.included ? 'text-gray-700' : 'text-gray-400'}>
                    {scopeItem.name}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Agent Capabilities */}
          <div className="bg-purple-50 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-purple-700 mb-2">AI Agent Capabilities</h4>
            <ul className="space-y-1 text-xs text-purple-600">
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>List and read recent emails</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>Search emails with advanced queries</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>Send emails on your behalf</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>Compose draft responses</span>
              </li>
            </ul>
          </div>

          {/* Disconnect Button */}
          <button
            onClick={onDisconnect}
            className="w-full px-4 py-2.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors font-medium"
          >
            Disconnect Gmail
          </button>
        </div>
      ) : (
        <button
          onClick={onConnect}
          className="w-full px-4 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg transition-all font-medium shadow-sm"
        >
          Connect Gmail
        </button>
      )}
    </div>
  )
}
