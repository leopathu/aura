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

// ---------------------------------------------------------------------------
// Brains
// ---------------------------------------------------------------------------

export interface Brain {
  id: string;
  name: string;
  description: string | null;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface BrainCreate {
  name: string;
  description?: string | undefined;
}

export interface BrainUpdate {
  name?: string | undefined;
  description?: string | undefined;
}

export interface BrainDocument {
  id: string;
  title: string;
  source: string | null;
  embed_status: "pending" | "processing" | "ready" | "failed";
  embed_error: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

export interface SourceChunk {
  document_title: string;
  chunk_index: number;
  content: string;
  similarity: number;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
  brain_id?: string | undefined;
}

export interface QueryResponse {
  answer: string;
  sources: SourceChunk[];
}

export interface ApiError {
  detail: string;
  code: string;
}

// ---------------------------------------------------------------------------
// AI Settings
// ---------------------------------------------------------------------------

export type LLMProvider = "openai" | "anthropic" | "google" | "ollama";
export type EmbeddingProvider = "openai" | "google" | "ollama";

export interface AISettingsUpdate {
  llm_provider: LLMProvider;
  llm_model: string;
  llm_api_key: string;
  llm_base_url: string;
  temperature: number;
  embedding_provider: EmbeddingProvider;
  embedding_model: string;
  embedding_api_key: string;
  embedding_base_url: string;
  chunk_size: number;
  chunk_overlap: number;
  retrieval_top_k: number;
}

export interface AISettingsResponse {
  llm_provider: LLMProvider;
  llm_model: string;
  llm_api_key_set: boolean;
  llm_base_url: string;
  temperature: number;
  embedding_provider: EmbeddingProvider;
  embedding_model: string;
  embedding_api_key_set: boolean;
  embedding_base_url: string;
  chunk_size: number;
  chunk_overlap: number;
  retrieval_top_k: number;
}
