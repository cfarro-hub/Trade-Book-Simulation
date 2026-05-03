import time
import uuid
from decimal import Decimal # Recommended for financial math
from enums import Side, OrderType, OrderStatus

class Order:
    def __init__(self, side, quantity, order_type, 
                 price=None, stop_price=None, parent_id=None):
        
        # Basic Validation
        if order_type == OrderType.LIMIT and price is None:
            raise ValueError("Limit orders must have a price")
        
        self.id = str(uuid.uuid4())
        self.side = side # Side.BUY or Side.SELL
        self.quantity = Decimal(str(quantity))
        self.remaining = Decimal(str(quantity))
        
        self.type = order_type
        self.price = Decimal(str(price)) if price else None
        self.stop_price = Decimal(str(stop_price)) if stop_price else None
        
        self.status = OrderStatus.NEW
        self.timestamp = time.time_ns() # Nanoseconds are better for high-frequency sorting
        
        self.parent_id = parent_id
        self.linked_orders = []

    @property
    def is_filled(self):
        return self.remaining <= 0

    def __repr__(self):
        return (f"Order({self.id[:8]}... {self.side.name} {self.type.name} "
                f"Qty:{self.remaining}/{self.quantity} @ {self.price})")