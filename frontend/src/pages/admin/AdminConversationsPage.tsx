import React, { useState, useEffect } from "react";
import { apiRequest } from "../../services/api";
import { Conversation, Message } from "../../types";
import { MessageSquare, Bot, User, FileText, Star, Search, RefreshCw } from "lucide-react";

export const AdminConversationsPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const res = await apiRequest<{ items: Conversation[] }>("/conversations", {
        params: { page: 1, page_size: 50 }
      });
      setConversations(res.items || []);
      if (res.items && res.items.length > 0 && !selectedConversation) {
        handleSelectConversation(res.items[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConversation = async (id: string) => {
    try {
      const conv = await apiRequest<Conversation>(`/conversations/${id}`);
      setSelectedConversation(conv);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">AI Chat Transcripts & Citations Audit</h1>
          <p className="text-sm text-slate-500">
            Review live conversations between customers and the LangGraph AI agent.
          </p>
        </div>
        <button
          onClick={loadConversations}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left List */}
        <div className="lg:col-span-1 bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden h-[650px] flex flex-col">
          <div className="p-4 border-b border-slate-200 font-bold text-xs uppercase tracking-wider text-slate-500">
            Past Conversations ({conversations.length})
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {loading ? (
              <div className="p-6 text-center text-slate-400 text-xs">Loading sessions...</div>
            ) : conversations.length === 0 ? (
              <div className="p-6 text-center text-slate-400 text-xs">No conversations recorded yet.</div>
            ) : (
              conversations.map((c) => (
                <div
                  key={c.id}
                  onClick={() => handleSelectConversation(c.id)}
                  className={`p-3.5 cursor-pointer transition flex flex-col gap-1 ${
                    selectedConversation?.id === c.id
                      ? "bg-indigo-50/70 border-l-4 border-indigo-600"
                      : "hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-slate-900 line-clamp-1">{c.title}</span>
                    <span className="text-[10px] text-slate-400">{new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">ID: #{c.id.slice(0, 8)}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Transcript Inspection */}
        <div className="lg:col-span-2">
          {selectedConversation ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col h-[650px]">
              <div className="border-b border-slate-200 pb-3 mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-indigo-600 font-semibold">
                    Session ID: #{selectedConversation.id}
                  </span>
                  <span className="text-xs text-slate-400">
                    Started on {new Date(selectedConversation.created_at).toLocaleString()}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-1">{selectedConversation.title}</h3>
              </div>

              {/* Message Transcript */}
              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {selectedConversation.messages && selectedConversation.messages.map((m) => {
                  const isUser = m.sender_type === "USER";
                  return (
                    <div
                      key={m.id}
                      className={`flex gap-3 max-w-xl ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}
                    >
                      <div
                        className={`w-7 h-7 rounded-full shrink-0 flex items-center justify-center text-xs font-bold ${
                          isUser ? "bg-slate-800 text-white" : "bg-indigo-600 text-white"
                        }`}
                      >
                        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                      </div>

                      <div
                        className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                          isUser ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-800 border border-slate-200"
                        }`}
                      >
                        <div className="whitespace-pre-wrap">{m.content}</div>

                        {/* Citations Audit */}
                        {!isUser && m.citations && m.citations.length > 0 && (
                          <div className="mt-2.5 pt-2 border-t border-slate-200 text-[11px] text-slate-600 space-y-1">
                            <span className="font-semibold text-indigo-700 flex items-center gap-1">
                              <FileText className="w-3 h-3" /> Cited Official Knowledge ({m.citations.length}):
                            </span>
                            {m.citations.map((cit, i) => (
                              <div key={i} className="bg-white/80 border border-slate-200 p-1.5 rounded">
                                📄 {cit.document_name} · Page {cit.page_number} ({Math.round(cit.relevance_score * 100)}% match)
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400 h-[650px] flex flex-col items-center justify-center">
              <MessageSquare className="w-12 h-12 text-slate-300 mb-3" />
              <p className="text-sm font-medium">Select a conversation from the left to view transcripts</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
