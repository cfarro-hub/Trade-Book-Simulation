from enums import Side

class OrderBook:
    def __init__(self):
        # Bids: Buyers want the HIGHEST price first (Descending)
        self.bids = []  
        # Asks: Sellers want the LOWEST price first (Ascending)
        self.asks = []  

    def add_order(self, order):
        if order.side == Side.BUY:
            self.bids.append(order)
            # Sort by Price (High to Low), then by Timestamp (Oldest first)
            self.bids.sort(key=lambda x: (-x.price, x.timestamp))
        else:
            self.asks.append(order)
            # Sort by Price (Low to High), then by Timestamp (Oldest first)
            self.asks.sort(key=lambda x: (x.price, x.timestamp))

    def __repr__(self):
        # A simple visual representation of the book
        res = "--- Order Book ---\n"
        res += "ASKS (Sellers):\n"
        for ask in reversed(self.asks[:5]): # Show top 5
            res += f"  {ask.price} | {ask.remaining}\n"
        res += "------------------\n"
        for bid in self.bids[:5]: # Show top 5
            res += f"  {bid.price} | {bid.remaining}\n"
        res += "BIDS (Buyers):\n"
        return res
    