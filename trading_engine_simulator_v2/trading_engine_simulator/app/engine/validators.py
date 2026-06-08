"""
Pre-submission validation for incoming order requests.
"""

from __future__ import annotations
from typing import Tuple

from app.config import MIN_PRICE, MIN_QUANTITY, SUPPORTED_SYMBOLS
from app.models.enums import OrderType
from app.models.order import OrderRequest


def validate_order(request: OrderRequest) -> Tuple[bool, str]:
    if request.symbol not in SUPPORTED_SYMBOLS:
        return False, f"Unsupported symbol: {request.symbol}"
    if request.quantity <= 0:
        return False, "Quantity must be greater than zero"
    if request.quantity < MIN_QUANTITY:
        return False, f"Quantity below minimum ({MIN_QUANTITY})"

    if request.type == OrderType.LIMIT:
        if request.price is None or request.price <= 0:
            return False, "LIMIT order requires a positive price"
        if request.price < MIN_PRICE:
            return False, f"Price below minimum ({MIN_PRICE})"

    elif request.type == OrderType.MARKET:
        if request.price is not None:
            return False, "MARKET order must not specify a price"

    elif request.type == OrderType.LIMIT_MAKER:
        if request.price is None or request.price <= 0:
            return False, "LIMIT_MAKER order requires a positive price"

    elif request.type == OrderType.STOP_LOSS:
        if request.stop_price is None or request.stop_price <= 0:
            return False, "STOP_LOSS order requires a positive stop_price"

    elif request.type == OrderType.STOP_LOSS_LIMIT:
        if request.stop_price is None or request.stop_price <= 0:
            return False, "STOP_LOSS_LIMIT order requires a positive stop_price"
        if request.price is None or request.price <= 0:
            return False, "STOP_LOSS_LIMIT order requires a positive price"

    return True, "Order is valid"
