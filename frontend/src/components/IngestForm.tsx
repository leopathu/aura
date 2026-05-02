"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { documentService } from "@/services/document-service";
import { getErrorMessage } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface IngestFormProps {
  onSuccess: () => void;
}

/**
 * Form for ingesting a new document into the RAG pipeline.
 */
export function IngestForm({ onSuccess }: IngestFormProps) {
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [content, setContent] = useState("");

  const mutation = useMutation({
    mutationFn: () => documentService.ingest({ title, ...(source ? { source } : {}), content }),
    onSuccess: (data) => {
      alert(`Ingested ${data.chunks_created} chunks for document ${data.document_id}`);
      setTitle("");
      setSource("");
      setContent("");
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  const inputClass = cn(
    "w-full border border-slate-300 rounded-lg px-4 py-2 text-sm outline-none",
    "focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
  );

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 border border-slate-200 rounded-xl p-6">
      <h2 className="font-semibold text-slate-700">Ingest New Document</h2>

      {mutation.isError && (
        <p className="text-red-600 text-sm">{getErrorMessage(mutation.error)}</p>
      )}

      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-500 font-medium">Title *</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={inputClass}
          placeholder="My Document"
          required
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-500 font-medium">Source URL</label>
        <input
          type="url"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className={inputClass}
          placeholder="https://example.com/doc"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-500 font-medium">Content *</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className={cn(inputClass, "resize-y min-h-[120px]")}
          placeholder="Paste document text here…"
          required
        />
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className={cn(
          "self-start px-5 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-medium",
          "hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        )}
      >
        {mutation.isPending ? "Ingesting…" : "Ingest Document"}
      </button>
    </form>
  );
}
