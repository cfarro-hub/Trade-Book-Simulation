"""
/trades endpoints — view executed trades.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.engine.matching_engine import MatchingEngine

router = APIRouter(tags=["Trades"])
_engine: MatchingEngine | None = None


def set_engine(engine: MatchingEngine) -> None:
    global _engine
    _engine = engine


@router.get("/trades/{symbol}", summary="View executed trades")
def get_trades(symbol: str, limit: int = Query(default=50, ge=1, le=1000)):
    return _engine.get_trades(symbol, limit)
