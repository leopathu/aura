"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAgents } from "@/hooks/useAgents";
import type { Agent, AgentCreate } from "@/types";

/**
 * Left sidebar — lists all agents and allows creating new ones.
 */
export function AgentSidebar() {
  const { agents, isLoading, selectedAgent, setSelectedAgent, createAgent, deleteAgent } =
    useAgents();
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    const payload: AgentCreate = {
      name: newName.trim(),
      ...(newDesc.trim() ? { description: newDesc.trim() } : {}),
    };
    await createAgent(payload);
    setNewName("");
    setNewDesc("");
    setShowModal(false);
    setCreating(false);
  };

  return (
    <>
      <aside className="w-64 shrink-0 flex flex-col border-r border-slate-200 bg-white h-full">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-slate-100">
          <span className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            Agents
          </span>
          <button
            onClick={() => setShowModal(true)}
            title="Add agent"
            className="w-7 h-7 rounded-full bg-brand-600 text-white text-lg flex items-center justify-center hover:bg-brand-700 transition-colors leading-none"
          >
            +
          </button>
        </div>

        {/* Agent list */}
        <nav className="flex-1 overflow-y-auto py-2">
          {isLoading && (
            <p className="px-4 py-3 text-xs text-slate-400">Loading…</p>
          )}
          {!isLoading && agents.length === 0 && (
            <p className="px-4 py-3 text-xs text-slate-400">
              No agents yet. Create one to get started.
            </p>
          )}
          {agents.map((agent: Agent) => (
            <div
              key={agent.id}
              className={cn(
                "group flex items-center justify-between px-3 py-2.5 mx-2 rounded-lg cursor-pointer transition-colors",
                selectedAgent?.id === agent.id
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100"
              )}
              onClick={() => setSelectedAgent(agent)}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-base shrink-0">🤖</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{agent.name}</p>
                  {agent.description && (
                    <p className="text-xs text-slate-400 truncate">{agent.description}</p>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteConfirm(agent.id);
                }}
                className="shrink-0 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 transition-all ml-1 text-sm"
                title="Delete agent"
              >
                ✕
              </button>
            </div>
          ))}
        </nav>
      </aside>

      {/* Create agent modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">New Agent</h2>
            <form onSubmit={(e) => void handleCreate(e)} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  autoFocus
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Engineering Agent"
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Description
                </label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="What does this agent do?"
                  rows={2}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newName.trim()}
                  className="px-4 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors"
                >
                  {creating ? "Creating…" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirm modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-2">Delete Agent?</h2>
            <p className="text-sm text-slate-500 mb-6">
              This will permanently delete the agent and all its connections, synced documents, and
              conversations. This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  void deleteAgent(deleteConfirm);
                  setDeleteConfirm(null);
                }}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
