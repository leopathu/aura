"use client";

import { useState } from "react";
import { queryService } from "@/services/query-service";
import { useQueryStore } from "@/store/query-store";
import { getErrorMessage } from "@/lib/api-client";
import type { QueryResponse } from "@/types";

interface UseQueryReturn {
  submit: (question: string, topK?: number) => Promise<QueryResponse | null>;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook that wraps the RAG query service with loading and error state.
 */
export function useQuery(): UseQueryReturn {
  const [error, setError] = useState<string | null>(null);
  const { addEntry, setLoading, isLoading } = useQueryStore();

  const submit = async (question: string, topK = 5): Promise<QueryResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await queryService.query({ query: question, top_k: topK });
      addEntry({ question, response, timestamp: new Date() });
      return response;
    } catch (err) {
      setError(getErrorMessage(err));
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { submit, isLoading, error };
}
