"""
Binance Public Market Data Loader.

Fetches REAL market data from Binance using their FREE public API.
NO API key or account required.

Endpoint: https://data-api.binance.vision/api/v3/...
Reference: https://developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only
"""

from __future__ import annotations

import requests
from typing import Optional

BINANCE_BASE_URL = "https://data-api.binance.vision"


def fetch_klines_sync(
    symbol: str, interval: str = "1m", limit: int = 500,
    start_time: Optional[int] = None, end_time: Optional[int] = None,
) -> list[dict]:
    """Fetch candlestick/kline data from Binance (free, no auth)."""
    params = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time
    try:
        resp = requests.get(f"{BINANCE_BASE_URL}/api/v3/klines", params=params, timeout=10)
        resp.raise_for_status()
        return parse_klines(resp.json())
    except Exception as e:
        print(f"[data_loader] Failed to fetch klines: {e}")
        return []


def parse_klines(raw_data: list) -> list[dict]:
    """Parse raw Binance kline response."""
    candles = []
    for k in raw_data:
        candles.append({
            "time": int(k[0]) // 1000,
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return candles


def fetch_recent_trades_sync(symbol: str, limit: int = 50) -> list[dict]:
    """Fetch recent trades from Binance (public, no auth)."""
    params = {"symbol": symbol.upper(), "limit": min(limit, 1000)}
    try:
        resp = requests.get(f"{BINANCE_BASE_URL}/api/v3/trades", params=params, timeout=10)
        resp.raise_for_status()
        return [{
            "id": t["id"], "price": float(t["price"]),
            "quantity": float(t["qty"]), "time": t["time"],
            "isBuyerMaker": t["isBuyerMaker"],
        } for t in resp.json()]
    except Exception as e:
        print(f"[data_loader] Failed to fetch trades: {e}")
        return []


def fetch_order_book_sync(symbol: str, limit: int = 20) -> dict:
    """Fetch the current order book from Binance (public, no auth)."""
    params = {"symbol": symbol.upper(), "limit": min(limit, 5000)}
    try:
        resp = requests.get(f"{BINANCE_BASE_URL}/api/v3/depth", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "bids": [[float(b[0]), float(b[1])] for b in data.get("bids", [])],
            "asks": [[float(a[0]), float(a[1])] for a in data.get("asks", [])],
        }
    except Exception as e:
        print(f"[data_loader] Failed to fetch order book: {e}")
        return {"bids": [], "asks": []}


def fetch_ticker_price_sync(symbol: str) -> Optional[float]:
    """Fetch the current price for a symbol."""
    try:
        resp = requests.get(
            f"{BINANCE_BASE_URL}/api/v3/ticker/price",
            params={"symbol": symbol.upper()}, timeout=10,
        )
        resp.raise_for_status()
        return float(resp.json()["price"])
    except Exception:
        return None
