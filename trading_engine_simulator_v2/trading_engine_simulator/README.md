# 🏦 Trading Engine Simulator v2

A **production-grade, Binance-inspired exchange matching-engine simulator** with a
**Groww-style live trading UI**, **WebSocket real-time streaming**, **rate limiting**,
and **SQLite database persistence**.

---

## ✨ Features

| Area | Details |
|------|---------|
| **Order Types** | `LIMIT`, `MARKET`, `LIMIT_MAKER`, `STOP_LOSS`, `STOP_LOSS_LIMIT` |
| **Time-in-Force** | `GTC`, `IOC`, `FOK` |
| **Matching** | Price-time priority, partial fills, maker/taker tracking |
| **Stop Orders** | Auto-triggered when last-trade price crosses `stop_price` |
| **REST API** | Submit / cancel / query orders, view order book & trades |
| **WebSocket** | Real-time trade, order book, ticker & order-status updates |
| **Rate Limiting** | 120 requests/minute per IP (configurable via `slowapi`) |
| **Database** | SQLite persistence via SQLAlchemy — survives restarts |
| **Live UI** | Groww-inspired dark-theme SPA with candlestick charts |

---

## 📁 Project Structure

```
trading_engine_simulator/
├── README.md
├── requirements.txt
├── .gitignore
├── run.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── enums.py
│   │   ├── order.py
│   │   ├── trade.py
│   │   └── responses.py
│   ├── database/
│   │   ├── db.py
│   │   └── models.py
│   ├── engine/
│   │   ├── order_book.py
│   │   ├── matching_engine.py
│   │   └── validators.py
│   └── api/
│       ├── routes_orders.py
│       ├── routes_book.py
│       ├── routes_trades.py
│       └── websocket.py
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   ├── test_engine.py
│   └── test_api.py
└── scripts/
    └── demo.py
```

---

## 🚀 Quick Start

```bash
cd trading_engine_simulator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open **http://localhost:8000** for the live trading UI.
Swagger docs at **http://localhost:8000/docs**.

### Using the UI

1. Click **🌱 Seed Market** to populate the order book with demo orders
2. Place orders using the right panel (toggle BUY/SELL, choose type, enter price & qty)
3. Watch real-time updates — chart, order book, and trade feed all update via WebSocket
4. Switch symbols via the watchlist or dropdown
5. Manage orders in the **My Orders** tab (cancel open orders)

---

## 🌐 WebSocket

Connect to `ws://localhost:8000/ws` and send subscription messages:

```json
{"action": "subscribe", "channel": "trades:BTCUSDT"}
{"action": "subscribe", "channel": "book:BTCUSDT"}
{"action": "subscribe", "channel": "orders"}
```

---

## 📡 REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/orders` | Submit an order |
| `POST` | `/orders/test` | Validate (dry run) |
| `GET` | `/orders` | List all orders |
| `GET` | `/orders/{id}` | Get order status |
| `DELETE` | `/orders/{id}` | Cancel an order |
| `GET` | `/book/{symbol}` | View order book |
| `GET` | `/trades/{symbol}` | View executed trades |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📝 License

MIT — use freely for learning, interviews, and personal projects.
