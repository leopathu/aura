"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import Link from "next/link";
import { ShieldCheck, Database, Bot, FileText, ArrowRight, Lock } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);

  useEffect(() => {
    if (token) {
      router.push("/chat");
    }
  }, [token, router]);

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      {/* Top Navbar */}
      <header className="flex h-16 items-center justify-between border-b border-slate-800 px-8">
        <div className="flex items-center space-x-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-aura-600 font-bold text-white shadow-lg shadow-aura-500/20">
            A
          </div>
          <span className="text-xl font-bold tracking-tight text-white">Aura</span>
          <span className="rounded-full bg-aura-500/10 px-2 py-0.5 text-xs font-medium text-aura-400 border border-aura-500/20">
            v0.1 OSS
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <Link
            href="/login"
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="rounded-lg bg-aura-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-aura-500 transition"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 text-center py-20">
        <div className="inline-flex items-center space-x-2 rounded-full border border-aura-500/30 bg-aura-500/10 px-3 py-1 text-xs text-aura-300 mb-8">
          <ShieldCheck className="h-4 w-4" />
          <span>Policy-Enforced Agentic Data & Knowledge Platform</span>
        </div>

        <h1 className="max-w-4xl text-5xl font-extrabold tracking-tight text-white sm:text-6xl">
          Connect your organization's data once.{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-aura-400 to-cyan-400">
            Query and act with secure AI agents.
          </span>
        </h1>

        <p className="mt-6 max-w-2xl text-lg text-slate-400">
          The open-source platform that sits between your LLM and your data. Enforce RBAC,
          row & column security policies, read-only SQL validation, document RAG, and MCP tools with full audit logging.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/register"
            className="flex items-center space-x-2 rounded-lg bg-aura-600 px-6 py-3 font-semibold text-white shadow-lg shadow-aura-500/25 hover:bg-aura-500 transition"
          >
            <span>Launch Platform</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-slate-700 bg-slate-900/60 px-6 py-3 font-semibold text-slate-300 hover:bg-slate-800 transition"
          >
            Sign in to Console
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="mt-20 grid max-w-5xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 text-left">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
            <Database className="h-8 w-8 text-aura-400 mb-4" />
            <h3 className="font-semibold text-white">Database Intelligence</h3>
            <p className="mt-2 text-sm text-slate-400">
              Live read-only SQL querying on PostgreSQL, MySQL, and SQLite with automatic AST safety parsing.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
            <FileText className="h-8 w-8 text-cyan-400 mb-4" />
            <h3 className="font-semibold text-white">Document RAG</h3>
            <p className="mt-2 text-sm text-slate-400">
              Ingest PDF, DOCX, XLSX, and CSV with recursive chunking, embeddings, and exact citation provenance.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
            <Lock className="h-8 w-8 text-emerald-400 mb-4" />
            <h3 className="font-semibold text-white">Policy Engine</h3>
            <p className="mt-2 text-sm text-slate-400">
              Fine-grained table & column restrictions, row-level filters, and real-time data masking for sensitive fields.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
            <Bot className="h-8 w-8 text-purple-400 mb-4" />
            <h3 className="font-semibold text-white">Agent Runtime</h3>
            <p className="mt-2 text-sm text-slate-400">
              Multi-step intent detection, planning, tool selection, report generation, and compliance audit trail.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
