"use client";

/**
 * Zustand store for managing the RAG query state (chat-like interface).
 */
import { create } from "zustand";
import type { QueryResponse } from "@/types";

interface QueryHistoryEntry {
  question: string;
  response: QueryResponse;
  timestamp: Date;
}

interface QueryStore {
  history: QueryHistoryEntry[];
  isLoading: boolean;
  addEntry: (entry: QueryHistoryEntry) => void;
  setLoading: (loading: boolean) => void;
  clearHistory: () => void;
}

export const useQueryStore = create<QueryStore>((set) => ({
  history: [],
  isLoading: false,
  addEntry: (entry) => set((state) => ({ history: [...state.history, entry] })),
  setLoading: (loading) => set({ isLoading: loading }),
  clearHistory: () => set({ history: [] }),
}));
