/**
 * Query service — HTTP call for RAG queries.
 */
import { apiClient } from "@/lib/api-client";
import type { QueryRequest, QueryResponse } from "@/types";

export const queryService = {
  /** Send a question to the RAG pipeline and receive an answer with sources. */
  async query(payload: QueryRequest): Promise<QueryResponse> {
    const { data } = await apiClient.post<QueryResponse>("/query/", payload);
    return data;
  },
};
