"""
MatchingEngine v2.1 — FIXED WebSocket broadcasts.

Uses asyncio.run_coroutine_threadsafe() to properly schedule
async broadcasts from the synchronous matching thread.
"""

from __future__ import annotations

import asyncio
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from app.config import DEFAULT_BOOK_DEPTH, FLOAT_TOLERANCE, SUPPORTED_SYMBOLS
from app.engine.order_book import OrderBook
from app.engine.validators import validate_order
from app.models.enums import OrderSide, OrderStatus, OrderType, TimeInForce
from app.models.order import Order, OrderRequest
from app.models.trade import Trade

if TYPE_CHECKING:
    from app.api.websocket import ConnectionManager


class MatchingEngine:
    def __init__(self, ws_manager=None, db_session_factory=None) -> None:
        self._lock = threading.RLock()
        self._books: dict[str, OrderBook] = {
            sym: OrderBook(sym) for sym in SUPPORTED_SYMBOLS
        }
        self._orders: dict[str, Order] = {}
        self._trades: dict[str, Trade] = {}
        self._trades_by_symbol: dict[str, list[Trade]] = defaultdict(list)
        self._stop_orders: dict[str, list[Order]] = defaultdict(list)
        self._last_trade_price: dict[str, float] = {}
        self._ws_manager: Optional[ConnectionManager] = ws_manager
        self._db_session_factory = db_session_factory
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Store the running asyncio event loop (call from startup)."""
        self._loop = loop

    # == PUBLIC API ==

    def submit_order(self, request: OrderRequest) -> Order:
        with self._lock:
            valid, msg = validate_order(request)
            if not valid:
                order = Order(request)
                order.reject(msg)
                self._orders[order.order_id] = order
                self._persist_order(order)
                self._broadcast_order(order)
                return order

            order = Order(request)
            self._orders[order.order_id] = order

            processors = {
                OrderType.LIMIT: self._process_limit_order,
                OrderType.MARKET: self._process_market_order,
                OrderType.LIMIT_MAKER: self._process_limit_maker_order,
                OrderType.STOP_LOSS: self._process_stop_loss_order,
                OrderType.STOP_LOSS_LIMIT: self._process_stop_loss_limit_order,
            }
            processors[order.type](order)
            self._persist_order(order)
            self._broadcast_order(order)
            self._broadcast_book(order.symbol)
            return order

    def cancel_order(self, order_id: str) -> Optional[Order]:
        with self._lock:
            order = self._orders.get(order_id)
            if order is None:
                return None
            book = self._books.get(order.symbol)
            if book and book.has_order(order_id):
                book.remove_order(order_id)
            if order.status == OrderStatus.PENDING_TRIGGER:
                stops = self._stop_orders.get(order.symbol, [])
                self._stop_orders[order.symbol] = [
                    o for o in stops if o.order_id != order_id
                ]
            order.cancel()
            self._persist_order(order)
            self._broadcast_order(order)
            self._broadcast_book(order.symbol)
            return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def get_order_book(self, symbol: str, depth: int = DEFAULT_BOOK_DEPTH) -> Optional[dict]:
        symbol = symbol.upper()
        book = self._books.get(symbol)
        if book is None:
            return None
        snapshot = book.get_snapshot(depth)
        snapshot["symbol"] = symbol
        snapshot["last_trade_price"] = self._last_trade_price.get(symbol)
        snapshot["timestamp"] = datetime.now(timezone.utc).isoformat()
        return snapshot

    def get_trades(self, symbol: str, limit: int = 50) -> list[dict]:
        symbol = symbol.upper()
        trades = self._trades_by_symbol.get(symbol, [])
        return [t.to_dict() for t in trades[-limit:]]

    def get_all_orders(self) -> list[dict]:
        return [o.to_dict() for o in self._orders.values()]

    def test_order(self, request: OrderRequest) -> dict:
        valid, msg = validate_order(request)
        details = {
            "symbol": request.symbol, "side": request.side.value,
            "type": request.type.value, "quantity": request.quantity,
            "price": request.price, "stop_price": request.stop_price,
            "time_in_force": request.time_in_force.value,
        }
        return {"valid": valid, "message": msg, "order_details": details}

    # == ORDER PROCESSORS ==

    def _process_limit_order(self, order: Order) -> None:
        book = self._books[order.symbol]
        if order.time_in_force == TimeInForce.FOK:
            if not self._can_fully_fill_limit(order, book):
                order.reject("FOK order cannot be fully filled immediately")
                return
        self._match_limit_order(order, book)
        if order.remaining_quantity <= FLOAT_TOLERANCE:
            return
        if order.time_in_force == TimeInForce.IOC:
            order.cancel()
        else:
            book.add_order(order)

    def _process_market_order(self, order: Order) -> None:
        book = self._books[order.symbol]
        self._match_market_order(order, book)
        if order.remaining_quantity > FLOAT_TOLERANCE:
            if order.filled_quantity > FLOAT_TOLERANCE:
                order.cancel()
            else:
                order.reject("No liquidity available for market order")

    def _process_limit_maker_order(self, order: Order) -> None:
        book = self._books[order.symbol]
        if order.side == OrderSide.BUY:
            if book.best_ask is not None and order.price >= book.best_ask:
                order.reject(f"LIMIT_MAKER buy would match (price {order.price} >= best ask {book.best_ask})")
                return
        else:
            if book.best_bid is not None and order.price <= book.best_bid:
                order.reject(f"LIMIT_MAKER sell would match (price {order.price} <= best bid {book.best_bid})")
                return
        book.add_order(order)

    def _process_stop_loss_order(self, order: Order) -> None:
        last_price = self._last_trade_price.get(order.symbol)
        if last_price is not None and self._is_stop_triggered(order, last_price):
            order.type = OrderType.MARKET
            self._process_market_order(order)
        else:
            order.status = OrderStatus.PENDING_TRIGGER
            self._stop_orders[order.symbol].append(order)

    def _process_stop_loss_limit_order(self, order: Order) -> None:
        last_price = self._last_trade_price.get(order.symbol)
        if last_price is not None and self._is_stop_triggered(order, last_price):
            order.type = OrderType.LIMIT
            order.status = OrderStatus.NEW
            self._process_limit_order(order)
        else:
            order.status = OrderStatus.PENDING_TRIGGER
            self._stop_orders[order.symbol].append(order)

    # == MATCHING LOGIC ==

    def _match_limit_order(self, order, book):
        if order.side == OrderSide.BUY:
            self._match_buy_limit(order, book)
        else:
            self._match_sell_limit(order, book)

    def _match_buy_limit(self, order, book):
        while order.remaining_quantity > FLOAT_TOLERANCE:
            best = book.peek_best_ask_order()
            if best is None or best.price > order.price:
                break
            fill_qty = min(order.remaining_quantity, best.remaining_quantity)
            self._execute_trade(order.symbol, best.price, fill_qty, order, best, best, order)
            if best.remaining_quantity <= FLOAT_TOLERANCE:
                book.remove_best_ask()

    def _match_sell_limit(self, order, book):
        while order.remaining_quantity > FLOAT_TOLERANCE:
            best = book.peek_best_bid_order()
            if best is None or best.price < order.price:
                break
            fill_qty = min(order.remaining_quantity, best.remaining_quantity)
            self._execute_trade(order.symbol, best.price, fill_qty, best, order, best, order)
            if best.remaining_quantity <= FLOAT_TOLERANCE:
                book.remove_best_bid()

    def _match_market_order(self, order, book):
        if order.side == OrderSide.BUY:
            while order.remaining_quantity > FLOAT_TOLERANCE:
                best = book.peek_best_ask_order()
                if best is None:
                    break
                fill_qty = min(order.remaining_quantity, best.remaining_quantity)
                self._execute_trade(order.symbol, best.price, fill_qty, order, best, best, order)
                if best.remaining_quantity <= FLOAT_TOLERANCE:
                    book.remove_best_ask()
        else:
            while order.remaining_quantity > FLOAT_TOLERANCE:
                best = book.peek_best_bid_order()
                if best is None:
                    break
                fill_qty = min(order.remaining_quantity, best.remaining_quantity)
                self._execute_trade(order.symbol, best.price, fill_qty, best, order, best, order)
                if best.remaining_quantity <= FLOAT_TOLERANCE:
                    book.remove_best_bid()

    # == TRADE EXECUTION ==

    def _execute_trade(self, symbol, price, quantity, buy_order, sell_order, maker, taker):
        trade = Trade(
            symbol=symbol, price=price, quantity=quantity,
            buyer_order_id=buy_order.order_id, seller_order_id=sell_order.order_id,
            maker_order_id=maker.order_id, taker_order_id=taker.order_id,
        )
        buy_order.fill(quantity, trade.trade_id)
        sell_order.fill(quantity, trade.trade_id)
        self._trades[trade.trade_id] = trade
        self._trades_by_symbol[symbol].append(trade)
        self._last_trade_price[symbol] = price

        self._persist_trade(trade)
        self._persist_order(buy_order)
        self._persist_order(sell_order)
        self._broadcast_trade(trade)

        self._check_stop_triggers(symbol, price)
        return trade

    # == STOP TRIGGERS ==

    def _check_stop_triggers(self, symbol, price):
        pending = self._stop_orders.get(symbol, [])
        still_pending, triggered = [], []
        for stop_order in pending:
            if self._is_stop_triggered(stop_order, price):
                triggered.append(stop_order)
            else:
                still_pending.append(stop_order)
        self._stop_orders[symbol] = still_pending
        for stop_order in triggered:
            if stop_order.type == OrderType.STOP_LOSS:
                stop_order.type = OrderType.MARKET
                stop_order.status = OrderStatus.NEW
                self._process_market_order(stop_order)
            elif stop_order.type == OrderType.STOP_LOSS_LIMIT:
                stop_order.type = OrderType.LIMIT
                stop_order.status = OrderStatus.NEW
                self._process_limit_order(stop_order)
            self._persist_order(stop_order)
            self._broadcast_order(stop_order)

    @staticmethod
    def _is_stop_triggered(order, price):
        if order.side == OrderSide.BUY:
            return price >= order.stop_price
        return price <= order.stop_price

    def _can_fully_fill_limit(self, order, book):
        needed = order.remaining_quantity
        if order.side == OrderSide.BUY:
            for key in book._asks.keys():
                if key > order.price:
                    break
                for resting in book._asks[key]:
                    needed -= resting.remaining_quantity
                    if needed <= FLOAT_TOLERANCE:
                        return True
        else:
            for key in book._bids.keys():
                if -key < order.price:
                    break
                for resting in book._bids[key]:
                    needed -= resting.remaining_quantity
                    if needed <= FLOAT_TOLERANCE:
                        return True
        return False

    # == PERSISTENCE HOOKS ==

    def _persist_order(self, order):
        if self._db_session_factory is None:
            return
        try:
            from app.database.models import OrderRecord
            db = self._db_session_factory()
            record = db.query(OrderRecord).filter(
                OrderRecord.order_id == order.order_id
            ).first()
            if record is None:
                record = OrderRecord(
                    order_id=order.order_id, client_order_id=order.client_order_id,
                    symbol=order.symbol, side=order.side.value, type=order.type.value,
                    original_quantity=order.original_quantity,
                    remaining_quantity=order.remaining_quantity,
                    filled_quantity=order.filled_quantity, price=order.price,
                    stop_price=order.stop_price, time_in_force=order.time_in_force.value,
                    status=order.status.value, reject_reason=order.reject_reason,
                )
                db.add(record)
            else:
                record.remaining_quantity = order.remaining_quantity
                record.filled_quantity = order.filled_quantity
                record.status = order.status.value
                record.type = order.type.value
                record.reject_reason = order.reject_reason
            db.commit()
            db.close()
        except Exception:
            pass

    def _persist_trade(self, trade):
        if self._db_session_factory is None:
            return
        try:
            from app.database.models import TradeRecord
            db = self._db_session_factory()
            record = TradeRecord(
                trade_id=trade.trade_id, symbol=trade.symbol,
                price=trade.price, quantity=trade.quantity,
                buyer_order_id=trade.buyer_order_id,
                seller_order_id=trade.seller_order_id,
                maker_order_id=trade.maker_order_id,
                taker_order_id=trade.taker_order_id,
            )
            db.add(record)
            db.commit()
            db.close()
        except Exception:
            pass

    # ══════════════════════════════════════════
    # WEBSOCKET BROADCAST HOOKS — FIXED in v2.1
    # Key: asyncio.run_coroutine_threadsafe()
    # ══════════════════════════════════════════

    def _broadcast_trade(self, trade):
        if self._ws_manager is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._ws_manager.broadcast(
                f"trades:{trade.symbol}",
                {"type": "trade", "data": trade.to_dict()}
            ),
            self._loop,
        )

    def _broadcast_order(self, order):
        if self._ws_manager is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._ws_manager.broadcast(
                "orders",
                {"type": "order_update", "data": order.to_dict()}
            ),
            self._loop,
        )

    def _broadcast_book(self, symbol):
        if self._ws_manager is None or self._loop is None:
            return
        snapshot = self.get_order_book(symbol)
        asyncio.run_coroutine_threadsafe(
            self._ws_manager.broadcast(
                f"book:{symbol}",
                {"type": "book_update", "data": snapshot}
            ),
            self._loop,
        )
