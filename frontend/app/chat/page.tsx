'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

interface ThoughtTrace {
  content: string
  timestamp: Date
}

export default function ChatPage() {
  const router = useRouter()
  const { user, currentOrg } = useAuthStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [thoughts, setThoughts] = useState<ThoughtTrace[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [showThoughts, setShowThoughts] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!user || !currentOrg) {
      router.push('/auth/login')
    }
  }, [user, currentOrg])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thoughts])

  const handleSend = async () => {
    if (!input.trim() || loading || !currentOrg) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setThoughts([])

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const token = localStorage.getItem('access_token')
      
      // For MVP, we'll use a simple POST request
      // In production, use EventSource for SSE streaming
      const response = await fetch(
        `${API_URL}/api/v1/organizations/${currentOrg.id}/agents/chat`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: input,
            agent_id: 'default', // Use first agent or create default
          }),
        }
      )

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      // For MVP, simulate streaming with a simple response
      const assistantMessage: Message = {
        role: 'assistant',
        content: 'I received your message and I\'m processing it. In the full version, I would connect to your apps via MCP and execute tasks.',
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
      
      // Simulate thought trace
      setThoughts([
        { content: 'Analyzing request...', timestamp: new Date() },
        { content: 'Checking available tools...', timestamp: new Date() },
        { content: 'Generating response...', timestamp: new Date() },
      ])
      
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure you have API credentials configured.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!user || !currentOrg) return null

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back
            </button>
            <h1 className="text-xl font-bold text-gray-900">Chat with Aura</h1>
          </div>
          
          <button
            onClick={() => setShowThoughts(!showThoughts)}
            className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200"
          >
            {showThoughts ? 'Hide' : 'Show'} Thoughts
          </button>
        </div>
      </header>

      {/* Main Chat Area */}
      <div className="flex-1 container mx-auto flex gap-4 p-4 overflow-hidden">
        {/* Messages */}
        <div className="flex-1 bg-white rounded-xl shadow-sm flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-20">
                <div className="text-6xl mb-4">👋</div>
                <h3 className="text-xl font-semibold mb-2">Welcome to Aura</h3>
                <p>Ask me anything about your connected apps and I'll help you out!</p>
              </div>
            )}
            
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-3">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask Aura to help you..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent resize-none"
                rows={1}
                disabled={loading}
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Thought Trace Sidebar */}
        {showThoughts && (
          <div className="w-80 bg-white rounded-xl shadow-sm p-4">
            <h3 className="font-semibold text-lg mb-4 text-gray-900">Agent Thoughts</h3>
            
            {thoughts.length === 0 ? (
              <p className="text-sm text-gray-500">
                Agent thinking process will appear here...
              </p>
            ) : (
              <div className="space-y-3">
                {thoughts.map((thought, index) => (
                  <div key={index} className="text-sm">
                    <div className="flex items-start gap-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full mt-1.5"></div>
                      <div className="flex-1">
                        <p className="text-gray-700">{thought.content}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {thought.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
