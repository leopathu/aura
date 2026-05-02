/** Shared TypeScript types for the Aura RAG system. */

export interface Document {
  id: string;
  title: string;
  source: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreate {
  title: string;
  source?: string;
  content: string;
}

export interface IngestResponse {
  document_id: string;
  chunks_created: number;
}

export interface SourceChunk {
  document_title: string;
  chunk_index: number;
  content: string;
  similarity: number;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
}

export interface QueryResponse {
  answer: string;
  sources: SourceChunk[];
}

export interface ApiError {
  detail: string;
  code: string;
}
