"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { DataSource, DataSourceTable, DocumentItem, RoleItem } from "@/types";
import Link from "next/link";
import {
  BrainCircuit,
  ArrowLeft,
  Database,
  FileText,
  Shield,
  Plus,
  Trash2,
  CheckCircle,
  Clock,
  AlertCircle,
  Eye,
  RefreshCw,
  Table,
  Upload,
  Layers,
  MessageSquare,
  Unlink
} from "lucide-react";

interface BrainDetail {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  sources: DataSource[];
  documents: DocumentItem[];
  roles: Array<{ id: string; name: string; description?: string; is_system: boolean }>;
}

export default function BrainViewPage() {
  const params = useParams();
  const router = useRouter();
  const brainId = params.id as string;

  const [brain, setBrain] = useState<BrainDetail | null>(null);
  const [allRoles, setAllRoles] = useState<RoleItem[]>([]);
  const [allOrgSources, setAllOrgSources] = useState<DataSource[]>([]);
  const [allOrgDocs, setAllOrgDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"sources" | "documents" | "roles">("sources");

  // Schema Inspection modal
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);
  const [schemaTables, setSchemaTables] = useState<DataSourceTable[]>([]);
  const [testStatus, setTestStatus] = useState<string | null>(null);

  // Document Inspection modal
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  // Add Source Modal
  const [showAddSourceModal, setShowAddSourceModal] = useState(false);
  const [sourceName, setSourceName] = useState("");
  const [sourceType, setSourceType] = useState("POSTGRES");
  const [connectionUri, setConnectionUri] = useState("");
  const [sourceDescription, setSourceDescription] = useState("");

  // Attach Existing Modals
  const [showAttachSourcesModal, setShowAttachSourcesModal] = useState(false);
  const [sourcesToAttach, setSourcesToAttach] = useState<string[]>([]);

  const [showAttachDocsModal, setShowAttachDocsModal] = useState(false);
  const [docsToAttach, setDocsToAttach] = useState<string[]>([]);

  // File Upload State
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Role Matrix State
  const [assignedRoleIds, setAssignedRoleIds] = useState<string[]>([]);

  useEffect(() => {
    loadBrainData();
  }, [brainId]);

  const loadBrainData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [brainData, rolesData, allSources, allDocs] = await Promise.all([
        apiRequest<BrainDetail>(`/brains/${brainId}`),
        apiRequest<RoleItem[]>("/rbac/roles"),
        apiRequest<DataSource[]>("/sources"),
        apiRequest<DocumentItem[]>("/documents"),
      ]);
      setBrain(brainData);
      setAllRoles(rolesData);
      setAllOrgSources(allSources);
      setAllOrgDocs(allDocs);
      setAssignedRoleIds(brainData.roles.map((r) => r.id));
    } catch (err: any) {
      console.error(err);
      if (showLoading) setStatusMsg(`Error loading Brain: ${err.message}`);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  // Auto-poll when any document is still processing
  useEffect(() => {
    const hasProcessing = brain?.documents.some((d) => d.status === "PROCESSING");
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      loadBrainData(false);
    }, 2500);

    return () => clearInterval(interval);
  }, [brain?.documents, brainId]);

  const handleRetryDoc = async (docId: string) => {
    try {
      await apiRequest(`/documents/${docId}/retry`, { method: "POST" });
      setStatusMsg("Document re-indexing queued.");
      loadBrainData(false);
    } catch (err: any) {
      alert(err.message || "Failed to retry indexing");
    }
  };

  // Connect new Data Source directly to this Brain
  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/sources", {
        method: "POST",
        body: JSON.stringify({
          name: sourceName,
          type: sourceType,
          connection_uri: connectionUri,
          description: sourceDescription,
          is_read_only: true,
          brain_id: brainId,
        }),
      });
      setShowAddSourceModal(false);
      setSourceName("");
      setConnectionUri("");
      setSourceDescription("");
      setStatusMsg(`Data Source '${sourceName}' connected to Brain.`);
      loadBrainData();
    } catch (err: any) {
      alert(err.message || "Failed to add data source");
    } finally {
      setSubmitting(false);
    }
  };

  // Upload Document directly into this Brain
  const handleUploadDocument = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("brain_id", brainId);

    try {
      await apiRequest("/documents/upload", {
        method: "POST",
        body: formData,
      });
      setStatusMsg(`Document '${file.name}' uploaded and queued for indexing in this Brain.`);
      loadBrainData();
    } catch (err: any) {
      alert(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  // Attach existing unassigned resources
  const handleAttachSources = async () => {
    if (sourcesToAttach.length === 0) return;
    setSubmitting(true);
    try {
      await apiRequest(`/brains/${brainId}/connect-resources`, {
        method: "POST",
        body: JSON.stringify({ source_ids: sourcesToAttach }),
      });
      setShowAttachSourcesModal(false);
      setSourcesToAttach([]);
      setStatusMsg("Data sources attached to Brain.");
      loadBrainData();
    } catch (err: any) {
      alert(err.message || "Failed to attach sources");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAttachDocs = async () => {
    if (docsToAttach.length === 0) return;
    setSubmitting(true);
    try {
      await apiRequest(`/brains/${brainId}/connect-resources`, {
        method: "POST",
        body: JSON.stringify({ document_ids: docsToAttach }),
      });
      setShowAttachDocsModal(false);
      setDocsToAttach([]);
      setStatusMsg("Documents attached to Brain.");
      loadBrainData();
    } catch (err: any) {
      alert(err.message || "Failed to attach documents");
    } finally {
      setSubmitting(false);
    }
  };

  // Detach single resources
  const handleDetachSource = async (sourceId: string, sourceName: string) => {
    if (!confirm(`Detach Data Source '${sourceName}' from this Brain?`)) return;
    try {
      await apiRequest(`/brains/${brainId}/sources/${sourceId}/detach`, { method: "POST" });
      setStatusMsg(`Data source '${sourceName}' detached.`);
      loadBrainData();
    } catch (err: any) {
      alert(err.message || "Failed to detach");
    }
  };

  const handleDetachDoc = async (docId: string, docTitle: string) => {
    if (!confirm(`Detach Document '${docTitle}' from this Brain?`)) return;
    try {
      await apiRequest(`/brains/${brainId}/documents/${docId}/detach`, { method: "POST" });
      setStatusMsg(`Document '${docTitle}' detached.`);
      loadBrainData();
    } catch (err: any) {
      alert(err.message || "Failed to detach");
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm("Permanently delete this document from the platform?")) return;
    try {
      await apiRequest(`/documents/${docId}`, { method: "DELETE" });
      setStatusMsg("Document deleted.");
      loadBrainData();
      if (selectedDoc?.id === docId) setSelectedDoc(null);
    } catch (err: any) {
      alert(err.message || "Failed to delete");
    }
  };

  // Inspect source schema
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
      setTestStatus("Schema sync scheduled. Refresh in a few seconds.");
      setTimeout(() => {
        if (selectedSource) viewSchema(selectedSource);
      }, 3000);
    } catch (err: any) {
      setTestStatus(`Sync error: ${err.message}`);
    }
  };

  // Inspect doc details
  const inspectDoc = async (id: string) => {
    try {
      const data = await apiRequest(`/documents/${id}`);
      setSelectedDoc(data);
    } catch (e) {
      console.error(e);
    }
  };

  // Save Role Assignments
  const handleSaveRoles = async () => {
    setSubmitting(true);
    try {
      await apiRequest(`/brains/${brainId}/assign-roles`, {
        method: "POST",
        body: JSON.stringify({ role_ids: assignedRoleIds }),
      });
      setStatusMsg("Role permissions updated successfully.");
      loadBrainData();
    } catch (err: any) {
      setStatusMsg(`Failed to save roles: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="py-20 text-center text-slate-400">Loading Brain details...</div>;
  }

  if (!brain) {
    return (
      <div className="py-20 text-center space-y-3">
        <h2 className="text-lg font-bold text-white">Brain Not Found</h2>
        <p className="text-sm text-slate-400">This Brain may have been removed or you do not have permission.</p>
        <Link
          href="/console/brains"
          className="inline-flex items-center space-x-2 text-aura-400 hover:text-aura-300 text-sm font-medium"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Brains</span>
        </Link>
      </div>
    );
  }

  // Available unassigned sources / docs
  const unassignedSources = allOrgSources.filter((s) => s.brain_id !== brainId);
  const unassignedDocs = allOrgDocs.filter((d) => d.brain_id !== brainId);

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <Link
            href="/console/brains"
            className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>All Brains</span>
          </Link>
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-aura-600/15 border border-aura-500/25 text-aura-400 shadow-sm">
              <BrainCircuit className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">{brain.name}</h1>
              <p className="text-xs text-slate-400 mt-0.5">{brain.description || "Isolated Knowledge & Data Brain"}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Link
            href={`/console/brains/${brain.id}/resources`}
            className="flex items-center space-x-1.5 rounded-lg bg-aura-600 hover:bg-aura-500 px-3.5 py-2 text-xs font-semibold text-white shadow-md shadow-aura-600/20 transition"
          >
            <Layers className="h-4 w-4" />
            <span>Connect Resources</span>
          </Link>
          <Link
            href="/chat"
            className="flex items-center space-x-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3.5 py-2 text-xs font-semibold text-slate-200 transition"
          >
            <MessageSquare className="h-4 w-4 text-aura-400" />
            <span>Chat with this Brain</span>
          </Link>
        </div>
      </div>

      {/* Status banner */}
      {statusMsg && (
        <div className="rounded-lg bg-slate-900 border border-slate-800 p-3 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2 text-slate-200">
            <CheckCircle className="h-4 w-4 text-aura-400" />
            <span>{statusMsg}</span>
          </div>
          <button onClick={() => setStatusMsg(null)} className="text-[11px] text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="border-b border-slate-800 flex items-center space-x-6">
        <button
          onClick={() => setActiveTab("sources")}
          className={`pb-3 text-sm font-semibold flex items-center space-x-2 transition border-b-2 ${
            activeTab === "sources"
              ? "border-aura-500 text-aura-300"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Database className="h-4 w-4" />
          <span>Data Sources</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300 font-mono">
            {brain.sources.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("documents")}
          className={`pb-3 text-sm font-semibold flex items-center space-x-2 transition border-b-2 ${
            activeTab === "documents"
              ? "border-aura-500 text-aura-300"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="h-4 w-4" />
          <span>Documents (RAG)</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300 font-mono">
            {brain.documents.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("roles")}
          className={`pb-3 text-sm font-semibold flex items-center space-x-2 transition border-b-2 ${
            activeTab === "roles"
              ? "border-aura-500 text-aura-300"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Shield className="h-4 w-4" />
          <span>Role Governance & Access</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300 font-mono">
            {brain.roles.length}
          </span>
        </button>
      </div>

      {/* ============================================================== */}
      {/* TAB 1: DATA SOURCES */}
      {/* ============================================================== */}
      {activeTab === "sources" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-900/40 p-4 rounded-xl border border-slate-800">
            <div>
              <h2 className="text-sm font-bold text-white">Connected Databases & Warehouses</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Databases connected to this Brain can be queried by users whose roles have Brain access.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {unassignedSources.length > 0 && (
                <button
                  onClick={() => setShowAttachSourcesModal(true)}
                  className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-750 px-3 py-1.5 text-xs font-semibold text-slate-200 transition"
                >
                  <Layers className="h-3.5 w-3.5 text-slate-400" />
                  <span>Attach Existing ({unassignedSources.length})</span>
                </button>
              )}
              <button
                onClick={() => setShowAddSourceModal(true)}
                className="flex items-center space-x-1.5 rounded-lg bg-aura-600 hover:bg-aura-500 px-3 py-1.5 text-xs font-semibold text-white shadow transition"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Connect Database</span>
              </button>
            </div>
          </div>

          {brain.sources.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-800 p-10 text-center">
              <Database className="h-10 w-10 text-slate-600 mx-auto mb-2" />
              <h3 className="text-sm font-semibold text-slate-200">No Data Sources in this Brain</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Connect a PostgreSQL, MySQL, or SQLite database to let the agent query data within this Brain.
              </p>
              <button
                onClick={() => setShowAddSourceModal(true)}
                className="mt-4 inline-flex items-center space-x-1.5 rounded-lg bg-aura-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 transition"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Connect First Database</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {brain.sources.map((s) => (
                <div
                  key={s.id}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex flex-col justify-between hover:border-slate-700 transition"
                >
                  <div>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2.5">
                        <Database className="h-4 w-4 text-blue-400" />
                        <div>
                          <h3 className="font-semibold text-sm text-white">{s.name}</h3>
                          <span className="font-mono text-[10px] text-slate-400">{s.type}</span>
                        </div>
                      </div>
                      <span className="rounded bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                        Read-Only
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                      {s.description || "No description provided."}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => viewSchema(s)}
                        className="flex items-center space-x-1 rounded bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-[11px] font-medium text-slate-200 transition"
                      >
                        <Eye className="h-3 w-3 text-aura-400" />
                        <span>Inspect Schema</span>
                      </button>
                      <button
                        onClick={() => testConnection(s.id)}
                        className="rounded bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-[11px] font-medium text-slate-300 transition"
                      >
                        Test
                      </button>
                    </div>

                    <button
                      onClick={() => handleDetachSource(s.id, s.name)}
                      className="text-slate-500 hover:text-amber-400 p-1 transition flex items-center gap-1 text-[11px]"
                      title="Detach from this Brain"
                    >
                      <Unlink className="h-3 w-3" />
                      <span>Detach</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Schema Viewer Section */}
          {selectedSource && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 mt-6">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <Table className="h-4 w-4 text-aura-400" />
                  <h3 className="font-semibold text-sm text-white">
                    Discovered Schema: {selectedSource.name}
                  </h3>
                  <span className="text-xs text-slate-400">({schemaTables.length} tables)</span>
                </div>
                <div className="flex items-center space-x-2">
                  {testStatus && <span className="text-xs text-aura-300 font-mono">{testStatus}</span>}
                  <button
                    onClick={() => syncSchema(selectedSource.id)}
                    className="flex items-center space-x-1 rounded bg-slate-800 hover:bg-slate-700 px-2.5 py-1 text-xs text-slate-300 transition"
                  >
                    <RefreshCw className="h-3 w-3" />
                    <span>Sync Schema</span>
                  </button>
                  <button
                    onClick={() => setSelectedSource(null)}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    Close
                  </button>
                </div>
              </div>

              {schemaTables.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-500">
                  No tables discovered yet. Click &apos;Sync Schema&apos; to trigger automatic discovery.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {schemaTables.map((tbl) => (
                    <div key={tbl.id} className="rounded-lg border border-slate-800 bg-slate-950 p-3.5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-semibold text-aura-300">{tbl.table_name}</span>
                        <span className="text-[10px] text-slate-500">{tbl.row_count} rows</span>
                      </div>
                      <div className="max-h-36 overflow-y-auto divide-y divide-slate-850 text-[11px]">
                        {tbl.columns.map((c) => (
                          <div key={c.name} className="py-1 flex items-center justify-between text-slate-400">
                            <span className="font-mono text-slate-300">{c.name}</span>
                            <span className="text-[10px] text-slate-500 font-mono">{c.data_type}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 2: DOCUMENTS */}
      {/* ============================================================== */}
      {activeTab === "documents" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-900/40 p-4 rounded-xl border border-slate-800">
            <div>
              <h2 className="text-sm font-bold text-white">Indexed Documents & Knowledge Base</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Upload files (PDF, DOCX, XLSX, CSV, Markdown, TXT) to index into this Brain for semantic agent retrieval.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {unassignedDocs.length > 0 && (
                <button
                  onClick={() => setShowAttachDocsModal(true)}
                  className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-750 px-3 py-1.5 text-xs font-semibold text-slate-200 transition"
                >
                  <Layers className="h-3.5 w-3.5 text-slate-400" />
                  <span>Attach Existing ({unassignedDocs.length})</span>
                </button>
              )}

              <label className="flex items-center space-x-1.5 rounded-lg bg-aura-600 hover:bg-aura-500 px-3 py-1.5 text-xs font-semibold text-white shadow cursor-pointer transition">
                <Upload className="h-3.5 w-3.5" />
                <span>{uploading ? "Ingesting..." : "Upload File"}</span>
                <input
                  type="file"
                  onChange={handleUploadDocument}
                  disabled={uploading}
                  className="hidden"
                  accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.md"
                />
              </label>
            </div>
          </div>

          {brain.documents.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-800 p-10 text-center">
              <FileText className="h-10 w-10 text-slate-600 mx-auto mb-2" />
              <h3 className="text-sm font-semibold text-slate-200">No Documents in this Brain</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Upload policy guidelines, financial sheets, or technical docs to build this Brain&apos;s knowledge graph.
              </p>
              <label className="mt-4 inline-flex items-center space-x-1.5 rounded-lg bg-aura-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 cursor-pointer transition">
                <Upload className="h-3.5 w-3.5" />
                <span>Upload First Document</span>
                <input
                  type="file"
                  onChange={handleUploadDocument}
                  disabled={uploading}
                  className="hidden"
                  accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.md"
                />
              </label>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {brain.documents.map((doc) => (
                <div
                  key={doc.id}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex flex-col justify-between hover:border-slate-700 transition"
                >
                  <div>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2.5 truncate">
                        <FileText className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                        <div className="truncate">
                          <h3 className="font-semibold text-sm text-white truncate">{doc.title}</h3>
                          <span className="font-mono text-[10px] text-slate-400">{doc.file_name}</span>
                        </div>
                      </div>
                      <span className="font-mono text-[10px] uppercase rounded bg-slate-800 border border-slate-700 px-1.5 py-0.5 text-slate-300">
                        {doc.file_type}
                      </span>
                    </div>

                    <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                      <span className="text-[11px]">
                        {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : "File"}
                      </span>
                      {doc.status === "INDEXED" ? (
                        <span className="flex items-center space-x-1 text-emerald-400 text-[11px]">
                          <CheckCircle className="h-3 w-3" />
                          <span>{doc.chunk_count} chunks indexed</span>
                        </span>
                      ) : doc.status === "FAILED" ? (
                        <div className="flex items-center space-x-2">
                          <span className="flex items-center space-x-1 text-rose-400 text-[11px]" title={doc.error_message || "Ingestion failed"}>
                            <AlertCircle className="h-3 w-3" />
                            <span>Failed</span>
                          </span>
                          <button
                            onClick={() => handleRetryDoc(doc.id)}
                            className="text-[10px] text-aura-400 hover:text-aura-300 underline font-medium"
                          >
                            Retry
                          </button>
                        </div>
                      ) : (
                        <span className="flex items-center space-x-1 text-amber-400 text-[11px]">
                          <Clock className="h-3 w-3 animate-spin" />
                          <span>Processing...</span>
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                    <button
                      onClick={() => inspectDoc(doc.id)}
                      className="rounded bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-[11px] font-medium text-slate-300 transition"
                    >
                      Inspect Chunks
                    </button>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleDetachDoc(doc.id, doc.title)}
                        className="text-slate-500 hover:text-amber-400 p-1 transition flex items-center gap-1 text-[11px]"
                        title="Detach from Brain"
                      >
                        <Unlink className="h-3 w-3" />
                        <span>Detach</span>
                      </button>
                      <button
                        onClick={() => handleDeleteDoc(doc.id)}
                        className="text-slate-500 hover:text-red-400 p-1 transition"
                        title="Delete Document"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Document Chunks Inspection Section */}
          {selectedDoc && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 mt-6">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <FileText className="h-4 w-4 text-emerald-400" />
                  <h3 className="font-semibold text-sm text-white">
                    Chunks Preview: {selectedDoc.title}
                  </h3>
                  <span className="text-xs text-slate-400">({selectedDoc.chunks?.length || 0} chunks)</span>
                </div>
                <button onClick={() => setSelectedDoc(null)} className="text-xs text-slate-400 hover:text-white">
                  Close
                </button>
              </div>

              <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                {selectedDoc.chunks?.map((chunk: any) => (
                  <div key={chunk.id} className="rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs text-slate-300 space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-500">
                      <span>Chunk #{chunk.chunk_index}</span>
                      <span>{chunk.embedding_dim ? `${chunk.embedding_dim}-dim Vector` : "Vectorized"}</span>
                    </div>
                    <p className="line-clamp-3 font-mono text-[11px] text-slate-300">{chunk.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 3: ROLES & ACCESS GOVERNANCE */}
      {/* ============================================================== */}
      {activeTab === "roles" && (
        <div className="space-y-6">
          <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-white">Brain Access & Permissions Matrix</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Users with assigned roles can view, query, and trigger agent reasoning on this Brain.
              </p>
            </div>
            <button
              onClick={handleSaveRoles}
              disabled={submitting}
              className="rounded-lg bg-aura-600 hover:bg-aura-500 px-4 py-1.5 text-xs font-semibold text-white shadow transition disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save Role Permissions"}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {allRoles.map((r) => {
              const checked = assignedRoleIds.includes(r.id);
              return (
                <div
                  key={r.id}
                  onClick={() => {
                    if (checked) setAssignedRoleIds(assignedRoleIds.filter((id) => id !== r.id));
                    else setAssignedRoleIds([...assignedRoleIds, r.id]);
                  }}
                  className={`p-4 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                    checked
                      ? "border-aura-500/60 bg-aura-950/20 text-white shadow-sm"
                      : "border-slate-800 bg-slate-900/40 text-slate-300 hover:border-slate-700"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-white">{r.name}</span>
                      {r.is_system && (
                        <span className="rounded bg-slate-800 text-[10px] text-slate-400 px-1.5 py-0.5 font-mono">
                          System
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400">{r.description || "Enterprise role definition"}</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => {}}
                    className="rounded border-slate-700 text-aura-600 focus:ring-aura-500 h-4 w-4"
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL: CONNECT NEW DATABASE TO BRAIN */}
      {/* ============================================================== */}
      {showAddSourceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-400" />
              Connect Database to &apos;{brain.name}&apos;
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Enter database credentials. This database will be automatically assigned to this Brain.
            </p>

            <form onSubmit={handleCreateSource} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Source Name</label>
                <input
                  type="text"
                  required
                  value={sourceName}
                  onChange={(e) => setSourceName(e.target.value)}
                  placeholder="e.g. Production Analytics DB"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Database Type</label>
                <select
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
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
                  value={sourceDescription}
                  onChange={(e) => setSourceDescription(e.target.value)}
                  placeholder="Context for agent analytical queries..."
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddSourceModal(false)}
                  className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-aura-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 disabled:opacity-50"
                >
                  {submitting ? "Connecting..." : "Add to Brain"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL: ATTACH EXISTING DATA SOURCES */}
      {/* ============================================================== */}
      {showAttachSourcesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-400" />
              Attach Existing Data Sources
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Select configured data sources in your organization to associate with &apos;{brain.name}&apos;.
            </p>

            <div className="max-h-60 overflow-y-auto space-y-2 mb-4">
              {unassignedSources.map((s) => {
                const checked = sourcesToAttach.includes(s.id);
                return (
                  <label
                    key={s.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950 text-xs text-slate-200 cursor-pointer hover:border-slate-700"
                  >
                    <div>
                      <div className="font-semibold text-white">{s.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{s.type}</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        if (e.target.checked) setSourcesToAttach([...sourcesToAttach, s.id]);
                        else setSourcesToAttach(sourcesToAttach.filter((id) => id !== s.id));
                      }}
                      className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                    />
                  </label>
                );
              })}
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowAttachSourcesModal(false)}
                className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleAttachSources}
                disabled={submitting || sourcesToAttach.length === 0}
                className="rounded-lg bg-aura-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 disabled:opacity-50"
              >
                {submitting ? "Attaching..." : `Attach (${sourcesToAttach.length})`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL: ATTACH EXISTING DOCUMENTS */}
      {/* ============================================================== */}
      {showAttachDocsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <FileText className="h-5 w-5 text-emerald-400" />
              Attach Existing Documents
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Select existing uploaded documents to assign to &apos;{brain.name}&apos;.
            </p>

            <div className="max-h-60 overflow-y-auto space-y-2 mb-4">
              {unassignedDocs.map((d) => {
                const checked = docsToAttach.includes(d.id);
                return (
                  <label
                    key={d.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950 text-xs text-slate-200 cursor-pointer hover:border-slate-700"
                  >
                    <div className="truncate pr-2">
                      <div className="font-semibold text-white truncate">{d.title}</div>
                      <div className="text-[10px] text-slate-400">{d.file_name}</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        if (e.target.checked) setDocsToAttach([...docsToAttach, d.id]);
                        else setDocsToAttach(docsToAttach.filter((id) => id !== d.id));
                      }}
                      className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                    />
                  </label>
                );
              })}
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowAttachDocsModal(false)}
                className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleAttachDocs}
                disabled={submitting || docsToAttach.length === 0}
                className="rounded-lg bg-aura-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 disabled:opacity-50"
              >
                {submitting ? "Attaching..." : `Attach (${docsToAttach.length})`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
