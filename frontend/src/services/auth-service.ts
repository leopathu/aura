/**
 * Auth service — register, login, and fetch current user.
 */
import { apiClient } from "@/lib/api-client";
import type { Token, User, UserCreate, UserLogin } from "@/types";

export const authService = {
  /** Register a new user account. */
  async register(payload: UserCreate): Promise<User> {
    const { data } = await apiClient.post<User>("/auth/register", payload);
    return data;
  },

  /** Authenticate and receive a JWT token. */
  async login(payload: UserLogin): Promise<Token> {
    const { data } = await apiClient.post<Token>("/auth/login", payload);
    return data;
  },

  /** Fetch the profile of the currently authenticated user. */
  async me(token: string): Promise<User> {
    const { data } = await apiClient.get<User>("/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
};
