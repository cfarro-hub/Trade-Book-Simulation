from order_types import Side


def handle_market_order(order, engine):
    """
    Executes a market order immediately against the best
    available prices in the order book.

    Market orders NEVER enter the order book.
    """

    trades = []

    # BUY market order consumes asks
    if order.side == Side.BUY:
        book_side = engine.book.asks

    # SELL market order consumes bids
    else:
        book_side = engine.book.bids

    while order.remaining > 0 and book_side:

        best = book_side[0]

        trade_qty = min(order.remaining, best.remaining)

        # Execute at resting order price
        trade_price = best.price

        # Update quantities
        order.remaining -= trade_qty
        best.remaining -= trade_qty

        # Store trade
        trades.append({
            "price": trade_price,
            "quantity": trade_qty,
            "buy_order_id": (
                order.id if order.side == Side.BUY else best.id
            ),
            "sell_order_id": (
                order.id if order.side == Side.SELL else best.id
            )
        })

        # Remove filled resting order
        if best.remaining == 0:
            book_side.pop(0)

    return trades