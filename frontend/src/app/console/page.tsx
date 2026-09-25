"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import Link from "next/link";
import {
  BrainCircuit,
  Database,
  FileText,
  Cpu,
  ShieldCheck,
  Bot,
  ClipboardList,
  ArrowRight,
  TrendingUp,
  Server
} from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    brains: 0,
    sources: 0,
    documents: 0,
    models: 0,
    policies: 0,
    mcp: 0,
    runs: 0,
  });
  const [recentLogs, setRecentLogs] = useState<any[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [brains, sources, docs, models, policies, mcp, runs, logs] = await Promise.all([
        apiRequest<any[]>("/brains").catch(() => []),
        apiRequest<any[]>("/sources").catch(() => []),
        apiRequest<any[]>("/documents").catch(() => []),
        apiRequest<any[]>("/models/providers").catch(() => []),
        apiRequest<any[]>("/policies").catch(() => []),
        apiRequest<any[]>("/mcp/servers").catch(() => []),
        apiRequest<any[]>("/agent-runs?limit=5").catch(() => []),
        apiRequest<any[]>("/audit?limit=6").catch(() => []),
      ]);

      setStats({
        brains: brains.length,
        sources: sources.length,
        documents: docs.length,
        models: models.length,
        policies: policies.length,
        mcp: mcp.length,
        runs: runs.length,
      });
      setRecentLogs(logs);
    } catch (e) {
      console.error("Dashboard error", e);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Platform Overview</h1>
        <p className="mt-1 text-sm text-slate-400">
          Monitor your organization&apos;s isolated Brains, connected databases, security policies, AI gateways, and audit activities.
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <Link
          href="/console/brains"
          className="group rounded-xl border border-slate-800 bg-slate-900/50 p-5 hover:border-aura-500/50 transition col-span-1 sm:col-span-2"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-aura-600/15 border border-aura-500/25 text-aura-400">
                <BrainCircuit className="h-5 w-5" />
              </div>
              <div>
                <span className="text-xs font-semibold uppercase text-slate-400">Knowledge & Data Brains</span>
                <span className="block text-[11px] text-slate-500">
                  {stats.sources} Databases &bull; {stats.documents} Documents
                </span>
              </div>
            </div>
            <span className="text-3xl font-bold text-white">{stats.brains}</span>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-aura-400">
            <span>Manage Brains, Databases & Documents</span>
            <span className="flex items-center space-x-1 group-hover:translate-x-1 transition font-medium">
              <span>Open</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </span>
          </div>
        </Link>

        <Link
          href="/console/policies"
          className="group rounded-xl border border-slate-800 bg-slate-900/50 p-5 hover:border-emerald-500/50 transition"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Active Policies</span>
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-white">{stats.policies}</span>
            <span className="text-xs text-emerald-400 flex items-center space-x-1 group-hover:translate-x-0.5 transition">
              <span>Security rules</span>
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
        </Link>

        <Link
          href="/console/models"
          className="group rounded-xl border border-slate-800 bg-slate-900/50 p-5 hover:border-purple-500/50 transition"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">AI Gateways</span>
            <Cpu className="h-5 w-5 text-purple-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-white">{stats.models}</span>
            <span className="text-xs text-purple-400 flex items-center space-x-1 group-hover:translate-x-0.5 transition">
              <span>Providers</span>
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
        </Link>

        <Link
          href="/console/mcp"
          className="group rounded-xl border border-slate-800 bg-slate-900/50 p-5 hover:border-amber-500/50 transition"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">MCP Servers</span>
            <Server className="h-5 w-5 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-white">{stats.mcp}</span>
            <span className="text-xs text-amber-400 flex items-center space-x-1 group-hover:translate-x-0.5 transition">
              <span>Tools</span>
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
        </Link>

        <Link
          href="/chat"
          className="group rounded-xl border border-slate-800 bg-slate-900/50 p-5 hover:border-aura-500/50 transition"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Agent Runs</span>
            <Bot className="h-5 w-5 text-aura-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-white">{stats.runs}</span>
            <span className="text-xs text-aura-400 flex items-center space-x-1 group-hover:translate-x-0.5 transition">
              <span>Open Chat</span>
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
        </Link>
      </div>

      {/* Recent Audit Trails */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <ClipboardList className="h-5 w-5 text-aura-400" />
            <h2 className="font-semibold text-white">Recent Compliance & Audit Events</h2>
          </div>
          <Link href="/console/audit" className="text-xs font-medium text-aura-400 hover:text-aura-300">
            View all logs →
          </Link>
        </div>

        <div className="divide-y divide-slate-800/80">
          {recentLogs.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-500">No recent audit records found.</div>
          ) : (
            recentLogs.map((log) => (
              <div key={log.id} className="py-3 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3">
                  <span className="font-mono text-aura-300 font-semibold">{log.action}</span>
                  <span className="text-slate-400">[{log.resource_type || "SYSTEM"}]</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="rounded bg-emerald-500/10 text-emerald-400 px-2 py-0.5 text-[10px] font-medium border border-emerald-500/20">
                    {log.status}
                  </span>
                  <span className="text-slate-400">{new Date(log.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
