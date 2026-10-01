import { useAuthStore } from "@/store/authStore";

const API_BASE = "/api/v1";

export async function apiRequest<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : null;
  const orgId = typeof window !== "undefined" ? localStorage.getItem("aura_org_id") : null;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (orgId) {
    headers["X-Organization-Id"] = orgId;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      try {
        useAuthStore.getState().logout();
      } catch {}
      if (!window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/register")) {
        window.location.href = "/login?expired=true";
      }
    }
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}

export async function streamAgentChat(
  conversationId: string,
  content: string,
  onEvent: (event: string, data: any) => void,
  brainId?: string
): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : null;
  const orgId = typeof window !== "undefined" ? localStorage.getItem("aura_org_id") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (orgId) headers["X-Organization-Id"] = orgId;

  const res = await fetch(`${API_BASE}/chat/conversations/${conversationId}/messages`, {
    method: "POST",
    headers,
    body: JSON.stringify({ content, brain_id: brainId || undefined }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to start streaming");
  }

  const reader = res.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const chunk of lines) {
      if (!chunk.trim()) continue;
      const eventMatch = chunk.match(/event:\s*(.+)/);
      const dataMatch = chunk.match(/data:\s*(.+)/);

      const eventType = eventMatch ? eventMatch[1].trim() : "message";
      const rawData = dataMatch ? dataMatch[1].trim() : "{}";

      try {
        const parsed = JSON.parse(rawData);
        onEvent(eventType, parsed);
      } catch (e) {
        onEvent(eventType, rawData);
      }
    }
  }
}
