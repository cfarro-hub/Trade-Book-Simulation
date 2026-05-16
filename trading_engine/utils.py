from pathlib import Path
import os

from binance.client import Client
from dotenv import load_dotenv
import pandas as pd


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
DEFAULT_SYMBOL = "BTCUSDT"
REQUEST_TIMEOUT_SECONDS = 10


def load_binance_credentials(env_path: Path = ENV_PATH) -> tuple[str, str]:
    """Load Binance API credentials from the project .env file."""
    load_dotenv(env_path)

    api_key = os.getenv("BINANCE_API_KEY_TEST")
    api_secret = os.getenv("BINANCE_API_SECRET_TEST")

    if not api_key or not api_secret:
        raise RuntimeError(
            f"Missing Binance credentials in {env_path}. "
            "Set BINANCE_API_KEY_TEST and BINANCE_API_SECRET_TEST."
        )

    return api_key, api_secret


def create_binance_client(testnet: bool = True) -> Client:
    api_key, api_secret = load_binance_credentials()
    return Client(
        api_key,
        api_secret,
        testnet=testnet,
        requests_params={"timeout": REQUEST_TIMEOUT_SECONDS},
    )


def get_recent_trades(symbol: str = DEFAULT_SYMBOL, limit: int = 500) -> pd.DataFrame:
    client = create_binance_client()
    trades = client.get_recent_trades(symbol=symbol, limit=limit)
    return pd.DataFrame(trades)


def get_order_book(symbol: str = DEFAULT_SYMBOL) -> pd.DataFrame:
    client = create_binance_client()
    market_depth = client.get_order_book(symbol=symbol)

    bids = pd.DataFrame(market_depth["bids"], columns=["price", "bids"])
    asks = pd.DataFrame(market_depth["asks"], columns=["price", "asks"])
    return pd.concat([bids, asks]).fillna(0)


def main() -> None:
    client = create_binance_client()
    client.ping()

    recent_trades = get_recent_trades()
    print(recent_trades.head())


if __name__ == "__main__":
    main()
