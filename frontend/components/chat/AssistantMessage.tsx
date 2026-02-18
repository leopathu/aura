'use client'

import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'

interface AssistantMessageProps {
  content: string
  timestamp: string
  metadata?: {
    thought_trace?: any[]
    tool_calls?: any[]
    streaming?: boolean
  }
}

export default function AssistantMessage({ content, timestamp, metadata }: AssistantMessageProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [showThoughts, setShowThoughts] = useState(false)
  const [showTools, setShowTools] = useState(false)

  const copyToClipboard = (code: string, language: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(language)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const hasThoughts = metadata?.thought_trace && metadata.thought_trace.length > 0
  const hasTools = metadata?.tool_calls && metadata.tool_calls.length > 0

  return (
    <div className="flex justify-start">
      <div className="flex items-start gap-3 max-w-2xl">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-500 rounded-full flex items-center justify-center text-white font-medium text-sm">
            AI
          </div>
        </div>
        <div className="flex-1">
          {/* Thought Trace */}
          {hasThoughts && (
            <div className="mb-2">
              <button
                onClick={() => setShowThoughts(!showThoughts)}
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                <svg 
                  className={`h-4 w-4 transition-transform ${showThoughts ? 'rotate-90' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                </svg>
                <span className="font-medium">Thought Process ({metadata.thought_trace?.length})</span>
              </button>
              
              {showThoughts && (
                <div className="mt-2 space-y-2">
                  {metadata.thought_trace?.map((thought: any, idx: number) => (
                    <div key={idx} className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-purple-700 uppercase">
                          {thought.node || `Step ${thought.step}`}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          thought.status === 'completed' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {thought.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{thought.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tool Calls */}
          {hasTools && (
            <div className="mb-2">
              <button
                onClick={() => setShowTools(!showTools)}
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                <svg 
                  className={`h-4 w-4 transition-transform ${showTools ? 'rotate-90' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                </svg>
                <span className="font-medium">Tool Calls ({metadata.tool_calls?.length})</span>
              </button>
              
              {showTools && (
                <div className="mt-2 space-y-2">
                  {metadata.tool_calls?.map((tool: any, idx: number) => (
                    <div key={idx} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-blue-700">
                          {tool.tool_name}
                        </span>
                        {tool.duration_ms && (
                          <span className="text-xs text-gray-500">
                            {tool.duration_ms}ms
                          </span>
                        )}
                      </div>
                      {tool.arguments && (
                        <pre className="text-xs bg-white border border-blue-100 rounded p-2 mt-1 overflow-x-auto">
                          {JSON.stringify(tool.arguments, null, 2)}
                        </pre>
                      )}
                      {tool.result && (
                        <div className="mt-2">
                          <span className="text-xs font-medium text-gray-600">Result:</span>
                          <pre className="text-xs bg-white border border-blue-100 rounded p-2 mt-1 overflow-x-auto">
                            {typeof tool.result === 'string' ? tool.result : JSON.stringify(tool.result, null, 2)}
                          </pre>
                        </div>
                      )}
                      {tool.error && (
                        <div className="mt-2 text-xs text-red-600">
                          Error: {tool.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Main Message */}
          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
            {metadata?.streaming && (
              <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
                <div className="animate-pulse flex gap-1">
                  <div className="w-1.5 h-1.5 bg-purple-600 rounded-full"></div>
                  <div className="w-1.5 h-1.5 bg-purple-600 rounded-full animation-delay-200"></div>
                  <div className="w-1.5 h-1.5 bg-purple-600 rounded-full animation-delay-400"></div>
                </div>
                <span>Streaming...</span>
              </div>
            )}
            
            <div className="prose prose-sm max-w-none prose-headings:mt-3 prose-headings:mb-2 prose-p:my-2 prose-pre:my-2 prose-ul:my-2 prose-ol:my-2">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '')
                    const language = match ? match[1] : ''
                    const code = String(children).replace(/\n$/, '')
                    const inline = !className

                    return !inline && match ? (
                      <div className="relative group">
                        <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => copyToClipboard(code, language)}
                            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded transition-colors"
                          >
                            {copiedCode === language ? 'Copied!' : 'Copy'}
                          </button>
                        </div>
                        <SyntaxHighlighter
                          style={oneDark as any}
                          language={language}
                          PreTag="div"
                          {...props}
                        >
                          {code}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <code className="bg-gray-100 text-purple-700 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {formatDistanceToNow(new Date(timestamp), { addSuffix: true })}
          </p>
        </div>
      </div>
    </div>
  )
}
