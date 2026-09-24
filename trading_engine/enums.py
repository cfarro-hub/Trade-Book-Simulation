from enum import Enum

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"
    OCO = "OCO"
    OTO = "OTO"

class OrderStatus(str, Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITED"
    OPEN = "OPEN"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"

class TimeInForce(str, Enum):
    GTC = "GTC" 
    IOC = "IOC"
    FOK = "FOK"
    
