"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { PolicyItem } from "@/types";
import { ShieldCheck, Plus, Trash2, Lock, EyeOff, Filter, Check } from "lucide-react";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<PolicyItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Form modal
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  // Rule creation modal
  const [activePolicyId, setActivePolicyId] = useState<string | null>(null);
  const [resourceType, setResourceType] = useState("COLUMN");
  const [resourceName, setResourceName] = useState("");
  const [effect, setEffect] = useState("ALLOW");
  const [dataMaskingRule, setDataMaskingRule] = useState("MASK_EMAIL");
  const [rowFilterExpr, setRowFilterExpr] = useState("");

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<PolicyItem[]>("/policies");
      setPolicies(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/policies", {
        method: "POST",
        body: JSON.stringify({ name, description }),
      });
      setShowModal(false);
      setName("");
      setDescription("");
      loadPolicies();
    } catch (err: any) {
      alert(err.message || "Failed to create policy");
    }
  };

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePolicyId) return;

    try {
      await apiRequest(`/policies/${activePolicyId}/rules`, {
        method: "POST",
        body: JSON.stringify({
          resource_type: resourceType,
          resource_name: resourceName,
          effect,
          data_masking_rule: dataMaskingRule || null,
          row_filter_expr: rowFilterExpr || null,
        }),
      });
      setActivePolicyId(null);
      setResourceName("");
      loadPolicies();
    } catch (err: any) {
      alert(err.message || "Failed to add rule");
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await apiRequest(`/policies/rules/${ruleId}`, { method: "DELETE" });
      loadPolicies();
    } catch (err: any) {
      alert(err.message || "Failed to delete rule");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Policy Engine & Data Boundaries</h1>
          <p className="mt-1 text-sm text-slate-400">
            Enforce table/column permissions, row-level filters, and real-time data masking independent of LLM prompts.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 rounded-lg bg-aura-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-aura-500 transition"
        >
          <Plus className="h-4 w-4" />
          <span>New Security Policy</span>
        </button>
      </div>

      <div className="space-y-6">
        {policies.map((p) => (
          <div key={p.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <ShieldCheck className="h-6 w-6 text-emerald-400" />
                <div>
                  <h3 className="font-bold text-base text-white">{p.name}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{p.description}</p>
                </div>
              </div>
              <button
                onClick={() => setActivePolicyId(p.id)}
                className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add Security Rule</span>
              </button>
            </div>

            {/* Rules table */}
            <div className="mt-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Active Security Rules ({p.rules.length})
              </div>
              {p.rules.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-500">
                  No rules configured in this policy.
                </div>
              ) : (
                <div className="divide-y divide-slate-800 border border-slate-800 rounded-lg overflow-hidden bg-slate-900/80">
                  {p.rules.map((r) => (
                    <div key={r.id} className="p-3.5 flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-3">
                        <span className="font-mono rounded bg-slate-800 px-2 py-0.5 text-[10px] text-slate-300 font-bold border border-slate-700">
                          {r.resource_type}
                        </span>
                        <span className="font-mono text-sm font-semibold text-white">{r.resource_name}</span>
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                            r.effect === "DENY"
                              ? "bg-red-500/10 text-red-400 border border-red-500/20"
                              : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          }`}
                        >
                          {r.effect}
                        </span>
                        {r.data_masking_rule && (
                          <span className="rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 px-2 py-0.5 text-[10px] flex items-center space-x-1">
                            <EyeOff className="h-3 w-3" />
                            <span>{r.data_masking_rule}</span>
                          </span>
                        )}
                        {r.row_filter_expr && (
                          <span className="rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 px-2 py-0.5 text-[10px] flex items-center space-x-1 font-mono">
                            <Filter className="h-3 w-3" />
                            <span>WHERE {r.row_filter_expr}</span>
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => handleDeleteRule(r.id)}
                        className="text-slate-500 hover:text-red-400 p-1"
                        title="Delete Rule"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Add Policy Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Create Security Policy</h3>
            <form onSubmit={handleCreatePolicy} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Policy Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Sales Column Access Policy"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Explains what this policy protects..."
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-2">
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
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Rule Modal */}
      {activePolicyId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add Security Rule</h3>
            <form onSubmit={handleAddRule} className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase">Resource Type</label>
                  <select
                    value={resourceType}
                    onChange={(e) => setResourceType(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                  >
                    <option value="COLUMN">Column</option>
                    <option value="TABLE">Table</option>
                    <option value="TOOL">Tool</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase">Effect</label>
                  <select
                    value={effect}
                    onChange={(e) => setEffect(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                  >
                    <option value="ALLOW">ALLOW</option>
                    <option value="DENY">DENY</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">
                  Target Resource Name
                </label>
                <input
                  type="text"
                  required
                  value={resourceName}
                  onChange={(e) => setResourceName(e.target.value)}
                  placeholder="e.g. salary, customers, email"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">
                  Data Masking Rule (Optional)
                </label>
                <select
                  value={dataMaskingRule}
                  onChange={(e) => setDataMaskingRule(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs text-white"
                >
                  <option value="">None</option>
                  <option value="MASK_EMAIL">Mask Email (e.g. jo***@domain.com)</option>
                  <option value="REDACT">Full Redaction ([REDACTED])</option>
                  <option value="MASK_NUMERIC">Mask Numbers (***)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase">
                  Row Filter Expression (Optional SQL WHERE)
                </label>
                <input
                  type="text"
                  value={rowFilterExpr}
                  onChange={(e) => setRowFilterExpr(e.target.value)}
                  placeholder="e.g. country = 'India'"
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 p-2.5 text-xs font-mono text-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setActivePolicyId(null)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-aura-600 px-4 py-2 text-xs font-medium text-white hover:bg-aura-500"
                >
                  Save Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
