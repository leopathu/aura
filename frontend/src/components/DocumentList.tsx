"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentService } from "@/services/document-service";
import { IngestForm } from "./IngestForm";
import type { Document } from "@/types";

/**
 * Displays all ingested documents and provides an ingest form.
 */
export function DocumentList() {
  const queryClient = useQueryClient();

  const { data: documents, isLoading, error } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentService.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  if (isLoading) return <p className="text-slate-400">Loading documents…</p>;
  if (error) return <p className="text-red-600">Failed to load documents.</p>;

  return (
    <div className="flex flex-col gap-8">
      <IngestForm onSuccess={() => queryClient.invalidateQueries({ queryKey: ["documents"] })} />

      {documents?.length === 0 ? (
        <p className="text-slate-400 text-sm">No documents ingested yet.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {documents?.map((doc: Document) => (
            <li
              key={doc.id}
              className="flex items-center justify-between border border-slate-200 rounded-lg px-5 py-4"
            >
              <div>
                <p className="font-medium text-slate-700">{doc.title}</p>
                {doc.source && <p className="text-xs text-slate-400 mt-0.5">{doc.source}</p>}
              </div>
              <button
                onClick={() => deleteMutation.mutate(doc.id)}
                disabled={deleteMutation.isPending}
                className="text-xs text-red-500 hover:text-red-700 transition-colors disabled:opacity-50"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
