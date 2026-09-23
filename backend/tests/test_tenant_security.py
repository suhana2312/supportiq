import pytest
from httpx import AsyncClient
from backend.app.core.security import create_access_token
from backend.app.models.models import Order, Document
from backend.app.models.enums import OrderStatus, DocumentStatus
from backend.tests.conftest import TestSessionLocal

@pytest.mark.asyncio
async def test_cross_tenant_order_access_blocked(client: AsyncClient, seeded_org_and_users):
    org2 = seeded_org_and_users["org2"]
    cust1 = seeded_org_and_users["customer1"]
    cust2 = seeded_org_and_users["customer2"]

    # Create order in Org 2
    async with TestSessionLocal() as session:
        order2 = Order(
            organization_id=org2.id,
            customer_id=cust2.id,
            order_number="ORG2-777",
            status=OrderStatus.DELIVERED,
            total_amount=500.0,
            currency="USD",
            shipping_address="777 Private Rd"
        )
        session.add(order2)
        await session.commit()
        await session.refresh(order2)
        order2_id = order2.id

    # User from Org 1 tries to access Org 2 order
    token1 = create_access_token({"sub": cust1.id, "org_id": cust1.organization_id, "role": cust1.role.value})
    resp = await client.get(
        f"/api/v1/orders/{order2_id}",
        headers={"Authorization": f"Bearer {token1}"}
    )
    # Must fail: 404 or 403
    assert resp.status_code in [403, 404]
    assert resp.json()["success"] is False

@pytest.mark.asyncio
async def test_cross_tenant_document_isolation(client: AsyncClient, seeded_org_and_users):
    org2 = seeded_org_and_users["org2"]
    admin1 = seeded_org_and_users["admin1"]

    async with TestSessionLocal() as session:
        doc2 = Document(
            organization_id=org2.id,
            filename="confidential_org2_policy.pdf",
            file_type=".pdf",
            file_size=1024,
            storage_path="/tmp/fake.pdf",
            status=DocumentStatus.PROCESSED
        )
        session.add(doc2)
        await session.commit()
        await session.refresh(doc2)
        doc2_id = doc2.id

    token_admin1 = create_access_token({"sub": admin1.id, "org_id": admin1.organization_id, "role": admin1.role.value})
    resp = await client.get(
        f"/api/v1/documents/{doc2_id}",
        headers={"Authorization": f"Bearer {token_admin1}"}
    )
    assert resp.status_code in [403, 404]
    assert resp.json()["success"] is False
