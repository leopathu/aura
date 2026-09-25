"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { MCPServerItem } from "@/types";
import { Server, Plus, CheckCircle, XCircle, ShieldAlert, RefreshCw } from "lucide-react";

export default function MCPPage() {
  const [servers, setServers] = useState<MCPServerItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Form modal
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [transportType, setTransportType] = useState("STDIO");
  const [endpointUrl, setEndpointUrl] = useState("");
  const [command, setCommand] = useState("");

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<MCPServerItem[]>("/mcp/servers");
      setServers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleTool = async (toolId: string) => {
    try {
      await apiRequest(`/mcp/tools/${toolId}/approve`, { method: "PUT" });
      loadServers();
    } catch (err: any) {
      alert(err.message || "Failed to toggle tool approval");
    }
  };

  const handleDiscover = async (serverId: string) => {
    try {
      await apiRequest(`/mcp/servers/${serverId}/discover`, { method: "POST" });
      loadServers();
    } catch (err: any) {
      alert(err.message || "Discovery failed");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/mcp/servers", {
        method: "POST",
        body: JSON.stringify({
          name,
          transport_type: transportType,
          endpoint_url: endpointUrl || null,
          command: command || null,
        }),
      });
      setShowModal(false);
      setName("");
      setEndpointUrl("");
      setCommand("");
      loadServers();
    } catch (err: any) {
      alert(err.message || "Failed to register server");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Model Context Protocol (MCP)</h1>
          <p className="mt-1 text-sm text-slate-400">
            Connect external MCP tool servers with administrative approval gates before tools are exposed to agents.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-aura-500 transition"
        >
          <Plus className="h-4 w-4" />
          <span>Register MCP Server</span>
        </button>
      </div>

      <div className="space-y-6">
        {servers.map((s) => (
          <div key={s.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <Server className="h-6 w-6 text-amber-400" />
                <div>
                  <h3 className="font-bold text-base text-white">{s.name}</h3>
                  <div className="flex items-center space-x-2 mt-0.5 text-xs text-slate-400">
                    <span className="font-mono rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-300 border border-slate-700">
                      {s.transport_type}
                    </span>
                    <span>Status: <strong className="text-emerald-400">{s.status}</strong></span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleDiscover(s.id)}
                className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Re-discover Tools</span>
              </button>
            </div>

            {/* Tools approval matrix */}
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
                <ShieldAlert className="h-4 w-4 text-amber-400" />
                <span>Exposed Tools & Administrative Approvals ({s.tools.length})</span>
              </div>

              <div className="divide-y divide-slate-800 border border-slate-800 rounded-lg overflow-hidden bg-slate-900/80">
                {s.tools.map((t) => (
                  <div key={t.id} className="p-3.5 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-mono font-semibold text-white">{t.name}</div>
                      <div className="text-slate-400 text-[11px] mt-0.5">{t.description || "No description"}</div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => handleToggleTool(t.id)}
                        className={`flex items-center space-x-1.5 rounded-lg px-3 py-1 text-xs font-medium transition border ${
                          t.is_approved
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20"
                            : "bg-red-500/10 text-red-400 border-red-500/30 hover:bg-red-500/20"
                        }`}
                      >
                        {t.is_approved ? (
                          <>
                            <CheckCircle className="h-3.5 w-3.5" />
                            <span>Approved for Agents</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="h-3.5 w-3.5" />
                            <span>Unapproved (Blocked)</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Register MCP Server</h3>
            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Server Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. GitHub MCP / Slack MCP"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Transport Protocol</label>
                <select
                  value={transportType}
                  onChange={(e) => setTransportType(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                >
                  <option value="STDIO">STDIO (Local Binary/Script)</option>
                  <option value="SSE">SSE (Server-Sent Events HTTP Endpoint)</option>
                </select>
              </div>

              {transportType === "SSE" ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase">Endpoint URL</label>
                  <input
                    type="text"
                    value={endpointUrl}
                    onChange={(e) => setEndpointUrl(e.target.value)}
                    placeholder="https://mcp.internal.acme.com"
                    className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase">Execution Command</label>
                  <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder="npx -y @modelcontextprotocol/server-github"
                    className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white"
                  />
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-aura-600 px-4 py-2 text-xs font-medium text-white hover:bg-aura-500"
                >
                  Register
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
