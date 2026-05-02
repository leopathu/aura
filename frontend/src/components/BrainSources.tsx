"use client";

import React, { useRef, useState, useCallback, useEffect } from "react";
import { useBrainDocuments } from "@/hooks/useBrains";
import { documentService } from "@/services/document-service";
import { brainService } from "@/services/brain-service";
import { getErrorMessage } from "@/lib/api-client";
import type { Brain, BrainDocument } from "@/types";
import { cn } from "@/lib/utils";

interface BrainSourcesProps {
  brain: Brain;
}

const FILE_ACCEPT = ".pdf,.docx,.xlsx,.xls,.csv,.txt";

function fileIcon(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "📄";
  if (ext === "docx") return "📝";
  if (ext === "xlsx" || ext === "xls") return "📊";
  if (ext === "csv") return "📋";
  return "📃";
}

function StatusBadge({ doc }: { doc: BrainDocument }) {
  const status = doc.embed_status ?? "pending";

  if (status === "ready") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" />
        Ready
      </span>
    );
  }
  if (status === "processing") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
        <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
        Embedding…
      </span>
    );
  }
  if (status === "pending") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
        <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 inline-block animate-pulse" />
        Pending
      </span>
    );
  }
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 cursor-help"
      title={doc.embed_error ?? "Embedding failed"}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
      Failed
    </span>
  );
}

/**
 * Sources tab — upload files into a brain and manage connected documents.
 */
export function BrainSources({ brain }: BrainSourcesProps) {
  const { documents, isLoading, removeDocument, refetch } = useBrainDocuments(brain.id);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset status when brain changes
  useEffect(() => {
    setError(null);
    setSuccess(null);
  }, [brain.id]);

  // Poll every 3 s while any document is pending or processing
  useEffect(() => {
    const hasBusy = documents.some(
      (d: BrainDocument) => d.embed_status === "pending" || d.embed_status === "processing"
    );
    if (!hasBusy) return;
    const timer = setInterval(() => { void refetch(); }, 6000);
    return () => clearInterval(timer);
  }, [documents, refetch]);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      setUploading(true);
      setError(null);
      setSuccess(null);
      const uploaded: string[] = [];
      for (const file of Array.from(files)) {
        try {
          // Upload returns immediately — embedding happens in background
          const result = await documentService.uploadFile(file);
          await brainService.addDocument(brain.id, result.document_id);
          uploaded.push(`"${file.name}"`);
        } catch (err) {
          setError(`Failed to upload "${file.name}": ${getErrorMessage(err)}`);
          setUploading(false);
          refetch();
          return;
        }
      }
      setSuccess(`✓ Uploaded ${uploaded.join(", ")} — embedding in background…`);
      setUploading(false);
      refetch();
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    [brain.id, refetch]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragOver(false);
      void handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleDelete = async (doc: BrainDocument) => {
    setDeletingId(doc.id);
    setError(null);
    try {
      await documentService.delete(doc.id);
      refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  void removeDocument;

  const filtered = documents.filter((d: BrainDocument) =>
    d.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 pt-5 pb-3 shrink-0">
        <h3 className="text-sm font-semibold text-slate-700">
          Sources — <span className="text-brand-700">{brain.name}</span>
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Upload files to feed this brain. Supported: PDF, DOCX, XLSX, CSV, TXT.
        </p>
      </div>

      {/* Drop zone */}
      <div className="px-6 pb-4 shrink-0">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "relative border-2 border-dashed rounded-xl p-6 cursor-pointer transition-colors text-center",
            dragOver
              ? "border-brand-400 bg-brand-50"
              : "border-slate-300 hover:border-brand-400 hover:bg-brand-50/50"
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={FILE_ACCEPT}
            multiple
            className="hidden"
            onChange={(e) => void handleFiles(e.target.files)}
          />
          {uploading ? (
            <div className="flex flex-col items-center gap-2">
              <svg className="animate-spin h-6 w-6 text-brand-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span className="text-sm text-brand-600 font-medium">Uploading…</span>
            </div>
          ) : (
            <>
              <div className="text-2xl mb-1">⬆️</div>
              <p className="text-sm font-medium text-slate-600">
                Drop files here or <span className="text-brand-600 underline">browse</span>
              </p>
              <p className="text-xs text-slate-400 mt-0.5">PDF · DOCX · XLSX · CSV · TXT</p>
            </>
          )}
        </div>

        {/* Status messages */}
        {success && (
          <p className="mt-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-xs text-green-700">
            {success}
          </p>
        )}
        {error && (
          <p className="mt-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600">
            {error}
          </p>
        )}
      </div>

      {/* Search */}
      <div className="px-6 mb-3 shrink-0">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search documents…"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-2">
        {isLoading && documents.length === 0 && (
          <p className="text-xs text-slate-400 py-4 text-center">Loading…</p>
        )}
        {!isLoading && filtered.length === 0 && (
          <p className="text-xs text-slate-400 py-6 text-center">
            {documents.length === 0
              ? "No documents yet. Upload files above to feed this brain."
              : "No documents match your search."}
          </p>
        )}
        {filtered.map((doc: BrainDocument) => (
          <div
            key={doc.id}
            className="flex items-center justify-between p-3 rounded-xl border border-brand-200 bg-brand-50 transition-colors"
          >
            <div className="min-w-0 flex-1 flex items-center gap-2">
              <span className="text-lg shrink-0">{fileIcon(doc.title)}</span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-700 truncate">{doc.title}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <p className="text-xs text-slate-400">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </p>
                  <StatusBadge doc={doc} />
                </div>
              </div>
            </div>
            <button
              onClick={() => void handleDelete(doc)}
              disabled={deletingId === doc.id}
              className="ml-3 shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-200 bg-white text-slate-500 hover:border-red-300 hover:text-red-600 transition-colors disabled:opacity-50"
            >
              {deletingId === doc.id ? "…" : "Delete"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
