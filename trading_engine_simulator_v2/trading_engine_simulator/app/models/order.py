"""
Order request schema (Pydantic) and internal Order domain object.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.enums import OrderSide, OrderStatus, OrderType, TimeInForce
from app.config import FLOAT_TOLERANCE


class OrderRequest(BaseModel):
    """Inbound order request from the REST API."""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    client_order_id: Optional[str] = None

    @field_validator("symbol", mode="before")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()


class Order:
    """Internal order representation used by the matching engine."""

    def __init__(self, request: OrderRequest) -> None:
        now = datetime.now(timezone.utc)
        self.order_id: str = str(uuid.uuid4())
        self.client_order_id: str = request.client_order_id or self.order_id
        self.symbol: str = request.symbol
        self.side: OrderSide = request.side
        self.type: OrderType = request.type
        self.original_quantity: float = request.quantity
        self.remaining_quantity: float = request.quantity
        self.filled_quantity: float = 0.0
        self.price: Optional[float] = request.price
        self.stop_price: Optional[float] = request.stop_price
        self.time_in_force: TimeInForce = request.time_in_force
        self.status: OrderStatus = OrderStatus.NEW
        self.timestamp: datetime = now
        self.update_time: datetime = now
        self.trades: list[str] = []
        self.reject_reason: Optional[str] = None

    def fill(self, quantity: float, trade_id: str) -> None:
        self.filled_quantity += quantity
        self.remaining_quantity -= quantity
        self.trades.append(trade_id)
        self.update_time = datetime.now(timezone.utc)
        if self.remaining_quantity <= FLOAT_TOLERANCE:
            self.remaining_quantity = 0.0
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELED
        self.update_time = datetime.now(timezone.utc)

    def reject(self, reason: str) -> None:
        self.status = OrderStatus.REJECTED
        self.reject_reason = reason
        self.update_time = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.type.value,
            "original_quantity": self.original_quantity,
            "remaining_quantity": self.remaining_quantity,
            "filled_quantity": self.filled_quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "time_in_force": self.time_in_force.value,
            "status": self.status.value,
            "reject_reason": self.reject_reason,
            "timestamp": self.timestamp.isoformat(),
            "update_time": self.update_time.isoformat(),
            "trades": self.trades,
        }
