"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { chatService } from "@/services/chat-service";
import { getErrorMessage } from "@/lib/api-client";
import type { Brain, ConversationSummary, ChatMessageData, SourceChunk } from "@/types";
import { cn } from "@/lib/utils";

interface LocalMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  streaming?: boolean;
}

interface BrainChatProps {
  brain: Brain;
}

function SourcesPanel({ sources }: { sources: SourceChunk[] }) {
  if (sources.length === 0) return null;
  return (
    <div className="mt-3 pt-3 border-t border-slate-200 space-y-1">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Sources</p>
      {sources.map((src, i) => (
        <div key={i} className="text-xs text-slate-500 bg-slate-50 rounded-lg px-2 py-1">
          <span className="font-medium text-slate-600">{src.document_title}</span>
          {" · "}chunk {src.chunk_index}
          {" · "}
          <span className="text-brand-600">{(src.similarity * 100).toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}

export function BrainChat({ brain }: BrainChatProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<(() => void) | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load conversation list
  const loadConversations = useCallback(async () => {
    try {
      const list = await chatService.listConversations(brain.id);
      setConversations(list);
    } catch {
      // silent
    }
  }, [brain.id]);

  useEffect(() => {
    setConversations([]);
    setActiveConvId(null);
    setMessages([]);
    setError(null);
    loadConversations();
  }, [brain.id, loadConversations]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [input]);

  const loadConversation = useCallback(async (convId: string) => {
    try {
      const detail = await chatService.getConversation(convId);
      const msgs: LocalMessage[] = detail.messages.map((m: ChatMessageData) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        ...(m.sources_json
          ? { sources: JSON.parse(m.sources_json) as SourceChunk[] }
          : {}),
      }));
      setMessages(msgs);
      setActiveConvId(convId);
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  const startNewChat = useCallback(() => {
    abortRef.current?.();
    setActiveConvId(null);
    setMessages([]);
    setError(null);
    setInput("");
  }, []);

  const handleDelete = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    setDeletingId(convId);
    try {
      await chatService.deleteConversation(convId);
      if (activeConvId === convId) startNewChat();
      setConversations((prev) => prev.filter((c) => c.id !== convId));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  const handleSend = useCallback(() => {
    const query = input.trim();
    if (!query || isStreaming) return;

    setInput("");
    setError(null);

    // Optimistically add user message
    const userMsgId = crypto.randomUUID();
    const assistantMsgId = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: query },
      { id: assistantMsgId, role: "assistant", content: "", streaming: true },
    ]);
    setIsStreaming(true);

    let resolvedConvId = activeConvId;

    const abort = chatService.streamChat(
      {
        brain_id: brain.id,
        message: query,
        ...(activeConvId ? { conversation_id: activeConvId } : {}),
        top_k: 5,
      },
      (event) => {
        if (event.type === "meta") {
          resolvedConvId = event.conversation_id;
          setActiveConvId(event.conversation_id);
          const sources = event.sources;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId ? { ...m, sources } : m
            )
          );
          // Refresh conversation list to show new entry
          loadConversations();
        } else if (event.type === "token") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: m.content + event.token }
                : m
            )
          );
        } else if (event.type === "done") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId ? { ...m, streaming: false } : m
            )
          );
          setIsStreaming(false);
          loadConversations(); // refresh titles / order
        } else if (event.type === "error") {
          setMessages((prev) => prev.filter((m) => m.id !== assistantMsgId));
          setError(event.message);
          setIsStreaming(false);
        }
      }
    );

    abortRef.current = abort;
  }, [input, isStreaming, activeConvId, brain.id, loadConversations]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
    if (diffDays === 0) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return d.toLocaleDateString([], { weekday: "short" });
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── Conversation sidebar ── */}
      <aside className="w-56 shrink-0 flex flex-col border-r border-slate-200 bg-white">
        <div className="px-3 py-3 border-b border-slate-100">
          <button
            onClick={startNewChat}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition-colors"
          >
            <span className="text-lg leading-none">+</span>
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-1">
          {conversations.length === 0 && (
            <p className="px-3 py-4 text-xs text-slate-400 text-center">No conversations yet</p>
          )}
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => { if (conv.id !== activeConvId) loadConversation(conv.id); }}
              className={cn(
                "group flex items-start justify-between px-3 py-2.5 mx-1 my-0.5 rounded-lg cursor-pointer transition-colors",
                conv.id === activeConvId
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100"
              )}
            >
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium truncate leading-snug">{conv.title}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">{formatDate(conv.updated_at)}</p>
              </div>
              <button
                onClick={(e) => void handleDelete(e, conv.id)}
                disabled={deletingId === conv.id}
                className="shrink-0 opacity-0 group-hover:opacity-100 ml-1 text-slate-400 hover:text-red-500 transition-all text-xs disabled:opacity-50"
                title="Delete"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* ── Chat panel ── */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-slate-50">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 py-16">
              <span className="text-5xl mb-4">🧠</span>
              <p className="text-base font-medium text-slate-600">{brain.name}</p>
              <p className="text-sm mt-1 max-w-xs">
                Ask anything about the sources connected to this brain.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
              <div
                className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-3 text-sm",
                  msg.role === "user"
                    ? "bg-brand-600 text-white rounded-br-sm"
                    : "bg-white border border-slate-200 text-slate-800 rounded-bl-sm shadow-sm"
                )}
              >
                {msg.role === "assistant" && msg.streaming && msg.content === "" ? (
                  <div className="flex gap-1 py-1">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                )}
                {msg.streaming && msg.content !== "" && (
                  <span className="inline-block w-0.5 h-4 bg-slate-500 ml-0.5 animate-pulse align-middle" />
                )}
                {msg.sources && <SourcesPanel sources={msg.sources} />}
              </div>
            </div>
          ))}

          <div ref={bottomRef} />
        </div>

        {/* Error */}
        {error && (
          <div className="mx-6 mb-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        {/* Input */}
        <div className="px-6 py-4 border-t border-slate-200 bg-white">
          <div className="flex items-end gap-3 bg-slate-100 rounded-2xl px-4 py-2 border border-slate-200 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-100 transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask ${brain.name}… (Shift+Enter for newline)`}
              disabled={isStreaming}
              rows={1}
              className="flex-1 bg-transparent text-sm resize-none outline-none placeholder:text-slate-400 disabled:opacity-50 max-h-40 py-1"
            />
            {isStreaming ? (
              <button
                onClick={() => { abortRef.current?.(); setIsStreaming(false); }}
                className="shrink-0 px-3 py-1.5 rounded-xl text-xs font-medium bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
              >
                Stop
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="shrink-0 px-3 py-1.5 rounded-xl text-sm font-medium bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-40 transition-colors"
              >
                Send
              </button>
            )}
          </div>
          <p className="text-[10px] text-slate-400 mt-1.5 text-center">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}

