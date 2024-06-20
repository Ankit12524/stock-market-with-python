from __future__ import print_function
import time
import upstox_client
from upstox_client.rest import ApiException
from pprint import pprint
import requests
import pandas as pd
from datetime import datetime
import os
import pandas_ta as ta
from IPython.display import clear_output



token = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzWUFRTFkiLCJqdGkiOiI2NjczYWQ2NzNjYmJmMDUyODc2ZTU5YTgiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzE4ODU3MDYzLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3MTg5MjA4MDB9.eG9-RuqlqssXFTjOWKI1jk1ry-LgzxB8z0oHlvM1ZSk'



class tradetowin:



    def __init__(self,token,symbols):


        self.length = 9
        self.trade = []
        self.data_list = []
        self.data_store = {}
        self.symbols = symbols
        self.api_version = '2.0' # str | API Version Header
        self.token = token
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = token
        self.streamer = upstox_client.MarketDataStreamer(
            upstox_client.ApiClient(self.configuration))



    def place_order(self,symbol,price,qty,transaction_type):

        '''Invalid value for `validity` (D), must be one of ['DAY', 'IOC']
        Invalid value for `product` (das), must be one of ['I', 'D', 'CO', 'OCO', 'MTF']
        Invalid value for `transaction_type` (buy), must be one of ['BUY', 'SELL']'''


        # create an instance of the API class
        api_instance = upstox_client.OrderApi(upstox_client.ApiClient(self.configuration))
        body = upstox_client.PlaceOrderRequest(price=price,quantity=qty,product='I',instrument_token=symbol,order_type='LIMIT',transaction_type=transaction_type,validity='DAY',disclosed_quantity=1,trigger_price=price,is_amo=False) # PlaceOrderRequest |


        try:
            # Place order
            api_response = api_instance.place_order(body, self.api_version)
            pprint(api_response)
            self.trade.append({'datetime':dt.datetime.now,'order id':api_response.data.order_id,'price':price,'qty':qty,'type':transaction_type})
            return api_response

        except ApiException as e:
            print("Exception when calling OrderApi->place_order: %s\n" % e)
            pprint(e)


    def cancel_order(self,orderid): # create an instance of the API class
        api_instance = upstox_client.OrderApi(upstox_client.ApiClient(self.configuration))
        ''' str | The order ID for which the order must be cancelled'''


        try:
            # Cancel order
            api_response = api_instance.cancel_order(orderid, self.api_version)
            pprint(api_response)
            return api_response.data.order_id
        except ApiException as e:
            print("Exception when calling OrderApi->cancel_order: %s\n" % e)

    def order_book(self):
        # create an instance of the API class
        api_instance = upstox_client.OrderApi(upstox_client.ApiClient(self.configuration))


        try:
            # Get order book
            api_response = api_instance.get_order_book(self.api_version)
            pprint(api_response)
            return api_response

        except ApiException as e:
            print("Exception when calling OrderApi->get_order_book: %s\n" % e)


    def parse_timestamp(self, ts):
        return datetime.fromtimestamp(int(ts) / 1000)

    def process_data(self, data):
        for instrument, details in data['feeds'].items():
            try:
                ltp = details['ff']['marketFF']['ltpc']['ltp']
                timestamp = details['ff']['marketFF']['ltpc']['ltt']
                volume = details['ff']['marketFF']['ltpc'].get('ltq', None)

            except KeyError:
                ltp = details['ff']['indexFF']['ltpc']['ltp']
                timestamp = details['ff']['indexFF']['ltpc']['ltt']
                volume = None

            time = self.parse_timestamp(timestamp)

            if instrument not in self.data_store:
                self.data_store[instrument] = []

            self.data_store[instrument].append([time, ltp, volume])




    def save_tick_data(self):
      for instrument, ticks in self.data_store.items():
          df = pd.DataFrame(ticks, columns=['time', 'ltp', 'volume'])
          df.to_csv(f'{instrument}_tick_data.csv', index=False)

    def aggregate_to_1min(self):
      aggregated_data = {}
      for instrument, ticks in self.data_store.items():
          df = pd.DataFrame(ticks, columns=['time', 'ltp', 'volume'])
          df.set_index('time', inplace=True)
          df_1min = df.resample('1T').agg({'ltp': 'last', 'volume': 'sum'}).dropna()
          aggregated_data[instrument] = df_1min
      return aggregated_data


    def on_message(self,message):
      #pprint(message)
      print('on message running')
      self.process_data(message)
      self.save_tick_data()
      data = self.aggregate_to_1min()

      aggregated_data = self.aggregate_to_1min()

      # Get the first instrument and calculate OHLC
      first_instrument = list(aggregated_data.keys())[0]
      first_df = aggregated_data[first_instrument][['open', 'high', 'low', 'close']]

      # Get the second instrument's close and volume
      second_instrument = list(aggregated_data.keys())[1]
      second_df = aggregated_data[second_instrument][['close', 'volume']].rename(columns={'close': 'ce_close', 'volume': 'ce_volume'})

      # Get the third instrument's close and volume
      third_instrument = list(aggregated_data.keys())[2]
      third_df = aggregated_data[third_instrument][['close', 'volume']].rename(columns={'close': 'pe_close', 'volume': 'pe_volume'})

      # Combine all data into a single DataFrame
      df = first_df.join(second_df).join(third_df)
      print(df)

      if len(df)>self.length:
                super = ta.supertrend(df['high'],df['low'],df['close'],self.length,3)
                df = df.join(super[f'SUPERT_{self.length}_3.0'])

                #defining latest variables
                close = df['close'][-1]
                ce_close = df['ce_close'][-1]
                ce_volume = df['ce_volume'][-1]
                pe_close = df['pe_close'][-1]
                pe_volume = df['pe_volume'][-1]
                super = df[f'SUPERT_{self.length}_3.0'][-1]

                #previuos candle variables
                close_prev = df['close'][-2]
                super_prev = df[f'SUPERT_{self.length}_3.0'][-2]

                #buy signal
                if super_prev > close_prev and super < close:
                    self.place_order(self.symbols[1],ce_close,25,'BUY')
                    self.place_order(self.symbols[2],ce_close+2,25,'SELL')
                    print('buy')

                #sell signal
                elif super_prev < close_prev and super > close:
                    self.place_order(self.symbols[1],pe_close,25,'BUY')
                    self.place_order(self.symbols[2],pe_close+2,25,'SELL')
                    print('sell')



    def on_message2(self,message):
            pprint(message)

    def on_open(self,symbol=False):
            print(self.symbols)


            self.streamer.subscribe(
                    self.symbols, "full")


    def start(self,symbol=False):


        # Handle incoming market data messages\
        self.streamer.on('open',self.on_open)
        self.streamer.on("message", self.on_message)
        self.streamer.connect()



    def stop(self,symbol=False):


        if symbol == False:
            self.streamer.unsubscribe(self.symbols)
        else:
            self.streamer.unsubscribe(symbol)





#symbols
ac = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzWUFRTFkiLCJqdGkiOiI2NjczYWQ2NzNjYmJmMDUyODc2ZTU5YTgiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzE4ODU3MDYzLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3MTg5MjA4MDB9.eG9-RuqlqssXFTjOWKI1jk1ry-LgzxB8z0oHlvM1ZSk'
nifty_23700_ce = 'NSE_FO|64394'
nifty_23400_pe = 'NSE_FO|64363'
nifty = 'NSE_INDEX|Nifty 50'


demo = tradetowin(ac,[nifty,nifty_23700_ce,nifty_23400_pe])


demo.start()








