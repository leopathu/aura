"use client";

import { useState, useEffect } from "react";
import { useBrainDocuments } from "@/hooks/useBrains";
import { documentService } from "@/services/document-service";
import { getErrorMessage } from "@/lib/api-client";
import type { Brain, Document } from "@/types";
import { cn } from "@/lib/utils";

interface BrainSourcesProps {
  brain: Brain;
}

/**
 * Sources tab — attach or detach documents for a brain.
 */
export function BrainSources({ brain }: BrainSourcesProps) {
  const { documents, isLoading, addDocument, removeDocument } = useBrainDocuments(brain.id);
  const [allDocs, setAllDocs] = useState<Document[]>([]);
  const [loadingAll, setLoadingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  // Load all available documents
  useEffect(() => {
    setLoadingAll(true);
    documentService
      .list(100)
      .then(setAllDocs)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoadingAll(false));
  }, [brain.id]);

  const connectedIds = new Set(documents.map((d: { id: string }) => d.id));

  const filtered = allDocs.filter((d: Document) =>
    d.title.toLowerCase().includes(search.toLowerCase())
  );

  const handleToggle = async (docId: string, connected: boolean) => {
    setError(null);
    try {
      if (connected) {
        await removeDocument(docId);
      } else {
        await addDocument(docId);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <div className="flex flex-col h-full px-6 py-5 gap-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-700">
          Sources for{" "}
          <span className="text-brand-700">{brain.name}</span>
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Toggle documents on or off to include them in this brain&apos;s context.
        </p>
      </div>

      {/* Search */}
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search documents…"
        className="border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
      />

      {error && (
        <p className="text-xs text-red-500 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {/* Document list */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {(isLoading || loadingAll) && (
          <p className="text-xs text-slate-400 py-4 text-center">Loading…</p>
        )}
        {!isLoading && !loadingAll && filtered.length === 0 && (
          <p className="text-xs text-slate-400 py-4 text-center">
            {allDocs.length === 0
              ? "No documents ingested yet. Add documents from the Documents page."
              : "No documents match your search."}
          </p>
        )}
        {filtered.map((doc) => {
          const connected = connectedIds.has(doc.id);
          return (
            <div
              key={doc.id}
              className={cn(
                "flex items-center justify-between p-3 rounded-xl border transition-colors",
                connected
                  ? "border-brand-200 bg-brand-50"
                  : "border-slate-200 bg-white hover:border-slate-300"
              )}
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-700 truncate">{doc.title}</p>
                {doc.source && (
                  <p className="text-xs text-slate-400 truncate">{doc.source}</p>
                )}
                <p className="text-xs text-slate-300 mt-0.5">
                  {new Date(doc.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => handleToggle(doc.id, connected)}
                className={cn(
                  "ml-3 shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                  connected
                    ? "bg-brand-600 text-white hover:bg-brand-700"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                )}
              >
                {connected ? "Remove" : "Add"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
