"""
Pydantic response schemas for the REST API.
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel


class OrderResponse(BaseModel):
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    type: str
    original_quantity: float
    remaining_quantity: float
    filled_quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str
    status: str
    reject_reason: Optional[str] = None
    timestamp: str
    update_time: str
    trades: list[str]


class TradeResponse(BaseModel):
    trade_id: str
    symbol: str
    price: float
    quantity: float
    buyer_order_id: str
    seller_order_id: str
    maker_order_id: str
    taker_order_id: str
    timestamp: str


class OrderBookLevel(BaseModel):
    price: float
    quantity: float
    order_count: int


class OrderBookResponse(BaseModel):
    symbol: str
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]
    last_trade_price: Optional[float] = None
    timestamp: str


class ValidationResponse(BaseModel):
    valid: bool
    message: str
    order_details: Optional[dict[str, Any]] = None
