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
  Unlink,
  ExternalLink,
  ShieldAlert,
  Server
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

export default function BrainResourcesPage() {
  const params = useParams();
  const router = useRouter();
  const brainId = params.id as string;

  const [brain, setBrain] = useState<BrainDetail | null>(null);
  const [allOrgSources, setAllOrgSources] = useState<DataSource[]>([]);
  const [allOrgDocs, setAllOrgDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Schema Inspection modal
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);
  const [schemaTables, setSchemaTables] = useState<DataSourceTable[]>([]);
  const [testStatus, setTestStatus] = useState<string | null>(null);

  // Document Inspection modal
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  // Add Source Modal State
  const [showAddSourceModal, setShowAddSourceModal] = useState(false);
  const [addSourceTab, setAddSourceTab] = useState<"new" | "existing">("new");
  const [sourceName, setSourceName] = useState("");
  const [sourceType, setSourceType] = useState("POSTGRES");
  const [connectionUri, setConnectionUri] = useState("");
  const [sourceDescription, setSourceDescription] = useState("");
  const [sourcesToAttach, setSourcesToAttach] = useState<string[]>([]);

  // Add Document Modal State
  const [showAddDocModal, setShowAddDocModal] = useState(false);
  const [addDocTab, setAddDocTab] = useState<"upload" | "existing">("upload");
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const [docsToAttach, setDocsToAttach] = useState<string[]>([]);

  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadBrainData();
  }, [brainId]);

  const loadBrainData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [brainData, allSources, allDocs] = await Promise.all([
        apiRequest<BrainDetail>(`/brains/${brainId}`),
        apiRequest<DataSource[]>("/sources"),
        apiRequest<DocumentItem[]>("/documents"),
      ]);
      setBrain(brainData);
      setAllOrgSources(allSources);
      setAllOrgDocs(allDocs);
    } catch (err: any) {
      console.error(err);
      if (showLoading) setStatusMsg({ type: "error", text: `Error loading Brain resources: ${err.message}` });
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
      setStatusMsg({ type: "success", text: "Document re-indexing queued." });
      loadBrainData(false);
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Failed to retry indexing: ${err.message}` });
    }
  };

  // --- Data Source Handlers ---
  const handleCreateAndConnectSource = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setStatusMsg(null);
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
      setStatusMsg({ type: "success", text: `Database '${sourceName}' created and connected to Brain!` });
      loadBrainData();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Failed to connect database: ${err.message}` });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAttachExistingSources = async () => {
    if (sourcesToAttach.length === 0) return;
    setSubmitting(true);
    setStatusMsg(null);
    try {
      const currentSourceIds = brain?.sources.map((s) => s.id) || [];
      const updatedSourceIds = Array.from(new Set([...currentSourceIds, ...sourcesToAttach]));
      await apiRequest(`/brains/${brainId}/connect-resources`, {
        method: "POST",
        body: JSON.stringify({ source_ids: updatedSourceIds }),
      });
      setShowAddSourceModal(false);
      setSourcesToAttach([]);
      setStatusMsg({ type: "success", text: "Attached existing data sources successfully!" });
      loadBrainData();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Failed to attach data sources: ${err.message}` });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDetachSource = async (sourceId: string, name: string) => {
    if (!confirm(`Are you sure you want to detach database '${name}' from this Brain?`)) return;
    try {
      await apiRequest(`/brains/${brainId}/sources/${sourceId}/detach`, { method: "POST" });
      setStatusMsg({ type: "success", text: `Detached '${name}' from this Brain.` });
      loadBrainData();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Failed to detach: ${err.message}` });
    }
  };

  const handleTestSource = async (sourceId: string) => {
    setTestStatus("Testing connectivity...");
    try {
      const res = await apiRequest(`/sources/${sourceId}/test`, { method: "POST" });
      setTestStatus(res.message || (res.success ? "Connection successful!" : "Connection failed."));
    } catch (err: any) {
      setTestStatus(`Error: ${err.message}`);
    }
  };

  const handleSyncSchema = async (sourceId: string) => {
    try {
      await apiRequest(`/sources/${sourceId}/sync-schema`, { method: "POST" });
      setStatusMsg({ type: "success", text: "Schema discovery initiated in background." });
      loadBrainData();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Sync failed: ${err.message}` });
    }
  };

  const handleInspectSchema = async (source: DataSource) => {
    setSelectedSource(source);
    setTestStatus(null);
    try {
      const res = await apiRequest<DataSourceTable[]>(`/sources/${source.id}/schemas`);
      setSchemaTables(res);
    } catch (err: any) {
      console.error(err);
      setSchemaTables([]);
    }
  };

  // --- Document Handlers ---
  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileToUpload) return;
    setUploading(true);
    setStatusMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", fileToUpload);
      formData.append("title", uploadTitle || fileToUpload.name);
      formData.append("brain_id", brainId);

      await apiRequest("/documents", {
        method: "POST",
        body: formData,
      });

      setShowAddDocModal(false);
      setFileToUpload(null);
      setUploadTitle("");
      setStatusMsg({ type: "success", text: "Document uploaded and indexing started for this Brain!" });
      loadBrainData();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Upload failed: ${err.message}` });
    } finally {
      setUploading(false);
    }
  };

  const handleAttachExistingDocs = async () => {
    if (docsToAttach.length === 0) return;
    setSubmitting(true);
    setStatusMsg(null);
    try {
      const currentDocIds = brain?.documents.map((d) => d.id) || [];
      const updatedDocIds = Array.from(new Set([...currentDocIds, ...docsToAttach]));
      await apiRequest(`/brains/${brainId}/connect-resources`, {
        method: "POST",
        body: JSON.stringify({ document_ids: updatedDocIds }),
      });
      setShowAddDocModal(false);
      setDocsToAttach([]);
      setStatusMsg({ type: "success", text: "Attached existing documents successfully!" });
      loadBrainData();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Failed to attach documents: ${err.message}` });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDetachDoc = async (docId: string, title: string) => {
    if (!confirm(`Are you sure you want to detach '${title}' from this Brain?`)) return;
    try {
      await apiRequest(`/brains/${brainId}/documents/${docId}/detach`, { method: "POST" });
      setStatusMsg({ type: "success", text: `Detached '${title}' from this Brain.` });
      loadBrainData();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Failed to detach document: ${err.message}` });
    }
  };

  const handleDeleteDoc = async (docId: string, title: string) => {
    if (!confirm(`Permanently delete document '${title}' from the organization?`)) return;
    try {
      await apiRequest(`/documents/${docId}`, { method: "DELETE" });
      setStatusMsg({ type: "success", text: `Deleted '${title}' permanently.` });
      loadBrainData();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: `Failed to delete document: ${err.message}` });
    }
  };

  const handleInspectDoc = async (doc: DocumentItem) => {
    try {
      const details = await apiRequest(`/documents/${doc.id}`);
      setSelectedDoc(details);
    } catch (err: any) {
      setSelectedDoc(doc);
    }
  };

  // Helper filters for unattached resources
  const unattachedSources = allOrgSources.filter(
    (s) => !brain?.sources.some((bs) => bs.id === s.id)
  );
  const unattachedDocs = allOrgDocs.filter(
    (d) => !brain?.documents.some((bd) => bd.id === d.id)
  );

  if (loading && !brain) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-aura-500 border-t-transparent"></div>
          <span className="text-xs text-slate-400">Loading Brain resources...</span>
        </div>
      </div>
    );
  }

  if (!brain) {
    return (
      <div className="p-8 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-3" />
        <h2 className="text-lg font-bold text-white">Brain Not Found</h2>
        <p className="text-xs text-slate-400 mt-1 mb-4">The requested Brain could not be loaded or you do not have permission.</p>
        <Link
          href="/console/brains"
          className="inline-flex items-center space-x-2 rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-700 transition"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Brains</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center space-x-2 text-xs text-slate-400">
        <Link href="/console/brains" className="hover:text-aura-400 transition flex items-center gap-1">
          <BrainCircuit className="h-3.5 w-3.5" />
          <span>Brains</span>
        </Link>
        <span>/</span>
        <Link href={`/console/brains/${brain.id}`} className="hover:text-aura-400 transition">
          {brain.name}
        </Link>
        <span>/</span>
        <span className="text-white font-medium">Connect Resources</span>
      </div>

      {/* Top Header & Action Buttons */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-aura-950 border border-aura-800/80 text-aura-400 shadow-md">
                <Layers className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>Connect Resources: {brain.name}</span>
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Manage databases and documents connected directly to this Brain.
                </p>
              </div>
            </div>
          </div>

          {/* Action Buttons in Top */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => {
                setAddSourceTab("new");
                setShowAddSourceModal(true);
              }}
              className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white hover:bg-aura-500 shadow-lg shadow-aura-600/20 transition"
            >
              <Plus className="h-4 w-4" />
              <span>Add Data Source</span>
            </button>

            <button
              onClick={() => {
                setAddDocTab("upload");
                setShowAddDocModal(true);
              }}
              className="flex items-center space-x-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 shadow-lg shadow-emerald-600/20 transition"
            >
              <Upload className="h-4 w-4" />
              <span>Upload Document</span>
            </button>

            <Link
              href={`/console/brains/${brain.id}`}
              className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-800 px-3.5 py-2 text-xs font-medium text-slate-300 transition"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Brain Overview</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Status Notifications */}
      {statusMsg && (
        <div
          className={`flex items-center justify-between rounded-xl border p-4 text-xs ${
            statusMsg.type === "success"
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border-red-500/30 bg-red-500/10 text-red-300"
          }`}
        >
          <div className="flex items-center space-x-2">
            {statusMsg.type === "success" ? (
              <CheckCircle className="h-4 w-4 text-emerald-400 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
            )}
            <span>{statusMsg.text}</span>
          </div>
          <button onClick={() => setStatusMsg(null)} className="text-slate-400 hover:text-white">
            &times;
          </button>
        </div>
      )}

      {/* SECTION 1: ADDED DATA SOURCES TABLE */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-blue-950/60 border border-blue-800/60 text-blue-400">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Added Data Sources</h2>
              <p className="text-[11px] text-slate-400">
                Relational databases accessible by AI agents querying this Brain ({brain.sources.length})
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              setAddSourceTab("new");
              setShowAddSourceModal(true);
            }}
            className="flex items-center space-x-1.5 rounded-lg border border-aura-500/40 bg-aura-600/10 hover:bg-aura-600/20 px-3 py-1.5 text-xs font-semibold text-aura-300 transition"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Data Source</span>
          </button>
        </div>

        {brain.sources.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/40 p-8 text-center">
            <Database className="mx-auto h-10 w-10 text-slate-600 mb-2.5" />
            <h3 className="text-xs font-semibold text-slate-300">No Data Sources Connected</h3>
            <p className="text-[11px] text-slate-500 mt-1 max-w-sm mx-auto mb-4">
              Connect PostgreSQL, MySQL, or SQLite databases to this Brain so AI agents can safely inspect schemas and execute read-only queries.
            </p>
            <button
              onClick={() => {
                setAddSourceTab("new");
                setShowAddSourceModal(true);
              }}
              className="inline-flex items-center space-x-1.5 rounded-lg bg-aura-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 transition shadow-md shadow-aura-600/20"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Connect First Database</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3">Source Name & Engine</th>
                  <th className="px-4 py-3">Security & Mode</th>
                  <th className="px-4 py-3">Schema Status</th>
                  <th className="px-4 py-3">Added Date</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                {brain.sources.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3.5">
                      <div className="flex items-center space-x-2.5">
                        <div className="p-1.5 rounded bg-blue-950/80 border border-blue-800/60 text-blue-400">
                          <Database className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-200">{s.name}</div>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
                              {s.type}
                            </span>
                            {s.description && (
                              <span className="text-[11px] text-slate-500 line-clamp-1">
                                {s.description}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-col gap-1">
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                          <CheckCircle className="h-3 w-3" />
                          <span>Active</span>
                        </span>
                        {s.is_read_only && (
                          <span className="inline-flex items-center text-[10px] text-slate-400">
                            Read-Only AST Enforced
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <button
                        onClick={() => handleInspectSchema(s)}
                        className="flex items-center space-x-1.5 text-xs text-aura-400 hover:text-aura-300 font-medium"
                      >
                        <Table className="h-3.5 w-3.5" />
                        <span>Inspect Schema</span>
                      </button>
                    </td>
                    <td className="px-4 py-3.5 text-slate-400">
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex items-center justify-end space-x-1.5">
                        <button
                          onClick={() => handleTestSource(s.id)}
                          title="Test Connection"
                          className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-[11px] font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition"
                        >
                          Test
                        </button>
                        <button
                          onClick={() => handleSyncSchema(s.id)}
                          title="Sync Schema"
                          className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-[11px] font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition"
                        >
                          <RefreshCw className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => handleDetachSource(s.id, s.name)}
                          title="Detach from this Brain"
                          className="rounded border border-red-500/30 bg-red-500/10 px-2 py-1 text-[11px] font-medium text-red-400 hover:bg-red-500/20 transition flex items-center gap-1"
                        >
                          <Unlink className="h-3 w-3" />
                          <span>Detach</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* SECTION 2: ADDED DOCUMENTS TABLE */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-emerald-400">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Added Documents</h2>
              <p className="text-[11px] text-slate-400">
                Indexed knowledge documents and vector chunks for this Brain ({brain.documents.length})
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              setAddDocTab("upload");
              setShowAddDocModal(true);
            }}
            className="flex items-center space-x-1.5 rounded-lg border border-emerald-500/40 bg-emerald-600/10 hover:bg-emerald-600/20 px-3 py-1.5 text-xs font-semibold text-emerald-300 transition"
          >
            <Upload className="h-3.5 w-3.5" />
            <span>Upload Document</span>
          </button>
        </div>

        {brain.documents.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/40 p-8 text-center">
            <FileText className="mx-auto h-10 w-10 text-slate-600 mb-2.5" />
            <h3 className="text-xs font-semibold text-slate-300">No Documents Uploaded</h3>
            <p className="text-[11px] text-slate-500 mt-1 max-w-sm mx-auto mb-4">
              Upload PDF, DOCX, XLSX, CSV, or Markdown files to this Brain. The platform will chunk, embed, and index them for semantic search and citations.
            </p>
            <button
              onClick={() => {
                setAddDocTab("upload");
                setShowAddDocModal(true);
              }}
              className="inline-flex items-center space-x-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition shadow-md shadow-emerald-600/20"
            >
              <Upload className="h-3.5 w-3.5" />
              <span>Upload First Document</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3">Document Title & File</th>
                  <th className="px-4 py-3">Format & Size</th>
                  <th className="px-4 py-3">Chunks & Vectors</th>
                  <th className="px-4 py-3">Index Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                {brain.documents.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3.5">
                      <div className="flex items-center space-x-2.5">
                        <div className="p-1.5 rounded bg-emerald-950/80 border border-emerald-800/60 text-emerald-400">
                          <FileText className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-200">{d.title}</div>
                          <div className="text-[10px] text-slate-500 font-mono">{d.file_name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-1.5">
                        <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono uppercase text-slate-300">
                          {d.file_type}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          {Math.round(d.file_size / 1024)} KB
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <button
                        onClick={() => handleInspectDoc(d)}
                        className="flex items-center space-x-1.5 text-xs text-aura-400 hover:text-aura-300 font-medium"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        <span>{d.chunk_count} Chunks</span>
                      </button>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`inline-flex items-center space-x-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                            d.status === "INDEXED"
                              ? "bg-emerald-950 text-emerald-400 border border-emerald-800/60"
                              : d.status === "PROCESSING"
                              ? "bg-blue-950 text-blue-400 border border-blue-800/60"
                              : "bg-red-950 text-red-400 border border-red-800/60"
                          }`}
                        >
                          {d.status === "INDEXED" ? (
                            <CheckCircle className="h-3 w-3" />
                          ) : d.status === "PROCESSING" ? (
                            <Clock className="h-3 w-3 animate-spin" />
                          ) : (
                            <AlertCircle className="h-3 w-3" />
                          )}
                          <span>{d.status === "PROCESSING" ? "Processing..." : d.status}</span>
                        </span>
                        {d.status === "FAILED" && (
                          <button
                            onClick={() => handleRetryDoc(d.id)}
                            className="text-[10px] text-aura-400 hover:text-aura-300 underline font-medium"
                          >
                            Retry
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex items-center justify-end space-x-1.5">
                        <button
                          onClick={() => handleDetachDoc(d.id, d.title)}
                          title="Detach from this Brain"
                          className="rounded border border-red-500/30 bg-red-500/10 px-2 py-1 text-[11px] font-medium text-red-400 hover:bg-red-500/20 transition flex items-center gap-1"
                        >
                          <Unlink className="h-3 w-3" />
                          <span>Detach</span>
                        </button>
                        <button
                          onClick={() => handleDeleteDoc(d.id, d.title)}
                          title="Delete from organization"
                          className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-[11px] font-medium text-slate-400 hover:text-red-400 hover:border-red-500/40 transition"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* MODAL: ADD DATA SOURCE */}
      {showAddSourceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl my-8">
            <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <Database className="h-5 w-5 text-aura-400" />
              Add Data Source to &apos;{brain.name}&apos;
            </h2>

            {/* Modal Tabs: Connect New vs Attach Existing */}
            <div className="flex border-b border-slate-800 mb-4">
              <button
                type="button"
                onClick={() => setAddSourceTab("new")}
                className={`py-2 px-4 text-xs font-semibold border-b-2 transition ${
                  addSourceTab === "new"
                    ? "border-aura-500 text-aura-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                + Connect New Database
              </button>
              <button
                type="button"
                onClick={() => setAddSourceTab("existing")}
                className={`py-2 px-4 text-xs font-semibold border-b-2 transition ${
                  addSourceTab === "existing"
                    ? "border-aura-500 text-aura-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Attach Existing ({unattachedSources.length})
              </button>
            </div>

            {addSourceTab === "new" ? (
              <form onSubmit={handleCreateAndConnectSource} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Source Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Production Analytics DB"
                    value={sourceName}
                    onChange={(e) => setSourceName(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-aura-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Database Engine</label>
                  <select
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-aura-500 focus:outline-none"
                  >
                    <option value="POSTGRES">PostgreSQL (asyncpg)</option>
                    <option value="MYSQL">MySQL (pymysql)</option>
                    <option value="SQLITE">SQLite (aiosqlite)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Connection URI</label>
                  <input
                    type="text"
                    required
                    placeholder={
                      sourceType === "POSTGRES"
                        ? "postgresql://user:pass@host:5432/dbname"
                        : sourceType === "MYSQL"
                        ? "mysql+pymysql://user:pass@host:3306/dbname"
                        : "sqlite:///./storage/my_database.db"
                    }
                    value={connectionUri}
                    onChange={(e) => setConnectionUri(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-aura-500 focus:outline-none font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-1 block">
                    Credentials are encrypted at rest with Fernet symmetric encryption.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Description (Optional)</label>
                  <textarea
                    rows={2}
                    placeholder="Primary business purpose of this database..."
                    value={sourceDescription}
                    onChange={(e) => setSourceDescription(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-aura-500 focus:outline-none"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddSourceModal(false)}
                    className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="rounded-lg bg-aura-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 transition disabled:opacity-50"
                  >
                    {submitting ? "Connecting..." : "Connect Database"}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <p className="text-xs text-slate-400">
                  Select existing organization databases to attach to this Brain:
                </p>

                <div className="max-h-56 overflow-y-auto space-y-1.5 rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                  {unattachedSources.length === 0 ? (
                    <span className="text-xs text-slate-500 italic">
                      All existing organization databases are already connected to this Brain.
                    </span>
                  ) : (
                    unattachedSources.map((s) => {
                      const checked = sourcesToAttach.includes(s.id);
                      return (
                        <label
                          key={s.id}
                          className="flex items-center space-x-2 p-2 rounded hover:bg-slate-900 cursor-pointer text-xs text-slate-300"
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) setSourcesToAttach([...sourcesToAttach, s.id]);
                              else setSourcesToAttach(sourcesToAttach.filter((id) => id !== s.id));
                            }}
                            className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                          />
                          <span className="font-semibold text-white">{s.name}</span>
                          <span className="text-[10px] text-slate-500 font-mono">({s.type})</span>
                        </label>
                      );
                    })
                  )}
                </div>

                <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddSourceModal(false)}
                    className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleAttachExistingSources}
                    disabled={submitting || sourcesToAttach.length === 0}
                    className="rounded-lg bg-aura-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 transition disabled:opacity-50"
                  >
                    {submitting ? "Attaching..." : `Attach (${sourcesToAttach.length})`}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: ADD DOCUMENT */}
      {showAddDocModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl my-8">
            <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <FileText className="h-5 w-5 text-emerald-400" />
              Upload Document to &apos;{brain.name}&apos;
            </h2>

            {/* Modal Tabs */}
            <div className="flex border-b border-slate-800 mb-4">
              <button
                type="button"
                onClick={() => setAddDocTab("upload")}
                className={`py-2 px-4 text-xs font-semibold border-b-2 transition ${
                  addDocTab === "upload"
                    ? "border-emerald-500 text-emerald-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                + Upload New File
              </button>
              <button
                type="button"
                onClick={() => setAddDocTab("existing")}
                className={`py-2 px-4 text-xs font-semibold border-b-2 transition ${
                  addDocTab === "existing"
                    ? "border-emerald-500 text-emerald-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Attach Existing ({unattachedDocs.length})
              </button>
            </div>

            {addDocTab === "upload" ? (
              <form onSubmit={handleUploadDocument} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Select File (PDF, DOCX, XLSX, CSV, MD, TXT)
                  </label>
                  <input
                    type="file"
                    required
                    accept=".pdf,.docx,.xlsx,.csv,.md,.txt"
                    onChange={(e) => {
                      const f = e.target.files?.[0] || null;
                      setFileToUpload(f);
                      if (f && !uploadTitle) setUploadTitle(f.name.replace(/\.[^/.]+$/, ""));
                    }}
                    className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-white hover:file:bg-slate-700 cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Document Title</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Employee Leave Policy 2026"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-aura-500 focus:outline-none"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddDocModal(false)}
                    className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={uploading || !fileToUpload}
                    className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition disabled:opacity-50"
                  >
                    {uploading ? "Uploading & Indexing..." : "Upload & Index"}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <p className="text-xs text-slate-400">
                  Select existing organization documents to attach to this Brain:
                </p>

                <div className="max-h-56 overflow-y-auto space-y-1.5 rounded-lg border border-slate-800 bg-slate-950 p-2.5">
                  {unattachedDocs.length === 0 ? (
                    <span className="text-xs text-slate-500 italic">
                      All existing organization documents are already connected to this Brain.
                    </span>
                  ) : (
                    unattachedDocs.map((d) => {
                      const checked = docsToAttach.includes(d.id);
                      return (
                        <label
                          key={d.id}
                          className="flex items-center space-x-2 p-2 rounded hover:bg-slate-900 cursor-pointer text-xs text-slate-300"
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) setDocsToAttach([...docsToAttach, d.id]);
                              else setDocsToAttach(docsToAttach.filter((id) => id !== d.id));
                            }}
                            className="rounded border-slate-700 text-emerald-600 focus:ring-emerald-500"
                          />
                          <span className="font-semibold text-white">{d.title}</span>
                          <span className="text-[10px] text-slate-500 font-mono">({d.file_name})</span>
                        </label>
                      );
                    })
                  )}
                </div>

                <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddDocModal(false)}
                    className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleAttachExistingDocs}
                    disabled={submitting || docsToAttach.length === 0}
                    className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition disabled:opacity-50"
                  >
                    {submitting ? "Attaching..." : `Attach (${docsToAttach.length})`}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: SCHEMA INSPECTOR */}
      {selectedSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 overflow-y-auto">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Database className="h-5 w-5 text-blue-400" />
                <h3 className="text-base font-bold text-white">Schema: {selectedSource.name}</h3>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>

            {testStatus && (
              <div className="mt-3 p-2.5 rounded-lg bg-slate-800 text-xs text-aura-300 font-mono">
                {testStatus}
              </div>
            )}

            <div className="mt-4 max-h-96 overflow-y-auto space-y-4">
              {schemaTables.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-500">
                  No tables discovered yet. Click &apos;Sync Schema&apos; to discover database structure.
                </div>
              ) : (
                schemaTables.map((t) => (
                  <div key={t.id} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-white font-mono flex items-center gap-1.5">
                        <Table className="h-3.5 w-3.5 text-aura-400" />
                        {t.table_name}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {t.columns?.length || 0} columns • {t.row_count || 0} rows (est)
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-[11px]">
                        <thead>
                          <tr className="text-slate-500 border-b border-slate-800/80">
                            <th className="py-1">Column</th>
                            <th className="py-1">Data Type</th>
                            <th className="py-1">Primary Key</th>
                            <th className="py-1">Nullable</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-900">
                          {t.columns?.map((c) => (
                            <tr key={c.name} className="text-slate-300">
                              <td className="py-1 font-mono">{c.name}</td>
                              <td className="py-1 text-slate-400 font-mono">{c.data_type}</td>
                              <td className="py-1">
                                {c.is_primary_key && (
                                  <span className="text-[9px] bg-amber-950 text-amber-300 border border-amber-800/60 px-1 py-0.2 rounded">
                                    PK
                                  </span>
                                )}
                              </td>
                              <td className="py-1 text-slate-500">{c.is_nullable ? "YES" : "NO"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={() => setSelectedSource(null)}
                className="rounded-lg bg-slate-800 px-4 py-1.5 text-xs text-slate-300 hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: DOCUMENT CHUNK INSPECTOR */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 overflow-y-auto">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <FileText className="h-5 w-5 text-emerald-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">{selectedDoc.title}</h3>
                  <div className="text-[10px] text-slate-400">{selectedDoc.file_name}</div>
                </div>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <div className="mt-4 max-h-96 overflow-y-auto space-y-3">
              {selectedDoc.chunks && selectedDoc.chunks.length > 0 ? (
                selectedDoc.chunks.map((ch: any) => (
                  <div key={ch.id || ch.chunk_index} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-500">
                      <span className="font-semibold text-aura-400">Chunk #{ch.chunk_index}</span>
                      <span>Length: {ch.content?.length || 0} characters</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap line-clamp-4">
                      {ch.content}
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-xs text-slate-500">
                  No individual chunks preview available for this document.
                </div>
              )}
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={() => setSelectedDoc(null)}
                className="rounded-lg bg-slate-800 px-4 py-1.5 text-xs text-slate-300 hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
