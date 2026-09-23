import asyncio
import os
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.db.database import AsyncSessionLocal
from backend.app.models.models import (
    Organization, User, Order, OrderItem, Refund, SupportTicket, TicketMessage,
    FAQ, Document, DocumentChunk, Conversation, Message, Feedback, Citation
)
from backend.app.models.enums import (
    UserRole, OrderStatus, RefundStatus, TicketPriority, TicketStatus,
    DocumentStatus, MessageSender
)
from backend.app.services.document_service import DocumentProcessor

async def enrich_database():
    print("[SHOWCASE] Connecting to SupportIQ Database...")
    async with AsyncSessionLocal() as session:
        # 1. Fetch Organization and Users
        res = await session.execute(select(Organization).where(Organization.slug == "acme-retail"))
        org = res.scalar_one_or_none()
        if not org:
            print("[ERROR] Acme Tech Retail organization not found. Please run seed.py first.")
            return

        # Fetch users
        users_res = await session.execute(
            select(User).where(User.organization_id == org.id)
        )
        users = list(users_res.scalars().all())
        admin = next((u for u in users if u.role == UserRole.ORGANIZATION_ADMIN), None)
        agents = [u for u in users if u.role == UserRole.SUPPORT_AGENT]
        customers = [u for u in users if u.role == UserRole.CUSTOMER]

        if not admin or not agents or not customers:
            print("[ERROR] Required users not found.")
            return

        agent_sarah = agents[0]
        agent_alex = agents[1] if len(agents) > 1 else agents[0]
        cust1 = customers[0]
        cust2 = customers[1] if len(customers) > 1 else customers[0]
        cust3 = customers[2] if len(customers) > 2 else customers[0]

        now = datetime.now(timezone.utc)

        # 2. Enrich Orders with Line Items
        print("[SHOWCASE] Ensuring all orders have detailed line items...")
        orders_res = await session.execute(
            select(Order).options(selectinload(Order.items)).where(Order.organization_id == org.id)
        )
        orders = list(orders_res.scalars().all())

        product_catalog = [
            ("Apex Pro Mechanical Gaming Keyboard", 129.99),
            ("ProSound True Wireless ANC Earbuds", 89.99),
            ("Thunderbolt 4 Docking Station 12-in-1", 199.50),
            ("Smart Thermostat Pro Gen 3", 159.00),
            ("Titanium Series Smart Fitness Watch", 249.99),
            ("4K Ultra HD Streaming Webcam", 79.99),
            ("Ergonomic Mesh Lumbar Desk Chair", 289.00),
            ("Braided Fast Charge USB-C 2M Cable", 19.99),
            ("Magnetic Qi2 Wireless Charging Pad", 39.99),
            ("Noise-Isolating Studio Studio Monitor", 349.00)
        ]

        for i, order in enumerate(orders):
            if not order.items or len(order.items) == 0:
                p1_name, p1_price = product_catalog[i % len(product_catalog)]
                p2_name, p2_price = product_catalog[(i + 3) % len(product_catalog)]
                item1 = OrderItem(order_id=order.id, product_name=p1_name, quantity=1, price=p1_price)
                session.add(item1)
                if i % 3 == 0:
                    item2 = OrderItem(order_id=order.id, product_name=p2_name, quantity=2, price=p2_price)
                    session.add(item2)
        await session.commit()

        # 3. Add Showcase Refund Requests
        print("[SHOWCASE] Seeding Showcase Refund Requests...")
        existing_refunds = await session.execute(select(Refund).where(Refund.organization_id == org.id))
        if len(list(existing_refunds.scalars().all())) == 0:
            order_4523 = next((o for o in orders if o.order_number == "4523"), orders[2])
            order_4522 = next((o for o in orders if o.order_number == "4522"), orders[1])
            order_4526 = next((o for o in orders if o.order_number == "4526"), orders[5])
            order_4527 = next((o for o in orders if o.order_number == "4527"), orders[6])

            refunds = [
                # 1. Pending high-value refund request for Admin review
                Refund(
                    organization_id=org.id,
                    order_id=order_4523.id,
                    customer_id=order_4523.customer_id,
                    amount=order_4523.total_amount,
                    reason="Screen arrived cracked during shipping. Requesting replacement or complete refund under high-value policy.",
                    status=RefundStatus.REQUESTED,
                    created_at=now - timedelta(hours=4)
                ),
                # 2. Completed automatic cancellation refund
                Refund(
                    organization_id=org.id,
                    order_id=order_4522.id,
                    customer_id=order_4522.customer_id,
                    amount=order_4522.total_amount,
                    reason="Order cancelled before warehouse dispatch. 100% automated refund.",
                    status=RefundStatus.COMPLETED,
                    created_at=now - timedelta(days=2),
                    processed_at=now - timedelta(days=2)
                ),
                # 3. Approved refund awaiting payment settlement
                Refund(
                    organization_id=org.id,
                    order_id=order_4526.id,
                    customer_id=order_4526.customer_id,
                    amount=120.00,
                    reason="Customer returned merchandise within 30-day window. Warehouse inspection passed.",
                    status=RefundStatus.APPROVED,
                    created_at=now - timedelta(days=1),
                    processed_at=now - timedelta(hours=12)
                ),
                # 4. Processing refund
                Refund(
                    organization_id=org.id,
                    order_id=order_4527.id,
                    customer_id=order_4527.customer_id,
                    amount=order_4527.total_amount,
                    reason="Defective power supply unit confirmed by support diagnostic.",
                    status=RefundStatus.PROCESSING,
                    created_at=now - timedelta(days=3)
                )
            ]
            session.add_all(refunds)
            await session.commit()

        # 4. Enrich Support Tickets with Interactive Message Threads & Internal Notes
        print("[SHOWCASE] Adding realistic conversation threads to support tickets...")
        tickets_res = await session.execute(
            select(SupportTicket).options(selectinload(SupportTicket.messages)).where(SupportTicket.organization_id == org.id)
        )
        tickets = list(tickets_res.scalars().all())

        for idx, ticket in enumerate(tickets):
            if not ticket.messages or len(ticket.messages) == 0:
                t_msgs = [
                    TicketMessage(
                        ticket_id=ticket.id,
                        sender_id=ticket.customer_id,
                        sender_type="CUSTOMER",
                        message=f"Hello, I am contacting you regarding: {ticket.description}. Could you please help me resolve this as soon as possible?",
                        is_internal_note=False,
                        created_at=ticket.created_at + timedelta(minutes=5)
                    ),
                    TicketMessage(
                        ticket_id=ticket.id,
                        sender_id=agent_sarah.id,
                        sender_type="SUPPORT_AGENT",
                        message="[Internal Note]: Checked order history and customer loyalty profile. No prior delivery complaints. Authorizing standard resolution protocol.",
                        is_internal_note=True,
                        created_at=ticket.created_at + timedelta(minutes=25)
                    ),
                    TicketMessage(
                        ticket_id=ticket.id,
                        sender_id=agent_sarah.id,
                        sender_type="SUPPORT_AGENT",
                        message=f"Hi there! Thank you for reaching out to Acme Tech Retail. I am looking into your request regarding '{ticket.subject}'. We have logged this with our fulfillment team and will provide an update shortly.",
                        is_internal_note=False,
                        created_at=ticket.created_at + timedelta(minutes=30)
                    )
                ]

                if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                    t_msgs.append(
                        TicketMessage(
                            ticket_id=ticket.id,
                            sender_id=agent_sarah.id,
                            sender_type="SUPPORT_AGENT",
                            message="Good news! Your issue has been fully processed and resolved according to company policy. Please reply if you need any further assistance.",
                            is_internal_note=False,
                            created_at=ticket.created_at + timedelta(hours=2)
                        )
                    )
                session.add_all(t_msgs)
        await session.commit()

        # 5. Add Realistic Multi-Turn Conversations with AI Agent
        print("[SHOWCASE] Seeding Showcase AI Support Conversations with citations & tools...")
        # Check existing conversation titles
        conv_res = await session.execute(select(Conversation).where(Conversation.organization_id == org.id))
        existing_convs = list(conv_res.scalars().all())

        if len(existing_convs) <= 1:
            # Showcase Conversation 2: RAG Knowledge Base Search & Citation
            conv2 = Conversation(
                organization_id=org.id,
                user_id=cust2.id,
                title="Return Policy for Opened Hardware",
                status="COMPLETED"
            )
            session.add(conv2)
            await session.commit()
            await session.refresh(conv2)

            msg2_1 = Message(
                conversation_id=conv2.id,
                sender_type=MessageSender.USER,
                content="Hi! I opened my wireless keyboard but realized I want a mechanical one instead. Can I still return it?",
                created_at=now - timedelta(hours=3, minutes=10)
            )
            msg2_2 = Message(
                conversation_id=conv2.id,
                sender_type=MessageSender.AI,
                content="Yes! According to our **Return and Refund Policy**, you can return opened electronics within **30 calendar days** of delivery for a full refund, provided the item is in like-new condition with all original packaging and accessories.\n\nOnce received and inspected by our warehouse team, refunds are typically credited back to your original payment method in **3 to 5 business days**.",
                metadata_json={
                    "intent": "POLICY_INQUIRY",
                    "tools_called": ["search_knowledge_base"]
                },
                created_at=now - timedelta(hours=3, minutes=9)
            )
            session.add_all([msg2_1, msg2_2])
            await session.commit()
            await session.refresh(msg2_2)

            # Add Citation
            session.add(Citation(
                message_id=msg2_2.id,
                document_name="refund_policy.md",
                page_number=1,
                relevance_score=0.94
            ))

            # Add 5-Star CSAT Rating
            session.add(Feedback(
                conversation_id=conv2.id,
                message_id=msg2_2.id,
                rating=5,
                comment="Super fast response and very clear policy citation!"
            ))

            # Showcase Conversation 3: Human Escalation Flow
            conv3 = Conversation(
                organization_id=org.id,
                user_id=cust3.id,
                title="Urgent: Damaged Package Escalation",
                status="ESCALATED"
            )
            session.add(conv3)
            await session.commit()
            await session.refresh(conv3)

            msg3_1 = Message(
                conversation_id=conv3.id,
                sender_type=MessageSender.USER,
                content="My 4K monitor package arrived completely crushed and the screen is shattered! I need to speak with a human supervisor immediately!",
                created_at=now - timedelta(hours=1, minutes=45)
            )
            msg3_2 = Message(
                conversation_id=conv3.id,
                sender_type=MessageSender.AI,
                content="I am so sorry to hear that your monitor arrived damaged! I understand how frustrating this is.\n\nI have immediately escalated this to our priority support supervisor team and created an **URGENT** support ticket (**#TICK-8492**).\n\nOur agent Sarah has been assigned to your ticket and will follow up with a complimentary expedited return label and immediate replacement.",
                metadata_json={
                    "intent": "HUMAN_ESCALATION",
                    "tools_called": ["escalate_to_human", "create_support_ticket"],
                    "ticket_id": "TICK-8492"
                },
                created_at=now - timedelta(hours=1, minutes=44)
            )
            session.add_all([msg3_1, msg3_2])
            await session.commit()

        # 6. Ingest Additional Markdown Knowledge Docs
        print("[SHOWCASE] Adding supplementary knowledge base policies...")
        processor = DocumentProcessor(session)

        vip_policy = """# Acme Tech Retail — VIP Customer Perks & Loyalty Program
Section 1: Loyalty Tiers
Acme Tech Retail rewards frequent customers through three distinct membership tiers:
- Silver Member: Annual spend of $500+. Free standard shipping on all orders.
- Gold Member: Annual spend of $1,500+. Free expedited 2-day delivery, 45-day return window.
- Platinum Member: Annual spend of $3,000+. Dedicated 24/7 VIP concierge line, 60-day return window, no restocking fees on opened high-end electronics.

Section 2: Extended Returns
Gold and Platinum members receive automatic extensions beyond the standard 30-day return policy to 45 and 60 days respectively."""

        intl_shipping = """# Acme Tech Retail — International Shipping and Customs
Section 1: International Coverage
We ship to over 55 countries worldwide via DHL Express and FedEx International Priority.

Section 2: Customs, Duties & Taxes
All applicable customs duties and VAT taxes are calculated and collected directly at checkout (DDP - Delivered Duty Paid). Customers will not be charged any unexpected fees upon arrival.

Section 3: Delivery Timelines
- Canada & Mexico: 2 to 4 business days.
- United Kingdom & European Union: 3 to 5 business days.
- Asia-Pacific & Australia: 4 to 7 business days."""

        extra_docs = [
            ("vip_loyalty_perks.md", ".md", vip_policy),
            ("international_shipping.md", ".md", intl_shipping)
        ]

        for fname, ftype, content in extra_docs:
            doc_exist = await session.execute(
                select(Document).where(Document.organization_id == org.id, Document.filename == fname)
            )
            if not doc_exist.scalar_one_or_none():
                fpath = os.path.join(settings.UPLOAD_DIR, fname)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)

                d = Document(
                    organization_id=org.id,
                    filename=fname,
                    file_type=ftype,
                    file_size=len(content.encode("utf-8")),
                    storage_path=fpath,
                    status=DocumentStatus.PROCESSED,
                    uploaded_by=admin.id,
                    processed_at=now
                )
                session.add(d)
                await session.commit()
                await session.refresh(d)

                chunks = processor.split_into_chunks([(1, content)], chunk_size=800, chunk_overlap=100)
                chunk_objs = []
                for c in chunks:
                    emb = processor.generate_embedding(c["content"])
                    chunk_objs.append(DocumentChunk(
                        document_id=d.id,
                        organization_id=org.id,
                        content=c["content"],
                        page_number=c["page_number"],
                        chunk_index=c["chunk_index"],
                        metadata_json={"document_id": d.id, "filename": fname},
                        embedding_json=json.dumps(emb)
                    ))
                session.add_all(chunk_objs)
                await session.commit()

        print("\n[SUCCESS] Showcase data successfully loaded into SupportIQ!")
        print("="*60)
        print("[OK] 20 Detailed retail orders with line items & statuses")
        print("[OK] 4 Varied refund claims (Requested, Approved, Processing, Completed)")
        print("[OK] 10 Support tickets with customer/agent threads and internal notes")
        print("[OK] 3 Multi-turn AI chat transcripts with citations & CSAT ratings")
        print("[OK] 5 Categorized Knowledge Base documents with vector embeddings")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(enrich_database())
