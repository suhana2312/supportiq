export type UserRole = "SUPER_ADMIN" | "ORGANIZATION_ADMIN" | "SUPPORT_AGENT" | "CUSTOMER";

export interface User {
  id: string;
  organization_id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type OrderStatus =
  | "PENDING"
  | "CONFIRMED"
  | "PROCESSING"
  | "SHIPPED"
  | "OUT_FOR_DELIVERY"
  | "DELIVERED"
  | "CANCELLED";

export interface OrderItem {
  id: string;
  product_name: string;
  quantity: number;
  price: number;
}

export interface Order {
  id: string;
  organization_id: string;
  customer_id: string;
  order_number: string;
  status: OrderStatus;
  total_amount: number;
  currency: string;
  ordered_at: string;
  estimated_delivery?: string;
  delivered_at?: string;
  shipping_address: string;
  items: OrderItem[];
}

export type RefundStatus = "REQUESTED" | "APPROVED" | "REJECTED" | "PROCESSING" | "COMPLETED";

export interface Refund {
  id: string;
  organization_id: string;
  order_id: string;
  customer_id: string;
  amount: number;
  reason: string;
  status: RefundStatus;
  created_at: string;
  processed_at?: string;
}

export interface RefundCheckResult {
  eligible: boolean;
  reason: string;
  refund_amount: number;
  order_id?: string;
  order_number?: string;
  requires_manual_approval: boolean;
  policy_citation?: string;
}

export type TicketPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";
export type TicketStatus = "OPEN" | "IN_PROGRESS" | "WAITING_FOR_CUSTOMER" | "ESCALATED" | "RESOLVED" | "CLOSED";

export interface TicketMessage {
  id: string;
  ticket_id: string;
  sender_id: string;
  sender_type: string;
  message: string;
  is_internal_note: boolean;
  created_at: string;
  sender_name?: string;
}

export interface SupportTicket {
  id: string;
  organization_id: string;
  customer_id: string;
  conversation_id?: string;
  assigned_agent_id?: string;
  subject: string;
  description: string;
  priority: TicketPriority;
  status: TicketStatus;
  ai_summary?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  customer_name?: string;
  assigned_agent_name?: string;
  messages: TicketMessage[];
}

export type DocumentStatus = "UPLOADED" | "PROCESSING" | "PROCESSED" | "FAILED";

export interface Document {
  id: string;
  organization_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  uploaded_by?: string;
  error_message?: string;
  created_at: string;
  processed_at?: string;
  chunk_count?: number;
}

export interface FAQ {
  id: string;
  organization_id: string;
  question: string;
  answer: string;
  category: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  id?: string;
  document_name: string;
  page_number: number;
  relevance_score: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: "USER" | "AI" | "HUMAN_AGENT" | "SYSTEM";
  content: string;
  metadata_json?: Record<string, any>;
  created_at: string;
  citations?: Citation[];
}

export interface Conversation {
  id: string;
  organization_id: string;
  user_id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface AnalyticsOverview {
  total_customers: number;
  total_conversations: number;
  open_tickets: number;
  escalated_tickets: number;
  total_documents: number;
  ai_resolution_rate: number;
  avg_response_time_seconds: number;
  customer_satisfaction_score: number;
  total_orders: number;
  refund_requests: number;
}

export interface AnalyticsTrends {
  conversations_trend: { date: string; count: number }[];
  tickets_trend: { date: string; count: number }[];
  ticket_categories: { category: string; count: number }[];
  resolution_distribution: Record<string, number>;
  ratings_distribution: Record<string, number>;
}
