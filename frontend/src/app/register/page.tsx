"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { useAuthStore } from "@/store/auth-store";

export default function RegisterPage() {
  const token = useAuthStore((s) => s.token);
  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const router = useRouter();

  useEffect(() => {
    if (hasHydrated && token) {
      router.replace("/brains");
    }
  }, [hasHydrated, token, router]);

  if (!hasHydrated || token) return null;

  return <AuthForm mode="register" />;
}
