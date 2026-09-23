import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Bot, Lock, Mail, ArrowRight, ShieldCheck, Sparkles, CheckCircle2 } from "lucide-react";

export const Login: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login, quickLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/chat");
    } catch (err: any) {
      setError(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = async (role: "admin" | "agent" | "customer") => {
    setError(null);
    setLoading(true);
    try {
      await quickLogin(role);
      if (role === "admin" || role === "agent") {
        navigate("/admin");
      } else {
        navigate("/chat");
      }
    } catch (err: any) {
      setError(err.message || "Quick demo login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex w-14 h-14 rounded-2xl bg-indigo-600 items-center justify-center text-white shadow-xl shadow-indigo-500/30 mb-4">
          <Bot className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-white">SupportIQ</h2>
        <p className="mt-2 text-sm text-slate-400">
          Production AI Customer Support & Knowledge Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white/10 backdrop-blur-md py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-white/10 text-slate-900">
          {/* Quick Demo Selector */}
          <div className="mb-6 p-4 rounded-xl bg-indigo-900/40 border border-indigo-500/30 text-slate-200">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-indigo-300 uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-indigo-400" /> Instant Demo Personas
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleQuickDemo("admin")}
                className="py-2 px-2 bg-indigo-600/80 hover:bg-indigo-600 rounded-lg text-white font-medium transition text-center"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemo("agent")}
                className="py-2 px-2 bg-blue-600/80 hover:bg-blue-600 rounded-lg text-white font-medium transition text-center"
              >
                Agent
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemo("customer")}
                className="py-2 px-2 bg-emerald-600/80 hover:bg-emerald-600 rounded-lg text-white font-medium transition text-center"
              >
                Customer
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-200 text-sm">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-medium text-slate-300">Email Address</label>
              <div className="mt-1 relative">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@supportiq.com"
                  className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                />
                <Mail className="w-4 h-4 text-slate-500 absolute right-3 top-2.5" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300">Password</label>
              <div className="mt-1 relative">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                />
                <Lock className="w-4 h-4 text-slate-500 absolute right-3 top-2.5" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-md shadow-indigo-600/30 transition flex items-center justify-center gap-2 text-sm disabled:opacity-50"
            >
              {loading ? "Signing in..." : "Sign In to Account"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-slate-400">
            Don't have an organization account yet?{" "}
            <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-semibold underline">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
