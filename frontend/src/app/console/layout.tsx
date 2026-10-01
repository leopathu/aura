"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import Link from "next/link";
import {
  LayoutDashboard,
  BrainCircuit,
  Cpu,
  ShieldCheck,
  Users,
  Key,
  FolderOpen,
  ClipboardList,
  Server,
  MessageSquare,
  LogOut
} from "lucide-react";

export default function ConsoleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { token, user, organizationName, logout } = useAuthStore();

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    // Verify token validity against current backend instance
    fetch("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok && res.status === 401) {
          logout();
          router.push("/login?expired=true");
        }
      })
      .catch(() => {});
  }, [token, router, logout]);

  const navItems = [
    { label: "Dashboard", href: "/console", icon: LayoutDashboard },
    { label: "Brains", href: "/console/brains", icon: BrainCircuit },
    { label: "AI Models", href: "/console/models", icon: Cpu },
    { label: "Policy Engine", href: "/console/policies", icon: ShieldCheck },
    { label: "Roles & RBAC", href: "/console/roles", icon: Key },
    { label: "Team Members", href: "/console/users", icon: Users },
    { label: "MCP Servers", href: "/console/mcp", icon: Server },
    { label: "Reports", href: "/console/reports", icon: FolderOpen },
    { label: "Audit Logs", href: "/console/audit", icon: ClipboardList },
  ];

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Console Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/60 flex flex-col justify-between">
        <div>
          {/* Logo */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-aura-600 font-bold text-white shadow shadow-aura-500/20">
                A
              </div>
              <div>
                <span className="font-bold text-base text-white">Aura Console</span>
                <span className="block text-[10px] text-slate-400">{organizationName || "Acme Corp"}</span>
              </div>
            </Link>
          </div>

          {/* Quick Chat Link */}
          <div className="p-3">
            <Link
              href="/chat"
              className="flex items-center space-x-2 w-full rounded-lg bg-aura-600/20 border border-aura-500/30 px-3 py-2 text-xs font-semibold text-aura-300 hover:bg-aura-600/30 transition"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Go to AI Chat</span>
            </Link>
          </div>

          {/* Nav Links */}
          <nav className="p-3 space-y-1">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 px-3 py-1">
              Management
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-2.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
                    isActive
                      ? "bg-aura-600 text-white shadow"
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User bar */}
        <div className="p-3 border-t border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center space-x-2 truncate">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300">
              {user?.name?.[0] || "U"}
            </div>
            <div className="truncate text-xs">
              <div className="font-medium text-slate-200 truncate">{user?.name}</div>
              <div className="text-[10px] text-slate-400 truncate">{user?.email}</div>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition"
            title="Log out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  );
}
