'use client'

import { useState, useEffect, useRef } from 'react'
import ProtectedRoute from '@/components/ProtectedRoute'
import { useAuthStore } from '@/store/authStore'
import { useOrganizationStore } from '@/store/organizationStore'
import MessageList from '@/components/chat/MessageList'
import MessageInput from '@/components/chat/MessageInput'
import ConversationSidebar from '@/components/chat/ConversationSidebar'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}

interface Conversation {
  id: string
  title: string
  updated_at: string
}

export default function ChatPage() {
  const user = useAuthStore((state) => state.user)
  const currentOrganization = useOrganizationStore((state) => state.currentOrganization)
  
  const [messages, setMessages] = useState<Message[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load conversations on mount
  useEffect(() => {
    if (currentOrganization) {
      loadConversations()
    }
  }, [currentOrganization])

  const loadConversations = async () => {
    if (!currentOrganization) return
    
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/history?org_id=${currentOrganization.id}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setConversations(data)
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const loadConversation = async (conversationId: string) => {
    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/${conversationId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages)
        setCurrentConversationId(conversationId)
      }
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }

  const handleSendMessage = async (content: string) => {
    if (!currentOrganization) return
    
    // For now, use a default agent ID (this should be selectable)
    const agentId = 'default-agent-id' // TODO: Add agent selection
    
    setIsLoading(true)
    
    // Optimistic update
    const tempMessage: Message = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    }
    setMessages((prev) => [...prev, tempMessage])

    try {
      const token = useAuthStore.getState().accessToken
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            agent_id: agentId,
            message: content,
            conversation_id: currentConversationId,
            stream: true
          })
        }
      )

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      // Handle SSE streaming
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      let assistantMessage = ''
      let conversationId = currentConversationId

      while (true) {
        const { done, value } = await reader!.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            
            if (data === '[DONE]') {
              break
            }

            try {
              const parsed = JSON.parse(data)
              
              if (parsed.conversation_id) {
                conversationId = parsed.conversation_id
                setCurrentConversationId(conversationId)
              }
              
              if (parsed.chunk) {
                assistantMessage += parsed.chunk
                
                // Update assistant message in real-time
                setMessages((prev) => {
                  const withoutTemp = prev.filter((m) => !m.id.startsWith('assistant-temp'))
                  return [
                    ...withoutTemp,
                    {
                      id: 'assistant-temp-' + Date.now(),
                      role: 'assistant',
                      content: assistantMessage,
                      created_at: new Date().toISOString()
                    }
                  ]
                })
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }

      // Reload conversations to update sidebar
      loadConversations()
      
    } catch (error) {
      console.error('Failed to send message:', error)
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => !m.id.startsWith('temp-')))
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setCurrentConversationId(null)
  }

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-gray-50">
        {/* Sidebar */}
        <ConversationSidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          onSelectConversation={loadConversation}
          onNewChat={handleNewChat}
        />

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {!isSidebarOpen && (
                  <button
                    onClick={() => setIsSidebarOpen(true)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                )}
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">
                    {currentConversationId 
                      ? conversations.find(c => c.id === currentConversationId)?.title || 'Chat'
                      : 'New Chat'
                    }
                  </h1>
                  <p className="text-sm text-gray-500">{currentOrganization?.name}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                    <svg className="h-8 w-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                    Start a conversation
                  </h2>
                  <p className="text-gray-600">
                    Ask anything, and your AI assistant will help you out.
                  </p>
                </div>
              </div>
            ) : (
              <>
                <MessageList messages={messages} />
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 bg-white px-6 py-4">
            <MessageInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              disabled={!currentOrganization}
            />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
