"""
/orders endpoints — submit, test, query, and cancel orders.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.engine.matching_engine import MatchingEngine
from app.models.order import OrderRequest

router = APIRouter(tags=["Orders"])
_engine: MatchingEngine | None = None


def set_engine(engine: MatchingEngine) -> None:
    global _engine
    _engine = engine


@router.post("/orders", summary="Submit a new order")
def submit_order(request: OrderRequest):
    order = _engine.submit_order(request)
    return order.to_dict()


@router.post("/orders/test", summary="Validate an order (dry run)")
def test_order(request: OrderRequest):
    return _engine.test_order(request)


@router.get("/orders", summary="List all orders")
def list_orders():
    return _engine.get_all_orders()


@router.get("/orders/{order_id}", summary="Get order status")
def get_order(order_id: str):
    order = _engine.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.to_dict()


@router.delete("/orders/{order_id}", summary="Cancel an order")
def cancel_order(order_id: str):
    order = _engine.cancel_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.to_dict()
