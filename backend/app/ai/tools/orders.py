from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.order_repo import OrderRepository

async def get_order(
    order_number: str,
    organization_id: str,
    db: AsyncSession
) -> Optional[Dict[str, Any]]:
    """
    Tool 2: Retrieves live order details by order_number.
    """
    repo = OrderRepository(db)
    # Strip any leading '#' sign
    clean_number = order_number.strip().lstrip("#")
    order = await repo.get_by_number(clean_number, organization_id)
    if not order:
        return None

    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "ordered_at": order.ordered_at.isoformat() if order.ordered_at else None,
        "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "shipping_address": order.shipping_address,
        "items": [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price": item.price
            }
            for item in order.items
        ]
    }

async def get_customer_orders(
    customer_id: str,
    organization_id: str,
    db: AsyncSession,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Tool 3: Retrieves recent orders for the authenticated customer.
    """
    repo = OrderRepository(db)
    orders = await repo.get_customer_orders(customer_id, organization_id, limit=limit)
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "status": o.status.value,
            "total_amount": o.total_amount,
            "currency": o.currency,
            "ordered_at": o.ordered_at.isoformat() if o.ordered_at else None,
            "item_count": len(o.items)
        }
        for o in orders
    ]
