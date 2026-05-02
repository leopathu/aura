"use client";

import { useState } from "react";
import { useQuery } from "@/hooks/useQuery";
import { useQueryStore } from "@/store/query-store";
import { cn } from "@/lib/utils";
import { SourceCard } from "./SourceCard";

/**
 * Main RAG query interface with question input, answer display, and source citations.
 */
export function QueryInterface() {
  const [question, setQuestion] = useState("");
  const { submit, isLoading, error } = useQuery();
  const history = useQueryStore((s) => s.history);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    await submit(question.trim());
    setQuestion("");
  };

  return (
    <div className="flex flex-col gap-6">
      {/* History */}
      <div className="flex flex-col gap-6">
        {history.map((entry, i) => (
          <div key={i} className="flex flex-col gap-3 border border-slate-200 rounded-xl p-6">
            <p className="font-semibold text-slate-700">Q: {entry.question}</p>
            <p className="text-slate-800 whitespace-pre-wrap">{entry.response.answer}</p>
            {entry.response.sources.length > 0 && (
              <div>
                <p className="text-xs text-slate-400 uppercase font-medium mb-2">Sources</p>
                <div className="grid gap-2">
                  {entry.response.sources.map((src, j) => (
                    <SourceCard key={j} source={src} />
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <p className="text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
          {error}
        </p>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents…"
          disabled={isLoading}
          className={cn(
            "flex-1 border border-slate-300 rounded-lg px-4 py-3 text-sm outline-none",
            "focus:ring-2 focus:ring-brand-500 focus:border-brand-500",
            "disabled:opacity-50"
          )}
        />
        <button
          type="submit"
          disabled={isLoading || !question.trim()}
          className={cn(
            "px-5 py-3 bg-brand-600 text-white rounded-lg font-medium text-sm",
            "hover:bg-brand-700 transition-colors",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          {isLoading ? "Thinking…" : "Ask"}
        </button>
      </form>
    </div>
  );
}
