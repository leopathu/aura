import { formatDistanceToNow } from 'date-fns'

interface UserMessageProps {
  content: string
  timestamp: string
}

export default function UserMessage({ content, timestamp }: UserMessageProps) {
  return (
    <div className="flex justify-end">
      <div className="flex items-start gap-3 max-w-2xl">
        <div className="flex-1">
          <div className="bg-purple-600 text-white rounded-2xl rounded-tr-sm px-4 py-3">
            <p className="whitespace-pre-wrap break-words">{content}</p>
          </div>
          <p className="text-xs text-gray-500 mt-1 text-right">
            {formatDistanceToNow(new Date(timestamp), { addSuffix: true })}
          </p>
        </div>
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
            U
          </div>
        </div>
      </div>
    </div>
  )
}
