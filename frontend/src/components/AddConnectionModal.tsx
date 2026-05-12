"use client";

import { useState } from "react";
import Image from "next/image";
import { agentService } from "@/services/agent-service";
import { getErrorMessage } from "@/lib/api-client";
import type { AppType, AgentConnection } from "@/types";

interface AppOption {
  type: AppType;
  label: string;
  description: string;
  color: string;
}

const APP_OPTIONS: AppOption[] = [
  { type: "gdrive", label: "Google Drive", description: "Docs, Sheets, PDFs", color: "bg-blue-50 border-blue-200" },
  { type: "gmail", label: "Gmail", description: "Emails & threads", color: "bg-red-50 border-red-200" },
  { type: "slack", label: "Slack", description: "Channels & messages", color: "bg-purple-50 border-purple-200" },
  { type: "jira", label: "Jira", description: "Issues & comments", color: "bg-blue-50 border-blue-200" },
  { type: "notion", label: "Notion", description: "Pages & databases", color: "bg-slate-50 border-slate-200" },
  { type: "github", label: "GitHub", description: "Issues, PRs & wikis", color: "bg-gray-50 border-gray-200" },
  { type: "confluence", label: "Confluence", description: "Spaces & pages", color: "bg-blue-50 border-blue-200" },
  { type: "linear", label: "Linear", description: "Issues & projects", color: "bg-indigo-50 border-indigo-200" },
];

interface AddConnectionModalProps {
  agentId: string;
  onClose: () => void;
  onConnected: (connection: AgentConnection) => void;
}

/**
 * App picker modal — select an app type, create the connection, then
 * redirect the user through the OAuth flow.
 */
export function AddConnectionModal({ agentId, onClose, onConnected }: AddConnectionModalProps) {
  const [selected, setSelected] = useState<AppType | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [step, setStep] = useState<"pick" | "name">("pick");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedApp = APP_OPTIONS.find((a) => a.type === selected);

  const handlePickApp = (type: AppType) => {
    setSelected(type);
    const app = APP_OPTIONS.find((a) => a.type === type);
    setDisplayName(app?.label ?? "");
    setStep("name");
    setError(null);
  };

  const handleConnect = async () => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      // 1. Create the connection record
      const conn = await agentService.createConnection(agentId, {
        app_type: selected,
        display_name: (displayName.trim() || selectedApp?.label) ?? selected,
      });
      onConnected(conn);

      // 2. Get OAuth URL and redirect
      const { url } = await agentService.getOAuthStartUrl(agentId, conn.id);
      window.location.href = url;
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-slate-800">
            {step === "pick" ? "Connect an App" : `Connect ${selectedApp?.label}`}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors text-xl leading-none"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5">
          {step === "pick" ? (
            <>
              <p className="text-sm text-slate-500 mb-4">
                Choose an app to connect. You&apos;ll be redirected to authorise Aura.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {APP_OPTIONS.map((app) => (
                  <button
                    key={app.type}
                    onClick={() => handlePickApp(app.type)}
                    className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all hover:shadow-sm ${app.color}`}
                  >
                    <div className="w-9 h-9 shrink-0 relative">
                      <Image
                        src={`/icons/${app.type}.svg`}
                        alt={app.label}
                        width={36}
                        height={36}
                        className="rounded-md"
                      />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-700">{app.label}</p>
                      <p className="text-xs text-slate-400 truncate">{app.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-5 p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="w-10 h-10 shrink-0 relative">
                  <Image
                    src={`/icons/${selected}.svg`}
                    alt={selectedApp?.label ?? ""}
                    width={40}
                    height={40}
                    className="rounded-md"
                  />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-700">{selectedApp?.label}</p>
                  <p className="text-xs text-slate-400">{selectedApp?.description}</p>
                </div>
              </div>

              <div className="mb-5">
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Display name
                </label>
                <input
                  autoFocus
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder={selectedApp?.label}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              {error && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4">
                  {error}
                </p>
              )}

              <div className="flex justify-between">
                <button
                  onClick={() => setStep("pick")}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  ← Back
                </button>
                <button
                  onClick={() => void handleConnect()}
                  disabled={loading}
                  className="px-5 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? "Redirecting…" : "Authorise →"}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
