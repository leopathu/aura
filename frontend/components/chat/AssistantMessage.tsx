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
}

export default function AssistantMessage({ content, timestamp }: AssistantMessageProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const copyToClipboard = (code: string, language: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(language)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  return (
    <div className="flex justify-start">
      <div className="flex items-start gap-3 max-w-2xl">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-500 rounded-full flex items-center justify-center text-white font-medium text-sm">
            AI
          </div>
        </div>
        <div className="flex-1">
          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
            <div className="prose prose-sm max-w-none prose-headings:mt-3 prose-headings:mb-2 prose-p:my-2 prose-pre:my-2 prose-ul:my-2 prose-ol:my-2">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const language = match ? match[1] : ''
                    const code = String(children).replace(/\n$/, '')

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
                          style={oneDark}
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
