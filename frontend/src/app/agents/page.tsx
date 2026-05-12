"use client";

import { ProtectedLayout } from "@/components/ProtectedLayout";
import { AgentSidebar } from "@/components/AgentSidebar";
import { AgentPanel } from "@/components/AgentPanel";
import { useAgentStore } from "@/store/agent-store";

/**
 * Main Agents page — sidebar (agent list) + agent panel (tabbed detail).
 */
export default function AgentsPage() {
  return (
    <ProtectedLayout>
      <AgentsContent />
    </ProtectedLayout>
  );
}

function AgentsContent() {
  const selectedAgent = useAgentStore((s) => s.selectedAgent);

  return (
    <div className="flex h-[calc(100vh-57px)]">
      <AgentSidebar />
      <main className="flex-1 overflow-hidden bg-slate-50">
        {selectedAgent ? (
          <AgentPanel agent={selectedAgent} />
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 px-6">
            <span className="text-6xl mb-4">🤖</span>
            <h2 className="text-xl font-semibold text-slate-600">Select an Agent</h2>
            <p className="text-sm mt-2 max-w-xs">
              Choose an agent from the sidebar or create a new one to start connecting apps and
              chatting.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
