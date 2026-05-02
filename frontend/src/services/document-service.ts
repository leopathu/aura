/**
 * Document service — all HTTP calls related to document ingestion and management.
 */
import { apiClient } from "@/lib/api-client";
import type { Document, DocumentCreate, IngestResponse } from "@/types";

export const documentService = {
  /** Ingest a new document into the RAG pipeline. */
  async ingest(payload: DocumentCreate): Promise<IngestResponse> {
    const { data } = await apiClient.post<IngestResponse>("/documents/", payload);
    return data;
  },

  /** Fetch a paginated list of all documents. */
  async list(limit = 50, offset = 0): Promise<Document[]> {
    const { data } = await apiClient.get<Document[]>("/documents/", {
      params: { limit, offset },
    });
    return data;
  },

  /** Fetch a single document by UUID. */
  async getById(id: string): Promise<Document> {
    const { data } = await apiClient.get<Document>(`/documents/${id}`);
    return data;
  },

  /** Delete a document by UUID. */
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`);
  },

  /** Upload a file (PDF, DOCX, XLSX, CSV, TXT) and ingest it into the RAG pipeline. */
  async uploadFile(file: File): Promise<IngestResponse> {
    const form = new FormData();
    form.append("file", file);
    const { data } = await apiClient.post<IngestResponse>("/documents/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
};
