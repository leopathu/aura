"use client";

import { useState, useEffect, useCallback } from "react";
import { agentService } from "@/services/agent-service";
import { useAgentStore } from "@/store/agent-store";
import { getErrorMessage } from "@/lib/api-client";
import type { Agent, AgentCreate } from "@/types";

/** Hook for listing, creating, and deleting agents. */
export function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { selectedAgent, setSelectedAgent } = useAgentStore();

  const fetchAgents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await agentService.list();
      setAgents(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const createAgent = async (payload: AgentCreate): Promise<Agent | null> => {
    try {
      const agent = await agentService.create(payload);
      setAgents((prev) => [...prev, agent]);
      setSelectedAgent(agent);
      return agent;
    } catch (err) {
      setError(getErrorMessage(err));
      return null;
    }
  };

  const deleteAgent = async (agentId: string): Promise<void> => {
    try {
      await agentService.remove(agentId);
      setAgents((prev) => prev.filter((a) => a.id !== agentId));
      if (selectedAgent?.id === agentId) {
        setSelectedAgent(null);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return {
    agents,
    isLoading,
    error,
    selectedAgent,
    setSelectedAgent,
    createAgent,
    deleteAgent,
    refetch: fetchAgents,
  };
}
