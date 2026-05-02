"use client";

import { useState, useRef, useEffect } from "react";
import { queryService } from "@/services/query-service";
import { getErrorMessage } from "@/lib/api-client";
import type { Brain, QueryResponse, SourceChunk } from "@/types";
import { cn } from "@/lib/utils";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  sources?: SourceChunk[];
}

interface BrainChatProps {
  brain: Brain;
}

/**
 * Chat interface scoped to a specific brain.
 */
export function BrainChat({ brain }: BrainChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Reset conversation when brain changes
    setMessages([]);
    setError(null);
  }, [brain.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || isLoading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setIsLoading(true);

    try {
      const response: QueryResponse = await queryService.query({
        query,
        top_k: 5,
        brain_id: brain.id,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: response.answer, sources: response.sources },
      ]);
    } catch (err) {
      setError(getErrorMessage(err));
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 py-16">
            <span className="text-5xl mb-4">🧠</span>
            <p className="text-base font-medium text-slate-600">{brain.name}</p>
            <p className="text-sm mt-1">Ask anything about the sources connected to this brain.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-4 py-3 text-sm",
                msg.role === "user"
                  ? "bg-brand-600 text-white rounded-br-sm"
                  : "bg-white border border-slate-200 text-slate-800 rounded-bl-sm shadow-sm"
              )}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-200 space-y-1">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Sources</p>
                  {msg.sources.map((src, si) => (
                    <div key={si} className="text-xs text-slate-500 bg-slate-50 rounded-lg px-2 py-1">
                      <span className="font-medium text-slate-600">{src.document_title}</span>
                      {" · "}chunk {src.chunk_index}
                      {" · "}
                      <span className="text-brand-600">{(src.similarity * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mb-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={handleSend}
        className="px-6 py-4 border-t border-slate-200 bg-white flex gap-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Ask ${brain.name}…`}
          disabled={isLoading}
          className="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-4 py-2.5 bg-brand-600 text-white rounded-xl text-sm font-medium hover:bg-brand-700 disabled:opacity-50 transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}
