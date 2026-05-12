"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { useAuthStore } from "@/store/auth-store";

export default function LoginPage() {
  const token = useAuthStore((s) => s.token);
  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const router = useRouter();

  useEffect(() => {
    if (hasHydrated && token) {
      router.replace("/brains");
    }
  }, [hasHydrated, token, router]);

  // Show nothing while hydrating or if already logged in
  if (!hasHydrated || token) return null;

  return <AuthForm mode="login" />;
}
