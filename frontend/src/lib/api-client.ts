/**
 * Typed Axios client for the Aura FastAPI backend.
 * All service files should import from this module, never use raw fetch/axios in components.
 */
import axios, { AxiosError } from "axios";
import type { ApiError } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

// Attach Bearer token from localStorage on every request (client-side only)
// Only set if not already explicitly provided by the caller.
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined" && !config.headers.Authorization) {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

/** Extract a human-readable error message from an Axios error. */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiError | undefined;
    return data?.detail ?? error.message;
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
}
