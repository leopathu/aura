/**
 * Settings service — AI model configuration API calls.
 */
import { apiClient } from "@/lib/api-client";
import type { AISettingsResponse, AISettingsUpdate } from "@/types";

export const settingsService = {
  /** Fetch current user's AI settings (returns defaults if not yet configured). */
  async get(): Promise<AISettingsResponse> {
    const { data } = await apiClient.get<AISettingsResponse>("/settings");
    return data;
  },

  /** Create or update current user's AI settings. */
  async update(payload: AISettingsUpdate): Promise<AISettingsResponse> {
    const { data } = await apiClient.put<AISettingsResponse>("/settings", payload);
    return data;
  },
};
