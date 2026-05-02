"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authService } from "@/services/auth-service";
import { useAuthStore } from "@/store/auth-store";
import { getErrorMessage } from "@/lib/api-client";
import type { UserCreate, UserLogin } from "@/types";

interface UseAuthReturn {
  login: (payload: UserLogin) => Promise<boolean>;
  register: (payload: UserCreate) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook that wraps auth actions with loading/error state and navigation.
 */
export function useAuth(): UseAuthReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setAuth, clearAuth, token } = useAuthStore();
  const router = useRouter();

  const login = async (payload: UserLogin): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      const tokenData = await authService.login(payload);
      // Persist token before calling /me so the interceptor can attach it naturally
      localStorage.setItem("access_token", tokenData.access_token);
      const user = await authService.me(tokenData.access_token);
      setAuth(user, tokenData.access_token);
      router.push("/query");
      return true;
    } catch (err) {
      setError(getErrorMessage(err));
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: UserCreate): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.register(payload);
      // Auto-login after registration
      return await login({ email: payload.email, password: payload.password });
    } catch (err) {
      setError(getErrorMessage(err));
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearAuth();
    router.push("/login");
  };

  return { login, register, logout, isLoading, error };
}
