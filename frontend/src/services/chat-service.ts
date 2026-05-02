/**
 * Chat service — manages conversations and streaming SSE chat.
 */
import { apiClient } from "@/lib/api-client";
import type { ConversationSummary, ConversationDetail, SourceChunk } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface StreamMetaEvent {
  type: "meta";
  conversation_id: string;
  sources: SourceChunk[];
}

export interface StreamTokenEvent {
  type: "token";
  token: string;
}

export interface StreamDoneEvent {
  type: "done";
}

export interface StreamErrorEvent {
  type: "error";
  message: string;
}

export type StreamEvent = StreamMetaEvent | StreamTokenEvent | StreamDoneEvent | StreamErrorEvent;

export const chatService = {
  /** List conversations for a brain. */
  listConversations: async (brainId: string): Promise<ConversationSummary[]> => {
    const res = await apiClient.get<ConversationSummary[]>("/chat/conversations", {
      params: { brain_id: brainId },
    });
    return res.data;
  },

  /** Create a new conversation. */
  createConversation: async (brainId: string, title?: string): Promise<ConversationSummary> => {
    const res = await apiClient.post<ConversationSummary>("/chat/conversations", {
      brain_id: brainId,
      title: title ?? "New Chat",
    });
    return res.data;
  },

  /** Fetch full conversation with messages. */
  getConversation: async (conversationId: string): Promise<ConversationDetail> => {
    const res = await apiClient.get<ConversationDetail>(`/chat/conversations/${conversationId}`);
    return res.data;
  },

  /** Delete a conversation. */
  deleteConversation: async (conversationId: string): Promise<void> => {
    await apiClient.delete(`/chat/conversations/${conversationId}`);
  },

  /**
   * Stream a chat response. Calls onEvent for each SSE event.
   * Returns a cleanup function (aborts the stream).
   */
  streamChat: (
    params: {
      brain_id: string;
      message: string;
      conversation_id?: string;
      top_k?: number;
    },
    onEvent: (event: StreamEvent) => void,
  ): (() => void) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

    const controller = new AbortController();

    fetch(`${BASE_URL}/api/v1/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(params),
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
                const event = JSON.parse(line.slice(6)) as StreamEvent;
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
