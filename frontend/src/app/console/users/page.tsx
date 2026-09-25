"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { Users, Shield, Plus, Check } from "lucide-react";

export default function UsersPage() {
  const [members, setMembers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMembers();
  }, []);

  const loadMembers = async () => {
    setLoading(true);
    try {
      const [mList, rList] = await Promise.all([
        apiRequest<any[]>("/organizations/users"),
        apiRequest<any[]>("/rbac/roles"),
      ]);
      setMembers(mList);
      setRoles(rList);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId: string, roleId: string) => {
    try {
      await apiRequest("/rbac/assign", {
        method: "POST",
        body: JSON.stringify({ user_id: userId, role_id: roleId }),
      });
      loadMembers();
    } catch (err: any) {
      alert(err.message || "Failed to update role");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Organization Team Members</h1>
          <p className="mt-1 text-sm text-slate-400">
            Manage organization users, memberships, and assigned operational roles.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 shadow-sm overflow-hidden">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900/90 border-b border-slate-800 text-[11px] font-semibold uppercase text-slate-400">
            <tr>
              <th className="px-6 py-3.5">User</th>
              <th className="px-6 py-3.5">Email</th>
              <th className="px-6 py-3.5">Status</th>
              <th className="px-6 py-3.5">Assigned Role</th>
              <th className="px-6 py-3.5">Joined Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {members.map((m) => (
              <tr key={m.id} className="hover:bg-slate-900/80">
                <td className="px-6 py-4 font-semibold text-white flex items-center space-x-2">
                  <div className="h-6 w-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-[10px] text-slate-300">
                    {m.name[0]}
                  </div>
                  <span>{m.name}</span>
                </td>
                <td className="px-6 py-4 font-mono text-slate-400">{m.email}</td>
                <td className="px-6 py-4">
                  <span className="rounded bg-emerald-500/10 text-emerald-400 px-2 py-0.5 text-[10px] font-bold border border-emerald-500/20">
                    {m.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <select
                    value={m.role?.id || ""}
                    onChange={(e) => handleRoleChange(m.id, e.target.value)}
                    className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-white focus:outline-none focus:border-aura-500"
                  >
                    <option value="" disabled>Select Role</option>
                    {roles.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-6 py-4 text-slate-400">
                  {m.joined_at ? new Date(m.joined_at).toLocaleDateString() : "Active"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
