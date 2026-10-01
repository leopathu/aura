"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { DocumentItem, BrainItem } from "@/types";
import { FileText, Upload, Trash2, CheckCircle, Clock, AlertTriangle, Layers, BrainCircuit } from "lucide-react";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [brains, setBrains] = useState<BrainItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadBrainId, setUploadBrainId] = useState<string>("");
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [docsData, brainsData] = await Promise.all([
        apiRequest<DocumentItem[]>("/documents"),
        apiRequest<BrainItem[]>("/brains"),
      ]);
      setDocuments(docsData);
      setBrains(brainsData);
    } catch (e) {
      console.error(e);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  // Auto-poll when any document is still processing
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === "PROCESSING");
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      loadDocuments(false);
    }, 2500);

    return () => clearInterval(interval);
  }, [documents]);

  const handleRetry = async (docId: string) => {
    try {
      await apiRequest(`/documents/${docId}/retry`, { method: "POST" });
      loadDocuments(false);
    } catch (err: any) {
      alert(err.message || "Failed to retry indexing");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    if (uploadBrainId) {
      formData.append("brain_id", uploadBrainId);
    }

    try {
      await apiRequest("/documents/upload", {
        method: "POST",
        body: formData,
      });
      loadDocuments();
    } catch (err: any) {
      alert(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  const inspectDoc = async (id: string) => {
    try {
      const data = await apiRequest(`/documents/${id}`);
      setSelectedDoc(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this document from the knowledge base?")) return;
    try {
      await apiRequest(`/documents/${id}`, { method: "DELETE" });
      loadDocuments();
      if (selectedDoc?.id === id) setSelectedDoc(null);
    } catch (e: any) {
      alert(e.message || "Failed to delete");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Document Knowledge Base (RAG)</h1>
          <p className="mt-1 text-sm text-slate-400">
            Ingest and index company documents (PDF, DOCX, XLSX, CSV, Markdown) for semantic agent retrieval.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
            <BrainCircuit className="h-3.5 w-3.5 text-aura-400" />
            <select
              value={uploadBrainId}
              onChange={(e) => setUploadBrainId(e.target.value)}
              className="bg-transparent text-xs text-white focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-slate-900 text-white">Upload to Global / No Brain</option>
              {brains.map((b) => (
                <option key={b.id} value={b.id} className="bg-slate-900 text-white">
                  Upload to &apos;{b.name}&apos;
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-aura-500 cursor-pointer transition">
            <Upload className="h-4 w-4" />
            <span>{uploading ? "Ingesting..." : "Upload File"}</span>
            <input
              type="file"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
              accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.md"
            />
          </label>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Document list */}
        <div className="space-y-3">
          <div className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
            Indexed Documents ({documents.length})
          </div>
          {documents.map((doc) => (
            <div
              key={doc.id}
              onClick={() => inspectDoc(doc.id)}
              className={`cursor-pointer rounded-xl border p-4 transition ${
                selectedDoc?.id === doc.id
                  ? "border-cyan-500 bg-slate-900 shadow-md"
                  : "border-slate-800 bg-slate-900/50 hover:bg-slate-900"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5 truncate">
                  <FileText className="h-4 w-4 text-cyan-400 flex-shrink-0" />
                  <span className="font-semibold text-sm text-white truncate">{doc.title}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(doc.id);
                  }}
                  className="p-1 text-slate-500 hover:text-red-400 transition"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                <div className="flex items-center space-x-1.5">
                  <span className="font-mono uppercase text-slate-400">{doc.file_type}</span>
                  {doc.brain_id && (
                    <span className="flex items-center gap-1 rounded bg-aura-950 border border-aura-800/60 px-1.5 py-0.5 text-[9px] text-aura-300 font-medium">
                      <BrainCircuit className="h-2.5 w-2.5" />
                      {brains.find((b) => b.id === doc.brain_id)?.name || "Brain"}
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {doc.status === "INDEXED" ? (
                    <span className="text-emerald-400 flex items-center space-x-1">
                      <CheckCircle className="h-3 w-3" />
                      <span>{doc.chunk_count} chunks</span>
                    </span>
                  ) : doc.status === "FAILED" ? (
                    <div className="flex items-center space-x-1.5">
                      <span className="text-rose-400 flex items-center space-x-1" title={doc.error_message || "Ingestion failed"}>
                        <AlertTriangle className="h-3 w-3" />
                        <span>Failed</span>
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRetry(doc.id);
                        }}
                        className="text-[10px] text-aura-400 hover:text-aura-300 underline font-medium"
                      >
                        Retry
                      </button>
                    </div>
                  ) : (
                    <span className="text-amber-400 flex items-center space-x-1">
                      <Clock className="h-3 w-3 animate-spin" />
                      <span>Processing...</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Chunks inspector */}
        <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
          {selectedDoc ? (
            <div className="space-y-4">
              <div className="border-b border-slate-800 pb-4">
                <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                  <FileText className="h-5 w-5 text-cyan-400" />
                  <span>{selectedDoc.title}</span>
                </h2>
                <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-400">
                  <span>File: <code className="text-slate-300">{selectedDoc.file_name}</code></span>
                  <span>Size: {(selectedDoc.file_size / 1024).toFixed(1)} KB</span>
                  <span>Total Chunks: <strong className="text-cyan-400">{selectedDoc.chunk_count}</strong></span>
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
                  <Layers className="h-4 w-4 text-cyan-400" />
                  <span>Sample Vector Chunks</span>
                </div>

                <div className="space-y-3">
                  {selectedDoc.sample_chunks?.map((chunk: any) => (
                    <div key={chunk.chunk_index} className="rounded-lg border border-slate-800 bg-slate-900/80 p-3 text-xs">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 border-b border-slate-800 pb-1">
                        <span className="font-semibold text-aura-300">Chunk #{chunk.chunk_index + 1}</span>
                        <span>
                          Page: {chunk.metadata?.page || 1} • {chunk.metadata?.section || "General"}
                        </span>
                      </div>
                      <p className="text-slate-300 font-mono text-[11px] whitespace-pre-wrap leading-relaxed">
                        {chunk.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-xs text-slate-500">
              Select a document to inspect its parsed vector chunks.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
