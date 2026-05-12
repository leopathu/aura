"use client";

import { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import { agentService } from "@/services/agent-service";
import { getErrorMessage } from "@/lib/api-client";
import type { AgentConnection, SyncStatusResponse } from "@/types";

interface AgentConnectionCardProps {
  agentId: string;
  connection: AgentConnection;
  onDisconnect: (connId: string) => void;
}

const STATUS_STYLES = {
  idle: "bg-green-100 text-green-700",
  syncing: "bg-yellow-100 text-yellow-700",
  error: "bg-red-100 text-red-600",
};

const STATUS_LABEL = {
  idle: "Idle",
  syncing: "Syncing…",
  error: "Error",
};

/**
 * Card showing a single connected app: icon, status badge, last sync time,
 * Sync Now button, and Disconnect option.
 */
export function AgentConnectionCard({
  agentId,
  connection,
  onDisconnect,
}: AgentConnectionCardProps) {
  const [status, setStatus] = useState<SyncStatusResponse | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<
    { id: string; started_at: string; finished_at: string | null; items_changed: number; error: string | null }[]
  >([]);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const s = await agentService.getSyncStatus(agentId, connection.id);
      setStatus(s);
    } catch {
      // silent
    }
  }, [agentId, connection.id]);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  // Poll while syncing
  useEffect(() => {
    if (status?.sync_status !== "syncing") return;
    const interval = setInterval(() => void loadStatus(), 3000);
    return () => clearInterval(interval);
  }, [status?.sync_status, loadStatus]);

  const handleSyncNow = async () => {
    setSyncing(true);
    setError(null);
    try {
      await agentService.triggerSync(agentId, connection.id);
      await loadStatus();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSyncing(false);
    }
  };

  const handleShowHistory = async () => {
    if (showHistory) {
      setShowHistory(false);
      return;
    }
    try {
      const logs = await agentService.getSyncHistory(agentId, connection.id);
      setHistory(logs);
      setShowHistory(true);
    } catch {
      setShowHistory(true);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "Never";
    const d = new Date(iso);
    return d.toLocaleString([], { dateStyle: "short", timeStyle: "short" });
  };

  const currentStatus = status?.sync_status ?? connection.sync_status;
  const isSyncing = currentStatus === "syncing" || syncing;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      {/* Top row: icon + name + badge */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 shrink-0 relative">
          <Image
            src={`/icons/${connection.app_type}.svg`}
            alt={connection.app_type}
            width={40}
            height={40}
            className="rounded-md"
          />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-700 truncate">{connection.display_name}</p>
          <p className="text-xs text-slate-400 capitalize">{connection.app_type}</p>
        </div>
        <span
          className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_STYLES[currentStatus]}`}
        >
          {isSyncing ? "Syncing…" : STATUS_LABEL[currentStatus]}
        </span>
      </div>

      {/* Metrics row */}
      {status && (
        <div className="mt-3 flex gap-4 text-xs text-slate-500">
          <span>
            <span className="font-medium text-slate-700">{status.ready_docs}</span>
            /{status.total_docs} docs ready
          </span>
          <span>
            Last synced:{" "}
            <span className="font-medium text-slate-700">{formatDate(status.last_synced_at)}</span>
          </span>
        </div>
      )}

      {/* Error display */}
      {status?.sync_error && (
        <p className="mt-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-2 py-1">
          {status.sync_error}
        </p>
      )}
      {error && (
        <p className="mt-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-2 py-1">
          {error}
        </p>
      )}

      {/* Actions */}
      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => void handleSyncNow()}
          disabled={isSyncing}
          className="flex-1 text-xs font-medium px-3 py-1.5 bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors"
        >
          {isSyncing ? "Syncing…" : "↻ Sync Now"}
        </button>
        <button
          onClick={() => void handleShowHistory()}
          className="text-xs font-medium px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-colors"
        >
          History
        </button>
        <button
          onClick={() => setDeleteConfirm(true)}
          className="text-xs font-medium px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
          title="Disconnect"
        >
          Disconnect
        </button>
      </div>

      {/* Sync history */}
      {showHistory && (
        <div className="mt-3 border-t border-slate-100 pt-3 space-y-1.5">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            Recent syncs
          </p>
          {history.length === 0 ? (
            <p className="text-xs text-slate-400">No sync history yet.</p>
          ) : (
            history.slice(0, 5).map((log) => (
              <div key={log.id} className="flex items-center justify-between text-xs text-slate-500">
                <span>{formatDate(log.started_at)}</span>
                <span className="text-slate-700">+{log.items_changed} changed</span>
                {log.error && <span className="text-red-500 truncate max-w-[120px]">{log.error}</span>}
              </div>
            ))
          )}
        </div>
      )}

      {/* Delete confirm */}
      {deleteConfirm && (
        <div className="mt-3 border-t border-slate-100 pt-3">
          <p className="text-xs text-slate-600 mb-2">
            Disconnect and delete all synced data from this connection?
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setDeleteConfirm(false)}
              className="flex-1 text-xs px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                onDisconnect(connection.id);
                setDeleteConfirm(false);
              }}
              className="flex-1 text-xs px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Disconnect
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
