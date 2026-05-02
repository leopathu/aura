"use client";

/**
 * Zustand store for the selected brain.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Brain } from "@/types";

interface BrainStore {
  selectedBrain: Brain | null;
  setSelectedBrain: (brain: Brain | null) => void;
}

export const useBrainStore = create<BrainStore>()(
  persist(
    (set) => ({
      selectedBrain: null,
      setSelectedBrain: (brain) => set({ selectedBrain: brain }),
    }),
    {
      name: "aura-brain",
      partialize: (state) => ({ selectedBrain: state.selectedBrain }),
    }
  )
);
