"""
Integration tests for the REST API using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client():
    application = create_app()
    return TestClient(application)


def test_submit_limit_order(client):
    resp = client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT",
        "quantity": 1.5, "price": 62000,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "NEW"

def test_submit_invalid_symbol(client):
    resp = client.post("/orders", json={
        "symbol": "FAKEUSDT", "side": "BUY", "type": "LIMIT",
        "quantity": 1.0, "price": 100,
    })
    assert resp.json()["status"] == "REJECTED"

def test_submit_market_order_no_liquidity(client):
    resp = client.post("/orders", json={
        "symbol": "ETHUSDT", "side": "BUY", "type": "MARKET", "quantity": 1.0,
    })
    assert resp.json()["status"] == "REJECTED"

def test_validate_order(client):
    resp = client.post("/orders/test", json={
        "symbol": "BTCUSDT", "side": "SELL", "type": "LIMIT",
        "quantity": 0.5, "price": 63000,
    })
    assert resp.json()["valid"] is True

def test_validate_order_fails(client):
    resp = client.post("/orders/test", json={
        "symbol": "BTCUSDT", "side": "BUY", "type": "MARKET",
        "quantity": 1.0, "price": 100,
    })
    assert resp.json()["valid"] is False

def test_get_order(client):
    create_resp = client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "SELL", "type": "LIMIT",
        "quantity": 1.0, "price": 65000,
    })
    oid = create_resp.json()["order_id"]
    resp = client.get(f"/orders/{oid}")
    assert resp.status_code == 200
    assert resp.json()["order_id"] == oid

def test_get_order_not_found(client):
    resp = client.get("/orders/nonexistent-id")
    assert resp.status_code == 404

def test_cancel_order(client):
    create_resp = client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT",
        "quantity": 1.0, "price": 59000,
    })
    oid = create_resp.json()["order_id"]
    resp = client.delete(f"/orders/{oid}")
    assert resp.json()["status"] == "CANCELED"

def test_cancel_not_found(client):
    resp = client.delete("/orders/nonexistent-id")
    assert resp.status_code == 404

def test_get_order_book(client):
    client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT",
        "quantity": 1.0, "price": 59000,
    })
    resp = client.get("/book/BTCUSDT")
    assert resp.status_code == 200
    assert len(resp.json()["bids"]) == 1

def test_get_trades(client):
    client.post("/orders", json={
        "symbol": "ETHUSDT", "side": "SELL", "type": "LIMIT",
        "quantity": 1.0, "price": 3000,
    })
    client.post("/orders", json={
        "symbol": "ETHUSDT", "side": "BUY", "type": "LIMIT",
        "quantity": 1.0, "price": 3000,
    })
    resp = client.get("/trades/ETHUSDT")
    assert len(resp.json()) == 1
