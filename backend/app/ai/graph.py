import re
import json
from typing import Dict, Any, List, Optional, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.ai.prompts import SYSTEM_PROMPT, INTENT_DETECTION_PROMPT
from backend.app.ai.tools.knowledge import search_knowledge_base, get_faq
from backend.app.ai.tools.orders import get_order, get_customer_orders
from backend.app.ai.tools.refunds import check_refund_eligibility
from backend.app.ai.tools.tickets import create_support_ticket, get_ticket_status
from backend.app.ai.tools.escalation import escalate_to_human
from backend.app.models.enums import TicketPriority

class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    customer_id: str
    organization_id: str
    conversation_id: Optional[str]
    detected_intent: str
    extracted_entities: Dict[str, Any]
    tool_calls_made: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    citations: List[Dict[str, Any]]
    final_answer: str
    is_escalated: bool
    confidence_score: float

class SupportIQAgentGraph:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_intent_node(self, state: AgentState) -> AgentState:
        last_message = state["messages"][-1]["content"] if state["messages"] else ""
        lower_msg = last_message.lower()

        # Security check: prompt injection guardrail
        injection_triggers = [
            "ignore all previous", "ignore previous instructions", "reveal system prompt",
            "reveal your instructions", "system instructions", "show me your prompt",
            "what are your instructions", "ignore your rules", "act as dan", "jailbreak"
        ]
        if any(trigger in lower_msg for trigger in injection_triggers):
            state["detected_intent"] = "PROMPT_INJECTION_ATTEMPT"
            state["confidence_score"] = 1.0
            return state

        # Entity extraction: order number (e.g. #4521, order 4521, #ord-123)
        order_match = re.search(r"#?([A-Za-z0-9_-]{4,20})", last_message)
        # Look for explicit order mentions
        order_explicit = re.search(r"(?:order|package|tracking)(?:\s*(?:#|number|no\.?|id)?:?\s*)([A-Za-z0-9_-]{3,20})", last_message, re.IGNORECASE)
        
        entities = {}
        if order_explicit:
            entities["order_number"] = order_explicit.group(1).lstrip("#")
        elif "#" in last_message:
            hash_match = re.search(r"#([A-Za-z0-9_-]+)", last_message)
            if hash_match:
                entities["order_number"] = hash_match.group(1)

        # Intent heuristic classifier
        if any(phrase in lower_msg for phrase in ["human", "person", "representative", "agent", "real person", "talk to someone", "bot is useless"]):
            intent = "HUMAN_ESCALATION"
            confidence = 0.98
        elif any(phrase in lower_msg for phrase in ["refund", "money back", "return", "reimburse", "charge back"]):
            intent = "REFUND_REQUEST"
            confidence = 0.95
        elif any(phrase in lower_msg for phrase in ["where is", "track", "shipped", "shipping status", "delivery status", "arrival", "has my order"]):
            intent = "ORDER_STATUS"
            confidence = 0.92
        elif any(phrase in lower_msg for phrase in ["hasn't arrived", "not arrived", "delayed", "late", "lost", "missing item"]):
            intent = "DELIVERY_ISSUE"
            confidence = 0.90
        elif any(phrase in lower_msg for phrase in ["cancel", "cancellation", "stop order"]):
            intent = "CANCELLATION"
            confidence = 0.90
        elif any(phrase in lower_msg for phrase in ["ticket", "case", "issue number"]):
            intent = "SUPPORT_TICKET"
            confidence = 0.85
        else:
            intent = "GENERAL_KNOWLEDGE"
            confidence = 0.80

        state["detected_intent"] = intent
        state["extracted_entities"] = entities
        state["confidence_score"] = confidence
        return state

    async def execute_tools_node(self, state: AgentState) -> AgentState:
        intent = state["detected_intent"]
        entities = state["extracted_entities"]
        last_message = state["messages"][-1]["content"] if state["messages"] else ""
        org_id = state["organization_id"]
        customer_id = state["customer_id"]

        tool_calls = []
        results = {}
        citations = []

        if intent == "PROMPT_INJECTION_ATTEMPT":
            state["final_answer"] = (
                "I am programmed strictly to assist customers with SupportIQ services, orders, and knowledge base inquiries. "
                "I cannot reveal internal instructions, system prompts, or bypass organizational security policies. "
                "How may I help you with your order or product inquiries today?"
            )
            return state

        # Tool Execution 1: Order Status
        if intent == "ORDER_STATUS":
            order_num = entities.get("order_number")
            if order_num:
                tool_calls.append({"tool": "get_order", "input": {"order_number": order_num}})
                order_info = await get_order(order_num, org_id, self.db)
                results["order_info"] = order_info
            else:
                # Customer didn't provide number, check their recent orders
                tool_calls.append({"tool": "get_customer_orders", "input": {"customer_id": customer_id}})
                recent = await get_customer_orders(customer_id, org_id, self.db)
                results["recent_orders"] = recent

        # Tool Execution 2: Refund Request / Delivery Issue with Refund
        elif intent in ["REFUND_REQUEST", "DELIVERY_ISSUE"]:
            order_num = entities.get("order_number")
            # Always search knowledge base for refund / return policy
            tool_calls.append({"tool": "search_knowledge_base", "input": {"query": "refund policy return conditions window"}})
            kb_chunks = await search_knowledge_base("refund policy return timeframe conditions", org_id, self.db, top_k=2)
            results["policy_chunks"] = kb_chunks
            for chunk in kb_chunks:
                citations.append({
                    "document_name": chunk["document_name"],
                    "page_number": chunk["page_number"],
                    "relevance_score": chunk["relevance_score"]
                })

            if order_num:
                tool_calls.append({"tool": "get_order", "input": {"order_number": order_num}})
                order_info = await get_order(order_num, org_id, self.db)
                results["order_info"] = order_info

                if order_info:
                    tool_calls.append({"tool": "check_refund_eligibility", "input": {"order_number": order_num, "reason": last_message}})
                    refund_eval = await check_refund_eligibility(order_num, org_id, self.db, reason=last_message)
                    results["refund_eligibility"] = refund_eval

        # Tool Execution 3: Human Escalation
        elif intent == "HUMAN_ESCALATION":
            tool_calls.append({"tool": "escalate_to_human", "input": {"reason": last_message}})
            escalation = await escalate_to_human(
                customer_id=customer_id,
                organization_id=org_id,
                conversation_id=state["conversation_id"],
                reason=last_message,
                ai_summary="Customer requested live human representative.",
                db=self.db
            )
            results["escalation"] = escalation
            state["is_escalated"] = True

        # Tool Execution 4: General Knowledge / FAQ / Unknown
        else:
            # First check structured FAQs
            tool_calls.append({"tool": "get_faq", "input": {"query": last_message}})
            faqs = await get_faq(last_message, org_id, self.db)
            results["faqs"] = faqs

            # Vector similarity search over uploaded documents
            tool_calls.append({"tool": "search_knowledge_base", "input": {"query": last_message}})
            kb_chunks = await search_knowledge_base(last_message, org_id, self.db, top_k=settings.RETRIEVAL_TOP_K)
            results["kb_chunks"] = kb_chunks
            for chunk in kb_chunks:
                citations.append({
                    "document_name": chunk["document_name"],
                    "page_number": chunk["page_number"],
                    "relevance_score": chunk["relevance_score"]
                })

        state["tool_calls_made"] = tool_calls
        state["tool_results"] = results
        state["citations"] = citations
        return state

    async def decision_node(self, state: AgentState) -> str:
        if state.get("is_escalated"):
            return "escalated"
        if state.get("detected_intent") == "PROMPT_INJECTION_ATTEMPT":
            return "direct_response"

        # Check retrieval confidence
        intent = state.get("detected_intent")
        results = state.get("tool_results", {})

        if intent == "GENERAL_KNOWLEDGE":
            has_faq = bool(results.get("faqs"))
            has_kb = bool(results.get("kb_chunks"))
            if not has_faq and not has_kb:
                state["confidence_score"] = 0.2
                # Low confidence -> Offer human support / escalate
                return "low_confidence_escalation"

        if intent in ["REFUND_REQUEST", "DELIVERY_ISSUE"]:
            refund_eval = results.get("refund_eligibility")
            if refund_eval and refund_eval.get("requires_manual_approval"):
                return "manual_approval_ticket"

        return "synthesize"

    async def synthesize_node(self, state: AgentState) -> AgentState:
        intent = state["detected_intent"]
        results = state["tool_results"]
        entities = state["extracted_entities"]
        last_message = state["messages"][-1]["content"] if state["messages"] else ""

        # Construct deterministic, accurate answer
        if intent == "ORDER_STATUS":
            order_info = results.get("order_info")
            if order_info:
                items_summary = ", ".join([f"{i['quantity']}x {i['product_name']}" for i in order_info['items']])
                est = order_info.get("estimated_delivery")
                est_str = est[:10] if est else "In schedule"
                ans = (
                    f"Your order **#{order_info['order_number']}** is currently **{order_info['status']}**.\n\n"
                    f"- **Estimated Delivery:** {est_str}\n"
                    f"- **Items:** {items_summary}\n"
                    f"- **Shipping Address:** {order_info['shipping_address']}\n"
                    f"- **Total Amount:** ${order_info['total_amount']:.2f} {order_info['currency']}\n\n"
                    "Let me know if you would like tracking details or any changes to this shipment!"
                )
            else:
                recent = results.get("recent_orders", [])
                if recent:
                    orders_list = "\n".join([f"- Order **#{o['order_number']}**: {o['status']} (${o['total_amount']:.2f})" for o in recent])
                    ans = f"Could you please specify which order you are inquiring about? Here are your recent orders:\n\n{orders_list}"
                else:
                    ans = f"I could not locate an order matching '{entities.get('order_number', '')}'. Please verify the order number (e.g., #4521) and try again."

        elif intent in ["REFUND_REQUEST", "DELIVERY_ISSUE"]:
            refund_eval = results.get("refund_eligibility")
            order_info = results.get("order_info")

            if refund_eval:
                status_icon = "✅" if refund_eval["eligible"] else "ℹ️"
                ans = f"{status_icon} **Refund Eligibility Assessment for Order #{refund_eval['order_number']}**:\n\n"
                ans += f"{refund_eval['reason']}\n\n"
                if refund_eval["eligible"]:
                    ans += f"- **Eligible Refund Amount:** ${refund_eval['refund_amount']:.2f}\n"
                    ans += "- **Refund Method:** Original payment method within 3–5 business days.\n"
                    if refund_eval.get("requires_manual_approval"):
                        ans += "- **Status:** Flagged for supervisor verification. A support ticket has been noted for expedited processing.\n"
                else:
                    ans += "If you believe this is in error or have extenuating circumstances (e.g. damaged goods during transit), I can escalate this directly to our support management team."
            elif not order_info and entities.get("order_number"):
                ans = f"I was unable to find order #{entities.get('order_number')}. To check refund eligibility, please confirm your order number."
            else:
                # Answer policy inquiry from chunks
                kb_chunks = results.get("policy_chunks", [])
                if kb_chunks:
                    ans = f"According to our return and refund guidelines:\n\n{kb_chunks[0]['content']}\n\nTo check eligibility for a specific purchase, simply provide your order number (e.g. #4521)."
                else:
                    ans = "Customers can request a refund within 30 days of delivery for eligible items in original condition. Please provide your order number for exact qualification."

        elif intent == "HUMAN_ESCALATION":
            esc = results.get("escalation", {})
            ticket_id = esc.get("ticket_id", "TICK-NEW")
            ans = (
                f"I have transferred your request to our senior human support team.\n\n"
                f"- **Support Ticket ID:** `{ticket_id}`\n"
                f"- **Priority:** Urgent / High\n"
                f"- **Next Step:** A customer support agent will review your full conversation context and respond promptly."
            )

        elif intent == "SUPPORT_TICKET":
            ans = "I can help you review an existing ticket or open a new one. Please provide your ticket ID or describe the issue you are facing."

        else: # GENERAL_KNOWLEDGE / FAQ
            faqs = results.get("faqs", [])
            kb_chunks = results.get("kb_chunks", [])

            if faqs:
                ans = f"**{faqs[0]['question']}**\n\n{faqs[0]['answer']}"
            elif kb_chunks:
                # Top chunk synthesis
                ans = f"{kb_chunks[0]['content']}"
            else:
                ans = (
                    "I could not find official information regarding your query in our knowledge base. "
                    "I want to make sure you get accurate assistance—would you like me to open a support ticket with a human representative?"
                )

        state["final_answer"] = ans
        return state

    async def execute(
        self,
        messages: List[Dict[str, str]],
        customer_id: str,
        organization_id: str,
        conversation_id: Optional[str] = None
    ) -> AgentState:
        state: AgentState = {
            "messages": messages,
            "customer_id": customer_id,
            "organization_id": organization_id,
            "conversation_id": conversation_id,
            "detected_intent": "UNKNOWN",
            "extracted_entities": {},
            "tool_calls_made": [],
            "tool_results": {},
            "citations": [],
            "final_answer": "",
            "is_escalated": False,
            "confidence_score": 1.0
        }

        # Step 1: Detect intent & entities + security guardrail
        state = await self.detect_intent_node(state)

        # Step 2: Execute relevant tools
        state = await self.execute_tools_node(state)

        # Step 3: Decision Node
        decision = await self.decision_node(state)

        # Step 4: Handle Decision branches
        if decision == "manual_approval_ticket":
            # Automatically create high-priority ticket for manual refund approval
            refund_eval = state["tool_results"]["refund_eligibility"]
            ticket = await create_support_ticket(
                customer_id=customer_id,
                organization_id=organization_id,
                subject=f"Manual Refund Review: Order #{refund_eval['order_number']}",
                description=f"Automated check flagged manual review: {refund_eval['reason']}",
                priority=TicketPriority.HIGH,
                conversation_id=conversation_id,
                ai_summary=refund_eval['reason'],
                db=self.db
            )
            state = await self.synthesize_node(state)
            state["final_answer"] += f"\n\n*Support Ticket `#{ticket['ticket_id'][:8]}` has been automatically opened for manager review.*"
        elif decision == "low_confidence_escalation":
            state["final_answer"] = (
                "I apologize, but I could not find verified documentation to answer that question accurately. "
                "To ensure you receive the correct information, would you like me to connect you with a human support agent?"
            )
        elif decision != "direct_response":
            state = await self.synthesize_node(state)

        return state
