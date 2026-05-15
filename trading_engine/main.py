from order import Order
from order_book import OrderBook
from order_types import Side, OrderType
from matching_engine import MatchingEngine
from order_manager import OrderManager


book = OrderBook()

engine = MatchingEngine(book)

manager = OrderManager(book, engine)

# -----------------------------------
# TEST 1 — LIMIT MATCH
# -----------------------------------

buy = Order(
    id=1,
    side=Side.BUY,
    quantity=10,
    price=100
)

sell = Order(
    id=2,
    side=Side.SELL,
    quantity=10,
    price=100
)

book.add_order(buy)
book.add_order(sell)

trades = engine.match()

print("\nLIMIT MATCH TEST")
print(trades)

# -----------------------------------
# TEST 2 — STOP LIMIT
# -----------------------------------

stop_order = Order(
    id=3,
    side=Side.BUY,
    quantity=5,
    price=106,
    order_type=OrderType.STOP_LIMIT,
    stop_price=105
)

manager.add_stop_order(stop_order)

manager.check_stop_orders(105)

print("\nSTOP ORDER TEST")
print(book.bids)

# -----------------------------------
# TEST 3 — OCO
# -----------------------------------

take_profit = Order(
    id=4,
    side=Side.SELL,
    quantity=5,
    price=120
)

stop_loss = Order(
    id=5,
    side=Side.SELL,
    quantity=5,
    price=95,
    order_type=OrderType.STOP_LIMIT,
    stop_price=95
)

manager.create_oco(take_profit, stop_loss)

print("\nOCO TEST")
print(book.asks)
print(manager.stop_orders)

# -----------------------------------
# TEST 4 — OTO
# -----------------------------------

parent = Order(
    id=6,
    side=Side.BUY,
    quantity=5,
    price=99
)

child = Order(
    id=7,
    side=Side.SELL,
    quantity=5,
    price=110
)

manager.create_oto(parent, child)

print("\nOTO TEST")
print(book.bids)