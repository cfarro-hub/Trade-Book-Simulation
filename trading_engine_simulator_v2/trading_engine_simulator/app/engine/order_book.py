"""
OrderBook — per-symbol, price-time priority order book backed by SortedDict.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

from sortedcontainers import SortedDict

from app.models.order import Order
from app.models.enums import OrderSide


class OrderBook:
    """Maintains bid and ask sides for a single trading pair."""

    def __init__(self, symbol: str) -> None:
        self.symbol: str = symbol
        self._bids: SortedDict = SortedDict()   # -price -> deque[Order]
        self._asks: SortedDict = SortedDict()   # +price -> deque[Order]
        self._order_index: dict[str, tuple[OrderSide, float]] = {}

    @property
    def best_bid(self) -> Optional[float]:
        if not self._bids:
            return None
        return -self._bids.keys()[0]

    @property
    def best_ask(self) -> Optional[float]:
        if not self._asks:
            return None
        return self._asks.keys()[0]

    @property
    def spread(self) -> Optional[float]:
        if self.best_bid is not None and self.best_ask is not None:
            return self.best_ask - self.best_bid
        return None

    def add_order(self, order: Order) -> None:
        if order.side == OrderSide.BUY:
            key = -order.price
            book_side = self._bids
        else:
            key = order.price
            book_side = self._asks
        if key not in book_side:
            book_side[key] = deque()
        book_side[key].append(order)
        self._order_index[order.order_id] = (order.side, key)

    def remove_order(self, order_id: str) -> Optional[Order]:
        if order_id not in self._order_index:
            return None
        side, price_key = self._order_index.pop(order_id)
        book_side = self._bids if side == OrderSide.BUY else self._asks
        level: deque = book_side.get(price_key, deque())
        for i, o in enumerate(level):
            if o.order_id == order_id:
                del level[i]
                if not level:
                    del book_side[price_key]
                return o
        return None

    def peek_best_bid_order(self) -> Optional[Order]:
        if not self._bids:
            return None
        return self._bids.values()[0][0]

    def peek_best_ask_order(self) -> Optional[Order]:
        if not self._asks:
            return None
        return self._asks.values()[0][0]

    def remove_best_bid(self) -> Optional[Order]:
        if not self._bids:
            return None
        key = self._bids.keys()[0]
        level: deque = self._bids[key]
        order = level.popleft()
        self._order_index.pop(order.order_id, None)
        if not level:
            del self._bids[key]
        return order

    def remove_best_ask(self) -> Optional[Order]:
        if not self._asks:
            return None
        key = self._asks.keys()[0]
        level: deque = self._asks[key]
        order = level.popleft()
        self._order_index.pop(order.order_id, None)
        if not level:
            del self._asks[key]
        return order

    def has_order(self, order_id: str) -> bool:
        return order_id in self._order_index

    def get_snapshot(self, depth: int = 20) -> dict:
        bids: list[dict] = []
        for idx, key in enumerate(self._bids.keys()):
            if idx >= depth:
                break
            level: deque = self._bids[key]
            total_qty = sum(o.remaining_quantity for o in level)
            bids.append({"price": -key, "quantity": round(total_qty, 8), "order_count": len(level)})

        asks: list[dict] = []
        for idx, key in enumerate(self._asks.keys()):
            if idx >= depth:
                break
            level: deque = self._asks[key]
            total_qty = sum(o.remaining_quantity for o in level)
            asks.append({"price": key, "quantity": round(total_qty, 8), "order_count": len(level)})

        return {"bids": bids, "asks": asks}
