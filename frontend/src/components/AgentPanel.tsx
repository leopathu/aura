"use client";

import { useState, useEffect, useCallback } from "react";
import { AgentChat } from "@/components/AgentChat";
import { AgentConnectionCard } from "@/components/AgentConnectionCard";
import { AgentDocumentList } from "@/components/AgentDocumentList";
import { AddConnectionModal } from "@/components/AddConnectionModal";
import { agentService } from "@/services/agent-service";
import { getErrorMessage } from "@/lib/api-client";
import type { Agent, AgentConnection } from "@/types";
import { cn } from "@/lib/utils";

type Tab = "chat" | "connections" | "documents";

interface AgentPanelProps {
  agent: Agent;
}

/**
 * Main content panel for a selected agent.
 * Tabs: Chat | Connections | Documents
 */
export function AgentPanel({ agent }: AgentPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const [connections, setConnections] = useState<AgentConnection[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [connError, setConnError] = useState<string | null>(null);

  const loadConnections = useCallback(async () => {
    try {
      const list = await agentService.listConnections(agent.id);
      setConnections(list);
    } catch (err) {
      setConnError(getErrorMessage(err));
    }
  }, [agent.id]);

  useEffect(() => {
    setConnections([]);
    setConnError(null);
    void loadConnections();
  }, [agent.id, loadConnections]);

  const handleDisconnect = async (connId: string) => {
    try {
      await agentService.removeConnection(agent.id, connId);
      setConnections((prev) => prev.filter((c) => c.id !== connId));
    } catch (err) {
      setConnError(getErrorMessage(err));
    }
  };

  const TAB_LABELS: Record<Tab, string> = {
    chat: "💬 Chat",
    connections: `🔌 Connections${connections.length > 0 ? ` (${connections.length})` : ""}`,
    documents: "📄 Documents",
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex items-center gap-1 px-6 pt-4 pb-0 border-b border-slate-200 bg-white">
        <div className="flex gap-1">
          {(["chat", "connections", "documents"] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-t-lg transition-colors",
                activeTab === tab
                  ? "bg-brand-50 text-brand-700 border border-b-white border-slate-200 -mb-px"
                  : "text-slate-500 hover:text-slate-700"
              )}
            >
              {TAB_LABELS[tab]}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "chat" && <AgentChat agent={agent} />}

        {activeTab === "connections" && (
          <div className="h-full overflow-y-auto">
            <div className="max-w-3xl mx-auto px-6 py-6">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="text-base font-semibold text-slate-800">Connected Apps</h2>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Manage the apps this agent syncs data from.
                  </p>
                </div>
                <button
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
                >
                  + Add Connection
                </button>
              </div>

              {connError && (
                <div className="mb-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                  {connError}
                </div>
              )}

              {connections.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center text-slate-400">
                  <span className="text-5xl mb-4">🔌</span>
                  <p className="text-base font-medium text-slate-600">No connections yet</p>
                  <p className="text-sm mt-1 max-w-xs">
                    Add a connection to start syncing data from your apps into this agent.
                  </p>
                  <button
                    onClick={() => setShowAddModal(true)}
                    className="mt-4 px-5 py-2 text-sm font-medium bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
                  >
                    + Add Connection
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {connections.map((conn) => (
                    <AgentConnectionCard
                      key={conn.id}
                      agentId={agent.id}
                      connection={conn}
                      onDisconnect={(connId) => void handleDisconnect(connId)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "documents" && <AgentDocumentList agent={agent} />}
      </div>

      {/* Add connection modal */}
      {showAddModal && (
        <AddConnectionModal
          agentId={agent.id}
          onClose={() => setShowAddModal(false)}
          onConnected={(conn) => {
            setConnections((prev) => [...prev, conn]);
            setShowAddModal(false);
          }}
        />
      )}
    </div>
  );
}
