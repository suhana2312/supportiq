import React, { useState, useEffect } from "react";
import { apiRequest } from "../../services/api";
import {
  Cpu,
  Save,
  CheckCircle2,
  AlertCircle,
  Building,
  Sliders,
  ShieldCheck,
  Sparkles,
  RefreshCw,
  Database
} from "lucide-react";

export const AdminSettingsPage: React.FC = () => {
  const [orgName, setOrgName] = useState("");
  const [slug, setSlug] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // AI settings
  const [model, setModel] = useState("gpt-4o-mini");
  const [temperature, setTemperature] = useState(0.2);
  const [topK, setTopK] = useState(4);
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(150);
  const [escalationThreshold, setEscalationThreshold] = useState(2);
  const [securityGuardrails, setSecurityGuardrails] = useState(true);
  const [deterministicRefunds, setDeterministicRefunds] = useState(true);

  useEffect(() => {
    const fetchOrg = async () => {
      try {
        setLoading(true);
        const res = await apiRequest<any>("/organization/me");
        if (res) {
          setOrgName(res.name || "");
          setSlug(res.slug || "");
          if (res.ai_settings) {
            setModel(res.ai_settings.model || "gpt-4o-mini");
            setTemperature(res.ai_settings.temperature ?? 0.2);
            setTopK(res.ai_settings.top_k ?? 4);
            setChunkSize(res.ai_settings.chunk_size ?? 1000);
            setChunkOverlap(res.ai_settings.chunk_overlap ?? 150);
            setEscalationThreshold(res.ai_settings.escalation_threshold ?? 2);
          }
        }
      } catch (err: any) {
        setError(err.message || "Failed to load organization settings");
      } finally {
        setLoading(false);
      }
    };

    fetchOrg();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      await apiRequest("/organization/me", {
        method: "PATCH",
        body: JSON.stringify({
          name: orgName,
          ai_settings: {
            model,
            temperature,
            top_k: topK,
            chunk_size: chunkSize,
            chunk_overlap: chunkOverlap,
            escalation_threshold: escalationThreshold,
            guardrails_enabled: securityGuardrails,
            deterministic_refunds: deterministicRefunds
          }
        })
      });

      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-500" />
        Loading organization settings...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
          <Cpu className="w-7 h-7 text-indigo-600" />
          AI & Organization Settings
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Tune LangGraph autonomous agent parameters, vector retrieval thresholds, and tenant identity.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-3 text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-3 text-emerald-700 text-sm">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          Settings successfully updated and deployed to the LangGraph execution runtime.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Organization Identity */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Building className="w-5 h-5 text-indigo-500" />
            Organization Identity
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Organization Name
              </label>
              <input
                type="text"
                required
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Organization Slug (Read-only)
              </label>
              <input
                type="text"
                disabled
                value={slug}
                className="w-full px-3 py-2 border border-slate-200 bg-slate-50 text-slate-500 rounded-lg text-sm cursor-not-allowed font-mono"
              />
            </div>
          </div>
        </div>

        {/* AI Agent Configuration */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            LangGraph Autonomous Agent Engine
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Foundation Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="gpt-4o-mini">OpenAI GPT-4o-mini (Recommended - Low Latency)</option>
                <option value="gpt-4o">OpenAI GPT-4o (High Reasoning)</option>
                <option value="claude-3-5-sonnet">Anthropic Claude 3.5 Sonnet</option>
                <option value="gemini-1.5-pro">Google Gemini 1.5 Pro</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">
                Model invoked by the LangGraph agent for tool calling and message synthesis.
              </p>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Sampling Temperature: <span className="font-mono text-indigo-600">{temperature}</span>
                </label>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-indigo-600"
              />
              <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                <span>0.0 (Deterministic / Grounded)</span>
                <span>1.0 (Creative)</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-4 border-t border-slate-100">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Top-K Vector Chunks
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value) || 4)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <p className="text-xs text-slate-400 mt-1">Max vector snippets injected into agent prompt</p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Chunk Size (Tokens)
              </label>
              <input
                type="number"
                min="300"
                max="2000"
                step="50"
                value={chunkSize}
                onChange={(e) => setChunkSize(parseInt(e.target.value) || 1000)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <p className="text-xs text-slate-400 mt-1">Target chunk length for new document ingestion</p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Chunk Overlap (Tokens)
              </label>
              <input
                type="number"
                min="20"
                max="300"
                step="10"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(parseInt(e.target.value) || 150)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <p className="text-xs text-slate-400 mt-1">Sliding token overlap between adjacent chunks</p>
            </div>
          </div>
        </div>

        {/* Safety & Determinism Guardrails */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <ShieldCheck className="w-5 h-5 text-indigo-500" />
            Safety, Security & Determinism Policies
          </h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <p className="font-semibold text-sm text-slate-900">Anti-Prompt Injection Guardrails</p>
                <p className="text-xs text-slate-500">
                  Inspects customer prompt prefixes for system-prompt overrides, jailbreaks, and sensitive leaks.
                </p>
              </div>
              <input
                type="checkbox"
                checked={securityGuardrails}
                onChange={(e) => setSecurityGuardrails(e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded-sm focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center justify-between p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <p className="font-semibold text-sm text-slate-900">Deterministic Refund Engine Enforcement</p>
                <p className="text-xs text-slate-500">
                  Guarantees AI cannot invent refund approvals. All refund claims strictly pass Python logic gates.
                </p>
              </div>
              <input
                type="checkbox"
                checked={deterministicRefunds}
                onChange={(e) => setDeterministicRefunds(e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded-sm focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-lg shadow-sm transition disabled:opacity-50"
          >
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Saving Configuration...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" /> Save Configuration
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
