"use client";

import { useEffect, useState, useMemo } from "react";
import { apiRequest } from "@/lib/api";
import { AIProviderItem, AIModelItem } from "@/types";
import {
  Cpu,
  Plus,
  CheckCircle,
  AlertCircle,
  Play,
  Trash2,
  Star,
  Layers,
  Bot,
  Sparkles,
  Server,
  Eye,
  EyeOff,
  Check,
  RefreshCw,
  ExternalLink,
  Info
} from "lucide-react";

type ProviderType = "OPENAI" | "ANTHROPIC" | "OLLAMA" | "CUSTOM_OPENAI" | "MOCK";
type ModelType = "CHAT" | "EMBEDDING";

interface ModelPreset {
  id: string;
  name: string;
  contextWindow: number;
  description?: string;
}

const PRESET_MODELS: Record<ProviderType, Record<ModelType, ModelPreset[]>> = {
  OPENAI: {
    CHAT: [
      { id: "gpt-4o", name: "GPT-4o Omnimodel", contextWindow: 128000, description: "Flagship fast & multimodal model" },
      { id: "gpt-4o-mini", name: "GPT-4o Mini", contextWindow: 128000, description: "Affordable, lightweight & fast" },
      { id: "gpt-4-turbo", name: "GPT-4 Turbo", contextWindow: 128000, description: "High-intelligence legacy model" },
      { id: "o1", name: "OpenAI o1 Reasoning", contextWindow: 128000, description: "Deep step-by-step thinking model" },
      { id: "o1-mini", name: "OpenAI o1-mini", contextWindow: 128000, description: "Fast reasoning for math & code" },
      { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", contextWindow: 16385, description: "Legacy standard model" },
    ],
    EMBEDDING: [
      { id: "text-embedding-3-small", name: "Text Embedding 3 Small", contextWindow: 8191, description: "Standard 1536-dim vector model" },
      { id: "text-embedding-3-large", name: "Text Embedding 3 Large", contextWindow: 8191, description: "Top-performance 3072-dim vectors" },
      { id: "text-embedding-ada-002", name: "Ada 002 (Legacy)", contextWindow: 8191, description: "Previous generation embedder" },
    ],
  },
  ANTHROPIC: {
    CHAT: [
      { id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet", contextWindow: 200000, description: "State-of-the-art coding & agent reasoning" },
      { id: "claude-3-5-haiku-20241022", name: "Claude 3.5 Haiku", contextWindow: 200000, description: "Blazing fast response speed" },
      { id: "claude-3-opus-20240229", name: "Claude 3 Opus", contextWindow: 200000, description: "Complex research & deep analysis" },
      { id: "claude-3-haiku-20240307", name: "Claude 3 Haiku", contextWindow: 200000, description: "Compact & responsive model" },
    ],
    EMBEDDING: [],
  },
  OLLAMA: {
    CHAT: [
      { id: "llama3.1:8b", name: "Meta Llama 3.1 8B", contextWindow: 128000, description: "Efficient open-weights powerhouse" },
      { id: "llama3.1:70b", name: "Meta Llama 3.1 70B", contextWindow: 128000, description: "High-capability open model" },
      { id: "llama3.2:3b", name: "Meta Llama 3.2 3B", contextWindow: 128000, description: "Lightweight edge & local model" },
      { id: "deepseek-r1:8b", name: "DeepSeek R1 Distill 8B", contextWindow: 128000, description: "Open reasoning and chain-of-thought" },
      { id: "deepseek-r1:14b", name: "DeepSeek R1 Distill 14B", contextWindow: 128000, description: "Stronger open reasoning model" },
      { id: "mistral:7b", name: "Mistral 7B Instruct", contextWindow: 32768, description: "Versatile European open model" },
      { id: "qwen2.5:7b", name: "Alibaba Qwen 2.5 7B", contextWindow: 128000, description: "Exceptional coding & multilingual" },
      { id: "phi3:mini", name: "Microsoft Phi-3 Mini", contextWindow: 4096, description: "Compact high-efficiency SLM" },
      { id: "gemma2:9b", name: "Google Gemma 2 9B", contextWindow: 8192, description: "Google open-weights model" },
    ],
    EMBEDDING: [
      { id: "nomic-embed-text", name: "Nomic Embed Text", contextWindow: 8192, description: "High-performance RAG vector model (768 dim)" },
      { id: "bge-m3", name: "BAAI BGE-M3", contextWindow: 8192, description: "Multi-lingual dense vector embedder (1024 dim)" },
      { id: "all-minilm", name: "all-MiniLM-L6-v2", contextWindow: 512, description: "Fast compact embedding model (384 dim)" },
      { id: "mxbai-embed-large", name: "MixedBread Embed Large", contextWindow: 512, description: "Dense semantic representations (1024 dim)" },
    ],
  },
  CUSTOM_OPENAI: {
    CHAT: [
      { id: "meta-llama/Llama-3-70b-chat-hf", name: "Llama 3 70B (Groq/vLLM)", contextWindow: 8192, description: "Groq or vLLM hosted open model" },
      { id: "mistralai/Mixtral-8x7B-Instruct-v0.1", name: "Mixtral 8x7B Instruct", contextWindow: 32768, description: "Sparse Mixture-of-Experts" },
    ],
    EMBEDDING: [
      { id: "text-embedding-3-small", name: "Custom Embed Small", contextWindow: 8192, description: "Custom gateway embedding" },
      { id: "BAAI/bge-large-en-v1.5", name: "BGE Large English", contextWindow: 512, description: "vLLM / TEI served embedder" },
    ],
  },
  MOCK: {
    CHAT: [
      { id: "mock-gpt-4", name: "Mock GPT-4 Reasoning", contextWindow: 128000, description: "Offline simulation model for tests" },
    ],
    EMBEDDING: [
      { id: "mock-embedding", name: "Mock Deterministic Embedder", contextWindow: 8192, description: "Offline zero-dependency embedder" },
    ],
  },
};

export default function ModelsPage() {
  const [providers, setProviders] = useState<AIProviderItem[]>([]);
  const [models, setModels] = useState<AIModelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"chat" | "embedding" | "providers">("chat");

  // Connection testing state
  const [testResult, setTestResult] = useState<
    Record<string, { status: "testing" | "success" | "error"; message: string; sample?: string }>
  >({});

  // Provider Form Modal
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [pName, setPName] = useState("");
  const [pType, setPType] = useState<ProviderType>("OPENAI");
  const [pBaseUrl, setPBaseUrl] = useState("");
  const [pApiKey, setPApiKey] = useState("");
  const [pShowApiKey, setPShowApiKey] = useState(false);
  const [pSubmitting, setPSubmitting] = useState(false);
  const [pError, setPError] = useState<string | null>(null);

  // Model Form Modal
  const [showModelModal, setShowModelModal] = useState(false);
  const [mProviderId, setMProviderId] = useState("");
  const [mType, setMType] = useState<ModelType>("CHAT");
  const [mSelectedPreset, setMSelectedPreset] = useState<string>("");
  const [mCustomModelId, setMCustomModelId] = useState("");
  const [mName, setMName] = useState("");
  const [mContextWindow, setMContextWindow] = useState(128000);
  const [mIsDefault, setMIsDefault] = useState(false);
  const [mSubmitting, setMSubmitting] = useState(false);
  const [mError, setMError] = useState<string | null>(null);

  // Dynamic models discovered from provider
  const [discoveredModels, setDiscoveredModels] = useState<string[]>([]);
  const [loadingDiscovered, setLoadingDiscovered] = useState(false);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [provData, modelData] = await Promise.all([
        apiRequest<AIProviderItem[]>("/models/providers"),
        apiRequest<AIModelItem[]>("/models"),
      ]);
      setProviders(provData);
      setModels(modelData);
    } catch (e) {
      console.error("Failed to load models data:", e);
    } finally {
      setLoading(false);
    }
  };

  // Switch Provider Type in Modal: Update placeholders and base URLs dynamically
  const handleProviderTypeChange = (newType: ProviderType) => {
    setPType(newType);
    if (newType === "OPENAI") {
      setPName("OpenAI Production");
      setPBaseUrl("https://api.openai.com/v1");
    } else if (newType === "ANTHROPIC") {
      setPName("Anthropic Claude");
      setPBaseUrl("https://api.anthropic.com");
    } else if (newType === "OLLAMA") {
      setPName("Local Ollama Server");
      setPBaseUrl("http://localhost:11434");
      setPApiKey("");
    } else if (newType === "CUSTOM_OPENAI") {
      setPName("Custom Inference Gateway");
      setPBaseUrl("https://api.groq.com/openai/v1");
    } else if (newType === "MOCK") {
      setPName("Offline Development Mock");
      setPBaseUrl("");
      setPApiKey("");
    }
  };

  const openAddProviderModal = () => {
    handleProviderTypeChange("OPENAI");
    setPApiKey("");
    setPError(null);
    setShowProviderModal(true);
  };

  const handleCreateProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    setPSubmitting(true);
    setPError(null);
    try {
      await apiRequest("/models/providers", {
        method: "POST",
        body: JSON.stringify({
          name: pName,
          provider_type: pType,
          base_url: pBaseUrl || null,
          api_key: pApiKey || null,
        }),
      });
      setShowProviderModal(false);
      await loadAllData();
    } catch (err: any) {
      setPError(err.message || "Failed to create provider");
    } finally {
      setPSubmitting(false);
    }
  };

  const handleDeleteProvider = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This will also remove all models associated with this provider.`)) {
      return;
    }
    try {
      await apiRequest(`/models/providers/${id}`, { method: "DELETE" });
      await loadAllData();
    } catch (err: any) {
      alert(err.message || "Failed to delete provider");
    }
  };

  const handleTestProvider = async (id: string) => {
    setTestResult((prev) => ({
      ...prev,
      [id]: { status: "testing", message: "Connecting to provider..." },
    }));
    try {
      const res = await apiRequest<{ status: string; message: string; sample_response?: string }>(
        `/models/providers/${id}/test`,
        { method: "POST" }
      );
      if (res.status === "success") {
        setTestResult((prev) => ({
          ...prev,
          [id]: {
            status: "success",
            message: res.message,
            sample: res.sample_response,
          },
        }));
      } else {
        setTestResult((prev) => ({
          ...prev,
          [id]: { status: "error", message: res.message },
        }));
      }
    } catch (err: any) {
      setTestResult((prev) => ({
        ...prev,
        [id]: { status: "error", message: err.message || "Connection failed" },
      }));
    }
  };

  const fetchDiscoveredModels = async (providerId: string) => {
    if (!providerId) {
      setDiscoveredModels([]);
      return;
    }
    setLoadingDiscovered(true);
    try {
      const res = await apiRequest<{ models: string[] }>(`/models/providers/${providerId}/available-models`);
      setDiscoveredModels(res.models || []);
    } catch {
      setDiscoveredModels([]);
    } finally {
      setLoadingDiscovered(false);
    }
  };

  // Open Model Modal
  const openAddModelModal = (preselectedType?: ModelType) => {
    const targetType = preselectedType || (activeTab === "embedding" ? "EMBEDDING" : "CHAT");
    setMType(targetType);
    setMError(null);

    // Pick first provider if available
    const initialProvider = providers[0];
    const initialProvId = initialProvider ? initialProvider.id : "";
    setMProviderId(initialProvId);

    if (initialProvId) {
      fetchDiscoveredModels(initialProvId);
    } else {
      setDiscoveredModels([]);
    }

    applyPresetDefaults(initialProvider ? (initialProvider.provider_type as ProviderType) : "OPENAI", targetType);
    setShowModelModal(true);
  };

  const applyPresetDefaults = (provType: ProviderType, modelType: ModelType) => {
    const availablePresets = PRESET_MODELS[provType]?.[modelType] || [];
    if (availablePresets.length > 0) {
      const firstPreset = availablePresets[0];
      setMSelectedPreset(firstPreset.id);
      setMCustomModelId("");
      setMName(firstPreset.name);
      setMContextWindow(firstPreset.contextWindow);
    } else {
      setMSelectedPreset("__custom__");
      setMCustomModelId("");
      setMName(modelType === "CHAT" ? "Custom Chat Model" : "Custom Embedding Model");
      setMContextWindow(modelType === "CHAT" ? 128000 : 8192);
    }
    setMIsDefault(false);
  };

  // Selected Provider in Model Modal
  const currentModalProvider = useMemo(() => {
    return providers.find((p) => p.id === mProviderId);
  }, [providers, mProviderId]);

  const currentPresets = useMemo(() => {
    const provType = (currentModalProvider?.provider_type as ProviderType) || "OPENAI";
    return PRESET_MODELS[provType]?.[mType] || [];
  }, [currentModalProvider, mType]);

  const handleProviderSelectChange = (newProvId: string) => {
    setMProviderId(newProvId);
    fetchDiscoveredModels(newProvId);
    const selectedProv = providers.find((p) => p.id === newProvId);
    if (selectedProv) {
      applyPresetDefaults(selectedProv.provider_type as ProviderType, mType);
    }
  };

  const handleModelTypeChange = (newType: ModelType) => {
    setMType(newType);
    const provType = (currentModalProvider?.provider_type as ProviderType) || "OPENAI";
    applyPresetDefaults(provType, newType);
  };

  const handlePresetSelectChange = (presetId: string) => {
    setMSelectedPreset(presetId);
    if (presetId === "__custom__") {
      setMCustomModelId("");
      setMName(mType === "CHAT" ? "Custom Model" : "Custom Embedder");
    } else {
      const preset = currentPresets.find((p) => p.id === presetId);
      if (preset) {
        setMCustomModelId("");
        setMName(preset.name);
        setMContextWindow(preset.contextWindow);
      } else if (discoveredModels.includes(presetId)) {
        // Selected an installed model from the provider
        setMCustomModelId("");
        // Clean up friendly name, e.g. "llama3:latest" -> "Llama3 (Local)"
        const cleanName = presetId.replace(/:latest$/, "").toUpperCase();
        setMName(`${cleanName} (${currentModalProvider?.provider_type === "OLLAMA" ? "Local" : "Provider"})`);
        setMContextWindow(mType === "CHAT" ? 128000 : 8192);
      }
    }
  };

  const handleCreateModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mProviderId) {
      setMError("Please select an AI Provider first.");
      return;
    }

    const finalModelId = mSelectedPreset === "__custom__" ? mCustomModelId.trim() : mSelectedPreset;
    if (!finalModelId) {
      setMError("Please specify a Model ID or select a preset.");
      return;
    }

    setMSubmitting(true);
    setMError(null);

    try {
      await apiRequest("/models", {
        method: "POST",
        body: JSON.stringify({
          provider_id: mProviderId,
          name: mName.trim() || finalModelId,
          model_id: finalModelId,
          model_type: mType,
          context_window: Number(mContextWindow) || (mType === "CHAT" ? 128000 : 8192),
          is_default: mIsDefault,
        }),
      });
      setShowModelModal(false);
      await loadAllData();
      setActiveTab(mType === "CHAT" ? "chat" : "embedding");
    } catch (err: any) {
      setMError(err.message || "Failed to create model");
    } finally {
      setMSubmitting(false);
    }
  };

  const handleSetDefaultModel = async (id: string, name: string) => {
    try {
      await apiRequest(`/models/${id}/set-default`, { method: "POST" });
      await loadAllData();
    } catch (err: any) {
      alert(err.message || `Failed to set ${name} as default.`);
    }
  };

  const handleDeleteModel = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete the model "${name}"?`)) {
      return;
    }
    try {
      await apiRequest(`/models/${id}`, { method: "DELETE" });
      await loadAllData();
    } catch (err: any) {
      alert(err.message || "Failed to delete model");
    }
  };

  const chatModels = models.filter((m) => m.model_type.toUpperCase() === "CHAT");
  const embeddingModels = models.filter((m) => m.model_type.toUpperCase() === "EMBEDDING");

  return (
    <div className="space-y-6 max-w-6xl pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="h-6 w-6 text-aura-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">AI Providers & Models</h1>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Configure multi-provider LLM gateways (OpenAI, Anthropic, Ollama, Custom endpoints, Mock) and register Chat & Embedding models.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={openAddProviderModal}
            className="flex items-center space-x-2 rounded-lg border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 hover:text-white transition shadow-sm"
          >
            <Server className="h-4 w-4 text-purple-400" />
            <span>+ Add Provider</span>
          </button>

          <button
            onClick={() => openAddModelModal()}
            disabled={providers.length === 0}
            className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white shadow-md hover:bg-aura-500 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <Plus className="h-4 w-4" />
            <span>Define AI Model</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm">
        <button
          onClick={() => setActiveTab("chat")}
          className={`pb-3 font-semibold flex items-center space-x-2 border-b-2 transition ${
            activeTab === "chat"
              ? "border-aura-500 text-aura-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Bot className="h-4 w-4" />
          <span>Chat Models</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
            {chatModels.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("embedding")}
          className={`pb-3 font-semibold flex items-center space-x-2 border-b-2 transition ${
            activeTab === "embedding"
              ? "border-aura-500 text-aura-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Embedding Models</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
            {embeddingModels.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("providers")}
          className={`pb-3 font-semibold flex items-center space-x-2 border-b-2 transition ${
            activeTab === "providers"
              ? "border-aura-500 text-aura-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Server className="h-4 w-4" />
          <span>Model Providers</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
            {providers.length}
          </span>
        </button>
      </div>

      {/* TAB 1: Chat Models */}
      {activeTab === "chat" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Active conversational and reasoning models powering Aura AI agents. The default model is automatically selected for interactive chat.
            </p>
            <button
              onClick={() => openAddModelModal("CHAT")}
              disabled={providers.length === 0}
              className="flex items-center space-x-1.5 text-xs text-aura-400 hover:text-aura-300 font-medium"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Chat Model</span>
            </button>
          </div>

          {loading ? (
            <div className="py-12 text-center text-slate-400">Loading models...</div>
          ) : chatModels.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center space-y-3">
              <Bot className="h-10 w-10 text-slate-600 mx-auto" />
              <h3 className="text-sm font-semibold text-white">No Chat Models Defined</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                {providers.length === 0
                  ? "First, connect an AI Provider (e.g. OpenAI, Anthropic, or Ollama) to start defining models."
                  : "Register a chat model from your connected providers to power agent conversations."}
              </p>
              {providers.length === 0 ? (
                <button
                  onClick={openAddProviderModal}
                  className="mt-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white hover:bg-aura-500 transition"
                >
                  + Add AI Provider
                </button>
              ) : (
                <button
                  onClick={() => openAddModelModal("CHAT")}
                  className="mt-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white hover:bg-aura-500 transition"
                >
                  + Define Chat Model
                </button>
              )}
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm">
              <table className="min-w-full divide-y divide-slate-800 text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 font-semibold text-slate-400">
                  <tr>
                    <th className="px-5 py-3.5">Model Name</th>
                    <th className="px-5 py-3.5">Model ID / Tag</th>
                    <th className="px-5 py-3.5">Provider</th>
                    <th className="px-5 py-3.5">Context Window</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {chatModels.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-5 py-3.5 font-medium text-white">
                        <div className="flex items-center space-x-2">
                          <Bot className="h-4 w-4 text-purple-400 shrink-0" />
                          <span>{m.name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <code className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-aura-300 border border-slate-700">
                          {m.model_id}
                        </code>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center space-x-1.5">
                          <span className="font-medium text-slate-300">{m.provider_name}</span>
                          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] font-mono text-slate-400 uppercase border border-slate-700">
                            {m.provider_type}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-slate-400">
                        {m.context_window ? `${(m.context_window / 1000).toFixed(0)}K tokens` : "128K"}
                      </td>
                      <td className="px-5 py-3.5">
                        {m.is_default ? (
                          <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-400">
                            <Star className="h-3 w-3 fill-emerald-400 text-emerald-400" />
                            <span>Default Chat</span>
                          </span>
                        ) : (
                          <button
                            onClick={() => handleSetDefaultModel(m.id, m.name)}
                            className="text-[11px] text-slate-400 hover:text-aura-400 transition underline underline-offset-2"
                          >
                            Set as default
                          </button>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={() => handleDeleteModel(m.id, m.name)}
                          className="rounded p-1 text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition"
                          title="Delete Model"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Embedding Models */}
      {activeTab === "embedding" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Embedding models generate dense vector representations for documents ingested into Brains and RAG semantic search.
            </p>
            <button
              onClick={() => openAddModelModal("EMBEDDING")}
              disabled={providers.length === 0}
              className="flex items-center space-x-1.5 text-xs text-aura-400 hover:text-aura-300 font-medium"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Embedding Model</span>
            </button>
          </div>

          {loading ? (
            <div className="py-12 text-center text-slate-400">Loading models...</div>
          ) : embeddingModels.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center space-y-3">
              <Layers className="h-10 w-10 text-slate-600 mx-auto" />
              <h3 className="text-sm font-semibold text-white">No Embedding Models Defined</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Define an embedding model (e.g. OpenAI text-embedding-3-small, Ollama nomic-embed-text) to index knowledge documents in Brains.
              </p>
              <button
                onClick={() => openAddModelModal("EMBEDDING")}
                disabled={providers.length === 0}
                className="mt-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white hover:bg-aura-500 transition disabled:opacity-50"
              >
                + Define Embedding Model
              </button>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm">
              <table className="min-w-full divide-y divide-slate-800 text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 font-semibold text-slate-400">
                  <tr>
                    <th className="px-5 py-3.5">Model Name</th>
                    <th className="px-5 py-3.5">Model ID / Tag</th>
                    <th className="px-5 py-3.5">Provider</th>
                    <th className="px-5 py-3.5">Vector Dimensions / Context</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {embeddingModels.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-5 py-3.5 font-medium text-white">
                        <div className="flex items-center space-x-2">
                          <Layers className="h-4 w-4 text-emerald-400 shrink-0" />
                          <span>{m.name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <code className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-aura-300 border border-slate-700">
                          {m.model_id}
                        </code>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center space-x-1.5">
                          <span className="font-medium text-slate-300">{m.provider_name}</span>
                          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] font-mono text-slate-400 uppercase border border-slate-700">
                            {m.provider_type}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-slate-400">
                        {m.context_window ? `${m.context_window} tokens` : "8192 tokens"}
                      </td>
                      <td className="px-5 py-3.5">
                        {m.is_default ? (
                          <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-400">
                            <Star className="h-3 w-3 fill-emerald-400 text-emerald-400" />
                            <span>Default Embedding</span>
                          </span>
                        ) : (
                          <button
                            onClick={() => handleSetDefaultModel(m.id, m.name)}
                            className="text-[11px] text-slate-400 hover:text-aura-400 transition underline underline-offset-2"
                          >
                            Set as default
                          </button>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={() => handleDeleteModel(m.id, m.name)}
                          className="rounded p-1 text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition"
                          title="Delete Model"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Model Providers */}
      {activeTab === "providers" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Configured AI engines and gateway endpoints. Each provider manages credentials and connects to one or more models.
            </p>
            <button
              onClick={openAddProviderModal}
              className="flex items-center space-x-1.5 text-xs text-aura-400 hover:text-aura-300 font-medium"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Provider</span>
            </button>
          </div>

          {loading ? (
            <div className="py-12 text-center text-slate-400">Loading providers...</div>
          ) : providers.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center space-y-3">
              <Server className="h-10 w-10 text-slate-600 mx-auto" />
              <h3 className="text-sm font-semibold text-white">No AI Providers Added</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Connect your first model provider (OpenAI, Anthropic Claude, Local Ollama, or Custom Gateway) to get started.
              </p>
              <button
                onClick={openAddProviderModal}
                className="mt-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white hover:bg-aura-500 transition"
              >
                + Add AI Provider
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {providers.map((p) => {
                const provModels = models.filter((m) => m.provider_id === p.id);
                const test = testResult[p.id];
                return (
                  <div
                    key={p.id}
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm space-y-4 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="rounded-lg bg-slate-800 p-2.5 text-purple-400 border border-slate-700">
                            <Cpu className="h-5 w-5" />
                          </div>
                          <div>
                            <h3 className="font-bold text-base text-white">{p.name}</h3>
                            <div className="flex items-center space-x-2 mt-0.5">
                              <span className="font-mono text-[10px] text-slate-300 uppercase rounded bg-slate-800 px-2 py-0.5 border border-slate-700">
                                {p.provider_type}
                              </span>
                              <span className="text-[11px] text-slate-400">
                                {provModels.length} {provModels.length === 1 ? "model" : "models"} configured
                              </span>
                            </div>
                          </div>
                        </div>

                        <button
                          onClick={() => handleDeleteProvider(p.id, p.name)}
                          className="rounded p-1 text-slate-500 hover:bg-rose-500/10 hover:text-rose-400 transition"
                          title="Delete Provider"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>

                      <div className="mt-4 rounded-lg bg-slate-950/60 border border-slate-800/80 p-3 space-y-1.5 text-xs">
                        <div className="flex items-center justify-between text-slate-400">
                          <span>Base URL:</span>
                          <span className="font-mono text-slate-200 truncate max-w-[260px]">
                            {p.base_url || "Default official API"}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-slate-400">
                          <span>State:</span>
                          <span className="flex items-center space-x-1 text-emerald-400 font-medium">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            <span>Active</span>
                          </span>
                        </div>
                      </div>

                      {/* Test feedback */}
                      {test && (
                        <div
                          className={`mt-3 rounded-lg border p-3 text-xs ${
                            test.status === "testing"
                              ? "border-slate-700 bg-slate-800 text-slate-300"
                              : test.status === "success"
                              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                              : "border-rose-500/30 bg-rose-500/10 text-rose-300"
                          }`}
                        >
                          <div className="font-medium flex items-center space-x-1.5">
                            {test.status === "testing" && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
                            {test.status === "success" && <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />}
                            {test.status === "error" && <AlertCircle className="h-3.5 w-3.5 text-rose-400" />}
                            <span>{test.message}</span>
                          </div>
                          {test.sample && (
                            <div className="mt-1 text-[11px] text-slate-400 italic font-mono bg-slate-900/60 p-1.5 rounded border border-slate-800">
                              Response: &quot;{test.sample}&quot;
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
                      <button
                        onClick={() => openAddModelModal()}
                        className="text-xs text-aura-400 hover:text-aura-300 font-medium flex items-center space-x-1"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        <span>Add Model to Provider</span>
                      </button>

                      <button
                        onClick={() => handleTestProvider(p.id)}
                        disabled={test?.status === "testing"}
                        className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
                      >
                        <Play className="h-3 w-3 text-aura-400" />
                        <span>{test?.status === "testing" ? "Testing..." : "Test Connection"}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* MODAL 1: ADD AI PROVIDER (Dynamic Settings per Provider Type) */}
      {showProviderModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Server className="h-5 w-5 text-aura-400" />
                <h3 className="text-base font-bold text-white">Add AI Model Provider</h3>
              </div>
              <button
                onClick={() => setShowProviderModal(false)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                ✕
              </button>
            </div>

            {pError && (
              <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{pError}</span>
              </div>
            )}

            <form onSubmit={handleCreateProvider} className="space-y-4">
              {/* Provider Type Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Provider Engine Type
                </label>
                <select
                  value={pType}
                  onChange={(e) => handleProviderTypeChange(e.target.value as ProviderType)}
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white focus:border-aura-500 focus:outline-none"
                >
                  <option value="OPENAI">OpenAI (Official Cloud API)</option>
                  <option value="ANTHROPIC">Anthropic (Claude 3.5 Sonnet / Haiku / Opus)</option>
                  <option value="OLLAMA">Ollama (Local Open Weights: Llama 3.1, DeepSeek, Mistral)</option>
                  <option value="CUSTOM_OPENAI">Custom OpenAI Compatible (vLLM, Groq, OpenRouter, Together AI)</option>
                  <option value="MOCK">Mock Provider (Offline Testing & Development)</option>
                </select>
              </div>

              {/* Dynamic Information Banner based on Provider */}
              <div className="rounded-lg bg-slate-800/60 border border-slate-700/60 p-3 text-xs text-slate-300 space-y-1">
                <div className="flex items-center space-x-1.5 text-aura-400 font-semibold">
                  <Info className="h-3.5 w-3.5 shrink-0" />
                  <span>
                    {pType === "OPENAI" && "Configuring OpenAI"}
                    {pType === "ANTHROPIC" && "Configuring Anthropic Claude"}
                    {pType === "OLLAMA" && "Configuring Local Ollama"}
                    {pType === "CUSTOM_OPENAI" && "Configuring Custom OpenAI Gateway"}
                    {pType === "MOCK" && "Offline Mock Mode"}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {pType === "OPENAI" &&
                    "Direct connection to OpenAI API for GPT-4o, GPT-4o Mini, and text-embedding-3 models. Requires an API key."}
                  {pType === "ANTHROPIC" &&
                    "Connects directly to Anthropic Claude 3.5. Requires an Anthropic API key starting with 'sk-ant-'."}
                  {pType === "OLLAMA" &&
                    "Connects to an Ollama server on localhost or your private network. No API key needed by default. Supports any locally pulled model."}
                  {pType === "CUSTOM_OPENAI" &&
                    "Connect to any self-hosted vLLM, Groq Cloud, OpenRouter, or Together AI endpoint adhering to the OpenAI specification."}
                  {pType === "MOCK" &&
                    "Generates fast, deterministic mock answers without external network calls. Perfect for offline UI testing and CI pipelines."}
                </p>
              </div>

              {/* Provider Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Provider Friendly Name
                </label>
                <input
                  type="text"
                  required
                  value={pName}
                  onChange={(e) => setPName(e.target.value)}
                  placeholder="e.g. Production OpenAI Gateway"
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white focus:border-aura-500 focus:outline-none"
                />
              </div>

              {/* Base URL (Shown for all except MOCK) */}
              {pType !== "MOCK" && (
                <div>
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Base Endpoint URL {pType === "OLLAMA" || pType === "CUSTOM_OPENAI" ? "(Required)" : "(Optional)"}
                    </label>
                    <span className="text-[10px] text-slate-400">
                      {pType === "OLLAMA" ? "e.g. http://localhost:11434" : "e.g. https://api.openai.com/v1"}
                    </span>
                  </div>
                  <input
                    type="text"
                    required={pType === "OLLAMA" || pType === "CUSTOM_OPENAI"}
                    value={pBaseUrl}
                    onChange={(e) => setPBaseUrl(e.target.value)}
                    placeholder={
                      pType === "OLLAMA"
                        ? "http://localhost:11434"
                        : pType === "ANTHROPIC"
                        ? "https://api.anthropic.com"
                        : pType === "CUSTOM_OPENAI"
                        ? "https://api.groq.com/openai/v1"
                        : "https://api.openai.com/v1"
                    }
                    className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white focus:border-aura-500 focus:outline-none"
                  />
                  {pType === "OLLAMA" && (
                    <p className="mt-1 text-[11px] text-amber-400/90">
                      💡 Ensure Ollama is running and accessible with CORS enabled (e.g. <code className="bg-slate-800 px-1 py-0.5 rounded">OLLAMA_ORIGINS=&quot;*&quot; ollama serve</code>).
                    </p>
                  )}
                </div>
              )}

              {/* API Key (Required for OPENAI/ANTHROPIC, Optional for CUSTOM, Not needed for OLLAMA/MOCK) */}
              {pType !== "MOCK" && pType !== "OLLAMA" && (
                <div>
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      API Key {pType === "CUSTOM_OPENAI" ? "(Optional)" : "(Required)"}
                    </label>
                    <button
                      type="button"
                      onClick={() => setPShowApiKey(!pShowApiKey)}
                      className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center space-x-1"
                    >
                      {pShowApiKey ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                      <span>{pShowApiKey ? "Hide" : "Show"}</span>
                    </button>
                  </div>
                  <input
                    type={pShowApiKey ? "text" : "password"}
                    required={pType === "OPENAI" || pType === "ANTHROPIC"}
                    value={pApiKey}
                    onChange={(e) => setPApiKey(e.target.value)}
                    placeholder={
                      pType === "OPENAI"
                        ? "sk-proj-..."
                        : pType === "ANTHROPIC"
                        ? "sk-ant-api03-..."
                        : "Bearer token or API Key"
                    }
                    className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white focus:border-aura-500 focus:outline-none"
                  />
                  <p className="mt-1 text-[10px] text-slate-400">
                    🔒 Keys are securely encrypted with AES-Fernet encryption at rest before being saved.
                  </p>
                </div>
              )}

              {pType === "OLLAMA" && (
                <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-2.5 text-xs text-emerald-300">
                  ✓ Ollama runs locally on your machine without requiring an API key.
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowProviderModal(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={pSubmitting}
                  className="rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white hover:bg-aura-500 disabled:opacity-50 transition shadow-sm"
                >
                  {pSubmitting ? "Saving..." : "Save Provider"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: DEFINE AI MODEL (Chat Models & Embedding Models) */}
      {showModelModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-5 w-5 text-aura-400" />
                <h3 className="text-base font-bold text-white">Define AI Model</h3>
              </div>
              <button
                onClick={() => setShowModelModal(false)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                ✕
              </button>
            </div>

            {mError && (
              <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{mError}</span>
              </div>
            )}

            <form onSubmit={handleCreateModel} className="space-y-4">
              {/* Select Connected Provider */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Target AI Provider
                </label>
                <select
                  value={mProviderId}
                  onChange={(e) => handleProviderSelectChange(e.target.value)}
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white focus:border-aura-500 focus:outline-none"
                >
                  {providers.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.provider_type})
                    </option>
                  ))}
                </select>
              </div>

              {/* Model Type Selector (CHAT vs EMBEDDING) */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Model Type & Role
                </label>
                <div className="grid grid-cols-2 gap-3 mt-1.5">
                  <button
                    type="button"
                    onClick={() => handleModelTypeChange("CHAT")}
                    className={`rounded-lg border p-3 text-left transition flex items-start space-x-2.5 ${
                      mType === "CHAT"
                        ? "border-aura-500 bg-aura-500/10 text-white"
                        : "border-slate-800 bg-slate-800/50 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <Bot className={`h-4 w-4 mt-0.5 ${mType === "CHAT" ? "text-aura-400" : "text-slate-500"}`} />
                    <div>
                      <div className="text-xs font-bold text-slate-200">Chat Model</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">Interactive agents & reasoning</div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleModelTypeChange("EMBEDDING")}
                    className={`rounded-lg border p-3 text-left transition flex items-start space-x-2.5 ${
                      mType === "EMBEDDING"
                        ? "border-aura-500 bg-aura-500/10 text-white"
                        : "border-slate-800 bg-slate-800/50 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <Layers className={`h-4 w-4 mt-0.5 ${mType === "EMBEDDING" ? "text-emerald-400" : "text-slate-500"}`} />
                    <div>
                      <div className="text-xs font-bold text-slate-200">Embedding Model</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">Brain documents & vector RAG</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Anthropic notice if embedding selected */}
              {currentModalProvider?.provider_type === "ANTHROPIC" && mType === "EMBEDDING" && (
                <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-2.5 text-xs text-amber-300">
                  ⚠️ Anthropic does not provide native vector embedding endpoints. We recommend using an OpenAI, Ollama, or Custom provider for embeddings.
                </div>
              )}

              {/* Model Presets List from Selected Provider */}
              <div>
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Available Models for {currentModalProvider?.provider_type}
                  </label>
                  {mProviderId && (
                    <button
                      type="button"
                      onClick={() => fetchDiscoveredModels(mProviderId)}
                      disabled={loadingDiscovered}
                      className="text-[11px] text-aura-400 hover:text-aura-300 flex items-center space-x-1"
                    >
                      <RefreshCw className={`h-3 w-3 ${loadingDiscovered ? "animate-spin" : ""}`} />
                      <span>{loadingDiscovered ? "Scanning..." : "Scan Provider"}</span>
                    </button>
                  )}
                </div>
                <select
                  value={mSelectedPreset}
                  onChange={(e) => handlePresetSelectChange(e.target.value)}
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white focus:border-aura-500 focus:outline-none"
                >
                  {discoveredModels.length > 0 && (
                    <optgroup label={`📥 Detected on ${currentModalProvider?.name || "Provider"} (${discoveredModels.length})`}>
                      {discoveredModels.map((dm) => (
                        <option key={dm} value={dm}>
                          ✓ {dm} (Installed)
                        </option>
                      ))}
                    </optgroup>
                  )}
                  <optgroup label="⭐ Curated Recommended Presets">
                    {currentPresets.map((preset) => (
                      <option key={preset.id} value={preset.id}>
                        {preset.name} ({preset.id})
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="⚙️ Custom Tag">
                    <option value="__custom__">⚙️ Enter Custom Model ID / Custom Tag...</option>
                  </optgroup>
                </select>
                <p className="mt-1 text-[11px] text-slate-400">
                  {discoveredModels.length > 0
                    ? `Found ${discoveredModels.length} installed model(s) on your provider. You can select one or choose a preset.`
                    : "Select from recommended presets or choose Custom Tag to enter any model tag from your local Ollama or inference cluster."}
                </p>
              </div>

              {/* Custom Model ID input if __custom__ selected */}
              {mSelectedPreset === "__custom__" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Custom Model ID / Tag
                  </label>
                  <input
                    type="text"
                    required
                    value={mCustomModelId}
                    onChange={(e) => setMCustomModelId(e.target.value)}
                    placeholder={
                      currentModalProvider?.provider_type === "OLLAMA"
                        ? "e.g. llama3.1:70b-instruct-q4_K_M"
                        : "e.g. meta-llama/Llama-3-70b-chat-hf"
                    }
                    className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white focus:border-aura-500 focus:outline-none"
                  />
                </div>
              )}

              {/* Display Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Model Display Name
                </label>
                <input
                  type="text"
                  required
                  value={mName}
                  onChange={(e) => setMName(e.target.value)}
                  placeholder="e.g. Production GPT-4o"
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white focus:border-aura-500 focus:outline-none"
                />
              </div>

              {/* Context Window */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Context Window (Tokens)
                </label>
                <input
                  type="number"
                  required
                  value={mContextWindow}
                  onChange={(e) => setMContextWindow(Number(e.target.value))}
                  className="mt-1.5 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white focus:border-aura-500 focus:outline-none"
                />
              </div>

              {/* Default Checkbox */}
              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="is_default_checkbox"
                  checked={mIsDefault}
                  onChange={(e) => setMIsDefault(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-aura-600 focus:ring-aura-500"
                />
                <label htmlFor="is_default_checkbox" className="text-xs text-slate-300 cursor-pointer">
                  Set as default <span className="font-semibold text-white">{mType.toLowerCase()}</span> model for the organization
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModelModal(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={mSubmitting}
                  className="rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white hover:bg-aura-500 disabled:opacity-50 transition shadow-sm"
                >
                  {mSubmitting ? "Registering..." : "Register Model"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
