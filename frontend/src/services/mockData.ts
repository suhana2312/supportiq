import { User, Order, Refund, SupportTicket, FAQ, Document, AnalyticsOverview } from "../types";

export const mockUsers: User[] = [
  {
    id: "user-admin-1",
    organization_id: "org-acme-1",
    name: "Alice Admin",
    email: "admin@supportiq.com",
    role: "ORGANIZATION_ADMIN",
    is_active: true,
    created_at: new Date(Date.now() - 30 * 86400000).toISOString(),
  },
  {
    id: "user-agent-1",
    organization_id: "org-acme-1",
    name: "Sarah Agent",
    email: "agent.sarah@supportiq.com",
    role: "SUPPORT_AGENT",
    is_active: true,
    created_at: new Date(Date.now() - 25 * 86400000).toISOString(),
  },
  {
    id: "user-agent-2",
    organization_id: "org-acme-1",
    name: "Alex Agent",
    email: "agent.alex@supportiq.com",
    role: "SUPPORT_AGENT",
    is_active: true,
    created_at: new Date(Date.now() - 20 * 86400000).toISOString(),
  },
  {
    id: "user-cust-1",
    organization_id: "org-acme-1",
    name: "Customer 1 Test",
    email: "customer1@example.com",
    role: "CUSTOMER",
    is_active: true,
    created_at: new Date(Date.now() - 15 * 86400000).toISOString(),
  }
];

export const mockOrders: Order[] = [
  {
    id: "ord-4521",
    organization_id: "org-acme-1",
    customer_id: "user-cust-1",
    order_number: "4521",
    status: "DELIVERED",
    total_amount: 149.99,
    currency: "USD",
    ordered_at: new Date(Date.now() - 16 * 86400000).toISOString(),
    delivered_at: new Date(Date.now() - 12 * 86400000).toISOString(),
    shipping_address: "742 Evergreen Terrace, Springfield, OR 97477",
    items: [
      { id: "item-1", product_name: "SonicPro Wireless ANC Headphones", quantity: 1, price: 149.99 }
    ]
  },
  {
    id: "ord-4522",
    organization_id: "org-acme-1",
    customer_id: "user-cust-1",
    order_number: "4522",
    status: "CANCELLED",
    total_amount: 89.50,
    currency: "USD",
    ordered_at: new Date(Date.now() - 2 * 86400000).toISOString(),
    shipping_address: "742 Evergreen Terrace, Springfield, OR 97477",
    items: [
      { id: "item-2", product_name: "Ergonomic Bluetooth Keyboard", quantity: 1, price: 89.50 }
    ]
  },
  {
    id: "ord-4523",
    organization_id: "org-acme-1",
    customer_id: "user-cust-1",
    order_number: "4523",
    status: "DELIVERED",
    total_amount: 1250.00,
    currency: "USD",
    ordered_at: new Date(Date.now() - 10 * 86400000).toISOString(),
    delivered_at: new Date(Date.now() - 6 * 86400000).toISOString(),
    shipping_address: "742 Evergreen Terrace, Springfield, OR 97477",
    items: [
      { id: "item-3", product_name: "UltraView 4K Curved Gaming Monitor", quantity: 1, price: 1250.00 }
    ]
  },
  {
    id: "ord-4524",
    organization_id: "org-acme-1",
    customer_id: "user-cust-1",
    order_number: "4524",
    status: "DELIVERED",
    total_amount: 65.00,
    currency: "USD",
    ordered_at: new Date(Date.now() - 50 * 86400000).toISOString(),
    delivered_at: new Date(Date.now() - 45 * 86400000).toISOString(),
    shipping_address: "742 Evergreen Terrace, Springfield, OR 97477",
    items: [
      { id: "item-4", product_name: "USB-C Dual 100W GaN Fast Charger", quantity: 1, price: 65.00 }
    ]
  },
  {
    id: "ord-4525",
    organization_id: "org-acme-1",
    customer_id: "user-cust-1",
    order_number: "4525",
    status: "SHIPPED",
    total_amount: 210.00,
    currency: "USD",
    ordered_at: new Date(Date.now() - 3 * 86400000).toISOString(),
    estimated_delivery: new Date(Date.now() + 2 * 86400000).toISOString(),
    shipping_address: "742 Evergreen Terrace, Springfield, OR 97477",
    items: [
      { id: "item-5", product_name: "Smart Home Environmental Hub", quantity: 1, price: 210.00 }
    ]
  }
];

export const mockRefunds: Refund[] = [
  {
    id: "ref-4523",
    organization_id: "org-acme-1",
    order_id: "ord-4523",
    customer_id: "user-cust-1",
    amount: 1250.00,
    reason: "Screen defect found on delivery. Exceeds $500 threshold requiring manual supervisor review.",
    status: "REQUESTED",
    created_at: new Date(Date.now() - 4 * 3600000).toISOString()
  },
  {
    id: "ref-4522",
    organization_id: "org-acme-1",
    order_id: "ord-4522",
    customer_id: "user-cust-1",
    amount: 89.50,
    reason: "Order cancelled before warehouse dispatch. Automated 100% refund.",
    status: "COMPLETED",
    created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
    processed_at: new Date(Date.now() - 2 * 86400000).toISOString()
  },
  {
    id: "ref-4526",
    organization_id: "org-acme-1",
    order_id: "ord-4526",
    customer_id: "user-cust-1",
    amount: 120.00,
    reason: "Merchandise returned within 30-day window. Warehouse inspection passed.",
    status: "APPROVED",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    processed_at: new Date(Date.now() - 12 * 3600000).toISOString()
  }
];

export const mockTickets: SupportTicket[] = [
  {
    id: "tick-1",
    organization_id: "org-acme-1",
    customer_id: "user-cust-1",
    customer_name: "Customer 1 Test",
    assigned_agent_id: "user-agent-1",
    assigned_agent_name: "Sarah Agent",
    subject: "Where is my package?",
    description: "Order delayed past estimated delivery date.",
    priority: "MEDIUM",
    status: "OPEN",
    ai_summary: "Automated summary: Where is my package?. Customer contacted support regarding delivery delay.",
    created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    messages: [
      {
        id: "tm-1",
        ticket_id: "tick-1",
        sender_id: "user-cust-1",
        sender_type: "CUSTOMER",
        message: "Hello, could you please give me an update on when my shipment will arrive?",
        is_internal_note: false,
        created_at: new Date(Date.now() - 2 * 86400000).toISOString()
      },
      {
        id: "tm-2",
        ticket_id: "tick-1",
        sender_id: "user-agent-1",
        sender_type: "SUPPORT_AGENT",
        message: "[Internal Note]: Contacted carrier dispatch. Package was transferred to local facility.",
        is_internal_note: true,
        created_at: new Date(Date.now() - 36 * 3600000).toISOString()
      },
      {
        id: "tm-3",
        ticket_id: "tick-1",
        sender_id: "user-agent-1",
        sender_type: "SUPPORT_AGENT",
        message: "Hi! The carrier has scanned your parcel at the regional depot. It is out for delivery today.",
        is_internal_note: false,
        created_at: new Date(Date.now() - 24 * 3600000).toISOString()
      }
    ]
  },
  {
    id: "tick-2",
    organization_id: "org-acme-1",
    customer_id: "user-cust-1",
    customer_name: "Customer 1 Test",
    assigned_agent_id: "user-agent-1",
    assigned_agent_name: "Sarah Agent",
    subject: "Screen damaged on arrival",
    description: "Screen has a crack across top corner.",
    priority: "URGENT",
    status: "ESCALATED",
    ai_summary: "Urgent hardware damage reported for 4K curved display.",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 4 * 3600000).toISOString(),
    messages: [
      {
        id: "tm-4",
        ticket_id: "tick-2",
        sender_id: "user-cust-1",
        sender_type: "CUSTOMER",
        message: "The packaging box was dented and the screen is completely cracked!",
        is_internal_note: false,
        created_at: new Date(Date.now() - 86400000).toISOString()
      },
      {
        id: "tm-5",
        ticket_id: "tick-2",
        sender_id: "user-agent-1",
        sender_type: "SUPPORT_AGENT",
        message: "We have prioritized your claim and dispatched a pre-paid return label. A replacement unit has been reserved.",
        is_internal_note: false,
        created_at: new Date(Date.now() - 4 * 3600000).toISOString()
      }
    ]
  }
];

export const mockDocs: Document[] = [
  {
    id: "doc-1",
    organization_id: "org-acme-1",
    filename: "refund_policy.md",
    file_type: ".md",
    file_size: 1420,
    status: "PROCESSED",
    chunk_count: 2,
    created_at: new Date(Date.now() - 10 * 86400000).toISOString()
  },
  {
    id: "doc-2",
    organization_id: "org-acme-1",
    filename: "shipping_policy.md",
    file_type: ".md",
    file_size: 1100,
    status: "PROCESSED",
    chunk_count: 1,
    created_at: new Date(Date.now() - 9 * 86400000).toISOString()
  },
  {
    id: "doc-3",
    organization_id: "org-acme-1",
    filename: "product_warranty.md",
    file_type: ".md",
    file_size: 890,
    status: "PROCESSED",
    chunk_count: 1,
    created_at: new Date(Date.now() - 8 * 86400000).toISOString()
  },
  {
    id: "doc-4",
    organization_id: "org-acme-1",
    filename: "vip_loyalty_perks.md",
    file_type: ".md",
    file_size: 950,
    status: "PROCESSED",
    chunk_count: 1,
    created_at: new Date(Date.now() - 7 * 86400000).toISOString()
  },
  {
    id: "doc-5",
    organization_id: "org-acme-1",
    filename: "international_shipping.md",
    file_type: ".md",
    file_size: 820,
    status: "PROCESSED",
    chunk_count: 1,
    created_at: new Date(Date.now() - 6 * 86400000).toISOString()
  }
];

export const mockFAQs: FAQ[] = [
  {
    id: "faq-1",
    organization_id: "org-acme-1",
    question: "What is your return and refund policy?",
    answer: "We offer a 30-day money-back guarantee on all eligible products delivered within the last 30 days. Items must be returned in their original packaging with all included accessories. Pre-shipment cancellations are eligible for immediate 100% automatic refunds.",
    category: "Returns & Refunds",
    created_at: new Date(Date.now() - 20 * 86400000).toISOString(),
    updated_at: new Date(Date.now() - 20 * 86400000).toISOString(),
  },
  {
    id: "faq-2",
    organization_id: "org-acme-1",
    question: "How long does standard shipping take?",
    answer: "Standard domestic shipping typically takes 3 to 5 business days from our fulfillment centers. Expedited 2-day delivery is available at checkout.",
    category: "Shipping",
    created_at: new Date(Date.now() - 19 * 86400000).toISOString(),
    updated_at: new Date(Date.now() - 19 * 86400000).toISOString(),
  },
  {
    id: "faq-3",
    organization_id: "org-acme-1",
    question: "What does the product warranty cover?",
    answer: "All hardware purchases come with an automatic 1-year limited manufacturer warranty covering internal hardware defects and component malfunctions.",
    category: "Warranty",
    created_at: new Date(Date.now() - 18 * 86400000).toISOString(),
    updated_at: new Date(Date.now() - 18 * 86400000).toISOString(),
  }
];

export const mockAnalytics: AnalyticsOverview = {
  total_customers: 245,
  total_conversations: 48,
  open_tickets: 5,
  escalated_tickets: 2,
  total_documents: 5,
  ai_resolution_rate: 94.2,
  avg_response_time_seconds: 1.4,
  customer_satisfaction_score: 5.0,
  total_orders: 20,
  refund_requests: 4
};
