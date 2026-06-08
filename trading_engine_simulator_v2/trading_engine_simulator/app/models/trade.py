"""
Trade domain object — a single execution between two orders.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


class Trade:
    def __init__(
        self, symbol: str, price: float, quantity: float,
        buyer_order_id: str, seller_order_id: str,
        maker_order_id: str, taker_order_id: str,
    ) -> None:
        self.trade_id: str = str(uuid.uuid4())
        self.symbol: str = symbol
        self.price: float = price
        self.quantity: float = quantity
        self.buyer_order_id: str = buyer_order_id
        self.seller_order_id: str = seller_order_id
        self.maker_order_id: str = maker_order_id
        self.taker_order_id: str = taker_order_id
        self.timestamp: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "price": self.price,
            "quantity": self.quantity,
            "buyer_order_id": self.buyer_order_id,
            "seller_order_id": self.seller_order_id,
            "maker_order_id": self.maker_order_id,
            "taker_order_id": self.taker_order_id,
            "timestamp": self.timestamp.isoformat(),
        }
