#alpaca import

#login
from alpaca.trading.client import TradingClient

#market order
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

#assets req
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass

#getting historical data
from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient

#creating request
from alpaca.data.requests import StockLatestQuoteRequest

#historical data
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime,timedelta

#data stream or websokets
from alpaca.data.live import CryptoDataStream, StockDataStream

#data analysis import
import pandas as pd
import numpy as np
import pprint as pp




key = 'PKZM8S2GMAAJB0AGGNUS'
secret = '9XzqSy9XwtEvwFj6oMK3v5fDHDkSyWDlDIUbTWU0'

# paper=True enables paper trading
trading_client = TradingClient(key,secret, paper=True)

#creating stream and history clients
# keys are required for live data
crypto_client = CryptoHistoricalDataClient(key,secret)
crypto_stream = CryptoDataStream(key, secret)

# keys required
stock_client = StockHistoricalDataClient(key,secret)
stock_stream = StockDataStream(key, secret)

#User Details
crypto_or_stock = 'crypto' #Enter only crypto or stock
instrument= 'BTC/USD'    #stock code example = 'SPY'  | #crypto code example = 'BTC/USD'    
old_data_candle = TimeFrame.Minute #put dot to see other option
start_date = datetime.now()-timedelta(hours=10)
end_date = datetime.now()


#craeting request param
request_params = CryptoBarsRequest(
                        symbol_or_symbols=[instrument],
                        timeframe=old_data_candle,
                        start=start_date,
                        end=end_date
                 )

bars = crypto_client.get_crypto_bars(request_params)
print(bars.df)
df = bars.df

#replacing missing data
df['timestamp'] = [datetime.fromtimestamp(x[1].timestamp())-timedelta(hours=5.5) for x in df.index]


# Function to insert row in the dataframe at place of missing data
def Insert_row_(row_number, df, row_value):
    # Slice the upper half of the dataframe
    df1 = df[0:row_number]
  
    # Store the result of lower half of the dataframe
    df2 = df[row_number:]
  
    # Insert the row in the upper half dataframe
    df1.loc[row_number]=row_value
  
    # Concat the two dataframes
    df_result = pd.concat([df1, df2])
  
    # Reassign the index labels
    #df_result.index = [*range(df_result.shape[0])]
  
    # Return the updated dataframe
    return df_result


start = df['timestamp'].to_list()[0].timestamp()
end = df['timestamp'].to_list()[-1].timestamp()
last_index = 0
#print(start,end)

for x in range(int(start),int(end),60):
    t = datetime.fromtimestamp(x)-timedelta(hours=5.5)
    if t in df['timestamp'].to_list():
        last_index = df['timestamp'].to_list().index(t)
        print(t,'yes')
    else:
        print(t,'no')
        print(last_index+1)
        df = Insert_row_(last_index+1,df,df.iloc[last_index])
        df['timestamp'].iloc[last_index+1] = t
        
#filtering data for every 5 minutes
df['minute'] = [x.minute%5 for x in df['timestamp']]
df_5min = df[df['minute']==0]
print('5 min data',df_5min)

# convert to dataframe
price =list(df_5min['close'])
print(price)

#orders 
# preparing orders
def place_order (side,qty,instrument=instrument):
    if side == 'buy':
        side = OrderSide.BUY
    else:
        side = OrderSide.SELL
    market_order_data = MarketOrderRequest(
                        symbol=instrument,
                        qty=qty,
                        side=side,
                        time_in_force=TimeInForce.GTC
                        )

    #placing order
    market_order = trading_client.submit_order(
                    order_data=market_order_data
                )
    return market_order




# fille values
hold = False
buy_price = 0
sell_price = 0
short_ema = 9
long_ema = 21
qty = 0.025 #amount of commodity to buy or sell in dollars 

# async handler
async def quote_data_handler(data):
    # quote data will arrive here
    global hold,price,buy_price,sell_price,short_ema,long_ema,notional

    #changing time stamp of data
    data_minute = data.timestamp.minute
    #data.timestamp=datetime.now()
    
    #getting close price of data
    close_price = data.close
    print(f'Change in Price = {close_price}')

    #appending to old list
    if data_minute%5==0:
        price.append(close_price)
        print(f'price appended to price list for the minute {data_minute} and time {data.timestamp}')
    else:
        print(f'data not appended for the minute {data_minute} and time {data.timestamp}')
    #getting average of 7 days 21 days
    ema_shorter = float(pd.DataFrame(price).ewm(span = short_ema).mean().iloc[-1].iloc[0])
    ema_longer = float(pd.DataFrame(price).ewm(span = long_ema).mean().iloc[-1].iloc[0])
    print(f'short_ema - {ema_shorter} | long_ema - {ema_longer}')

    
    if all((hold == False, ema_shorter>ema_longer)):
        print(f'buy at price{close_price}')
        hold = True
        buy_price = close_price
        place_order(side='buy',qty=qty)

    if all((hold == True , ema_shorter<ema_longer)):
        print(f'sell at {close_price}')
        hold=False
        sell_price = close_price
        place_order(side='sell',qty=trading_client.get_open_position('BTCUSD').qty)
        print(f'profit of {buy_price-sell_price}')
    #pp.pprint(data)

crypto_stream.subscribe_bars(quote_data_handler, instrument)

crypto_stream.run()
