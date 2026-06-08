"""
Application-wide configuration constants.
"""

APP_TITLE: str = "Trading Engine Simulator"
APP_VERSION: str = "2.0.0"
APP_DESCRIPTION: str = (
    "A Binance-inspired exchange matching engine simulator with a "
    "Groww-style live trading UI, WebSocket streaming, rate limiting, "
    "and SQLite persistence."
)

SUPPORTED_SYMBOLS: set[str] = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
}

MIN_QUANTITY: float = 0.00001
MIN_PRICE: float = 0.01
DEFAULT_BOOK_DEPTH: int = 20
FLOAT_TOLERANCE: float = 1e-10

DATABASE_URL: str = "sqlite:///./trading_engine.db"
RATE_LIMIT: str = "120/minute"
