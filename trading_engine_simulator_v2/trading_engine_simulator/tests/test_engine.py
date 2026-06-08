"""
Comprehensive unit tests for the matching engine.
"""

import pytest
from app.engine.matching_engine import MatchingEngine
from app.models.enums import OrderSide, OrderStatus, OrderType, TimeInForce
from app.models.order import OrderRequest


def _limit(side, qty, price, symbol="BTCUSDT", tif=TimeInForce.GTC):
    return OrderRequest(symbol=symbol, side=side, type=OrderType.LIMIT,
                        quantity=qty, price=price, time_in_force=tif)

def _market(side, qty, symbol="BTCUSDT"):
    return OrderRequest(symbol=symbol, side=side, type=OrderType.MARKET, quantity=qty)

def _limit_maker(side, qty, price, symbol="BTCUSDT"):
    return OrderRequest(symbol=symbol, side=side, type=OrderType.LIMIT_MAKER,
                        quantity=qty, price=price)

def _stop_loss(side, qty, stop_price, symbol="BTCUSDT"):
    return OrderRequest(symbol=symbol, side=side, type=OrderType.STOP_LOSS,
                        quantity=qty, stop_price=stop_price)

def _stop_loss_limit(side, qty, price, stop_price, symbol="BTCUSDT"):
    return OrderRequest(symbol=symbol, side=side, type=OrderType.STOP_LOSS_LIMIT,
                        quantity=qty, price=price, stop_price=stop_price)


@pytest.fixture
def engine():
    return MatchingEngine()


def test_limit_buy_rests_on_empty_book(engine):
    order = engine.submit_order(_limit(OrderSide.BUY, 1.0, 60000))
    assert order.status == OrderStatus.NEW
    assert order.remaining_quantity == 1.0

def test_limit_sell_rests_on_empty_book(engine):
    order = engine.submit_order(_limit(OrderSide.SELL, 2.0, 65000))
    assert order.status == OrderStatus.NEW

def test_limit_order_full_match(engine):
    sell = engine.submit_order(_limit(OrderSide.SELL, 1.0, 60000))
    buy = engine.submit_order(_limit(OrderSide.BUY, 1.0, 60000))
    assert sell.status == OrderStatus.FILLED
    assert buy.status == OrderStatus.FILLED

def test_limit_order_partial_fill(engine):
    engine.submit_order(_limit(OrderSide.SELL, 0.5, 60000))
    buy = engine.submit_order(_limit(OrderSide.BUY, 1.0, 60000))
    assert buy.filled_quantity == pytest.approx(0.5)
    assert buy.remaining_quantity == pytest.approx(0.5)

def test_price_time_priority(engine):
    sell1 = engine.submit_order(_limit(OrderSide.SELL, 1.0, 60000))
    sell2 = engine.submit_order(_limit(OrderSide.SELL, 1.0, 60000))
    buy = engine.submit_order(_limit(OrderSide.BUY, 1.0, 60000))
    assert sell1.status == OrderStatus.FILLED
    assert sell2.status == OrderStatus.NEW

def test_market_buy_fills_against_asks(engine):
    engine.submit_order(_limit(OrderSide.SELL, 2.0, 61000))
    mkt = engine.submit_order(_market(OrderSide.BUY, 1.0))
    assert mkt.status == OrderStatus.FILLED

def test_market_sell_fills_against_bids(engine):
    engine.submit_order(_limit(OrderSide.BUY, 2.0, 59000))
    mkt = engine.submit_order(_market(OrderSide.SELL, 1.5))
    assert mkt.status == OrderStatus.FILLED

def test_market_order_no_liquidity_rejected(engine):
    mkt = engine.submit_order(_market(OrderSide.BUY, 1.0))
    assert mkt.status == OrderStatus.REJECTED

def test_limit_maker_accepted(engine):
    engine.submit_order(_limit(OrderSide.SELL, 1.0, 65000))
    lm = engine.submit_order(_limit_maker(OrderSide.BUY, 1.0, 64000))
    assert lm.status == OrderStatus.NEW

def test_limit_maker_rejected(engine):
    engine.submit_order(_limit(OrderSide.SELL, 1.0, 65000))
    lm = engine.submit_order(_limit_maker(OrderSide.BUY, 1.0, 65000))
    assert lm.status == OrderStatus.REJECTED

def test_stop_loss_triggers_on_trade(engine):
    stop = engine.submit_order(_stop_loss(OrderSide.BUY, 0.5, 62000))
    assert stop.status == OrderStatus.PENDING_TRIGGER
    engine.submit_order(_limit(OrderSide.SELL, 1.0, 62000))
    engine.submit_order(_limit(OrderSide.BUY, 0.1, 62000))
    assert stop.status == OrderStatus.FILLED

def test_stop_loss_limit_triggers_on_trade(engine):
    stop = engine.submit_order(_stop_loss_limit(OrderSide.SELL, 0.5, 57500, 58000))
    assert stop.status == OrderStatus.PENDING_TRIGGER
    engine.submit_order(_limit(OrderSide.BUY, 1.0, 58000))
    engine.submit_order(_limit(OrderSide.SELL, 0.1, 58000))
    assert stop.status == OrderStatus.FILLED

def test_stop_order_pending_when_no_trades(engine):
    stop = engine.submit_order(_stop_loss(OrderSide.SELL, 1.0, 55000))
    assert stop.status == OrderStatus.PENDING_TRIGGER

def test_fok_rejected_insufficient_liquidity(engine):
    engine.submit_order(_limit(OrderSide.SELL, 0.5, 60000))
    fok = engine.submit_order(_limit(OrderSide.BUY, 1.0, 60000, tif=TimeInForce.FOK))
    assert fok.status == OrderStatus.REJECTED

def test_fok_filled(engine):
    engine.submit_order(_limit(OrderSide.SELL, 1.0, 60000))
    fok = engine.submit_order(_limit(OrderSide.BUY, 1.0, 60000, tif=TimeInForce.FOK))
    assert fok.status == OrderStatus.FILLED

def test_ioc_partial_fill_cancels_remainder(engine):
    engine.submit_order(_limit(OrderSide.SELL, 0.3, 60000))
    ioc = engine.submit_order(_limit(OrderSide.BUY, 1.0, 60000, tif=TimeInForce.IOC))
    assert ioc.filled_quantity == pytest.approx(0.3)
    assert ioc.status == OrderStatus.CANCELED

def test_cancel_order(engine):
    order = engine.submit_order(_limit(OrderSide.BUY, 1.0, 59000))
    result = engine.cancel_order(order.order_id)
    assert result.status == OrderStatus.CANCELED

def test_order_book_snapshot(engine):
    engine.submit_order(_limit(OrderSide.BUY, 1.0, 59000))
    engine.submit_order(_limit(OrderSide.BUY, 2.0, 59000))
    engine.submit_order(_limit(OrderSide.SELL, 0.5, 61000))
    snap = engine.get_order_book("BTCUSDT")
    assert len(snap["bids"]) == 1
    assert snap["bids"][0]["quantity"] == pytest.approx(3.0)
    assert snap["bids"][0]["order_count"] == 2
    assert len(snap["asks"]) == 1
