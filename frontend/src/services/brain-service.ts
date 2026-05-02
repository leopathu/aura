/**
 * Brain service — CRUD and document association calls to FastAPI.
 */
import { apiClient } from "@/lib/api-client";
import type { Brain, BrainCreate, BrainDocument, BrainUpdate } from "@/types";

export const brainService = {
  /** List all brains for the authenticated user. */
  async list(): Promise<Brain[]> {
    const { data } = await apiClient.get<Brain[]>("/brains");
    return data;
  },

  /** Create a new brain. */
  async create(payload: BrainCreate): Promise<Brain> {
    const { data } = await apiClient.post<Brain>("/brains", payload);
    return data;
  },

  /** Update a brain's name or description. */
  async update(brainId: string, payload: BrainUpdate): Promise<Brain> {
    const { data } = await apiClient.patch<Brain>(`/brains/${brainId}`, payload);
    return data;
  },

  /** Delete a brain. */
  async remove(brainId: string): Promise<void> {
    await apiClient.delete(`/brains/${brainId}`);
  },

  /** List documents connected to a brain. */
  async listDocuments(brainId: string): Promise<BrainDocument[]> {
    const { data } = await apiClient.get<BrainDocument[]>(`/brains/${brainId}/documents`);
    return data;
  },

  /** Attach a document to a brain. */
  async addDocument(brainId: string, documentId: string): Promise<void> {
    await apiClient.post(`/brains/${brainId}/documents/${documentId}`);
  },

  /** Detach a document from a brain. */
  async removeDocument(brainId: string, documentId: string): Promise<void> {
    await apiClient.delete(`/brains/${brainId}/documents/${documentId}`);
  },
};
