key = '9b1a951f11b716d16b0ee8318c8a4a52'
secret = '1b1afd15b70972fad1f61646bd081f8513a60cbc'
symbol = 'BTC/USD'

import pandas as pd
import pandas_ta as ta

from alpaca_trade_api.common import URL
from alpaca_trade_api.stream import Stream


import asyncio

async def trade_callback(t):
    print('trade', t)


async def quote_callback(q):
    print('quote', q)


# Initiate Class Instance
stream = Stream(key,
                secret,
                base_url=URL('https://127.0.0.1'),
                data_feed='iex')  # <- replace to 'sip' if you have PRO subscription

# subscribing to event
stream.subscribe_trades(trade_callback, 'AAPL')
stream.subscribe_quotes(quote_callback, 'IBM')


stream.run()