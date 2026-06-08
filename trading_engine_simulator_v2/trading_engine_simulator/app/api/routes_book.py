"""
/book endpoints — view the order book.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.config import DEFAULT_BOOK_DEPTH
from app.engine.matching_engine import MatchingEngine

router = APIRouter(tags=["Order Book"])
_engine: MatchingEngine | None = None


def set_engine(engine: MatchingEngine) -> None:
    global _engine
    _engine = engine


@router.get("/book/{symbol}", summary="View order book")
def get_order_book(symbol: str, depth: int = Query(default=DEFAULT_BOOK_DEPTH, ge=1, le=100)):
    snapshot = _engine.get_order_book(symbol, depth)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return snapshot
