#!/usr/bin/env python3
"""
Interactive demo script — run after starting the server with python run.py.
"""

import json
import requests

BASE = "http://localhost:8000"
SYMBOL = "BTCUSDT"


def pretty(label, data):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(json.dumps(data, indent=2))


def main():
    print("Trading Engine Simulator — Demo")
    print("=" * 60)

    # Seed asks
    for p in [62000, 62500, 63000]:
        r = requests.post(f"{BASE}/orders", json={
            "symbol": SYMBOL, "side": "SELL", "type": "LIMIT",
            "quantity": 1.0, "price": p,
        }).json()
        pretty(f"SELL LIMIT @ {p}", r)

    # Seed bids
    for p in [61000, 60500, 60000]:
        r = requests.post(f"{BASE}/orders", json={
            "symbol": SYMBOL, "side": "BUY", "type": "LIMIT",
            "quantity": 1.5, "price": p,
        }).json()
        pretty(f"BUY LIMIT @ {p}", r)

    # View book
    book = requests.get(f"{BASE}/book/{SYMBOL}").json()
    pretty("ORDER BOOK", book)

    # Market buy
    r = requests.post(f"{BASE}/orders", json={
        "symbol": SYMBOL, "side": "BUY", "type": "MARKET", "quantity": 1.2,
    }).json()
    pretty("MARKET BUY 1.2 BTC", r)

    # View trades
    trades = requests.get(f"{BASE}/trades/{SYMBOL}").json()
    pretty("TRADES", trades)

    print("\nDemo complete!")


if __name__ == "__main__":
    main()
