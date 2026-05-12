"use client";

/**
 * Zustand store for authentication state.
 * Token is persisted to localStorage so sessions survive page refreshes.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthStore {
  user: User | null;
  token: string | null;
  _hasHydrated: boolean;
  setHasHydrated: (v: boolean) => void;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      _hasHydrated: false,
      setHasHydrated: (v) => set({ _hasHydrated: v }),
      setAuth: (user, token) => {
        // Also write to localStorage so the Axios interceptor can read it
        localStorage.setItem("access_token", token);
        set({ user, token });
      },
      clearAuth: () => {
        localStorage.removeItem("access_token");
        set({ user: null, token: null });
      },
    }),
    {
      name: "aura-auth",
      partialize: (state) => ({ user: state.user, token: state.token }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
        // Keep localStorage in sync so the Axios interceptor always has the token
        if (state?.token) {
          localStorage.setItem("access_token", state.token);
        }
      },
    }
  )
);
