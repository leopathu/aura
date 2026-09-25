"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { AIProviderItem } from "@/types";
import { Cpu, Plus, CheckCircle, AlertCircle, Play } from "lucide-react";

export default function ModelsPage() {
  const [providers, setProviders] = useState<AIProviderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [testResult, setTestResult] = useState<Record<string, string>>({});

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [providerType, setProviderType] = useState("OPENAI");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<AIProviderItem[]>("/models/providers");
      setProviders(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (id: string) => {
    setTestResult((prev) => ({ ...prev, [id]: "Testing connection..." }));
    try {
      const res = await apiRequest<{ status: string; message: string; sample_response?: string }>(
        `/models/providers/${id}/test`,
        { method: "POST" }
      );
      setTestResult((prev) => ({
        ...prev,
        [id]: `${res.message} ${res.sample_response ? `("${res.sample_response}")` : ""}`,
      }));
    } catch (err: any) {
      setTestResult((prev) => ({ ...prev, [id]: `Error: ${err.message}` }));
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/models/providers", {
        method: "POST",
        body: JSON.stringify({
          name,
          provider_type: providerType,
          base_url: baseUrl || null,
          api_key: apiKey || null,
        }),
      });
      setShowModal(false);
      setName("");
      setBaseUrl("");
      setApiKey("");
      loadProviders();
    } catch (err: any) {
      alert(err.message || "Failed to create provider");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">AI Providers & Models</h1>
          <p className="mt-1 text-sm text-slate-400">
            Configure multi-provider LLM gateways (OpenAI, Anthropic, Ollama, Custom endpoints, Mock).
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-aura-500 transition"
        >
          <Plus className="h-4 w-4" />
          <span>Add AI Provider</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {providers.map((p) => (
          <div key={p.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Cpu className="h-6 w-6 text-purple-400" />
                <div>
                  <h3 className="font-bold text-base text-white">{p.name}</h3>
                  <span className="font-mono text-[10px] text-slate-400 uppercase rounded bg-slate-800 px-2 py-0.5 border border-slate-700">
                    {p.provider_type}
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleTest(p.id)}
                className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
              >
                <Play className="h-3 w-3 text-aura-400" />
                <span>Test Provider</span>
              </button>
            </div>

            <div className="text-xs text-slate-400 space-y-1">
              <div>Endpoint: <code className="text-slate-300">{p.base_url || "Standard Default URL"}</code></div>
              <div>Status: <span className="text-emerald-400">Active</span></div>
            </div>

            {testResult[p.id] && (
              <div className="rounded-lg border border-purple-500/30 bg-purple-500/10 p-3 text-xs text-purple-300">
                {testResult[p.id]}
              </div>
            )}
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add AI Model Provider</h3>
            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Provider Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Production OpenAI"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Provider Type</label>
                <select
                  value={providerType}
                  onChange={(e) => setProviderType(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                >
                  <option value="OPENAI">OpenAI</option>
                  <option value="ANTHROPIC">Anthropic (Claude)</option>
                  <option value="OLLAMA">Ollama (Local Models)</option>
                  <option value="CUSTOM_OPENAI">Custom OpenAI Compatible (vLLM, OpenRouter)</option>
                  <option value="MOCK">Mock Provider (Offline Testing)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">
                  Base URL (Optional)
                </label>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">
                  API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white"
                />
              </div>

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
                  Save Provider
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
