"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";
import { Navbar } from "@/components/Navbar";

/**
 * Wraps pages that require authentication.
 * Redirects unauthenticated users to /login.
 */
export function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const router = useRouter();

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [token, router]);

  if (!token) return null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <div className="flex-1">{children}</div>
    </div>
  );
}
