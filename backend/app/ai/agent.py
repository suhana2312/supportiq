import json
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.ai.graph import SupportIQAgentGraph, AgentState
from backend.app.models.models import Conversation, Message, Citation, User
from backend.app.models.enums import MessageSender
from backend.app.repositories.conversation_repo import ConversationRepository

class SupportAgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph = SupportIQAgentGraph(db)
        self.conv_repo = ConversationRepository(db)

    async def stream_chat_response(
        self,
        conversation_id: str,
        user_message: str,
        user: User
    ) -> AsyncGenerator[str, None]:
        """
        Executes the LangGraph agent and streams the response via Server-Sent Events (SSE).
        Emits:
        - tool_call events (when agent queries tools)
        - token events (progressive word-by-word streaming for natural UX)
        - done event (with complete response, citations, and metadata)
        """
        # 1. Retrieve or verify conversation
        conv = await self.conv_repo.get_by_org(conversation_id, user.organization_id)
        if not conv:
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': 'Conversation not found'}})}\n\n"
            return

        # 2. Persist the customer's incoming message
        customer_msg = Message(
            conversation_id=conversation_id,
            sender_type=MessageSender.USER,
            content=user_message,
            metadata_json={}
        )
        await self.conv_repo.add_message(customer_msg)

        # 3. Retrieve conversation history for contextual memory
        history_msgs = [
            {"role": "user" if m.sender_type == MessageSender.USER else "assistant", "content": m.content}
            for m in conv.messages[-6:]  # Context window management: last 6 turns
        ]
        history_msgs.append({"role": "user", "content": user_message})

        # 4. Notify frontend: Agent starting analysis
        yield f"data: {json.dumps({'event': 'status', 'data': {'status': 'Thinking and analyzing intent...'}})}\n\n"
        await asyncio.sleep(0.05)

        # 5. Run the LangGraph workflow
        state: AgentState = await self.graph.execute(
            messages=history_msgs,
            customer_id=user.id,
            organization_id=user.organization_id,
            conversation_id=conversation_id
        )

        # 6. Stream tool execution events to frontend
        for tool in state.get("tool_calls_made", []):
            yield f"data: {json.dumps({'event': 'tool_call', 'data': tool})}\n\n"
            await asyncio.sleep(0.05)

        # 7. Stream response tokens progressively
        final_answer = state.get("final_answer", "")
        # Tokenize by words for responsive real-time streaming feel
        words = final_answer.split(" ")
        for idx, word in enumerate(words):
            token = word + (" " if idx < len(words) - 1 else "")
            yield f"data: {json.dumps({'event': 'token', 'data': {'token': token}})}\n\n"
            await asyncio.sleep(0.02)  # Natural typing latency (20ms)

        # 8. Persist the AI response message and citations
        ai_msg = Message(
            conversation_id=conversation_id,
            sender_type=MessageSender.AI,
            content=final_answer,
            metadata_json={
                "intent": state.get("detected_intent"),
                "confidence": state.get("confidence_score"),
                "is_escalated": state.get("is_escalated")
            }
        )
        saved_ai_msg = await self.conv_repo.add_message(ai_msg)

        citations_list = []
        for cit in state.get("citations", []):
            citation_obj = Citation(
                message_id=saved_ai_msg.id,
                document_name=cit["document_name"],
                relevance_score=cit["relevance_score"],
                page_number=cit["page_number"]
            )
            citations_list.append(citation_obj)

        if citations_list:
            await self.conv_repo.add_citations(citations_list)

        # 9. Emit the completion event with full metadata
        yield f"data: {json.dumps({'event': 'done', 'data': {'message_id': saved_ai_msg.id, 'answer': final_answer, 'citations': state.get('citations', []), 'intent': state.get('detected_intent'), 'is_escalated': state.get('is_escalated')}})}\n\n"

    async def get_response_sync(
        self,
        conversation_id: str,
        user_message: str,
        user: User
    ) -> Dict[str, Any]:
        """Synchronous chat response execution for standard REST tests."""
        conv = await self.conv_repo.get_by_org(conversation_id, user.organization_id)
        if not conv:
            raise ValueError("Conversation not found")

        customer_msg = Message(
            conversation_id=conversation_id,
            sender_type=MessageSender.USER,
            content=user_message,
            metadata_json={}
        )
        await self.conv_repo.add_message(customer_msg)

        history_msgs = [
            {"role": "user" if m.sender_type == MessageSender.USER else "assistant", "content": m.content}
            for m in conv.messages[-6:]
        ]
        history_msgs.append({"role": "user", "content": user_message})

        state = await self.graph.execute(
            messages=history_msgs,
            customer_id=user.id,
            organization_id=user.organization_id,
            conversation_id=conversation_id
        )

        ai_msg = Message(
            conversation_id=conversation_id,
            sender_type=MessageSender.AI,
            content=state["final_answer"],
            metadata_json={
                "intent": state.get("detected_intent"),
                "confidence": state.get("confidence_score")
            }
        )
        saved_ai_msg = await self.conv_repo.add_message(ai_msg)

        citations_list = []
        for cit in state.get("citations", []):
            citation_obj = Citation(
                message_id=saved_ai_msg.id,
                document_name=cit["document_name"],
                relevance_score=cit["relevance_score"],
                page_number=cit["page_number"]
            )
            citations_list.append(citation_obj)

        if citations_list:
            await self.conv_repo.add_citations(citations_list)

        return {
            "message_id": saved_ai_msg.id,
            "answer": state["final_answer"],
            "citations": state.get("citations", []),
            "intent": state.get("detected_intent"),
            "is_escalated": state.get("is_escalated")
        }
