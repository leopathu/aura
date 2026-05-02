"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useBrains } from "@/hooks/useBrains";
import type { Brain, BrainCreate } from "@/types";

/**
 * Left sidebar — lists all brains and allows creating new ones.
 */
export function BrainSidebar() {
  const { brains, isLoading, selectedBrain, setSelectedBrain, createBrain, deleteBrain } =
    useBrains();
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    const payload: BrainCreate = {
      name: newName.trim(),
      ...(newDesc.trim() ? { description: newDesc.trim() } : {}),
    };
    await createBrain(payload);
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
            Brains
          </span>
          <button
            onClick={() => setShowModal(true)}
            title="Add brain"
            className="w-7 h-7 rounded-full bg-brand-600 text-white text-lg flex items-center justify-center hover:bg-brand-700 transition-colors leading-none"
          >
            +
          </button>
        </div>

        {/* Brain list */}
        <nav className="flex-1 overflow-y-auto py-2">
          {isLoading && (
            <p className="px-4 py-3 text-xs text-slate-400">Loading…</p>
          )}
          {!isLoading && brains.length === 0 && (
            <p className="px-4 py-3 text-xs text-slate-400">
              No brains yet. Create one to get started.
            </p>
          )}
          {brains.map((brain: Brain) => (
            <div
              key={brain.id}
              className={cn(
                "group flex items-center justify-between px-3 py-2.5 mx-2 rounded-lg cursor-pointer transition-colors",
                selectedBrain?.id === brain.id
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100"
              )}
              onClick={() => setSelectedBrain(brain)}
            >
              <div className="flex items-center gap-2 min-w-0">
                {/* Brain icon */}
                <span className="text-base shrink-0">🧠</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{brain.name}</p>
                  {brain.description && (
                    <p className="text-xs text-slate-400 truncate">{brain.description}</p>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteConfirm(brain.id);
                }}
                className="shrink-0 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 transition-all ml-1 text-sm"
                title="Delete brain"
              >
                ✕
              </button>
            </div>
          ))}
        </nav>
      </aside>

      {/* Create brain modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">New Brain</h2>
            <form onSubmit={handleCreate} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  autoFocus
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Research Papers"
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
                  placeholder="Optional description…"
                  rows={2}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                />
              </div>
              <div className="flex gap-2 justify-end pt-1">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setNewName(""); setNewDesc(""); }}
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

      {/* Delete confirmation modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-xs p-6 text-center">
            <p className="text-slate-700 font-medium mb-1">Delete this brain?</p>
            <p className="text-xs text-slate-400 mb-5">
              This removes the brain and all its document connections. Documents are not deleted.
            </p>
            <div className="flex gap-2 justify-center">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  await deleteBrain(deleteConfirm);
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
