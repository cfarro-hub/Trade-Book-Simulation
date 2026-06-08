"""
SQLAlchemy ORM models for persisting orders and trades.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, Integer

from app.database.db import Base


class OrderRecord(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, unique=True, index=True, nullable=False)
    client_order_id = Column(String, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)
    type = Column(String, nullable=False)
    original_quantity = Column(Float, nullable=False)
    remaining_quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, nullable=False, default=0.0)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    time_in_force = Column(String, nullable=False)
    status = Column(String, nullable=False)
    reject_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class TradeRecord(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String, unique=True, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    buyer_order_id = Column(String, nullable=False)
    seller_order_id = Column(String, nullable=False)
    maker_order_id = Column(String, nullable=False)
    taker_order_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
