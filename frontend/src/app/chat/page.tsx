"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { apiRequest, streamAgentChat } from "@/lib/api";
import { Conversation, ConversationMessage, BrainItem } from "@/types";
import Link from "next/link";
import {
  Bot,
  User,
  Send,
  Plus,
  Settings,
  Database,
  FileText,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  Clock,
  Sparkles,
  ExternalLink,
  LogOut,
  FolderOpen,
  BrainCircuit
} from "lucide-react";

export default function ChatPage() {
  const router = useRouter();
  const { token, user, organizationName, logout } = useAuthStore();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [brains, setBrains] = useState<BrainItem[]>([]);
  const [selectedBrainId, setSelectedBrainId] = useState<string | null>(null);
  const [inputPrompt, setInputPrompt] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  // Active streaming state indicators
  const [liveSteps, setLiveSteps] = useState<Array<{ title: string; status: string }>>([]);
  const [liveTools, setLiveTools] = useState<string[]>([]);
  const [liveTokens, setLiveTokens] = useState("");
  const [liveCitations, setLiveCitations] = useState<string[]>([]);
  const [liveReasoning, setLiveReasoning] = useState("");
  const [liveReport, setLiveReport] = useState<any>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    loadConversations();
    loadBrains();
  }, [token]);

  const loadBrains = async () => {
    try {
      const data = await apiRequest<BrainItem[]>("/brains");
      setBrains(data);
    } catch (err) {
      console.error("Failed to load brains", err);
    }
  };

  const loadConversations = async () => {
    try {
      const data = await apiRequest<Conversation[]>("/chat/conversations");
      setConversations(data);
      if (data.length > 0 && !activeConversationId) {
        selectConversation(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load conversations", err);
    }
  };

  const selectConversation = async (id: string) => {
    setActiveConversationId(id);
    try {
      const data = await apiRequest<{ messages: ConversationMessage[] }>(`/chat/conversations/${id}`);
      setMessages(data.messages);
    } catch (err) {
      console.error("Failed to load messages", err);
    }
  };

  const createNewConversation = async () => {
    try {
      const conv = await apiRequest<Conversation>("/chat/conversations", {
        method: "POST",
        body: JSON.stringify({ title: "New Conversation" }),
      });
      setConversations([conv, ...conversations]);
      setActiveConversationId(conv.id);
      setMessages([]);
    } catch (err) {
      console.error("Failed to create conversation", err);
    }
  };

  const handleSendMessage = async (promptToSend?: string) => {
    const text = promptToSend || inputPrompt;
    if (!text.trim() || isStreaming) return;

    let targetConvId = activeConversationId;
    if (!targetConvId) {
      const conv = await apiRequest<Conversation>("/chat/conversations", {
        method: "POST",
        body: JSON.stringify({ title: text.slice(0, 30) }),
      });
      setConversations([conv, ...conversations]);
      targetConvId = conv.id;
      setActiveConversationId(conv.id);
    }

    // Add user message to UI immediately
    const userMsg: ConversationMessage = {
      id: `temp-${Date.now()}`,
      sender: "USER",
      content: text,
      tool_calls: [],
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt("");
    setIsStreaming(true);

    // Reset live execution steps
    setLiveSteps([]);
    setLiveTools([]);
    setLiveTokens("");
    setLiveCitations([]);
    setLiveReasoning("");
    setLiveReport(null);

    let accumulatedTokens = "";
    let finalCitations: string[] = [];
    let finalReasoning = "";

    try {
      await streamAgentChat(
        targetConvId,
        text,
        (event, data) => {
          if (event === "step") {
            setLiveSteps((prev) => [...prev, { title: data.title, status: "completed" }]);
          } else if (event === "tool") {
            setLiveTools((prev) => Array.from(new Set([...prev, data.tool])));
          } else if (event === "token") {
            accumulatedTokens += data.token;
            setLiveTokens((prev) => prev + data.token);
          } else if (event === "report") {
            setLiveReport(data);
          } else if (event === "done") {
            finalCitations = data.citations || [];
            finalReasoning = data.reasoning_summary || "";
            setLiveCitations(finalCitations);
            setLiveReasoning(finalReasoning);
          }
        },
        selectedBrainId || undefined
      );

      // Commit assistant message
      const assistantMsg: ConversationMessage = {
        id: `asst-${Date.now()}`,
        sender: "ASSISTANT",
        content: accumulatedTokens,
        reasoning_summary: finalReasoning,
        tool_calls: liveTools,
        citations: finalCitations,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setLiveTokens("");
      setLiveSteps([]);
    } catch (err: any) {
      console.error("Stream error", err);
      const errMsg: ConversationMessage = {
        id: `err-${Date.now()}`,
        sender: "ASSISTANT",
        content: `Error executing request: ${err.message}`,
        tool_calls: [],
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsStreaming(false);
      loadConversations();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, liveTokens, liveSteps]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 border-r border-slate-800 bg-slate-900/60 flex flex-col justify-between">
        <div>
          {/* Logo / Header */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-aura-600 font-bold text-white shadow shadow-aura-500/20">
                A
              </div>
              <span className="font-bold text-lg text-white tracking-tight">Aura</span>
            </Link>
            <Link
              href="/console"
              className="flex items-center space-x-1 rounded-md bg-slate-800/80 px-2.5 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 transition"
              title="Admin Console"
            >
              <Settings className="h-3.5 w-3.5 text-aura-400" />
              <span>Console</span>
            </Link>
          </div>

          {/* Org & New Chat Button */}
          <div className="p-3 space-y-2">
            <div className="flex items-center space-x-2 rounded-lg bg-slate-800/40 px-3 py-2 border border-slate-800 text-xs">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <div className="truncate">
                <div className="text-[10px] text-slate-400 font-semibold uppercase">Organization</div>
                <div className="font-medium text-slate-200 truncate">{organizationName || "Acme Corporation"}</div>
              </div>
            </div>

            <button
              onClick={createNewConversation}
              className="w-full flex items-center justify-center space-x-2 rounded-lg bg-aura-600/90 hover:bg-aura-600 py-2 px-3 text-xs font-semibold text-white shadow transition"
            >
              <Plus className="h-4 w-4" />
              <span>New Conversation</span>
            </button>
          </div>

          {/* Conversation List */}
          <div className="px-3 py-2">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-2 mb-2">
              Recent Chats
            </div>
            <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-320px)] pr-1">
              {conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => selectConversation(c.id)}
                  className={`w-full text-left rounded-lg px-3 py-2 text-xs truncate transition flex items-center justify-between ${
                    c.id === activeConversationId
                      ? "bg-slate-800 text-white font-medium border border-slate-700"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                  }`}
                >
                  <span className="truncate">{c.title}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* User Footer */}
        <div className="p-3 border-t border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center space-x-2.5 truncate">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-semibold text-xs">
              {user?.name?.[0] || "U"}
            </div>
            <div className="truncate text-xs">
              <div className="font-medium text-slate-200 truncate">{user?.name || "User"}</div>
              <div className="text-[10px] text-slate-500 truncate">{user?.email}</div>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition"
            title="Log Out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>

      {/* Main Chat Interface */}
      <main className="flex-1 flex flex-col justify-between h-full bg-slate-950">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-slate-900/20 backdrop-blur-sm">
          <div className="flex items-center space-x-3">
            <Bot className="h-5 w-5 text-aura-400" />
            <h1 className="font-semibold text-sm text-slate-200">
              {conversations.find((c) => c.id === activeConversationId)?.title || "Aura Agent"}
            </h1>
          </div>
          <div className="flex items-center space-x-3 text-xs">
            {/* Brain Selector Dropdown */}
            <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1 text-slate-200 shadow-sm">
              <BrainCircuit className="h-3.5 w-3.5 text-aura-400" />
              <select
                value={selectedBrainId || ""}
                onChange={(e) => setSelectedBrainId(e.target.value || null)}
                className="bg-transparent text-xs text-white focus:outline-none cursor-pointer pr-1"
                title="Scope agent queries to a specific Brain"
              >
                <option value="" className="bg-slate-900 text-white">All Permitted Brains</option>
                {brains.map((b) => (
                  <option key={b.id} value={b.id} className="bg-slate-900 text-white">
                    {b.name}
                  </option>
                ))}
              </select>
            </div>

            <span className="inline-flex items-center space-x-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-emerald-400 border border-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Policy Gateway Active</span>
            </span>
            <span className="rounded-lg bg-slate-800/80 px-2.5 py-1 text-slate-300 border border-slate-700">
              GPT-4o / Hybrid Vector
            </span>
          </div>
        </header>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 max-w-4xl mx-auto w-full">
          {messages.length === 0 && !isStreaming && (
            <div className="flex flex-col items-center justify-center h-full py-16 text-center">
              <div className="h-14 w-14 rounded-2xl bg-aura-600/10 border border-aura-500/20 flex items-center justify-center text-aura-400 mb-4 shadow-sm">
                <Sparkles className="h-7 w-7" />
              </div>
              <h2 className="text-xl font-bold text-white">How can Aura assist your team today?</h2>
              <p className="mt-2 text-sm text-slate-400 max-w-md">
                Ask analytical questions across connected databases, company documents, or request formatted reports.
              </p>

              <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl text-left">
                <button
                  onClick={() =>
                    handleSendMessage("How much revenue did we generate this year and compare with previous period?")
                  }
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 text-xs text-slate-300 hover:border-aura-500/50 hover:bg-slate-900 transition"
                >
                  <div className="font-semibold text-white mb-1 flex items-center space-x-1.5">
                    <Database className="h-3.5 w-3.5 text-aura-400" />
                    <span>Query Financial Database</span>
                  </div>
                  "How much revenue did we generate this year?"
                </button>

                <button
                  onClick={() =>
                    handleSendMessage("What does our company policy say about employee annual and sick leave?")
                  }
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 text-xs text-slate-300 hover:border-cyan-500/50 hover:bg-slate-900 transition"
                >
                  <div className="font-semibold text-white mb-1 flex items-center space-x-1.5">
                    <FileText className="h-3.5 w-3.5 text-cyan-400" />
                    <span>Search Company Handbook</span>
                  </div>
                  "What does our policy say about leave?"
                </button>

                <button
                  onClick={() =>
                    handleSendMessage("Analyze sales trends across categories and generate an executive report.")
                  }
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 text-xs text-slate-300 hover:border-purple-500/50 hover:bg-slate-900 transition sm:col-span-2"
                >
                  <div className="font-semibold text-white mb-1 flex items-center space-x-1.5">
                    <FolderOpen className="h-3.5 w-3.5 text-purple-400" />
                    <span>Create Executive Report</span>
                  </div>
                  "Analyze sales data and create an executive report."
                </button>
              </div>
            </div>
          )}

          {/* Historical Messages */}
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${
                m.sender === "USER" ? "items-end" : "items-start"
              } space-y-1`}
            >
              <div
                className={`max-w-2xl rounded-2xl px-4 py-3 text-sm shadow-sm ${
                  m.sender === "USER"
                    ? "bg-aura-600 text-white rounded-br-none"
                    : "bg-slate-900/80 border border-slate-800 text-slate-200 rounded-bl-none"
                }`}
              >
                {/* Reasoning Disclosure for Assistant */}
                {m.sender === "ASSISTANT" && m.reasoning_summary && (
                  <div className="mb-3 rounded-lg bg-slate-800/50 border border-slate-700/50 p-2.5 text-xs text-slate-300">
                    <div className="flex items-center space-x-1.5 text-aura-400 font-medium mb-1">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Security & Policy Verified Execution</span>
                    </div>
                    <p className="text-slate-400">{m.reasoning_summary}</p>
                    {m.tool_calls && m.tool_calls.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {m.tool_calls.map((t, idx) => (
                          <span
                            key={idx}
                            className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-300 border border-slate-700"
                          >
                            ✓ {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Message Body */}
                <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>

                {/* Citations badges */}
                {m.sender === "ASSISTANT" && m.citations && m.citations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800">
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Provenance Citations
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {m.citations.map((cite, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center space-x-1 rounded-md bg-slate-800/80 px-2 py-1 text-xs text-aura-300 border border-slate-700/80"
                        >
                          <span className="font-bold text-[10px] text-aura-400">[{idx + 1}]</span>
                          <span>{cite}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Live Agent Execution Stepper (Streaming) */}
          {isStreaming && (
            <div className="max-w-2xl rounded-2xl bg-slate-900/90 border border-aura-500/30 p-4 text-sm shadow-md">
              <div className="flex items-center space-x-2 text-aura-400 font-semibold mb-3">
                <Bot className="h-4 w-4 animate-spin text-aura-400" />
                <span>Agent Execution in Progress...</span>
              </div>

              {/* Execution Steps */}
              <div className="space-y-1.5 border-l-2 border-aura-500/40 pl-3 my-2 text-xs">
                {liveSteps.map((s, idx) => (
                  <div key={idx} className="flex items-center space-x-2 text-slate-300">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                    <span>{s.title}</span>
                  </div>
                ))}
              </div>

              {/* Live Tools Used */}
              {liveTools.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {liveTools.map((t, idx) => (
                    <span
                      key={idx}
                      className="rounded bg-aura-500/10 border border-aura-500/30 px-2 py-0.5 text-xs text-aura-300 font-mono"
                    >
                      Executing: {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Live Streaming Content */}
              {liveTokens && (
                <div className="mt-4 pt-3 border-t border-slate-800 text-slate-200 whitespace-pre-wrap leading-relaxed">
                  {liveTokens}
                  <span className="inline-block h-3 w-1 bg-aura-400 ml-1 animate-pulse" />
                </div>
              )}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/40">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="max-w-4xl mx-auto flex items-center space-x-2"
          >
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder="Ask questions across databases and policies, or request an action..."
              className="flex-1 rounded-xl border border-slate-700 bg-slate-800/90 px-4 py-3 text-sm text-white placeholder-slate-400 focus:border-aura-500 focus:outline-none focus:ring-1 focus:ring-aura-500"
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={isStreaming || !inputPrompt.trim()}
              className="flex items-center justify-center rounded-xl bg-aura-600 px-5 py-3 font-semibold text-white shadow-lg shadow-aura-500/25 hover:bg-aura-500 disabled:opacity-50 transition"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
          <div className="max-w-4xl mx-auto mt-2 flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>Security boundary: Tools and queries strictly validated by Aura Policy Engine</span>
            <span>Aura v0.1 OSS</span>
          </div>
        </div>
      </main>
    </div>
  );
}
