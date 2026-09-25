"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { RoleItem } from "@/types";
import { Key, Plus, ShieldCheck, Check } from "lucide-react";

export default function RolesPage() {
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [permissions, setPermissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedPerms, setSelectedPerms] = useState<string[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [rData, pData] = await Promise.all([
        apiRequest<RoleItem[]>("/rbac/roles"),
        apiRequest<any[]>("/rbac/permissions"),
      ]);
      setRoles(rData);
      setPermissions(pData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const togglePermission = (code: string) => {
    setSelectedPerms((prev) =>
      prev.includes(code) ? prev.filter((p) => p !== code) : [...prev, code]
    );
  };

  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/rbac/roles", {
        method: "POST",
        body: JSON.stringify({
          name,
          description,
          permission_codes: selectedPerms,
        }),
      });
      setShowModal(false);
      setName("");
      setDescription("");
      setSelectedPerms([]);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create role");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Roles & Permissions (RBAC)</h1>
          <p className="mt-1 text-sm text-slate-400">
            Define fine-grained custom roles and manage authorization access across resources.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-aura-500 transition"
        >
          <Plus className="h-4 w-4" />
          <span>Create Custom Role</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {roles.map((r) => (
          <div key={r.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Key className="h-5 w-5 text-aura-400" />
                <h3 className="font-bold text-base text-white">{r.name}</h3>
              </div>
              <span
                className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                  r.is_system
                    ? "bg-slate-800 text-slate-400 border border-slate-700"
                    : "bg-aura-500/10 text-aura-300 border border-aura-500/20"
                }`}
              >
                {r.is_system ? "SYSTEM" : "CUSTOM"}
              </span>
            </div>

            <p className="text-xs text-slate-400">{r.description || "No description provided."}</p>

            <div>
              <div className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider mb-2">
                Permissions ({r.permissions.length})
              </div>
              <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
                {r.permissions.map((pCode) => (
                  <span
                    key={pCode}
                    className="rounded bg-slate-800/80 border border-slate-700/80 px-2 py-0.5 font-mono text-[10px] text-slate-300"
                  >
                    {pCode}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-white">Create Custom Role</h3>
            <form onSubmit={handleCreateRole} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Role Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Finance Analyst"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Role responsibilities..."
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-2">
                  Assign Permissions
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto border border-slate-800 rounded-lg p-2 bg-slate-950/60">
                  {permissions.map((perm) => {
                    const checked = selectedPerms.includes(perm.code);
                    return (
                      <div
                        key={perm.code}
                        onClick={() => togglePermission(perm.code)}
                        className={`flex items-center space-x-2 p-2 rounded-lg cursor-pointer text-xs transition border ${
                          checked
                            ? "bg-aura-600/20 border-aura-500/40 text-white"
                            : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800"
                        }`}
                      >
                        <div
                          className={`h-4 w-4 rounded flex items-center justify-center border ${
                            checked ? "bg-aura-600 border-aura-500 text-white" : "border-slate-700"
                          }`}
                        >
                          {checked && <Check className="h-3 w-3" />}
                        </div>
                        <span className="font-mono text-[11px] truncate">{perm.code}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-aura-600 px-4 py-2 text-xs font-medium text-white hover:bg-aura-500"
                >
                  Create Role
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
