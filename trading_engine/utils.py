from pathlib import Path
from dotenv import load_dotenv
import os
from binance.client import Client
import pandas as pd

# Load .env from same folder as this file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Get keys
api_key = os.getenv("BINANCE_API_KEY_TEST")
api_secret = os.getenv("BINANCE_API_SECRET_TEST")

print("KEY:", api_key)
print("SECRET:", api_secret)

# Create client
client = Client(api_key, api_secret, testnet=True)

tickers = client.get_all_tickers()

df = pd.DataFrame(tickers)

#print(df)

import requests
import json

url = "https://api.binance.com"

api_call = "/api/v3/ticker/price"

headers = {'content-type': 'application/json', 'X-MBX-APIKEY': api_key}

response = requests.get(url + api_call, headers=headers)
response = json.loads(response.text)

df = pd.DataFrame.from_records(response)

#print(df)


#Server statuse
client.ping()

import datetime

res = client.get_server_time()
ts = res['serverTime'] / 1000
your_dt = datetime.datetime.fromtimestamp(ts)
your_dt.strftime('%Y-%m-%d %H:%M:%S')
#print(your_dt)


#help(client.get_all_tickers)

coin_info = client.get_all_tickers()
df = pd.DataFrame(coin_info)
#print(df)

#Binance exchange info

exchange_info = client.get_exchange_info()
exchange_info.keys()

df = pd.DataFrame(exchange_info['symbols'])
#print(df)


symbol_info = client.get_symbol_info('BTCUSDT')
#print(symbol_info)

## Market Data

market_depth = client.get_order_book(symbol='BTCUSDT')

bids = pd.DataFrame(market_depth['bids'])
bids.columns = ['price', 'bids']
asks = pd.DataFrame(market_depth['asks'])
asks.columns = ['price', 'asks']
df = pd.concat([bids, asks]).fillna(0)




recent_trades = client.get_recent_trades(symbol='BTCUSDT')
df = pd.DataFrame(recent_trades)
   
# Historical trades

id = df.loc[450, 'id']
historical_trades = client.get_historical_trades(symbol='BTCUSDT',limit = 1000, fromId=id)
df = pd.DataFrame(historical_trades)

#print(df)

#Average price 

avg_price = client.get_avg_price(symbol='BTCUSDT')
#print(avg_price)

tickers = client.get_all_tickers()
df = pd.DataFrame(tickers)

#Get all tickers

tickers = client.get_all_tickers()
df = pd.DataFrame(tickers)
#print(df)


# Get account information
account_info = client.get_account()

#get assets details

assets_details = client.get_asset_details(asset='ETH')

#get binance Trades

trades = client.get_my_trades(symbol='BTCUSDT')

#Fetch all orders

orders = client.get_all_orders(symbol='BTCUSDT')

#Place Binance Order

buy_order = client.create_test_order(
    symbol='BTCUSDT', side = 'BUY', type = 'MARKET', quantity = 0.005
)

#print(buy_order) 

info = client.get_symbol_info('BTCUSDT')


