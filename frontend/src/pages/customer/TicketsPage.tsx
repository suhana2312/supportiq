import React, { useState, useEffect } from "react";
import { apiRequest } from "../../services/api";
import { SupportTicket, TicketMessage } from "../../types";
import { Ticket, Clock, CheckCircle2, AlertTriangle, Send, Plus, MessageSquare } from "lucide-react";

export const TicketsPage: React.FC = () => {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [replyText, setReplyText] = useState("");
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSubject, setNewSubject] = useState("");
  const [newDescription, setNewDescription] = useState("");

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    try {
      const data = await apiRequest<{ items: SupportTicket[] }>("/tickets", {
        params: { page: 1, page_size: 20 }
      });
      setTickets(data.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
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

  const handleSendReply = async () => {
    if (!replyText.trim() || !selectedTicket) return;
    try {
      const newMsg = await apiRequest<TicketMessage>(`/tickets/${selectedTicket.id}/messages`, {
        method: "POST",
        body: JSON.stringify({ message: replyText, is_internal_note: false })
      });
      setSelectedTicket((prev) => prev ? { ...prev, messages: [...prev.messages, newMsg] } : null);
      setReplyText("");
    } catch (e: any) {
      alert(e.message || "Failed to send message");
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSubject.trim() || !newDescription.trim()) return;
    try {
      const created = await apiRequest<SupportTicket>("/tickets", {
        method: "POST",
        body: JSON.stringify({ subject: newSubject, description: newDescription, priority: "MEDIUM" })
      });
      setTickets((prev) => [created, ...prev]);
      setSelectedTicket(created);
      setShowCreateModal(false);
      setNewSubject("");
      setNewDescription("");
    } catch (e: any) {
      alert(e.message || "Failed to create ticket");
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Support Tickets</h1>
          <p className="text-sm text-slate-500">Track and respond to human-assisted customer support requests.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
        >
          <Plus className="w-4 h-4" /> Open New Ticket
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ticket List */}
        <div className="lg:col-span-1 space-y-3">
          {loading ? (
            <div className="p-8 text-center text-slate-400">Loading tickets...</div>
          ) : tickets.length === 0 ? (
            <div className="p-8 bg-white border border-slate-200 rounded-2xl text-center text-slate-500 text-xs">
              No support tickets found.
            </div>
          ) : (
            tickets.map((t) => (
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
                <h4 className="font-semibold text-sm text-slate-800 line-clamp-1">{t.subject}</h4>
                <p className="text-xs text-slate-500 line-clamp-2">{t.description}</p>
                <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-100 flex justify-between">
                  <span>Assigned: {t.assigned_agent_name || "Support Queue"}</span>
                  <span>{new Date(t.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Ticket Detail / Conversation Thread */}
        <div className="lg:col-span-2">
          {selectedTicket ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col h-[600px]">
              <div className="border-b border-slate-200 pb-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-indigo-600 font-semibold">
                    Ticket ID: #{selectedTicket.id}
                  </span>
                  <div className="flex items-center gap-2">
                    {getPriorityBadge(selectedTicket.priority)}
                    {getStatusBadge(selectedTicket.status)}
                  </div>
                </div>
                <h2 className="text-lg font-bold text-slate-900">{selectedTicket.subject}</h2>
                {selectedTicket.ai_summary && (
                  <div className="mt-2 p-2.5 rounded-lg bg-indigo-50/70 border border-indigo-100 text-xs text-indigo-900">
                    <strong>AI Case Summary:</strong> {selectedTicket.ai_summary}
                  </div>
                )}
              </div>

              {/* Message History */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                {selectedTicket.messages && selectedTicket.messages.map((m) => (
                  <div
                    key={m.id}
                    className={`p-3 rounded-xl text-xs leading-relaxed max-w-lg ${
                      m.sender_type === "CUSTOMER"
                        ? "ml-auto bg-indigo-600 text-white"
                        : "mr-auto bg-slate-100 text-slate-800 border border-slate-200"
                    }`}
                  >
                    <div className="font-semibold text-[10px] opacity-80 mb-1">
                      {m.sender_name || (m.sender_type === "CUSTOMER" ? "You" : "Support Agent")} ·{" "}
                      {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                    <div>{m.message}</div>
                  </div>
                ))}
              </div>

              {/* Reply Input */}
              <div className="pt-4 border-t border-slate-200 mt-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Type your response to the support team..."
                    className="flex-1 px-4 py-2 border border-slate-300 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <button
                    onClick={handleSendReply}
                    disabled={!replyText.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold transition disabled:opacity-50 flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" /> Send
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400 h-[600px] flex flex-col items-center justify-center">
              <Ticket className="w-12 h-12 text-slate-300 mb-3" />
              <p className="text-sm font-medium">Select a ticket from the left to view the conversation history</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="font-bold text-lg text-slate-900 mb-2">Create New Support Ticket</h3>
            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Subject</label>
                <input
                  type="text"
                  required
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  placeholder="e.g. Inquiry regarding international shipment"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Detailed Description</label>
                <textarea
                  required
                  rows={4}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Provide all relevant details to help our team resolve your inquiry..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold"
                >
                  Submit Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
