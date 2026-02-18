import UserMessage from './UserMessage'
import AssistantMessage from './AssistantMessage'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  metadata?: {
    thought_trace?: any[]
    tool_calls?: any[]
    streaming?: boolean
  }
}

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {messages.map((message) => (
        message.role === 'user' ? (
          <UserMessage key={message.id} content={message.content} timestamp={message.created_at} />
        ) : message.role === 'assistant' ? (
          <AssistantMessage 
            key={message.id} 
            content={message.content} 
            timestamp={message.created_at}
            metadata={message.metadata}
          />
        ) : null
      ))}
    </div>
  )
}
