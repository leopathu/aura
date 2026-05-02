/** Shared TypeScript types for the Aura RAG system. */

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

export interface Document {
  id: string;
  title: string;
  source: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreate {
  title: string;
  source?: string | undefined;
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
