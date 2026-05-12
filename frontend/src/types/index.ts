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

// ---------------------------------------------------------------------------
// Chat / Conversations
// ---------------------------------------------------------------------------

export interface ConversationSummary {
  id: string;
  brain_id: string | null;
  agent_id: string | null;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources_json: string | null;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  brain_id: string | null;
  agent_id: string | null;
  title: string;
  messages: ChatMessageData[];
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Agents
// ---------------------------------------------------------------------------

export type AppType =
  | "gmail"
  | "gdrive"
  | "jira"
  | "slack"
  | "notion"
  | "github"
  | "confluence"
  | "linear";

export type SyncStatus = "idle" | "syncing" | "error";
export type EmbedStatus = "pending" | "processing" | "ready" | "failed";

export interface Agent {
  id: string;
  name: string;
  description: string | null;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  description?: string | undefined;
}

export interface AgentUpdate {
  name?: string | undefined;
  description?: string | undefined;
}

export interface AgentConnection {
  id: string;
  agent_id: string;
  app_type: AppType;
  display_name: string;
  sync_status: SyncStatus;
  sync_error: string | null;
  last_synced_at: string | null;
  sync_interval_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface AgentConnectionCreate {
  app_type: AppType;
  display_name: string;
  sync_interval_minutes?: number;
}

export interface AgentDocument {
  id: string;
  agent_id: string;
  agent_connection_id: string;
  external_id: string;
  title: string;
  source_url: string | null;
  embed_status: EmbedStatus;
  embed_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentSourceChunk {
  document_title: string;
  source_url: string | null;
  app_type: string;
  chunk_index: number;
  content: string;
  similarity: number;
}

export interface SyncStatusResponse {
  connection_id: string;
  sync_status: SyncStatus;
  last_synced_at: string | null;
  sync_error: string | null;
  total_docs: number;
  ready_docs: number;
}

export interface SyncLogEntry {
  id: string;
  connection_id: string;
  started_at: string;
  finished_at: string | null;
  items_total: number;
  items_changed: number;
  items_failed: number;
  error: string | null;
}
