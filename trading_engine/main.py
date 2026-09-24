from __future__ import annotations

import os
import random

from enums import OrderType, Side
from order import OCOOrder, OTOOrder, Order
from matching_engine import MatchingEngine
from order_manager import OrderManager
from utils import setup_logger

logger = setup_logger("main")

SYMBOL = os.getenv("SYMBOL", "BTCUSDT")

def seed_demo_orders(manager: OrderManager, mid_price: float) -> None:
    """Pre-populate the book with resting liquidity (the 'market maker')."""
    for i in range (1, 6):
        manager.submit(Order(
            symbol=SYMBOL, side=Side.BUY, order_type=OrderType.LIMIT,
            quantity=0.5, price=mid_price - i * 10,
        ))
        manager.submit(Order(
        symbol=SYMBOL, side=Side.SELL, order_type=OrderType.LIMIT,
            quantity=0.5, price=mid_price + i * 10,
        ))
    logger.info("Seeded demo book around %s", mid_price)
    logger.info("Book snapshot: %s", manager.engine.book.snapshot())

