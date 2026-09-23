import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Bot, User, LogOut, ShieldAlert, Sparkles, Building2 } from "lucide-react";

export const Navbar: React.FC = () => {
  const { user, logout, quickLogin } = useAuth();

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case "ORGANIZATION_ADMIN":
      case "SUPER_ADMIN":
        return <span className="bg-purple-100 text-purple-700 text-xs px-2.5 py-0.5 rounded-full font-medium">Org Admin</span>;
      case "SUPPORT_AGENT":
        return <span className="bg-blue-100 text-blue-700 text-xs px-2.5 py-0.5 rounded-full font-medium">Support Agent</span>;
      default:
        return <span className="bg-emerald-100 text-emerald-700 text-xs px-2.5 py-0.5 rounded-full font-medium">Customer</span>;
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-40 px-4 sm:px-6 flex items-center justify-between shadow-xs">
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-brand-400 flex items-center justify-center text-white shadow-md shadow-indigo-100 group-hover:scale-105 transition-transform">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg tracking-tight text-slate-900">SupportIQ</span>
              <span className="text-[10px] uppercase tracking-wider font-semibold bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded">AI RAG</span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">Customer Support & Knowledge Agent</p>
          </div>
        </Link>
      </div>

      <div className="flex items-center gap-3">
        {/* Quick Demo Persona Switcher */}
        <div className="hidden md:flex items-center bg-slate-100 p-1 rounded-lg text-xs font-medium">
          <span className="text-slate-500 px-2 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" /> Switch Demo:
          </span>
          <button
            onClick={() => quickLogin("admin")}
            className="px-2 py-1 rounded hover:bg-white text-slate-700 hover:shadow-xs transition"
            title="Login as Alice Admin (Admin123!)"
          >
            Admin
          </button>
          <button
            onClick={() => quickLogin("agent")}
            className="px-2 py-1 rounded hover:bg-white text-slate-700 hover:shadow-xs transition"
            title="Login as Sarah Agent (Agent123!)"
          >
            Agent
          </button>
          <button
            onClick={() => quickLogin("customer")}
            className="px-2 py-1 rounded hover:bg-white text-slate-700 hover:shadow-xs transition"
            title="Login as Customer 1 (Customer123!)"
          >
            Customer
          </button>
        </div>

        {user ? (
          <div className="flex items-center gap-3 border-l border-slate-200 pl-3">
            <div className="text-right hidden sm:block">
              <div className="flex items-center gap-2 justify-end">
                <span className="text-sm font-semibold text-slate-800">{user.name}</span>
                {getRoleBadge(user.role)}
              </div>
              <span className="text-xs text-slate-500">{user.email}</span>
            </div>
            <button
              onClick={logout}
              className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 px-3 py-1.5"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 px-4 py-1.5 rounded-lg shadow-xs transition"
            >
              Get Started
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
