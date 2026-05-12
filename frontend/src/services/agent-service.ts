/**
 * Agent service — CRUD for agents, connections, documents, and sync operations.
 */
import { apiClient } from "@/lib/api-client";
import type {
  Agent,
  AgentCreate,
  AgentUpdate,
  AgentConnection,
  AgentConnectionCreate,
  AgentDocument,
  SyncStatusResponse,
  SyncLogEntry,
} from "@/types";

export const agentService = {
  // ── Agents ────────────────────────────────────────────────────────────────

  /** List all agents for the authenticated user. */
  async list(): Promise<Agent[]> {
    const { data } = await apiClient.get<Agent[]>("/agents");
    return data;
  },

  /** Create a new agent. */
  async create(payload: AgentCreate): Promise<Agent> {
    const { data } = await apiClient.post<Agent>("/agents", payload);
    return data;
  },

  /** Update an agent's name or description. */
  async update(agentId: string, payload: AgentUpdate): Promise<Agent> {
    const { data } = await apiClient.patch<Agent>(`/agents/${agentId}`, payload);
    return data;
  },

  /** Delete an agent. */
  async remove(agentId: string): Promise<void> {
    await apiClient.delete(`/agents/${agentId}`);
  },

  // ── Connections ───────────────────────────────────────────────────────────

  /** List all connections for an agent. */
  async listConnections(agentId: string): Promise<AgentConnection[]> {
    const { data } = await apiClient.get<AgentConnection[]>(
      `/agents/${agentId}/connections`
    );
    return data;
  },

  /** Create a new connection (returns connection with id for OAuth). */
  async createConnection(
    agentId: string,
    payload: AgentConnectionCreate
  ): Promise<AgentConnection> {
    const { data } = await apiClient.post<AgentConnection>(
      `/agents/${agentId}/connections`,
      payload
    );
    return data;
  },

  /** Get OAuth start URL for a connection. */
  async getOAuthStartUrl(
    agentId: string,
    connId: string
  ): Promise<{ url: string }> {
    const { data } = await apiClient.get<{ url: string }>(
      `/agents/${agentId}/connections/${connId}/oauth/start`
    );
    return data;
  },

  /** Delete a connection. */
  async removeConnection(agentId: string, connId: string): Promise<void> {
    await apiClient.delete(`/agents/${agentId}/connections/${connId}`);
  },

  // ── Sync ──────────────────────────────────────────────────────────────────

  /** Trigger an immediate manual sync. */
  async triggerSync(agentId: string, connId: string): Promise<void> {
    await apiClient.post(`/agents/${agentId}/connections/${connId}/sync`);
  },

  /** Get sync status for a connection. */
  async getSyncStatus(
    agentId: string,
    connId: string
  ): Promise<SyncStatusResponse> {
    const { data } = await apiClient.get<SyncStatusResponse>(
      `/agents/${agentId}/connections/${connId}/sync/status`
    );
    return data;
  },

  /** Get sync history for a connection. */
  async getSyncHistory(
    agentId: string,
    connId: string
  ): Promise<SyncLogEntry[]> {
    const { data } = await apiClient.get<SyncLogEntry[]>(
      `/agents/${agentId}/connections/${connId}/sync/history`
    );
    return data;
  },

  // ── Documents ─────────────────────────────────────────────────────────────

  /** List all synced documents for an agent. */
  async listDocuments(agentId: string): Promise<AgentDocument[]> {
    const { data } = await apiClient.get<AgentDocument[]>(
      `/agents/${agentId}/documents`
    );
    return data;
  },
};
