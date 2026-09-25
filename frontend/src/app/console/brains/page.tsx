"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { BrainItem, RoleItem, DataSource, DocumentItem } from "@/types";
import {
  BrainCircuit,
  Plus,
  Shield,
  Database,
  FileText,
  Users,
  CheckCircle,
  AlertCircle,
  Trash2,
  Settings,
  Layers
} from "lucide-react";

export default function BrainsPage() {
  const [brains, setBrains] = useState<BrainItem[]>([]);
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // Create Brain Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Assign Roles Modal State
  const [showRolesModal, setShowRolesModal] = useState(false);
  const [activeBrain, setActiveBrain] = useState<BrainItem | null>(null);
  const [modalRoleIds, setModalRoleIds] = useState<string[]>([]);

  // Connect Resources Modal State
  const [showResourcesModal, setShowResourcesModal] = useState(false);
  const [modalSourceIds, setModalSourceIds] = useState<string[]>([]);
  const [modalDocIds, setModalDocIds] = useState<string[]>([]);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [brainsData, rolesData, sourcesData, docsData] = await Promise.all([
        apiRequest<BrainItem[]>("/brains"),
        apiRequest<RoleItem[]>("/roles"),
        apiRequest<DataSource[]>("/sources"),
        apiRequest<DocumentItem[]>("/documents"),
      ]);
      setBrains(brainsData);
      setRoles(rolesData);
      setSources(sourcesData);
      setDocuments(docsData);
    } catch (err: any) {
      console.error("Failed to load brain management data", err);
      setStatusMsg(`Error loading data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBrain = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setStatusMsg(null);
    try {
      await apiRequest("/brains", {
        method: "POST",
        body: JSON.stringify({
          name: newName,
          description: newDescription,
          role_ids: selectedRoleIds,
          source_ids: selectedSourceIds,
          document_ids: selectedDocIds,
        }),
      });
      setShowCreateModal(false);
      setNewName("");
      setNewDescription("");
      setSelectedRoleIds([]);
      setSelectedSourceIds([]);
      setSelectedDocIds([]);
      setStatusMsg("Brain created successfully!");
      loadAllData();
    } catch (err: any) {
      setStatusMsg(`Creation error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const openRolesModal = (brain: BrainItem) => {
    setActiveBrain(brain);
    // Map assigned role names to role IDs
    const currentRoleIds = roles
      .filter((r) => brain.assigned_roles.includes(r.name))
      .map((r) => r.id);
    setModalRoleIds(currentRoleIds);
    setShowRolesModal(true);
  };

  const handleSaveRoles = async () => {
    if (!activeBrain) return;
    setSubmitting(true);
    try {
      await apiRequest(`/brains/${activeBrain.id}/assign-roles`, {
        method: "POST",
        body: JSON.stringify({ role_ids: modalRoleIds }),
      });
      setShowRolesModal(false);
      setStatusMsg(`Updated role assignments for '${activeBrain.name}'`);
      loadAllData();
    } catch (err: any) {
      setStatusMsg(`Failed to assign roles: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const openResourcesModal = (brain: BrainItem) => {
    setActiveBrain(brain);
    const connectedSources = sources.filter((s) => s.brain_id === brain.id).map((s) => s.id);
    const connectedDocs = documents.filter((d) => d.brain_id === brain.id).map((d) => d.id);
    setModalSourceIds(connectedSources);
    setModalDocIds(connectedDocs);
    setShowResourcesModal(true);
  };

  const handleSaveResources = async () => {
    if (!activeBrain) return;
    setSubmitting(true);
    try {
      await apiRequest(`/brains/${activeBrain.id}/connect-resources`, {
        method: "POST",
        body: JSON.stringify({
          source_ids: modalSourceIds,
          document_ids: modalDocIds,
        }),
      });
      setShowResourcesModal(false);
      setStatusMsg(`Connected resources updated for '${activeBrain.name}'`);
      loadAllData();
    } catch (err: any) {
      setStatusMsg(`Failed to connect resources: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteBrain = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete Brain '${name}'? Connected sources and documents will be unassigned.`)) {
      return;
    }
    try {
      await apiRequest(`/brains/${id}`, { method: "DELETE" });
      setStatusMsg(`Brain '${name}' deleted.`);
      loadAllData();
    } catch (err: any) {
      setStatusMsg(`Delete error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <BrainCircuit className="h-7 w-7 text-aura-400" />
            Knowledge & Data Brains
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Group enterprise data sources and documents into isolated Brains and assign them to specific roles for fine-grained RBAC scoping.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-aura-500 transition"
        >
          <Plus className="h-4 w-4" />
          <span>Create Brain</span>
        </button>
      </div>

      {/* Status banner */}
      {statusMsg && (
        <div className="rounded-lg bg-slate-900 border border-slate-800 p-3.5 flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2 text-slate-200">
            <CheckCircle className="h-4 w-4 text-aura-400" />
            <span>{statusMsg}</span>
          </div>
          <button onClick={() => setStatusMsg(null)} className="text-xs text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Brains Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400">Loading Brains and access matrix...</div>
      ) : brains.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center">
          <BrainCircuit className="h-12 w-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-200">No Brains Created Yet</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
            Brains allow you to organize data sources and documents into role-scoped knowledge hubs.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 inline-flex items-center space-x-2 rounded-lg bg-aura-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 transition"
          >
            <Plus className="h-4 w-4" />
            <span>Create First Brain</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {brains.map((b) => (
            <div
              key={b.id}
              className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 flex flex-col justify-between hover:border-slate-700 transition"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-aura-600/10 border border-aura-500/20 text-aura-400">
                      <BrainCircuit className="h-5 w-5" />
                    </div>
                    <div>
                      <h2 className="font-semibold text-white text-base leading-snug">{b.name}</h2>
                      <span className="text-[11px] text-slate-400">
                        Created {new Date(b.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteBrain(b.id, b.name)}
                    className="text-slate-500 hover:text-red-400 p-1 transition"
                    title="Delete Brain"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <p className="text-xs text-slate-400 mt-3 line-clamp-2">
                  {b.description || "No description provided."}
                </p>

                {/* Metrics */}
                <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-2.5 flex items-center space-x-2">
                    <Database className="h-4 w-4 text-blue-400" />
                    <div>
                      <div className="font-bold text-slate-200">{b.sources_count}</div>
                      <div className="text-[10px] text-slate-400">Data Sources</div>
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-2.5 flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-emerald-400" />
                    <div>
                      <div className="font-bold text-slate-200">{b.documents_count}</div>
                      <div className="text-[10px] text-slate-400">Documents</div>
                    </div>
                  </div>
                </div>

                {/* Assigned Roles */}
                <div className="mt-4">
                  <span className="text-[11px] font-medium text-slate-400 block mb-1.5 flex items-center gap-1">
                    <Shield className="h-3 w-3 text-aura-400" />
                    Permitted Roles ({b.assigned_roles.length})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {b.assigned_roles.length === 0 ? (
                      <span className="text-[11px] text-amber-400/90 italic">No roles assigned (Admins only)</span>
                    ) : (
                      b.assigned_roles.map((r) => (
                        <span
                          key={r}
                          className="rounded bg-aura-950 border border-aura-800/60 px-2 py-0.5 text-[10px] font-medium text-aura-300"
                        >
                          {r}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center gap-2">
                <button
                  onClick={() => openRolesModal(b)}
                  className="flex-1 flex items-center justify-center space-x-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 transition"
                >
                  <Users className="h-3.5 w-3.5 text-aura-400" />
                  <span>Assign Roles</span>
                </button>
                <button
                  onClick={() => openResourcesModal(b)}
                  className="flex-1 flex items-center justify-center space-x-1.5 rounded-lg bg-aura-600/20 hover:bg-aura-600/30 border border-aura-500/30 px-3 py-1.5 text-xs font-semibold text-aura-300 transition"
                >
                  <Layers className="h-3.5 w-3.5 text-aura-400" />
                  <span>Connect Resources</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CREATE BRAIN MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl my-8">
            <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <BrainCircuit className="h-5 w-5 text-aura-400" />
              Create New Brain
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Define a logical knowledge domain, connect data sources & documents, and assign roles that can query it.
            </p>

            <form onSubmit={handleCreateBrain} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Brain Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Finance & Auditing Brain"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-aura-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Describe the knowledge domain and intended audience..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-aura-500 focus:outline-none"
                />
              </div>

              {/* Roles Multi-select */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Assign to Roles (Users with these roles can query this Brain)
                </label>
                <div className="max-h-28 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-2.5 space-y-1.5">
                  {roles.map((r) => {
                    const checked = selectedRoleIds.includes(r.id);
                    return (
                      <label key={r.id} className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            if (e.target.checked) setSelectedRoleIds([...selectedRoleIds, r.id]);
                            else setSelectedRoleIds(selectedRoleIds.filter((id) => id !== r.id));
                          }}
                          className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                        />
                        <span className="font-medium">{r.name}</span>
                        {r.description && <span className="text-[10px] text-slate-500">({r.description})</span>}
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Data Sources Multi-select */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Connect Data Sources</label>
                <div className="max-h-24 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-2.5 space-y-1.5">
                  {sources.length === 0 ? (
                    <span className="text-xs text-slate-500 italic">No data sources configured yet.</span>
                  ) : (
                    sources.map((s) => {
                      const checked = selectedSourceIds.includes(s.id);
                      return (
                        <label key={s.id} className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) setSelectedSourceIds([...selectedSourceIds, s.id]);
                              else setSelectedSourceIds(selectedSourceIds.filter((id) => id !== s.id));
                            }}
                            className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                          />
                          <span>{s.name}</span>
                          <span className="text-[10px] text-slate-500 font-mono">({s.type})</span>
                        </label>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Documents Multi-select */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Connect Documents</label>
                <div className="max-h-24 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-2.5 space-y-1.5">
                  {documents.length === 0 ? (
                    <span className="text-xs text-slate-500 italic">No documents uploaded yet.</span>
                  ) : (
                    documents.map((d) => {
                      const checked = selectedDocIds.includes(d.id);
                      return (
                        <label key={d.id} className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) setSelectedDocIds([...selectedDocIds, d.id]);
                              else setSelectedDocIds(selectedDocIds.filter((id) => id !== d.id));
                            }}
                            className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                          />
                          <span>{d.title}</span>
                          <span className="text-[10px] text-slate-500">({d.file_name})</span>
                        </label>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-aura-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 transition disabled:opacity-50"
                >
                  {submitting ? "Creating..." : "Create Brain"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ASSIGN ROLES MODAL */}
      {showRolesModal && activeBrain && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <Users className="h-5 w-5 text-aura-400" />
              Assign Roles to &apos;{activeBrain.name}&apos;
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Select which user roles have permission to view, query, and chat with resources in this Brain.
            </p>

            <div className="max-h-60 overflow-y-auto space-y-2 mb-5">
              {roles.map((r) => {
                const checked = modalRoleIds.includes(r.id);
                return (
                  <div
                    key={r.id}
                    onClick={() => {
                      if (checked) setModalRoleIds(modalRoleIds.filter((id) => id !== r.id));
                      else setModalRoleIds([...modalRoleIds, r.id]);
                    }}
                    className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                      checked
                        ? "border-aura-500/50 bg-aura-950/30 text-white"
                        : "border-slate-800 bg-slate-950 text-slate-300 hover:border-slate-700"
                    }`}
                  >
                    <div>
                      <div className="text-xs font-semibold">{r.name}</div>
                      <div className="text-[10px] text-slate-400">{r.description || "Custom enterprise role"}</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => {}}
                      className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                    />
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowRolesModal(false)}
                className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveRoles}
                disabled={submitting}
                className="rounded-lg bg-aura-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 transition disabled:opacity-50"
              >
                {submitting ? "Saving..." : "Save Role Assignments"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONNECT RESOURCES MODAL */}
      {showResourcesModal && activeBrain && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl my-8">
            <h2 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <Layers className="h-5 w-5 text-aura-400" />
              Manage Resources for &apos;{activeBrain.name}&apos;
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Select which enterprise data sources and documents belong to this Brain.
            </p>

            <div className="space-y-4 mb-5">
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-blue-400" />
                  Connected Data Sources ({modalSourceIds.length})
                </h3>
                <div className="max-h-36 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-2.5 space-y-1.5">
                  {sources.length === 0 ? (
                    <span className="text-xs text-slate-500 italic">No data sources configured.</span>
                  ) : (
                    sources.map((s) => {
                      const checked = modalSourceIds.includes(s.id);
                      return (
                        <label key={s.id} className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) setModalSourceIds([...modalSourceIds, s.id]);
                              else setModalSourceIds(modalSourceIds.filter((id) => id !== s.id));
                            }}
                            className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                          />
                          <span className="font-medium">{s.name}</span>
                          <span className="text-[10px] text-slate-500 font-mono">({s.type})</span>
                        </label>
                      );
                    })
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-emerald-400" />
                  Connected Documents ({modalDocIds.length})
                </h3>
                <div className="max-h-36 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-2.5 space-y-1.5">
                  {documents.length === 0 ? (
                    <span className="text-xs text-slate-500 italic">No documents uploaded.</span>
                  ) : (
                    documents.map((d) => {
                      const checked = modalDocIds.includes(d.id);
                      return (
                        <label key={d.id} className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) setModalDocIds([...modalDocIds, d.id]);
                              else setModalDocIds(modalDocIds.filter((id) => id !== d.id));
                            }}
                            className="rounded border-slate-700 text-aura-600 focus:ring-aura-500"
                          />
                          <span className="font-medium">{d.title}</span>
                          <span className="text-[10px] text-slate-500">({d.file_name})</span>
                        </label>
                      );
                    })
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowResourcesModal(false)}
                className="rounded-lg border border-slate-700 px-3.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveResources}
                disabled={submitting}
                className="rounded-lg bg-aura-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-aura-500 transition disabled:opacity-50"
              >
                {submitting ? "Saving..." : "Save Connected Resources"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
