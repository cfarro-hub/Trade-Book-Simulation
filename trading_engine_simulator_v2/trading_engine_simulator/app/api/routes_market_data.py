"""
/market endpoints — proxy to Binance public API for real market data,
and seed the simulator order book with real prices.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.data_loader import (
    fetch_klines_sync, fetch_recent_trades_sync,
    fetch_order_book_sync, fetch_ticker_price_sync,
)
from app.engine.matching_engine import MatchingEngine
from app.models.order import OrderRequest
from app.models.enums import OrderSide, OrderType

router = APIRouter(prefix="/market", tags=["Market Data (Binance)"])
_engine: MatchingEngine | None = None


def set_engine(engine: MatchingEngine) -> None:
    global _engine
    _engine = engine


@router.get("/klines/{symbol}", summary="Fetch real Binance klines")
def get_klines(
    symbol: str,
    interval: str = Query(default="1m"),
    limit: int = Query(default=300, ge=1, le=1000),
):
    data = fetch_klines_sync(symbol, interval, limit)
    if not data:
        raise HTTPException(status_code=502, detail="Failed to fetch from Binance")
    return data


@router.get("/trades/{symbol}", summary="Fetch real Binance trades")
def get_binance_trades(symbol: str, limit: int = Query(default=50, ge=1, le=1000)):
    data = fetch_recent_trades_sync(symbol, limit)
    if not data:
        raise HTTPException(status_code=502, detail="Failed to fetch trades from Binance")
    return data


@router.get("/depth/{symbol}", summary="Fetch real Binance order book")
def get_binance_depth(symbol: str, limit: int = Query(default=20, ge=1, le=100)):
    data = fetch_order_book_sync(symbol, limit)
    if not data["bids"] and not data["asks"]:
        raise HTTPException(status_code=502, detail="Failed to fetch depth from Binance")
    return data


@router.get("/price/{symbol}", summary="Fetch current Binance price")
def get_binance_price(symbol: str):
    price = fetch_ticker_price_sync(symbol)
    if price is None:
        raise HTTPException(status_code=502, detail="Failed to fetch price")
    return {"symbol": symbol.upper(), "price": price}


@router.post("/seed/{symbol}", summary="Seed order book with real Binance prices")
def seed_with_real_data(
    symbol: str,
    depth: int = Query(default=10, ge=1, le=50),
):
    """Fetch real Binance order book and seed the simulator."""
    symbol = symbol.upper()
    book_data = fetch_order_book_sync(symbol, depth)

    if not book_data["bids"] and not book_data["asks"]:
        raise HTTPException(status_code=502, detail="Failed to fetch Binance depth")

    orders_created = 0

    for price, qty in book_data["bids"][:depth]:
        scaled_qty = round(min(qty, 5.0), 5)
        if scaled_qty < 0.00001:
            scaled_qty = 0.001
        req = OrderRequest(
            symbol=symbol, side=OrderSide.BUY, type=OrderType.LIMIT,
            quantity=scaled_qty, price=round(price, 8),
        )
        _engine.submit_order(req)
        orders_created += 1

    for price, qty in book_data["asks"][:depth]:
        scaled_qty = round(min(qty, 5.0), 5)
        if scaled_qty < 0.00001:
            scaled_qty = 0.001
        req = OrderRequest(
            symbol=symbol, side=OrderSide.SELL, type=OrderType.LIMIT,
            quantity=scaled_qty, price=round(price, 8),
        )
        _engine.submit_order(req)
        orders_created += 1

    return {
        "message": f"Seeded {orders_created} orders from real Binance data",
        "symbol": symbol,
        "bid_levels": len(book_data["bids"][:depth]),
        "ask_levels": len(book_data["asks"][:depth]),
    }
