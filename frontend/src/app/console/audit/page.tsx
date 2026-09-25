"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { AuditLogItem } from "@/types";
import { ClipboardList, Bot, ShieldCheck, CheckCircle, XCircle, Search, Eye } from "lucide-react";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [tab, setTab] = useState<"AUDIT" | "RUNS">("AUDIT");
  const [selectedRun, setSelectedRun] = useState<any | null>(null);
  const [filterAction, setFilterAction] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [filterAction]);

  const loadData = async () => {
    setLoading(true);
    try {
      const url = filterAction ? `/audit?action=${encodeURIComponent(filterAction)}` : "/audit";
      const [lData, rData] = await Promise.all([
        apiRequest<AuditLogItem[]>(url),
        apiRequest<any[]>("/agent-runs"),
      ]);
      setLogs(lData);
      setRuns(rData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const inspectRun = async (id: string) => {
    try {
      const data = await apiRequest(`/agent-runs/${id}`);
      setSelectedRun(data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Compliance & Audit Logging</h1>
          <p className="mt-1 text-sm text-slate-400">
            Immutable audit records of all user actions, database queries, policy denials, and full agent execution traces.
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex rounded-lg bg-slate-900 border border-slate-800 p-1 text-xs">
          <button
            onClick={() => setTab("AUDIT")}
            className={`px-3 py-1.5 rounded-md font-medium transition ${
              tab === "AUDIT" ? "bg-aura-600 text-white shadow" : "text-slate-400 hover:text-white"
            }`}
          >
            Audit Logs
          </button>
          <button
            onClick={() => setTab("RUNS")}
            className={`px-3 py-1.5 rounded-md font-medium transition ${
              tab === "RUNS" ? "bg-aura-600 text-white shadow" : "text-slate-400 hover:text-white"
            }`}
          >
            Agent Run Traces
          </button>
        </div>
      </div>

      {tab === "AUDIT" && (
        <div className="space-y-4">
          {/* Filter */}
          <div className="flex items-center space-x-3">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Filter by action (e.g. USER_LOGIN)..."
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-850 pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-aura-500"
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden shadow-sm">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 border-b border-slate-800 text-[11px] font-semibold uppercase text-slate-400">
                <tr>
                  <th className="px-6 py-3.5">Action</th>
                  <th className="px-6 py-3.5">Resource</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">User</th>
                  <th className="px-6 py-3.5">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                      No audit records found.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-900/80">
                      <td className="px-6 py-3.5 font-mono font-bold text-aura-300">{log.action}</td>
                      <td className="px-6 py-3.5">
                        <span className="font-mono text-slate-300">
                          {log.resource_type ? `${log.resource_type}` : "SYSTEM"}
                        </span>
                      </td>
                      <td className="px-6 py-3.5">
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold border ${
                            log.status === "SUCCESS"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : "bg-red-500/10 text-red-400 border-red-500/20"
                          }`}
                        >
                          {log.status}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-slate-400 font-mono text-[11px]">
                        {log.user_id ? log.user_id.slice(0, 8) + "..." : "System"}
                      </td>
                      <td className="px-6 py-3.5 text-slate-400">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "RUNS" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Run list */}
          <div className="space-y-3">
            <div className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
              Execution Runs ({runs.length})
            </div>
            {runs.map((r) => (
              <div
                key={r.id}
                onClick={() => inspectRun(r.id)}
                className={`cursor-pointer rounded-xl border p-4 transition ${
                  selectedRun?.id === r.id
                    ? "border-aura-500 bg-slate-900 shadow-md"
                    : "border-slate-800 bg-slate-900/50 hover:bg-slate-900"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Bot className="h-4 w-4 text-aura-400" />
                    <span className="font-mono font-bold text-xs text-white">Run #{r.id.slice(0, 8)}</span>
                  </div>
                  <span className="rounded bg-emerald-500/10 text-emerald-400 px-2 py-0.5 text-[10px] font-bold border border-emerald-500/20">
                    {r.status}
                  </span>
                </div>
                <div className="mt-2 text-xs text-slate-400">
                  Intent: <strong className="text-white">{r.intent || "ASK"}</strong>
                </div>
                <div className="mt-3 text-[11px] text-slate-400 pt-2 border-t border-slate-800 flex justify-between">
                  <span>{r.plan?.length || 0} Planned Steps</span>
                  <span>{new Date(r.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Run Trace Detail */}
          <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
            {selectedRun ? (
              <div className="space-y-6">
                <div className="border-b border-slate-800 pb-4">
                  <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                    <Bot className="h-5 w-5 text-aura-400" />
                    <span>Agent Run Execution Trace: {selectedRun.id.slice(0, 12)}</span>
                  </h3>
                  <div className="mt-2 flex gap-4 text-xs text-slate-400">
                    <span>Status: <strong className="text-emerald-400">{selectedRun.status}</strong></span>
                    <span>Intent: <strong className="text-white">{selectedRun.intent}</strong></span>
                    <span>Total Steps: {selectedRun.steps?.length}</span>
                  </div>
                </div>

                {/* Steps Timeline */}
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                    Execution Steps
                  </div>
                  <div className="space-y-2 border-l-2 border-aura-500/30 pl-4 my-2">
                    {selectedRun.steps?.map((s: any) => (
                      <div key={s.index} className="text-xs">
                        <div className="font-bold text-white flex items-center space-x-2">
                          <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                          <span>{s.title}</span>
                          <span className="font-mono text-[10px] text-slate-400 uppercase rounded bg-slate-800 px-1.5 py-0.5 border border-slate-700">
                            {s.type}
                          </span>
                        </div>
                        {s.description && (
                          <div className="text-slate-400 mt-0.5 pl-5">{s.description}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tool Calls & Results */}
                {selectedRun.tool_calls && selectedRun.tool_calls.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                      Tools Invoked & Results
                    </div>
                    <div className="space-y-3">
                      {selectedRun.tool_calls.map((tc: any, idx: number) => (
                        <div key={idx} className="rounded-lg border border-slate-800 bg-slate-900/80 p-3 text-xs">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="font-mono font-bold text-aura-300">tool: {tc.tool_name}</span>
                            <span className="text-[10px] text-slate-400">
                              {tc.execution_time_ms ? `${tc.execution_time_ms} ms` : "Completed"}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono bg-slate-950 p-2 rounded border border-slate-800 overflow-x-auto">
                            Input: {JSON.stringify(tc.input)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-20 text-center text-xs text-slate-500">
                Select an agent run to inspect its step-by-step reasoning and tool call trace.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
