"use client";

/**
 * Zustand store for the selected agent.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Agent } from "@/types";

interface AgentStore {
  selectedAgent: Agent | null;
  setSelectedAgent: (agent: Agent | null) => void;
}

export const useAgentStore = create<AgentStore>()(
  persist(
    (set) => ({
      selectedAgent: null,
      setSelectedAgent: (agent) => set({ selectedAgent: agent }),
    }),
    {
      name: "aura-agent",
      partialize: (state) => ({ selectedAgent: state.selectedAgent }),
    }
  )
);
