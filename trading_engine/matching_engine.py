from order import Order
from order_book import OrderBook
from matching_engine import MatchingEngine
from enums import Side, OrderType

# Create order book
book = OrderBook()

# Create matching engine
engine = MatchingEngine(book)

# ---------------------------------
# CREATE LIMIT BUY ORDER
# ---------------------------------

buy_order = Order(
    side=Side.BUY,
    quantity=10,
    order_type=OrderType.LIMIT,
    price=100
)

# ---------------------------------
# CREATE LIMIT SELL ORDER
# ---------------------------------

sell_order = Order(
    side=Side.SELL,
    quantity=10,
    order_type=OrderType.LIMIT,
    price=100
)

# ---------------------------------
# ADD ORDERS TO BOOK
# ---------------------------------

book.add_order(buy_order)
book.add_order(sell_order)

# ---------------------------------
# RUN MATCHING ENGINE
# ---------------------------------

trades = engine.match()

# ---------------------------------
# PRINT RESULTS
# ---------------------------------

print("TRADES:")
print(trades)

print("\nBIDS:")
print(book.bids)

print("\nASKS:")
print(book.asks)