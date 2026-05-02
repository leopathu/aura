"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

/**
 * Reusable auth form used by both login and register pages.
 */
interface AuthFormProps {
  mode: "login" | "register";
}

export function AuthForm({ mode }: AuthFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, register, isLoading, error } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "login") {
      await login({ email, password });
    } else {
      await register({ email, password });
    }
  };

  const inputClass = cn(
    "w-full border border-slate-300 rounded-lg px-4 py-2.5 text-sm outline-none",
    "focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors"
  );

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-brand-700">Aura</h1>
          <p className="text-slate-500 mt-1 text-sm">
            {mode === "login" ? "Sign in to your account" : "Create your account"}
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8 flex flex-col gap-5"
        >
          <h2 className="text-lg font-semibold text-slate-700">
            {mode === "login" ? "Sign In" : "Register"}
          </h2>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-500">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-500">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
              placeholder={mode === "register" ? "At least 8 characters" : "••••••••"}
              required
              minLength={8}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={cn(
              "w-full py-2.5 bg-brand-600 text-white rounded-lg font-medium text-sm",
              "hover:bg-brand-700 transition-colors",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {isLoading
              ? mode === "login"
                ? "Signing in…"
                : "Creating account…"
              : mode === "login"
                ? "Sign In"
                : "Create Account"}
          </button>

          <p className="text-center text-sm text-slate-500">
            {mode === "login" ? (
              <>
                No account?{" "}
                <Link href="/register" className="text-brand-600 hover:underline font-medium">
                  Register
                </Link>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <Link href="/login" className="text-brand-600 hover:underline font-medium">
                  Sign In
                </Link>
              </>
            )}
          </p>
        </form>
      </div>
    </div>
  );
}
