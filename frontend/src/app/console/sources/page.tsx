"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { DataSource, DataSourceTable } from "@/types";
import { Database, Plus, RefreshCw, CheckCircle, AlertCircle, Table, Eye, Shield } from "lucide-react";

export default function SourcesPage() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);
  const [schemaTables, setSchemaTables] = useState<DataSourceTable[]>([]);
  const [testStatus, setTestStatus] = useState<string | null>(null);

  // Form modal
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("POSTGRES");
  const [connectionUri, setConnectionUri] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<DataSource[]>("/sources");
      setSources(data);
      if (data.length > 0 && !selectedSource) {
        viewSchema(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const viewSchema = async (source: DataSource) => {
    setSelectedSource(source);
    setTestStatus(null);
    try {
      const data = await apiRequest<{ tables: DataSourceTable[] }>(`/sources/${source.id}/schema`);
      setSchemaTables(data.tables || []);
    } catch (e) {
      console.error(e);
    }
  };

  const testConnection = async (id: string) => {
    setTestStatus("Testing connectivity...");
    try {
      const res = await apiRequest<{ status: string; message: string }>(`/sources/${id}/test`, {
        method: "POST",
      });
      setTestStatus(res.message);
    } catch (err: any) {
      setTestStatus(`Error: ${err.message}`);
    }
  };

  const syncSchema = async (id: string) => {
    try {
      await apiRequest(`/sources/${id}/sync-schema`, { method: "POST" });
      setTestStatus("Schema discovery queued. Refresh in a few seconds.");
      setTimeout(() => {
        if (selectedSource) viewSchema(selectedSource);
      }, 3000);
    } catch (err: any) {
      setTestStatus(`Sync error: ${err.message}`);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/sources", {
        method: "POST",
        body: JSON.stringify({ name, type, connection_uri: connectionUri, description, is_read_only: true }),
      });
      setShowModal(false);
      setName("");
      setConnectionUri("");
      setDescription("");
      loadSources();
    } catch (err: any) {
      alert(err.message || "Failed to add data source");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Data Sources & Gateways</h1>
          <p className="mt-1 text-sm text-slate-400">
            Connect PostgreSQL, MySQL, and SQLite databases with read-only security enforcement.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-aura-500 transition"
        >
          <Plus className="h-4 w-4" />
          <span>Connect Database</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Source List */}
        <div className="space-y-3">
          <div className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Configured Sources</div>
          {sources.map((s) => (
            <div
              key={s.id}
              onClick={() => viewSchema(s)}
              className={`cursor-pointer rounded-xl border p-4 transition ${
                selectedSource?.id === s.id
                  ? "border-aura-500 bg-slate-900 shadow-md"
                  : "border-slate-800 bg-slate-900/50 hover:bg-slate-900"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <Database className="h-4 w-4 text-aura-400" />
                  <span className="font-semibold text-sm text-white">{s.name}</span>
                </div>
                <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] text-slate-300 border border-slate-700">
                  {s.type}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-400 line-clamp-2">{s.description || "No description provided."}</p>
              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
                <span className="flex items-center space-x-1 text-emerald-400">
                  <Shield className="h-3 w-3" />
                  <span>Read-Only</span>
                </span>
                <span>{new Date(s.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Schema Inspector */}
        <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
          {selectedSource ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                    <span>{selectedSource.name}</span>
                    <span className="text-xs font-mono rounded bg-aura-500/10 text-aura-400 border border-aura-500/30 px-2 py-0.5">
                      {selectedSource.type}
                    </span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">{selectedSource.description}</p>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => testConnection(selectedSource.id)}
                    className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
                  >
                    Test Connection
                  </button>
                  <button
                    onClick={() => syncSchema(selectedSource.id)}
                    className="flex items-center space-x-1.5 rounded-lg bg-aura-600/20 border border-aura-500/30 px-3 py-1.5 text-xs font-medium text-aura-300 hover:bg-aura-600/30 transition"
                  >
                    <RefreshCw className="h-3 w-3" />
                    <span>Sync Schema</span>
                  </button>
                </div>
              </div>

              {testStatus && (
                <div className="rounded-lg border border-aura-500/30 bg-aura-500/10 p-3 text-xs text-aura-300">
                  {testStatus}
                </div>
              )}

              {/* Discovered Tables & Columns */}
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                  Discovered Tables & Schema ({schemaTables.length})
                </div>
                {schemaTables.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-400">
                    No schema tables discovered yet. Click "Sync Schema" to discover tables.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {schemaTables.map((tbl) => (
                      <div key={tbl.id} className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-mono text-sm font-bold text-white flex items-center space-x-2">
                            <Table className="h-4 w-4 text-aura-400" />
                            <span>{tbl.table_name}</span>
                          </span>
                          <span className="text-xs text-slate-400">{tbl.row_count} estimated rows</span>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 pt-3 border-t border-slate-800/60">
                          {tbl.columns.map((col) => (
                            <div key={col.name} className="rounded bg-slate-800/50 p-2 text-xs">
                              <div className="font-mono font-medium text-slate-200 truncate">
                                {col.name} {col.is_primary_key && <span className="text-amber-400 font-bold">*</span>}
                              </div>
                              <div className="text-[10px] text-slate-400">{col.data_type}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-xs text-slate-500">Select a data source to inspect schema.</div>
          )}
        </div>
      </div>

      {/* Connect Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Connect New Data Source</h3>
            <p className="mt-1 text-xs text-slate-400">
              Credentials are symmetrically encrypted using AES-256 before storage.
            </p>

            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Source Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Sales Warehouse"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Database Type</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                >
                  <option value="POSTGRES">PostgreSQL</option>
                  <option value="MYSQL">MySQL</option>
                  <option value="SQLITE">SQLite</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Connection URI</label>
                <input
                  type="text"
                  required
                  value={connectionUri}
                  onChange={(e) => setConnectionUri(e.target.value)}
                  placeholder="postgresql://user:password@host:5432/dbname"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Business context for agents and analysts..."
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-aura-600 px-4 py-2 text-xs font-medium text-white hover:bg-aura-500"
                >
                  {submitting ? "Connecting..." : "Add Source"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
