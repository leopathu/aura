"use client";

import { useState, useEffect, useCallback } from "react";
import { settingsService } from "@/services/settings-service";
import { getErrorMessage } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type {
  AISettingsUpdate,
  AISettingsResponse,
  LLMProvider,
  EmbeddingProvider,
} from "@/types";

// ---------------------------------------------------------------------------
// Model catalogs
// ---------------------------------------------------------------------------

const LLM_MODELS: Record<LLMProvider, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini"],
  anthropic: [
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-5-sonnet-20241022",
  ],
  google: [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
  ],
  ollama: [], // free text
};

const EMBEDDING_MODELS: Record<EmbeddingProvider, string[]> = {
  openai: [
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
  ],
  google: ["text-embedding-004", "text-embedding-preview-0409"],
  ollama: [], // free text
};

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google (Gemini)",
  ollama: "Ollama (Local)",
};

const PROVIDER_COLORS: Record<string, string> = {
  openai: "bg-emerald-50 border-emerald-200 text-emerald-700",
  anthropic: "bg-orange-50 border-orange-200 text-orange-700",
  google: "bg-blue-50 border-blue-200 text-blue-700",
  ollama: "bg-purple-50 border-purple-200 text-purple-700",
};

// ---------------------------------------------------------------------------
// Default settings
// ---------------------------------------------------------------------------

const DEFAULTS: AISettingsUpdate = {
  llm_provider: "openai",
  llm_model: "gpt-4o",
  llm_api_key: "",
  llm_base_url: "http://localhost:11434",
  temperature: 0.2,
  embedding_provider: "openai",
  embedding_model: "text-embedding-3-small",
  embedding_api_key: "",
  embedding_base_url: "http://localhost:11434",
  chunk_size: 512,
  chunk_overlap: 64,
  retrieval_top_k: 5,
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
      <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-5">
        <span className="text-lg">{icon}</span>
        {title}
      </h2>
      {children}
    </div>
  );
}

function FieldRow({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[180px_1fr] gap-4 items-start py-3 border-b border-slate-100 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
      </div>
      <div>{children}</div>
    </div>
  );
}

function Input({
  value,
  onChange,
  type = "text",
  placeholder,
  min,
  max,
  step,
}: {
  value: string | number;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      min={min}
      max={max}
      step={step}
      className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500 bg-white"
    />
  );
}

function ProviderButton({
  provider,
  active,
  onClick,
}: {
  provider: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all",
        active
          ? PROVIDER_COLORS[provider] ?? "bg-brand-50 border-brand-200 text-brand-700"
          : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
      )}
    >
      {PROVIDER_LABELS[provider] ?? provider}
    </button>
  );
}

function ModelSelect({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder?: string;
}) {
  if (options.length === 0) {
    // Free text input (Ollama)
    return (
      <Input value={value} onChange={onChange} placeholder={placeholder ?? "e.g. llama3.2"} />
    );
  }
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500 bg-white"
    >
      {options.map((m) => (
        <option key={m} value={m}>
          {m}
        </option>
      ))}
    </select>
  );
}

function ApiKeyInput({
  value,
  isSet,
  onChange,
  placeholder,
}: {
  value: string;
  isSet: boolean;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="flex gap-2">
      <div className="flex-1 relative">
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={isSet && !value ? "••••••••••••••••  (saved — enter to replace)" : placeholder}
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500 bg-white pr-10"
        />
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
        >
          {show ? "Hide" : "Show"}
        </button>
      </div>
      {isSet && !value && (
        <span className="flex items-center text-xs text-emerald-600 gap-1">
          <span>✓</span> Set
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function SettingsPage() {
  const [form, setForm] = useState<AISettingsUpdate>(DEFAULTS);
  const [savedKeys, setSavedKeys] = useState({ llm: false, embedding: false });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data: AISettingsResponse = await settingsService.get();
      setForm({
        llm_provider: data.llm_provider,
        llm_model: data.llm_model,
        llm_api_key: "",  // never pre-fill keys
        llm_base_url: data.llm_base_url,
        temperature: data.temperature,
        embedding_provider: data.embedding_provider,
        embedding_model: data.embedding_model,
        embedding_api_key: "",
        embedding_base_url: data.embedding_base_url,
        chunk_size: data.chunk_size,
        chunk_overlap: data.chunk_overlap,
        retrieval_top_k: data.retrieval_top_k,
      });
      setSavedKeys({ llm: data.llm_api_key_set, embedding: data.embedding_api_key_set });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const set = <K extends keyof AISettingsUpdate>(key: K, value: AISettingsUpdate[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleLLMProviderChange = (p: LLMProvider) => {
    const models = LLM_MODELS[p];
    set("llm_provider", p);
    set("llm_model", models[0] ?? "");
  };

  const handleEmbeddingProviderChange = (p: EmbeddingProvider) => {
    const models = EMBEDDING_MODELS[p];
    set("embedding_provider", p);
    set("embedding_model", models[0] ?? "");
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      await settingsService.update(form);
      setSuccess(true);
      setSavedKeys({
        llm: savedKeys.llm || !!form.llm_api_key,
        embedding: savedKeys.embedding || !!form.embedding_api_key,
      });
      set("llm_api_key", "");
      set("embedding_api_key", "");
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-slate-400">Loading settings…</p>
      </div>
    );
  }

  const llmIsOllama = form.llm_provider === "ollama";
  const embIsOllama = form.embedding_provider === "ollama";

  return (
    <div className="max-w-2xl mx-auto py-10 px-4 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-800">AI Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure language models, embeddings, and RAG pipeline parameters.
        </p>
      </div>

      <form onSubmit={(e) => void handleSave(e)} className="space-y-6">
        {/* ── LLM Configuration ─────────────────────────────── */}
        <SectionCard title="Language Model (LLM)" icon="🤖">
          <FieldRow label="Provider">
            <div className="flex flex-wrap gap-2">
              {(["openai", "anthropic", "google", "ollama"] as LLMProvider[]).map((p) => (
                <ProviderButton
                  key={p}
                  provider={p}
                  active={form.llm_provider === p}
                  onClick={() => handleLLMProviderChange(p)}
                />
              ))}
            </div>
          </FieldRow>

          <FieldRow label="Model">
            <ModelSelect
              value={form.llm_model}
              onChange={(v) => set("llm_model", v)}
              options={LLM_MODELS[form.llm_provider]}
              placeholder="e.g. llama3.2, mistral"
            />
          </FieldRow>

          {!llmIsOllama && (
            <FieldRow label="API Key" hint="Stored securely, never exposed">
              <ApiKeyInput
                value={form.llm_api_key}
                isSet={savedKeys.llm}
                onChange={(v) => set("llm_api_key", v)}
                placeholder={
                  form.llm_provider === "anthropic"
                    ? "sk-ant-…"
                    : form.llm_provider === "google"
                    ? "AIza…"
                    : "sk-…"
                }
              />
            </FieldRow>
          )}

          {llmIsOllama && (
            <FieldRow label="Ollama URL" hint="Base URL of your local Ollama server">
              <Input
                value={form.llm_base_url}
                onChange={(v) => set("llm_base_url", v)}
                placeholder="http://localhost:11434"
              />
            </FieldRow>
          )}

          <FieldRow label="Temperature" hint="0 = deterministic · 1 = creative">
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={0}
                max={2}
                step={0.05}
                value={form.temperature}
                onChange={(e) => set("temperature", parseFloat(e.target.value))}
                className="flex-1 accent-brand-600"
              />
              <span className="w-10 text-sm text-slate-600 text-right">
                {form.temperature.toFixed(2)}
              </span>
            </div>
          </FieldRow>
        </SectionCard>

        {/* ── Embedding Configuration ─────────────────────────── */}
        <SectionCard title="Embeddings" icon="🔢">
          {form.llm_provider === "anthropic" && (
            <div className="mb-4 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700">
              ⚠️ Anthropic does not provide an embeddings API. Select OpenAI or Ollama below and
              provide the corresponding API key.
            </div>
          )}

          <FieldRow label="Provider">
            <div className="flex flex-wrap gap-2">
              {(["openai", "google", "ollama"] as EmbeddingProvider[]).map((p) => (
                <ProviderButton
                  key={p}
                  provider={p}
                  active={form.embedding_provider === p}
                  onClick={() => handleEmbeddingProviderChange(p)}
                />
              ))}
            </div>
          </FieldRow>

          <FieldRow label="Model">
            <ModelSelect
              value={form.embedding_model}
              onChange={(v) => set("embedding_model", v)}
              options={EMBEDDING_MODELS[form.embedding_provider]}
              placeholder="e.g. nomic-embed-text"
            />
          </FieldRow>

          {!embIsOllama && (
            <FieldRow
              label="API Key"
              hint={
                form.embedding_provider === form.llm_provider
                  ? "Leave blank to reuse the LLM API key"
                  : "Separate key for the embedding provider"
              }
            >
              <ApiKeyInput
                value={form.embedding_api_key}
                isSet={savedKeys.embedding}
                onChange={(v) => set("embedding_api_key", v)}
                placeholder={
                  form.embedding_provider === "google" ? "AIza…" : "sk-…"
                }
              />
            </FieldRow>
          )}

          {embIsOllama && (
            <FieldRow label="Ollama URL">
              <Input
                value={form.embedding_base_url}
                onChange={(v) => set("embedding_base_url", v)}
                placeholder="http://localhost:11434"
              />
            </FieldRow>
          )}

          <div className="mt-3 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500">
            ⚠️ Changing the embedding model after ingesting documents requires re-uploading all
            files, as vector dimensions may differ.
          </div>
        </SectionCard>

        {/* ── RAG Pipeline ────────────────────────────────────── */}
        <SectionCard title="RAG Pipeline" icon="⚙️">
          <FieldRow label="Chunk Size" hint="Characters per chunk (64–4096)">
            <Input
              type="number"
              value={form.chunk_size}
              onChange={(v) => set("chunk_size", parseInt(v, 10))}
              min={64}
              max={4096}
            />
          </FieldRow>

          <FieldRow label="Chunk Overlap" hint="Overlapping chars between chunks (0–512)">
            <Input
              type="number"
              value={form.chunk_overlap}
              onChange={(v) => set("chunk_overlap", parseInt(v, 10))}
              min={0}
              max={512}
            />
          </FieldRow>

          <FieldRow label="Top-K Retrieval" hint="Number of chunks retrieved per query (1–20)">
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={1}
                max={20}
                step={1}
                value={form.retrieval_top_k}
                onChange={(e) => set("retrieval_top_k", parseInt(e.target.value, 10))}
                className="flex-1 accent-brand-600"
              />
              <span className="w-8 text-sm text-slate-600 text-right">{form.retrieval_top_k}</span>
            </div>
          </FieldRow>
        </SectionCard>

        {/* ── Status + Save ────────────────────────────────────── */}
        {error && (
          <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
            {error}
          </div>
        )}
        {success && (
          <div className="px-4 py-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700">
            ✓ Settings saved successfully.
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2.5 bg-brand-600 text-white rounded-xl text-sm font-medium hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {saving ? "Saving…" : "Save Settings"}
          </button>
        </div>
      </form>
    </div>
  );
}
