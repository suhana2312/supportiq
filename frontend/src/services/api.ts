import {
  mockUsers,
  mockOrders,
  mockRefunds,
  mockTickets,
  mockDocs,
  mockFAQs,
  mockAnalytics
} from "./mockData";
import { User, TokenResponse, Order, Refund, SupportTicket, FAQ, Document } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
}

// In-memory demo state for GitHub Pages standalone execution
let localOrders = [...mockOrders];
let localRefunds = [...mockRefunds];
let localTickets = [...mockTickets];
let localFAQs = [...mockFAQs];
let localUsers = [...mockUsers];

export async function apiRequest<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const isGitHubPages = typeof window !== "undefined" && window.location.hostname.includes("github.io");

  // If on GitHub Pages, use standalone client-side demo mode
  if (isGitHubPages) {
    return handleMockRequest<T>(endpoint, options);
  }

  // Otherwise try real backend first, with automatic fallback
  try {
    const token = localStorage.getItem("supportiq_access_token");
    let url = `${BASE_URL}${endpoint}`;
    if (options.params) {
      const searchParams = new URLSearchParams();
      Object.entries(options.params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          searchParams.append(k, String(v));
        }
      });
      const qs = searchParams.toString();
      if (qs) url += `?${qs}`;
    }

    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    };

    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    let response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      // If 404 or backend unavailable, fallback to mock demo handler
      if (response.status === 404 || response.status === 502 || response.status === 503) {
        return handleMockRequest<T>(endpoint, options);
      }
      const data = await response.json().catch(() => null);
      throw new Error(data?.error?.message || `Request failed with status ${response.status}`);
    }

    const data = await response.json();
    return data.data;
  } catch (err: any) {
    console.warn(`[SupportIQ] Backend call to ${endpoint} failed, falling back to client-side demo mode.`);
    return handleMockRequest<T>(endpoint, options);
  }
}

function handleMockRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const body = options.body ? (typeof options.body === "string" ? JSON.parse(options.body) : options.body) : {};

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 1. Auth Login
      if (endpoint === "/auth/login" && method === "POST") {
        const { email } = body;
        let matchedUser = localUsers.find(u => u.email.toLowerCase() === (email || "").toLowerCase());
        if (!matchedUser) {
          matchedUser = {
            id: `user-${Date.now()}`,
            organization_id: "org-acme-1",
            name: email.split("@")[0],
            email: email,
            role: email.includes("admin") ? "ORGANIZATION_ADMIN" : email.includes("agent") ? "SUPPORT_AGENT" : "CUSTOMER",
            is_active: true,
            created_at: new Date().toISOString()
          };
          localUsers.push(matchedUser);
        }
        const tokenRes: TokenResponse = {
          access_token: "mock-jwt-token-gh-pages",
          refresh_token: "mock-refresh-token-gh-pages",
          token_type: "bearer",
          user: matchedUser
        };
        return resolve(tokenRes as unknown as T);
      }

      // 2. Auth Register
      if (endpoint === "/auth/register" && method === "POST") {
        const newUser: User = {
          id: `user-${Date.now()}`,
          organization_id: "org-acme-1",
          name: body.name || "Demo User",
          email: body.email,
          role: "ORGANIZATION_ADMIN",
          is_active: true,
          created_at: new Date().toISOString()
        };
        localUsers.push(newUser);
        return resolve({
          access_token: "mock-jwt-token-gh-pages",
          refresh_token: "mock-refresh-token-gh-pages",
          token_type: "bearer",
          user: newUser
        } as unknown as T);
      }

      // 3. Organization Me
      if (endpoint === "/organization/me") {
        return resolve({
          id: "org-acme-1",
          name: "Acme Tech Retail",
          slug: "acme-retail",
          ai_settings: {
            model: "gpt-4o-mini",
            temperature: 0.2,
            top_k: 4,
            chunk_size: 1000,
            chunk_overlap: 150,
            escalation_threshold: 2
          }
        } as unknown as T);
      }

      // 4. Orders
      if (endpoint.startsWith("/orders")) {
        if (endpoint.includes("/number/")) {
          const num = endpoint.split("/number/")[1];
          const ord = localOrders.find(o => o.order_number === num) || localOrders[0];
          return resolve(ord as unknown as T);
        }
        return resolve({
          items: localOrders,
          total: localOrders.length,
          page: 1,
          page_size: 20,
          total_pages: 1
        } as unknown as T);
      }

      // 5. Refunds
      if (endpoint.startsWith("/refunds")) {
        if (endpoint === "/refunds/check-eligibility" && method === "POST") {
          const num = (body.order_number || "").replace("#", "");
          const is4521 = num === "4521" || !num;
          return resolve({
            eligible: is4521,
            reason: is4521 ? "Order delivered 12 days ago, fully within the 30-day return policy." : "Standard eligibility verified.",
            refund_amount: 149.99,
            order_number: num || "4521",
            requires_manual_approval: false,
            policy_citation: "refund_policy.md (Section 1.2)"
          } as unknown as T);
        }
        if (endpoint === "/refunds" && method === "POST") {
          const newRef: Refund = {
            id: `ref-${Date.now()}`,
            organization_id: "org-acme-1",
            order_id: body.order_id || "ord-4521",
            customer_id: "user-cust-1",
            amount: body.amount || 149.99,
            reason: body.reason || "Customer refund request",
            status: "REQUESTED",
            created_at: new Date().toISOString()
          };
          localRefunds.unshift(newRef);
          return resolve(newRef as unknown as T);
        }
        if (endpoint.includes("/status")) {
          const refId = endpoint.split("/")[2];
          const newStatus = endpoint.split("status_update=")[1] || "APPROVED";
          const ref = localRefunds.find(r => r.id === refId);
          if (ref) {
            ref.status = newStatus as any;
          }
          return resolve((ref || localRefunds[0]) as unknown as T);
        }
        return resolve(localRefunds as unknown as T);
      }

      // 6. Tickets
      if (endpoint.startsWith("/tickets")) {
        if (method === "POST" && endpoint === "/tickets") {
          const newTicket: SupportTicket = {
            id: `tick-${Date.now()}`,
            organization_id: "org-acme-1",
            customer_id: "user-cust-1",
            customer_name: "Customer 1 Test",
            subject: body.subject,
            description: body.description,
            priority: body.priority || "MEDIUM",
            status: "OPEN",
            ai_summary: `Customer inquiry regarding: ${body.subject}`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            messages: [
              {
                id: `tm-${Date.now()}`,
                ticket_id: `tick-${Date.now()}`,
                sender_id: "user-cust-1",
                sender_type: "CUSTOMER",
                message: body.description,
                is_internal_note: false,
                created_at: new Date().toISOString()
              }
            ]
          };
          localTickets.unshift(newTicket);
          return resolve(newTicket as unknown as T);
        }
        return resolve({
          items: localTickets,
          total: localTickets.length,
          page: 1,
          page_size: 20,
          total_pages: 1
        } as unknown as T);
      }

      // 7. Documents & FAQs
      if (endpoint === "/documents") {
        return resolve({
          items: mockDocs,
          total: mockDocs.length,
          page: 1,
          page_size: 20,
          total_pages: 1
        } as unknown as T);
      }
      if (endpoint.includes("/documents/faqs/list")) {
        return resolve(localFAQs as unknown as T);
      }
      if (endpoint === "/documents/faqs" && method === "POST") {
        const newFaq: FAQ = {
          id: `faq-${Date.now()}`,
          organization_id: "org-acme-1",
          question: body.question,
          answer: body.answer,
          category: body.category || "General",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        localFAQs.push(newFaq);
        return resolve(newFaq as unknown as T);
      }

      // 8. Analytics
      if (endpoint.includes("/analytics/overview")) {
        return resolve(mockAnalytics as unknown as T);
      }
      if (endpoint.includes("/analytics/trends")) {
        return resolve({
          conversations_trend: [
            { date: "Sep 17", count: 12 },
            { date: "Sep 18", count: 19 },
            { date: "Sep 19", count: 15 },
            { date: "Sep 20", count: 28 },
            { date: "Sep 21", count: 34 },
            { date: "Sep 22", count: 42 },
            { date: "Sep 23", count: 48 },
          ],
          tickets_trend: [
            { date: "Sep 17", count: 2 },
            { date: "Sep 18", count: 4 },
            { date: "Sep 19", count: 3 },
            { date: "Sep 20", count: 6 },
            { date: "Sep 21", count: 5 },
            { date: "Sep 22", count: 7 },
            { date: "Sep 23", count: 5 },
          ],
          ticket_categories: [
            { category: "Returns & Refunds", count: 4 },
            { category: "Shipping & Delivery", count: 3 },
            { category: "Technical Support", count: 2 },
            { category: "Billing", count: 1 },
          ],
          resolution_distribution: { AI_RESOLVED: 45, ESCALATED: 3 },
          ratings_distribution: { "5": 42, "4": 5, "3": 1, "2": 0, "1": 0 }
        } as unknown as T);
      }

      // 9. Users
      if (endpoint.startsWith("/users")) {
        return resolve({
          items: localUsers,
          total: localUsers.length,
          page: 1,
          page_size: 20,
          total_pages: 1
        } as unknown as T);
      }

      // 10. AI Chat / Conversations
      if (endpoint.startsWith("/conversations")) {
        if (endpoint === "/conversations" && method === "POST") {
          return resolve({
            id: `conv-${Date.now()}`,
            organization_id: "org-acme-1",
            user_id: "user-cust-1",
            title: body.title || "Support Conversation",
            status: "ACTIVE",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            messages: []
          } as unknown as T);
        }
        if (endpoint.includes("/messages") && method === "POST") {
          const userText = (body.content || "").toLowerCase();
          let replyContent = "I am your SupportIQ AI customer assistant. How can I help you today with your orders, returns, or technical questions?";
          let citations: any[] = [];

          if (userText.includes("4521") || userText.includes("order")) {
            replyContent = "Your order **#4521** is currently **DELIVERED**.\n\n- **Delivered Date:** Sept 11, 2026\n- **Items:** 1x SonicPro Wireless ANC Headphones ($149.99)\n- **Address:** 742 Evergreen Terrace, Springfield, OR 97477\n\nLet me know if you would like to initiate a return or tracking inquiry!";
          } else if (userText.includes("refund") || userText.includes("return")) {
            replyContent = "Under our **30-Day Money-Back Return Policy**, all items delivered within the past 30 days qualify for a full 100% refund.\n\n- **Policy Citation:** `refund_policy.md - Section 1.2`\n- **Processing Speed:** 3 to 5 business days upon carrier receipt.\n\nWould you like me to generate a return shipping label for order #4521?";
            citations = [{ document_name: "refund_policy.md", page_number: 1, relevance_score: 0.96 }];
          } else if (userText.includes("human") || userText.includes("agent") || userText.includes("manager")) {
            replyContent = "I have escalated your inquiry directly to our priority support team! Support Ticket **#TICK-9021** has been created with urgent priority. Our agent Sarah has been assigned to assist you.";
          }

          return resolve({
            id: `msg-${Date.now()}`,
            conversation_id: "conv-demo",
            sender_type: "AI",
            content: replyContent,
            created_at: new Date().toISOString(),
            citations
          } as unknown as T);
        }
        return resolve({
          items: [
            {
              id: "conv-1",
              organization_id: "org-acme-1",
              user_id: "user-cust-1",
              title: "Order #4521 Delivery Status",
              status: "ACTIVE",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1
        } as unknown as T);
      }

      // Default fallback
      return resolve({ success: true } as unknown as T);
    }, 250);
  });
}
