"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useAuthStore } from "@/store/auth-store";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/brains" as const, label: "Brains" },
  { href: "/settings" as const, label: "Settings" },
];

/**
 * Top navigation bar shown on all authenticated pages.
 */
export function Navbar() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();

  return (
    <nav className="border-b border-slate-200 bg-white px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <Link href="/" className="text-lg font-bold text-brand-700">
          Aura
        </Link>
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                pathname === href
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"
              )}
            >
              {label}
            </Link>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <span className="text-xs text-slate-400 hidden sm:block">{user.email}</span>
        )}
        <button
          onClick={logout}
          className="text-sm text-slate-500 hover:text-red-600 transition-colors font-medium"
        >
          Sign Out
        </button>
      </div>
    </nav>
  );
}
