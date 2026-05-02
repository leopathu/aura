import type { SourceChunk } from "@/types";

interface SourceCardProps {
  source: SourceChunk;
}

/**
 * Displays a single retrieved source chunk with its similarity score.
 */
export function SourceCard({ source }: SourceCardProps) {
  return (
    <div className="text-sm border border-slate-100 bg-slate-50 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-slate-600">{source.document_title}</span>
        <span className="text-xs text-slate-400">
          chunk {source.chunk_index} · {(source.similarity * 100).toFixed(1)}% match
        </span>
      </div>
      <p className="text-slate-500 line-clamp-3">{source.content}</p>
    </div>
  );
}
