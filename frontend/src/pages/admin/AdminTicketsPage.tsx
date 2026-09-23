import React, { useState, useEffect } from "react";
import { apiRequest } from "../../services/api";
import { SupportTicket, TicketStatus, TicketPriority, TicketMessage, User } from "../../types";
import {
  Ticket,
  Search,
  Filter,
  User as UserIcon,
  CheckCircle,
  AlertTriangle,
  Lock,
  Send,
  ArrowRight,
  ShieldAlert
} from "lucide-react";

export const AdminTicketsPage: React.FC = () => {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [agents, setAgents] = useState<User[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [replyMessage, setReplyMessage] = useState("");
  const [isInternalNote, setIsInternalNote] = useState(false);

  useEffect(() => {
    loadTickets();
    loadAgents();
  }, [statusFilter, priorityFilter]);

  const loadTickets = async () => {
    try {
      const params: any = { page: 1, page_size: 50 };
      if (statusFilter !== "ALL") params.status = statusFilter;
      if (priorityFilter !== "ALL") params.priority = priorityFilter;
      const res = await apiRequest<{ items: SupportTicket[] }>("/tickets", { params });
      setTickets(res.items || []);
      if (res.items && res.items.length > 0 && !selectedTicket) {
        handleSelectTicket(res.items[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadAgents = async () => {
    try {
      const res = await apiRequest<{ items: User[] }>("/users", { params: { role: "SUPPORT_AGENT" } });
      setAgents(res.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectTicket = async (id: string) => {
    try {
      const t = await apiRequest<SupportTicket>(`/tickets/${id}`);
      setSelectedTicket(t);
    } catch (e) {
      console.error(e);
    }
  };

  const handleStatusChange = async (newStatus: TicketStatus) => {
    if (!selectedTicket) return;
    try {
      const updated = await apiRequest<SupportTicket>(`/tickets/${selectedTicket.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus })
      });
      setSelectedTicket(updated);
      setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } catch (e: any) {
      alert(e.message || "Failed to update status");
    }
  };

  const handleAssignAgent = async (agentId: string) => {
    if (!selectedTicket) return;
    try {
      const updated = await apiRequest<SupportTicket>(`/tickets/${selectedTicket.id}`, {
        method: "PATCH",
        body: JSON.stringify({ assigned_agent_id: agentId })
      });
      setSelectedTicket(updated);
      setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } catch (e: any) {
      alert(e.message || "Failed to assign agent");
    }
  };

  const handleSendMessage = async () => {
    if (!replyMessage.trim() || !selectedTicket) return;
    try {
      const newMsg = await apiRequest<TicketMessage>(`/tickets/${selectedTicket.id}/messages`, {
        method: "POST",
        body: JSON.stringify({ message: replyMessage, is_internal_note: isInternalNote })
      });
      setSelectedTicket((prev) => prev ? { ...prev, messages: [...prev.messages, newMsg] } : null);
      setReplyMessage("");
      setIsInternalNote(false);
    } catch (e: any) {
      alert(e.message || "Failed to send message");
    }
  };

  const getPriorityBadge = (p: string) => {
    const colors: Record<string, string> = {
      URGENT: "bg-rose-50 text-rose-700 border-rose-200",
      HIGH: "bg-amber-50 text-amber-700 border-amber-200",
      MEDIUM: "bg-blue-50 text-blue-700 border-blue-200",
      LOW: "bg-slate-50 text-slate-700 border-slate-200"
    };
    return (
      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${colors[p] || colors.MEDIUM}`}>
        {p}
      </span>
    );
  };

  const getStatusBadge = (s: string) => {
    const colors: Record<string, string> = {
      OPEN: "bg-blue-50 text-blue-700 border-blue-200",
      IN_PROGRESS: "bg-indigo-50 text-indigo-700 border-indigo-200",
      ESCALATED: "bg-purple-50 text-purple-700 border-purple-200",
      RESOLVED: "bg-emerald-50 text-emerald-700 border-emerald-200",
      CLOSED: "bg-slate-100 text-slate-600 border-slate-200"
    };
    return (
      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${colors[s] || colors.OPEN}`}>
        {s.replace(/_/g, " ")}
      </span>
    );
  };

  const filteredTickets = tickets.filter((t) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.subject.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.id.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Support Ticket Workbench</h1>
        <p className="text-sm text-slate-500">
          Manage, triage, assign, and respond to escalated customer inquiries.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <div className="relative w-full">
            <input
              type="text"
              placeholder="Search by ticket ID, subject, customer..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-indigo-500"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="ESCALATED">Escalated</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500">Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700"
            >
              <option value="ALL">All Priorities</option>
              <option value="URGENT">Urgent</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tickets Column */}
        <div className="lg:col-span-1 space-y-3 max-h-[700px] overflow-y-auto pr-1">
          {loading ? (
            <div className="p-8 text-center text-slate-400 text-xs">Loading ticket queue...</div>
          ) : filteredTickets.length === 0 ? (
            <div className="p-8 bg-white border border-slate-200 rounded-2xl text-center text-slate-400 text-xs">
              No tickets matching active filters.
            </div>
          ) : (
            filteredTickets.map((t) => (
              <div
                key={t.id}
                onClick={() => handleSelectTicket(t.id)}
                className={`p-4 rounded-xl border transition cursor-pointer flex flex-col gap-2 ${
                  selectedTicket?.id === t.id
                    ? "bg-white border-indigo-500 shadow-xs ring-1 ring-indigo-500"
                    : "bg-white border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-400">#{t.id.slice(0, 8)}</span>
                  <div className="flex items-center gap-1.5">
                    {getPriorityBadge(t.priority)}
                    {getStatusBadge(t.status)}
                  </div>
                </div>
                <h4 className="font-semibold text-sm text-slate-900 line-clamp-1">{t.subject}</h4>
                <p className="text-xs text-slate-500 line-clamp-2">{t.description}</p>
                <div className="text-[11px] text-slate-400 pt-1.5 border-t border-slate-100 flex justify-between">
                  <span>Customer: {t.customer_name || "Customer"}</span>
                  <span>Agent: {t.assigned_agent_name || "Unassigned"}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Workbench Detail Workspace */}
        <div className="lg:col-span-2">
          {selectedTicket ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col h-[700px]">
              {/* Header Details */}
              <div className="border-b border-slate-200 pb-4 mb-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-indigo-600 font-bold">
                      Ticket #{selectedTicket.id}
                    </span>
                    {getPriorityBadge(selectedTicket.priority)}
                    {getStatusBadge(selectedTicket.status)}
                  </div>

                  {/* Status & Assignment Quick Toggles */}
                  <div className="flex items-center gap-2">
                    <select
                      value={selectedTicket.assigned_agent_id || ""}
                      onChange={(e) => handleAssignAgent(e.target.value)}
                      className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700"
                    >
                      <option value="">Assign Support Agent...</option>
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name}
                        </option>
                      ))}
                    </select>

                    <select
                      value={selectedTicket.status}
                      onChange={(e) => handleStatusChange(e.target.value as TicketStatus)}
                      className="px-2.5 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-semibold"
                    >
                      <option value="OPEN">Mark Open</option>
                      <option value="IN_PROGRESS">Mark In Progress</option>
                      <option value="ESCALATED">Mark Escalated</option>
                      <option value="RESOLVED">Mark Resolved</option>
                      <option value="CLOSED">Mark Closed</option>
                    </select>
                  </div>
                </div>

                <h2 className="text-base font-bold text-slate-900">{selectedTicket.subject}</h2>
                <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <span className="font-semibold text-slate-800">Initial Issue:</span> {selectedTicket.description}
                </div>

                {selectedTicket.ai_summary && (
                  <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-100 text-xs text-indigo-900">
                    <strong className="text-indigo-700">AI Context & Intent:</strong> {selectedTicket.ai_summary}
                  </div>
                )}
              </div>

              {/* Message History & Internal Notes */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                {selectedTicket.messages && selectedTicket.messages.map((m) => (
                  <div
                    key={m.id}
                    className={`p-3.5 rounded-xl text-xs leading-relaxed max-w-xl ${
                      m.is_internal_note
                        ? "bg-amber-50/80 border border-amber-200 text-amber-900 mx-auto"
                        : m.sender_type === "SUPPORT_AGENT"
                        ? "ml-auto bg-indigo-600 text-white"
                        : "mr-auto bg-slate-100 text-slate-800 border border-slate-200"
                    }`}
                  >
                    <div className="font-semibold text-[10px] opacity-80 mb-1 flex items-center justify-between">
                      <span className="flex items-center gap-1">
                        {m.is_internal_note && <Lock className="w-3 h-3 text-amber-600 inline" />}
                        {m.sender_name || m.sender_type}
                        {m.is_internal_note && " (Internal Staff Note - Hidden from Customer)"}
                      </span>
                      <span>
                        {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap">{m.message}</div>
                  </div>
                ))}
              </div>

              {/* Agent Reply Box */}
              <div className="pt-4 border-t border-slate-200 mt-2 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <label className="flex items-center gap-1.5 cursor-pointer text-slate-600 font-medium">
                    <input
                      type="checkbox"
                      checked={isInternalNote}
                      onChange={(e) => setIsInternalNote(e.target.checked)}
                      className="rounded text-indigo-600 focus:ring-indigo-500"
                    />
                    <Lock className="w-3.5 h-3.5 text-amber-600" />
                    <span>Private Internal Note (Only visible to support staff)</span>
                  </label>
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={replyMessage}
                    onChange={(e) => setReplyMessage(e.target.value)}
                    placeholder={
                      isInternalNote
                        ? "Write internal staff note (e.g. 'Customer called bank, refund approved by supervisor')..."
                        : "Write reply message to customer..."
                    }
                    className={`flex-1 px-4 py-2 border rounded-xl text-xs focus:outline-none focus:ring-2 ${
                      isInternalNote
                        ? "border-amber-300 bg-amber-50/40 focus:ring-amber-500"
                        : "border-slate-300 bg-white focus:ring-indigo-500"
                    }`}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!replyMessage.trim()}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50 flex items-center gap-1.5 text-white ${
                      isInternalNote ? "bg-amber-600 hover:bg-amber-700" : "bg-indigo-600 hover:bg-indigo-700"
                    }`}
                  >
                    <Send className="w-3.5 h-3.5" /> {isInternalNote ? "Save Note" : "Send Reply"}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400 h-[700px] flex flex-col items-center justify-center">
              <Ticket className="w-12 h-12 text-slate-300 mb-3" />
              <p className="text-sm font-medium">Select a ticket from the left queue to open the workbench</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
