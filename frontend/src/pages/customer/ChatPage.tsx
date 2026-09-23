import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../../context/AuthContext";
import { apiRequest } from "../../services/api";
import { Message, Conversation, Citation } from "../../types";
import {
  Send,
  Bot,
  User as UserIcon,
  Sparkles,
  FileText,
  AlertCircle,
  Star,
  CheckCircle,
  HelpCircle,
  Headphones,
  RefreshCw,
  Copy,
  ChevronDown,
  ChevronUp,
  Cpu
} from "lucide-react";

export const ChatPage: React.FC = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  const [toolLogs, setToolLogs] = useState<any[]>([]);
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, number>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestionPrompts = [
    "Where is my order #4521?",
    "What is your return and refund policy?",
    "Can I get a refund for order #4521?",
    "How long does standard shipping take?",
    "Talk to a human representative"
  ];

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming, toolLogs]);

  const loadConversations = async () => {
    try {
      const data = await apiRequest<{ items: Conversation[] }>("/conversations", {
        params: { page: 1, page_size: 10 }
      });
      setConversations(data.items || []);
      if (data.items && data.items.length > 0) {
        selectConversation(data.items[0].id);
      } else {
        createNewConversation();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const selectConversation = async (id: string) => {
    try {
      const conv = await apiRequest<Conversation>(`/conversations/${id}`);
      setCurrentConversation(conv);
      setMessages(conv.messages || []);
      setToolLogs([]);
    } catch (e) {
      console.error(e);
    }
  };

  const createNewConversation = async () => {
    try {
      const conv = await apiRequest<Conversation>("/conversations", {
        method: "POST",
        body: JSON.stringify({ title: "Customer Support Session" })
      });
      setConversations((prev) => [conv, ...prev]);
      setCurrentConversation(conv);
      setMessages([]);
      setToolLogs([]);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || !currentConversation || isStreaming) return;

    setInputMessage("");
    setToolLogs([]);

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversation.id,
      sender_type: "USER",
      content: text,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsStreaming(true);
    setStreamStatus("Connecting to SupportIQ Agent...");

    // Setup temporary streaming AI message
    const tempAiMsgId = `temp-ai-${Date.now()}`;
    let accumulatedAnswer = "";
    let accumulatedCitations: Citation[] = [];

    const token = localStorage.getItem("supportiq_access_token");
    const streamUrl = `/api/v1/conversations/${currentConversation.id}/stream?message=${encodeURIComponent(text)}`;

    try {
      const response = await fetch(streamUrl, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok || !response.body) {
        throw new Error("Streaming connection failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const eventPayload = JSON.parse(line.replace("data: ", ""));
              const eventType = eventPayload.event;
              const eventData = eventPayload.data;

              if (eventType === "status") {
                setStreamStatus(eventData.status);
              } else if (eventType === "tool_call") {
                setToolLogs((prev) => [...prev, eventData]);
                setStreamStatus(`Executing tool: ${eventData.tool}...`);
              } else if (eventType === "token") {
                accumulatedAnswer += eventData.token;
                setStreamStatus(null);
                setMessages((prev) => {
                  const filtered = prev.filter((m) => m.id !== tempAiMsgId);
                  return [
                    ...filtered,
                    {
                      id: tempAiMsgId,
                      conversation_id: currentConversation.id,
                      sender_type: "AI",
                      content: accumulatedAnswer,
                      citations: accumulatedCitations,
                      created_at: new Date().toISOString()
                    }
                  ];
                });
              } else if (eventType === "done") {
                accumulatedCitations = eventData.citations || [];
                setMessages((prev) => {
                  const filtered = prev.filter((m) => m.id !== tempAiMsgId);
                  return [
                    ...filtered,
                    {
                      id: eventData.message_id || tempAiMsgId,
                      conversation_id: currentConversation.id,
                      sender_type: "AI",
                      content: eventData.answer || accumulatedAnswer,
                      citations: accumulatedCitations,
                      created_at: new Date().toISOString()
                    }
                  ];
                });
              }
            } catch (err) {
              console.error("Stream parse error", err);
            }
          }
        }
      }
    } catch (err) {
      console.error("Streaming error, falling back to sync:", err);
      try {
        const fallbackRes = await apiRequest<Message>(`/conversations/${currentConversation.id}/messages`, {
          method: "POST",
          body: JSON.stringify({ content: text })
        });
        setMessages((prev) => [...prev.filter((m) => m.id !== tempAiMsgId), fallbackRes]);
      } catch (postErr: any) {
        alert(postErr.message || "Failed to get AI response.");
      }
    } finally {
      setIsStreaming(false);
      setStreamStatus(null);
    }
  };

  const handleRating = async (messageId: string, rating: number) => {
    if (!currentConversation) return;
    try {
      await apiRequest("/conversations/feedback", {
        method: "POST",
        body: JSON.stringify({
          conversation_id: currentConversation.id,
          message_id: messageId.startsWith("temp-") ? null : messageId,
          rating,
          comment: `Rated ${rating} stars via web chat`
        })
      });
      setFeedbackGiven((prev) => ({ ...prev, [messageId]: rating }));
    } catch (e) {
      console.error(e);
    }
  };

  const handleEscalateToHuman = () => {
    handleSendMessage("I would like to speak directly with a human customer support agent.");
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Left Conversation List Sidebar */}
      <div className="w-72 border-r border-slate-200 flex flex-col bg-slate-50/60 hidden md:flex shrink-0">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-semibold text-sm text-slate-800">Support Sessions</h3>
          <button
            onClick={createNewConversation}
            className="p-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium shadow-xs transition"
            title="Start New Chat"
          >
            + New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => selectConversation(c.id)}
              className={`w-full text-left p-3 rounded-xl text-xs transition flex flex-col gap-1 ${
                currentConversation?.id === c.id
                  ? "bg-white text-indigo-700 font-semibold shadow-xs border border-indigo-100"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="truncate">{c.title || "Support Chat"}</span>
                <span className="text-[10px] text-slate-400">
                  {new Date(c.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
              <span className="text-[10px] text-slate-400 truncate">ID: {c.id.slice(0, 8)}...</span>
            </button>
          ))}
        </div>

        {/* Human Escalation Action Box */}
        <div className="p-3 border-t border-slate-200 bg-white">
          <button
            onClick={handleEscalateToHuman}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-800 rounded-xl text-xs font-semibold transition shadow-xs"
          >
            <Headphones className="w-4 h-4 text-amber-600" />
            Request Human Support
          </button>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col h-full bg-white overflow-hidden">
        {/* Chat Header */}
        <div className="h-14 border-b border-slate-200 px-6 flex items-center justify-between bg-white shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                SupportIQ Assistant
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              </h2>
              <p className="text-[11px] text-slate-400">Powered by LangGraph Agent & RAG Vector Pipeline</p>
            </div>
          </div>
          <button
            onClick={handleEscalateToHuman}
            className="text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 px-3 py-1.5 rounded-lg border border-amber-200 transition md:hidden flex items-center gap-1.5"
          >
            <Headphones className="w-3.5 h-3.5" /> Escalate
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto py-12">
              <div className="w-16 h-16 rounded-3xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border border-indigo-100">
                <Sparkles className="w-8 h-8" />
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-1">How can we help you today?</h3>
              <p className="text-xs text-slate-500 mb-6">
                Ask about order status, 30-day return policy, shipping schedules, or product warranty.
              </p>
              <div className="w-full space-y-2">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Frequently Asked Questions
                </div>
                {suggestionPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSendMessage(prompt)}
                    className="w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-indigo-50/70 border border-slate-200 hover:border-indigo-200 text-xs text-slate-700 transition flex items-center justify-between group"
                  >
                    <span>{prompt}</span>
                    <Send className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 opacity-0 group-hover:opacity-100 transition" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.sender_type === "USER";
              return (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-2xl ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}
                >
                  <div
                    className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-semibold ${
                      isUser
                        ? "bg-slate-800 text-white"
                        : "bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white shadow-xs"
                    }`}
                  >
                    {isUser ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div className={`space-y-2 ${isUser ? "items-end" : "items-start"}`}>
                    <div
                      className={`p-4 rounded-2xl text-sm leading-relaxed ${
                        isUser
                          ? "bg-indigo-600 text-white rounded-br-xs shadow-xs"
                          : "bg-slate-100 text-slate-900 rounded-bl-xs border border-slate-200/70"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>

                      {/* Source Citations */}
                      {!isUser && msg.citations && msg.citations.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-200 text-xs">
                          <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 mb-1.5">
                            <FileText className="w-3.5 h-3.5 text-indigo-500" />
                            Verified Official Sources ({msg.citations.length}):
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {msg.citations.map((c, i) => (
                              <div
                                key={i}
                                className="inline-flex items-center gap-1.5 bg-white border border-slate-300 px-2 py-1 rounded-md text-[11px] font-medium text-slate-700 shadow-2xs hover:border-indigo-400 transition cursor-default"
                              >
                                <span>📄 {c.document_name}</span>
                                <span className="text-slate-400">·</span>
                                <span className="text-indigo-600 font-semibold">Page {c.page_number}</span>
                                <span className="text-slate-400">({Math.round(c.relevance_score * 100)}% match)</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Feedback Rating for AI Messages */}
                    {!isUser && (
                      <div className="flex items-center gap-2 text-xs text-slate-400 px-1">
                        <span>Was this helpful?</span>
                        <div className="flex items-center gap-0.5">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <button
                              key={star}
                              onClick={() => handleRating(msg.id, star)}
                              className={`p-0.5 hover:text-amber-500 transition ${
                                (feedbackGiven[msg.id] || 0) >= star ? "text-amber-400 fill-amber-400" : "text-slate-300"
                              }`}
                            >
                              <Star className="w-3.5 h-3.5" />
                            </button>
                          ))}
                        </div>
                        {feedbackGiven[msg.id] && (
                          <span className="text-[10px] text-emerald-600 font-medium flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" /> Thank you!
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {/* Real-time Tool Execution Logs */}
          {toolLogs.length > 0 && isStreaming && (
            <div className="max-w-md mx-auto my-2 p-2.5 rounded-xl bg-indigo-50/80 border border-indigo-100 text-xs text-indigo-900 shadow-2xs space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-[11px] text-indigo-700">
                <Cpu className="w-3.5 h-3.5 animate-spin" />
                LangGraph Tool Invocation:
              </div>
              {toolLogs.map((log, i) => (
                <div key={i} className="flex items-center justify-between text-[11px] bg-white/70 px-2 py-1 rounded">
                  <span>Executing: <code className="font-mono text-indigo-600">{log.tool}</code></span>
                  <span className="text-emerald-600 font-medium">Completed</span>
                </div>
              ))}
            </div>
          )}

          {/* Typing Indicator */}
          {streamStatus && (
            <div className="flex items-center gap-2 text-xs text-indigo-600 px-3 py-1.5 bg-indigo-50 rounded-full w-fit">
              <Bot className="w-3.5 h-3.5 animate-bounce" />
              <span>{streamStatus}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-200 bg-white shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask anything (e.g. 'Where is my order #4521?' or 'What is your refund policy?')..."
              disabled={isStreaming}
              className="flex-1 px-4 py-2.5 bg-slate-100 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isStreaming}
              className="p-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-xs transition disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400 px-1">
            <span>Official responses cited directly from verified company documentation.</span>
            <button
              onClick={handleEscalateToHuman}
              className="hover:text-indigo-600 hover:underline font-medium"
            >
              Need a human agent?
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
