import { create } from "zustand";
import { User } from "@/types";

interface AuthState {
  token: string | null;
  user: User | null;
  organizationId: string | null;
  organizationName: string | null;
  setAuth: (token: string, user: User, orgId: string, orgName: string) => void;
  setOrganization: (orgId: string, orgName: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: typeof window !== "undefined" ? localStorage.getItem("aura_token") : null,
  user: typeof window !== "undefined" ? JSON.parse(localStorage.getItem("aura_user") || "null") : null,
  organizationId: typeof window !== "undefined" ? localStorage.getItem("aura_org_id") : null,
  organizationName: typeof window !== "undefined" ? localStorage.getItem("aura_org_name") : null,

  setAuth: (token, user, orgId, orgName) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("aura_token", token);
      localStorage.setItem("aura_user", JSON.stringify(user));
      localStorage.setItem("aura_org_id", orgId);
      localStorage.setItem("aura_org_name", orgName);
    }
    set({ token, user, organizationId: orgId, organizationName: orgName });
  },

  setOrganization: (orgId, orgName) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("aura_org_id", orgId);
      localStorage.setItem("aura_org_name", orgName);
    }
    set({ organizationId: orgId, organizationName: orgName });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("aura_token");
      localStorage.removeItem("aura_user");
      localStorage.removeItem("aura_org_id");
      localStorage.removeItem("aura_org_name");
    }
    set({ token: null, user: null, organizationId: null, organizationName: null });
  },
}));
