'use client'

import { formatDistanceToNow } from 'date-fns'

interface Conversation {
  id: string
  title: string
  updated_at: string
}

interface ConversationSidebarProps {
  conversations: Conversation[]
  currentConversationId: string | null
  isOpen: boolean
  onToggle: () => void
  onSelectConversation: (id: string) => void
  onNewChat: () => void
}

export default function ConversationSidebar({
  conversations,
  currentConversationId,
  isOpen,
  onToggle,
  onSelectConversation,
  onNewChat
}: ConversationSidebarProps) {
  if (!isOpen) return null

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          <button
            onClick={onToggle}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
          </svg>
          <span className="font-medium">New Chat</span>
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-6 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-gray-100 rounded-full mb-3">
              <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p className="text-sm text-gray-600">No conversations yet</p>
            <p className="text-xs text-gray-500 mt-1">Start a new chat to begin</p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => onSelectConversation(conversation.id)}
                className={`w-full text-left px-3 py-3 rounded-lg transition-colors ${
                  currentConversationId === conversation.id
                    ? 'bg-purple-50 border border-purple-200'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <p className="font-medium text-gray-900 text-sm truncate">
                  {conversation.title}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatDistanceToNow(new Date(conversation.updated_at), { addSuffix: true })}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
