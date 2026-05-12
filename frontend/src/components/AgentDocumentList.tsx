"use client";

import { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import { agentService } from "@/services/agent-service";
import type { Agent, AgentDocument, EmbedStatus } from "@/types";

interface AgentDocumentListProps {
  agent: Agent;
}

const EMBED_BADGE: Record<EmbedStatus, { label: string; classes: string }> = {
  pending: { label: "Pending", classes: "bg-slate-100 text-slate-500" },
  processing: { label: "Processing", classes: "bg-yellow-100 text-yellow-700" },
  ready: { label: "Ready", classes: "bg-green-100 text-green-700" },
  failed: { label: "Failed", classes: "bg-red-100 text-red-600" },
};

/**
 * Table of all documents synced into an agent, with app icon, embed status
 * badge, and a link to the source URL.
 */
export function AgentDocumentList({ agent }: AgentDocumentListProps) {
  const [documents, setDocuments] = useState<AgentDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState<EmbedStatus | "all">("all");
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const docs = await agentService.listDocuments(agent.id);
      setDocuments(docs);
    } catch {
      // silent
    } finally {
      setIsLoading(false);
    }
  }, [agent.id]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = documents.filter((doc) => {
    const matchStatus = filter === "all" || doc.embed_status === filter;
    const matchSearch =
      !search || doc.title.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  const counts = {
    all: documents.length,
    ready: documents.filter((d) => d.embed_status === "ready").length,
    pending: documents.filter((d) => d.embed_status === "pending").length,
    processing: documents.filter((d) => d.embed_status === "processing").length,
    failed: documents.filter((d) => d.embed_status === "failed").length,
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-200 bg-white">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search documents…"
          className="flex-1 max-w-xs border border-slate-300 rounded-lg px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-brand-500"
        />
        <div className="flex gap-1.5">
          {(["all", "ready", "pending", "processing", "failed"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs px-2.5 py-1 rounded-full transition-colors capitalize ${
                filter === f
                  ? "bg-brand-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {f} ({counts[f]})
            </button>
          ))}
        </div>
        <button
          onClick={() => void load()}
          className="text-xs px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
            Loading documents…
          </div>
        )}
        {!isLoading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center text-slate-400">
            <span className="text-4xl mb-3">📄</span>
            <p className="text-sm font-medium text-slate-600">No documents yet</p>
            <p className="text-xs mt-1 max-w-xs">
              Connect an app and trigger a sync to start ingesting documents.
            </p>
          </div>
        )}
        {!isLoading && filtered.length > 0 && (
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Document
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-28">
                  App
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-28">
                  Status
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-36">
                  Updated
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((doc) => {
                const badge = EMBED_BADGE[doc.embed_status];
                return (
                  <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-3">
                      <div className="min-w-0">
                        {doc.source_url ? (
                          <a
                            href={doc.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-brand-700 hover:underline truncate block max-w-sm"
                          >
                            {doc.title}
                          </a>
                        ) : (
                          <p className="font-medium text-slate-700 truncate max-w-sm">
                            {doc.title}
                          </p>
                        )}
                        {doc.embed_error && (
                          <p className="text-xs text-red-500 truncate mt-0.5">{doc.embed_error}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <div className="w-5 h-5 shrink-0 relative">
                          <Image
                            src={`/icons/${doc.agent_connection_id ? "gdrive" : "gdrive"}.svg`}
                            alt=""
                            width={20}
                            height={20}
                            className="rounded"
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex text-xs font-medium px-2 py-0.5 rounded-full ${badge.classes}`}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {new Date(doc.updated_at).toLocaleDateString([], {
                        dateStyle: "medium",
                      })}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
