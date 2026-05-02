"use client";

import { useState } from "react";
import { BrainChat } from "@/components/BrainChat";
import { BrainSources } from "@/components/BrainSources";
import type { Brain } from "@/types";
import { cn } from "@/lib/utils";

type Tab = "chat" | "sources";

interface BrainPanelProps {
  brain: Brain;
}

/**
 * Main content panel for a selected brain.
 * Tabs: Chat (RAG query) | Sources (attach/detach documents).
 */
export function BrainPanel({ brain }: BrainPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("chat");

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex items-center gap-1 px-6 pt-4 pb-0 border-b border-slate-200 bg-white">
        <div className="flex gap-1">
          {(["chat", "sources"] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-t-lg transition-colors capitalize",
                activeTab === tab
                  ? "bg-brand-50 text-brand-700 border border-b-white border-slate-200 -mb-px"
                  : "text-slate-500 hover:text-slate-700"
              )}
            >
              {tab === "chat" ? "💬 Chat" : "📄 Sources"}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "chat" ? (
          <BrainChat brain={brain} />
        ) : (
          <BrainSources brain={brain} />
        )}
      </div>
    </div>
  );
}
