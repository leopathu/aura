/**
 * Agent chat service — manages agent conversations and SSE streaming.
 */
import { apiClient } from "@/lib/api-client";
import type { ConversationSummary, ConversationDetail, AgentSourceChunk } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface AgentStreamMetaEvent {
  type: "meta";
  conversation_id: string;
  sources: AgentSourceChunk[];
}

export interface AgentStreamTokenEvent {
  type: "token";
  token: string;
}

export interface AgentStreamDoneEvent {
  type: "done";
}

export interface AgentStreamErrorEvent {
  type: "error";
  message: string;
}

export type AgentStreamEvent =
  | AgentStreamMetaEvent
  | AgentStreamTokenEvent
  | AgentStreamDoneEvent
  | AgentStreamErrorEvent;

export const agentChatService = {
  /** List conversations for an agent. */
  listConversations: async (agentId: string): Promise<ConversationSummary[]> => {
    const res = await apiClient.get<ConversationSummary[]>(
      `/agents/${agentId}/chat/conversations`
    );
    return res.data;
  },

  /** Create a new agent conversation. */
  createConversation: async (
    agentId: string,
    title?: string
  ): Promise<ConversationSummary> => {
    const res = await apiClient.post<ConversationSummary>(
      `/agents/${agentId}/chat/conversations`,
      { title: title ?? "New Chat" }
    );
    return res.data;
  },

  /** Fetch full agent conversation with messages. */
  getConversation: async (
    agentId: string,
    conversationId: string
  ): Promise<ConversationDetail> => {
    const res = await apiClient.get<ConversationDetail>(
      `/agents/${agentId}/chat/conversations/${conversationId}`
    );
    return res.data;
  },

  /** Delete an agent conversation. */
  deleteConversation: async (
    agentId: string,
    conversationId: string
  ): Promise<void> => {
    await apiClient.delete(
      `/agents/${agentId}/chat/conversations/${conversationId}`
    );
  },

  /**
   * Stream a chat response. Calls onEvent for each SSE event.
   * Returns a cleanup function that aborts the stream.
   */
  streamChat: (
    params: {
      agent_id: string;
      message: string;
      conversation_id?: string;
    },
    onEvent: (event: AgentStreamEvent) => void
  ): (() => void) => {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

    const controller = new AbortController();

    fetch(`${BASE_URL}/api/v1/agents/${params.agent_id}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        message: params.message,
        ...(params.conversation_id
          ? { conversation_id: params.conversation_id }
          : {}),
      }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const text = await response.text();
          onEvent({ type: "error", message: text || "Stream request failed" });
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          onEvent({ type: "error", message: "No response body" });
          return;
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const event = JSON.parse(line.slice(6)) as AgentStreamEvent;
                onEvent(event);
              } catch {
                // skip malformed line
              }
            }
          }
        }
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name !== "AbortError") {
          onEvent({ type: "error", message: err.message });
        }
      });

    return () => controller.abort();
  },
};
