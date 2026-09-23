import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  MessageSquare,
  Package,
  Ticket,
  BarChart3,
  FileText,
  HelpCircle,
  Users,
  Settings,
  ShieldCheck,
  ShoppingBag,
  Cpu,
  Layers
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  if (!user) return null;

  const isAdminOrAgent = user.role !== "CUSTOMER";

  const customerNav = [
    { label: "AI Support Chat", to: "/chat", icon: MessageSquare },
    { label: "My Orders", to: "/orders", icon: Package },
    { label: "Support Tickets", to: "/tickets", icon: Ticket },
  ];

  const adminNav = [
    { label: "Executive Overview", to: "/admin", icon: BarChart3, end: true },
    { label: "Knowledge Base", to: "/admin/documents", icon: FileText },
    { label: "Structured FAQs", to: "/admin/faqs", icon: HelpCircle },
    { label: "Ticket Workbench", to: "/admin/tickets", icon: Ticket },
    { label: "Chat Transcripts", to: "/admin/conversations", icon: MessageSquare },
    { label: "Orders & Refunds", to: "/admin/orders", icon: ShoppingBag },
    { label: "Analytics & KPI", to: "/admin/analytics", icon: Layers },
    { label: "User Directory", to: "/admin/users", icon: Users },
    { label: "AI Configuration", to: "/admin/settings", icon: Cpu },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 border-r border-slate-800">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
          {isAdminOrAgent ? "Admin Workspace" : "Customer Portal"}
        </span>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {isAdminOrAgent ? (
          <>
            <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Operations & AI
            </div>
            {adminNav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
                  }`
                }
              >
                <item.icon className="w-4 h-4 shrink-0" />
                {item.label}
              </NavLink>
            ))}

            <div className="pt-4 px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Test Customer Chat
            </div>
            <NavLink
              to="/chat"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
                }`
              }
            >
              <MessageSquare className="w-4 h-4 shrink-0" />
              Customer Chat View
            </NavLink>
          </>
        ) : (
          <>
            <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Help Center
            </div>
            {customerNav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
                  }`
                }
              >
                <item.icon className="w-4 h-4 shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-400 space-y-1">
        <div className="flex items-center gap-2 text-indigo-400 font-medium">
          <ShieldCheck className="w-4 h-4" /> Multi-Tenant Active
        </div>
        <p className="text-[11px] text-slate-400">SupportIQ Engine v1.0.0</p>
      </div>
    </aside>
  );
};
