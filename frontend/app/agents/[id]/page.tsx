'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'

interface Agent {
  id: string
  name: string
  description: string
  system_prompt: string
  is_active: boolean
}

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function AgentChatPage() {
  const router = useRouter()
  const params = useParams()
  const { currentOrg } = useAuthStore()
  const [agent, setAgent] = useState<Agent | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (currentOrg && params.id) {
      loadAgent()
    }
  }, [currentOrg, params.id])

  const loadAgent = async () => {
    try {
      const response = await api.get(`/organizations/${currentOrg?.id}/agents/${params.id}`)
      setAgent(response.data)
    } catch (err: any) {
      setError('Failed to load agent')
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || !agent || !currentOrg) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const response = await api.post('/chat/', {
        message: input,
        agent_id: agent.id,
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.message
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message')
      // Remove the user message if the request failed
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (!currentOrg) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-blue-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">No Organization Selected</h1>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-purple-600 hover:text-purple-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-blue-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading agent...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
      <div className="max-w-5xl mx-auto h-screen flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-600 hover:text-gray-800 mb-2 text-sm"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
              {agent.description && (
                <p className="text-gray-600 text-sm mt-1">{agent.description}</p>
              )}
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              agent.is_active 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {agent.is_active ? 'Active' : 'Inactive'}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🤖</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Start a conversation with {agent.name}
              </h2>
              <p className="text-gray-600">
                Ask anything and I'll help you get it done
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-purple-600 text-white'
                      : 'bg-white text-gray-900 shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))
          )}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-900 shadow-sm rounded-2xl px-4 py-3">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-3">
              {error}
            </div>
          )}
          
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              placeholder="Type your message..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent disabled:bg-gray-50"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
          
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}
