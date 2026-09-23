import asyncio
import os
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select

from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.db.database import async_engine, Base, AsyncSessionLocal
from backend.app.models.models import (
    Organization, User, Order, OrderItem, Refund, SupportTicket, TicketMessage,
    FAQ, Document, DocumentChunk, Conversation, Message, Feedback
)
from backend.app.models.enums import (
    UserRole, OrderStatus, RefundStatus, TicketPriority, TicketStatus,
    DocumentStatus, MessageSender
)
from backend.app.services.document_service import DocumentProcessor

async def seed_data():
    print("[INIT] Initializing Database Schema...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        res = await session.execute(select(Organization).where(Organization.slug == "acme-retail"))
        if res.scalar_one_or_none():
            print("[INFO] Database already seeded with demo organization. Skipping duplicate seed.")
            return

        print("[ORG] Creating Demo Organization 'Acme Tech Retail'...")
        org = Organization(
            name="Acme Tech Retail",
            slug="acme-retail",
            ai_settings={
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "retrieval_top_k": 4,
                "chunk_size": 1000,
                "chunk_overlap": 150,
                "similarity_threshold": 0.35,
                "auto_escalation_threshold": 0.60
            }
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)

        print("[USERS] Creating Organization Admin, Agents, and Customers...")
        admin = User(
            organization_id=org.id,
            name="Alice Admin",
            email="admin@supportiq.com",
            password_hash=hash_password("Admin123!"),
            role=UserRole.ORGANIZATION_ADMIN,
            is_active=True
        )
        agent1 = User(
            organization_id=org.id,
            name="Sarah Agent",
            email="agent.sarah@supportiq.com",
            password_hash=hash_password("Agent123!"),
            role=UserRole.SUPPORT_AGENT,
            is_active=True
        )
        agent2 = User(
            organization_id=org.id,
            name="Alex Agent",
            email="agent.alex@supportiq.com",
            password_hash=hash_password("Agent123!"),
            role=UserRole.SUPPORT_AGENT,
            is_active=True
        )
        session.add_all([admin, agent1, agent2])
        await session.commit()
        await session.refresh(admin)

        customers = []
        for i in range(1, 6):
            c = User(
                organization_id=org.id,
                name=f"Customer {i} Test",
                email=f"customer{i}@example.com",
                password_hash=hash_password("Customer123!"),
                role=UserRole.CUSTOMER,
                is_active=True
            )
            customers.append(c)
        session.add_all(customers)
        await session.commit()
        for c in customers:
            await session.refresh(c)

        primary_customer = customers[0]

        print("[ORDERS] Creating 20 Realistic Orders...")
        now = datetime.now(timezone.utc)
        orders = []

        # Order #4521 - Special benchmark scenario (Delivered 12 days ago, eligible for refund)
        order_4521 = Order(
            organization_id=org.id,
            customer_id=primary_customer.id,
            order_number="4521",
            status=OrderStatus.DELIVERED,
            total_amount=149.99,
            currency="USD",
            ordered_at=now - timedelta(days=16),
            estimated_delivery=now - timedelta(days=12),
            delivered_at=now - timedelta(days=12),
            shipping_address="742 Evergreen Terrace, Springfield, OR 97477"
        )
        orders.append(order_4521)

        # Order #4522 - Cancelled before shipment (Eligible 100%)
        orders.append(Order(
            organization_id=org.id,
            customer_id=primary_customer.id,
            order_number="4522",
            status=OrderStatus.CANCELLED,
            total_amount=89.50,
            currency="USD",
            ordered_at=now - timedelta(days=2),
            estimated_delivery=now + timedelta(days=4),
            shipping_address="742 Evergreen Terrace, Springfield, OR 97477"
        ))

        # Order #4523 - High Value (Requires Manager Review)
        orders.append(Order(
            organization_id=org.id,
            customer_id=primary_customer.id,
            order_number="4523",
            status=OrderStatus.DELIVERED,
            total_amount=1250.00,
            currency="USD",
            ordered_at=now - timedelta(days=10),
            estimated_delivery=now - timedelta(days=6),
            delivered_at=now - timedelta(days=6),
            shipping_address="742 Evergreen Terrace, Springfield, OR 97477"
        ))

        # Order #4524 - Delivered 45 days ago (Exceeded 30-day window)
        orders.append(Order(
            organization_id=org.id,
            customer_id=primary_customer.id,
            order_number="4524",
            status=OrderStatus.DELIVERED,
            total_amount=65.00,
            currency="USD",
            ordered_at=now - timedelta(days=50),
            estimated_delivery=now - timedelta(days=45),
            delivered_at=now - timedelta(days=45),
            shipping_address="742 Evergreen Terrace, Springfield, OR 97477"
        ))

        # Order #4525 - Shipped / In Transit
        orders.append(Order(
            organization_id=org.id,
            customer_id=primary_customer.id,
            order_number="4525",
            status=OrderStatus.SHIPPED,
            total_amount=210.00,
            currency="USD",
            ordered_at=now - timedelta(days=3),
            estimated_delivery=now + timedelta(days=2),
            shipping_address="742 Evergreen Terrace, Springfield, OR 97477"
        ))

        # Remaining orders 4526 - 4540 across different customers
        statuses = [
            OrderStatus.DELIVERED, OrderStatus.PROCESSING, OrderStatus.SHIPPED,
            OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CONFIRMED, OrderStatus.DELIVERED
        ]
        for idx in range(6, 21):
            cust = customers[(idx - 1) % len(customers)]
            st = statuses[(idx - 1) % len(statuses)]
            deliv = now - timedelta(days=(idx % 20) + 1) if st == OrderStatus.DELIVERED else None
            orders.append(Order(
                organization_id=org.id,
                customer_id=cust.id,
                order_number=str(4520 + idx),
                status=st,
                total_amount=round(35.0 + (idx * 17.5), 2),
                currency="USD",
                ordered_at=now - timedelta(days=idx + 2),
                estimated_delivery=now - timedelta(days=idx - 1) if deliv else now + timedelta(days=3),
                delivered_at=deliv,
                shipping_address=f"{100 + idx} Market Street, Suite {idx}, Seattle, WA 98101"
            ))

        session.add_all(orders)
        await session.commit()
        for o in orders:
            await session.refresh(o)

        print("[ITEMS] Adding Order Items...")
        items = [
            OrderItem(order_id=order_4521.id, product_name="SonicPro Wireless ANC Headphones", quantity=1, price=149.99),
            OrderItem(order_id=orders[1].id, product_name="Ergonomic Bluetooth Keyboard", quantity=1, price=89.50),
            OrderItem(order_id=orders[2].id, product_name="UltraView 4K Curved Gaming Monitor", quantity=1, price=1250.00),
            OrderItem(order_id=orders[3].id, product_name="USB-C Dual 100W GaN Fast Charger", quantity=1, price=65.00),
            OrderItem(order_id=orders[4].id, product_name="Smart Home Environmental Hub", quantity=1, price=210.00)
        ]
        session.add_all(items)
        await session.commit()

        print("[TICKETS] Creating 10 Support Tickets...")
        tickets = []
        ticket_subjects = [
            ("Where is my package?", "Order delayed past estimated delivery date.", TicketPriority.MEDIUM, TicketStatus.OPEN),
            ("Return authorization request", "Need to exchange shoe size from 10 to 11.", TicketPriority.LOW, TicketStatus.IN_PROGRESS),
            ("Damaged on arrival", "Screen has a crack across top corner.", TicketPriority.URGENT, TicketStatus.ESCALATED),
            ("Invoice copy needed", "Need tax invoice for corporate accounting.", TicketPriority.LOW, TicketStatus.RESOLVED),
            ("Cancellation request", "Accidentally placed duplicate order.", TicketPriority.HIGH, TicketStatus.CLOSED),
            ("Warranty coverage question", "Does warranty cover accidental water spill?", TicketPriority.MEDIUM, TicketStatus.OPEN),
            ("Wrong color received", "Ordered Midnight Blue but received Space Gray.", TicketPriority.MEDIUM, TicketStatus.IN_PROGRESS),
            ("Promo discount code", "Discount code did not apply at checkout.", TicketPriority.LOW, TicketStatus.RESOLVED),
            ("Billing discrepancy", "Charged twice for single cart order.", TicketPriority.URGENT, TicketStatus.ESCALATED),
            ("Technical setup assistance", "Cannot sync bluetooth headset to Windows 11.", TicketPriority.MEDIUM, TicketStatus.OPEN)
        ]

        for i, (subj, desc, prio, stat) in enumerate(ticket_subjects):
            cust = customers[i % len(customers)]
            t = SupportTicket(
                organization_id=org.id,
                customer_id=cust.id,
                assigned_agent_id=agent1.id if i % 2 == 0 else agent2.id,
                subject=subj,
                description=desc,
                priority=prio,
                status=stat,
                ai_summary=f"Automated summary: {subj}. Customer contacted support regarding {desc.lower()}"
            )
            tickets.append(t)
        session.add_all(tickets)
        await session.commit()

        print("[FAQS] Creating 5 Structured FAQs...")
        faqs = [
            FAQ(
                organization_id=org.id,
                question="What is your return and refund policy?",
                answer="We offer a 30-day money-back guarantee on all eligible products delivered within the last 30 days. Items must be returned in their original packaging with all included accessories. Pre-shipment cancellations are eligible for immediate 100% automatic refunds.",
                category="Returns & Refunds"
            ),
            FAQ(
                organization_id=org.id,
                question="How long does standard shipping take?",
                answer="Standard domestic shipping typically takes 3 to 5 business days from our fulfillment centers. Expedited 2-day delivery is available at checkout. Tracking information is sent automatically via email once the carrier scans the parcel.",
                category="Shipping"
            ),
            FAQ(
                organization_id=org.id,
                question="How do I track my active order?",
                answer="You can check your order status at any time by asking our AI agent 'Where is order #<number>?' or visiting your Customer Dashboard under 'My Orders'. Live tracking updates will display current fulfillment and carrier transit milestones.",
                category="Orders"
            ),
            FAQ(
                organization_id=org.id,
                question="What does the product warranty cover?",
                answer="All hardware purchases come with an automatic 1-year limited manufacturer warranty covering internal hardware defects, component malfunctions, and battery failures. Accidental drops or cosmetic wear are not covered.",
                category="Warranty"
            ),
            FAQ(
                organization_id=org.id,
                question="How can I speak to a human support agent?",
                answer="You can request a human representative at any point during your conversation by saying 'Talk to a human' or clicking the 'Escalate to Agent' button. Our AI agent will instantly transfer your ticket with full conversation context to our priority support queue.",
                category="Customer Support"
            )
        ]
        session.add_all(faqs)
        await session.commit()

        print("[DOCS] Generating Knowledge Base Documents and Vector Chunks...")
        # 1. Refund Policy Document
        refund_text = """# Acme Tech Retail — Return and Refund Policy
Section 1: General Policy
Customers may return products purchased from Acme Tech Retail within 30 calendar days of delivery for a full refund of the purchase price.

Section 2: Cancellation Policy
Orders that have been cancelled prior to warehouse dispatch or fulfillment are eligible for an immediate, automatic 100% refund to the original payment method.

Section 3: Standard 30-Day Return Window
To qualify for a standard refund:
1. The return request must be submitted within 30 days of the verified delivery date.
2. The product must be in like-new condition, accompanied by all original accessories and packaging.
3. Once approved, refunds are credited back to the customer's payment method within 3 to 5 business days.

Section 4: Damaged or Defective Items
If your item arrived damaged or defective, please submit a claim immediately. Defective merchandise claims qualify for a free expedited return label and immediate replacement or full refund upon inspection.

Section 5: High-Value Transaction Approvals
Refund requests exceeding $500.00 require review by a customer service supervisor. A support ticket is automatically created to expedite verification within 24 hours.

Section 6: Non-Refundable Items
Digital gift cards, downloadable software licenses, and opened consumable goods cannot be returned."""

        # 2. Shipping Policy Document
        shipping_text = """# Acme Tech Retail — Shipping & Delivery Guidelines
Section 1: Processing Times
All in-stock orders are processed and prepared for dispatch within 24 to 48 business hours of order confirmation.

Section 2: Shipping Methods & Speeds
- Standard Ground Shipping: 3 to 5 business days across the continental United States.
- Priority Expedited Shipping: 2 business days.
- Express Overnight Delivery: Next business day delivery for orders placed before 1:00 PM EST.

Section 3: Order Tracking
Upon carrier pickup, an automated email notification containing the carrier name and tracking number is dispatched to the customer's registered email address.

Section 4: In-Transit Loss & Delivery Discrepancies
If an order is marked delivered by the carrier but cannot be located, or if transit is delayed by more than 7 business days past the estimated delivery date, a delivery investigation ticket will be opened for replacement or full refund."""

        # 3. Product Warranty Document
        warranty_text = """# Acme Tech Retail — Hardware Warranty & Care
Section 1: 1-Year Limited Manufacturer Warranty
All electronics and hardware products sold by Acme Tech Retail include a complimentary 1-year limited warranty against manufacturing defects in materials and workmanship.

Section 2: Warranty Coverage
Covered issues include:
- Internal circuitry failure
- Battery failure not caused by improper voltage
- Speaker or display failure under normal operating parameters

Not covered:
- Physical damage from accidental drops or water submersion
- Unauthorized third-party modifications or repairs."""

        docs_info = [
            ("refund_policy.md", ".md", refund_text),
            ("shipping_policy.md", ".md", shipping_text),
            ("product_warranty.md", ".md", warranty_text)
        ]

        for fname, ftype, content in docs_info:
            fpath = os.path.join(settings.UPLOAD_DIR, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)

            doc_record = Document(
                organization_id=org.id,
                filename=fname,
                file_type=ftype,
                file_size=len(content.encode("utf-8")),
                storage_path=fpath,
                status=DocumentStatus.PROCESSED,
                uploaded_by=admin.id,
                processed_at=now
            )
            session.add(doc_record)
            await session.commit()
            await session.refresh(doc_record)

            # Generate chunks and embeddings
            processor = DocumentProcessor(session)
            chunks_data = processor.split_into_chunks([(1, content)], chunk_size=800, chunk_overlap=120)
            chunk_objs = []
            for c in chunks_data:
                emb = processor.generate_embedding(c["content"])
                chunk_obj = DocumentChunk(
                    document_id=doc_record.id,
                    organization_id=org.id,
                    content=c["content"],
                    page_number=c["page_number"],
                    chunk_index=c["chunk_index"],
                    metadata_json={
                        "document_id": doc_record.id,
                        "filename": fname,
                        "page_number": c["page_number"]
                    },
                    embedding_json=json.dumps(emb)
                )
                chunk_objs.append(chunk_obj)
            session.add_all(chunk_objs)
            await session.commit()

        print("[CHAT] Seeding Sample Demo Conversation...")
        conv = Conversation(
            organization_id=org.id,
            user_id=primary_customer.id,
            title="Inquiry on Order #4521 Delivery",
            status="ACTIVE"
        )
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        msg1 = Message(
            conversation_id=conv.id,
            sender_type=MessageSender.USER,
            content="Hello, can you tell me the status of my order #4521?"
        )
        msg2 = Message(
            conversation_id=conv.id,
            sender_type=MessageSender.AI,
            content="Your order **#4521** was successfully **DELIVERED** on schedule. Items: 1x SonicPro Wireless ANC Headphones.\n\nLet me know if you need assistance with this purchase or have questions about our 30-day return policy!",
            metadata_json={"intent": "ORDER_STATUS"}
        )
        session.add_all([msg1, msg2])
        await session.commit()

        # Feedback
        fb = Feedback(
            conversation_id=conv.id,
            message_id=msg2.id,
            rating=5,
            comment="Instant and accurate answer regarding my package!"
        )
        session.add(fb)
        await session.commit()

        print("\n[DONE] SEEDING COMPLETE!")
        print("="*60)
        print("Demo Organization: Acme Tech Retail (slug: acme-retail)")
        print("Admin Login:       admin@supportiq.com / Admin123!")
        print("Agent 1 Login:     agent.sarah@supportiq.com / Agent123!")
        print("Agent 2 Login:     agent.alex@supportiq.com / Agent123!")
        print("Customer Login:    customer1@example.com / Customer123!")
        print("Special Order:     #4521 (Delivered, 12 days ago, eligible for refund)")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(seed_data())
