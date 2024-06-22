from __future__ import print_function
import time
import upstox_client
from upstox_client.rest import ApiException
from pprint import pprint
import requests
import pandas as pd
from datetime import datetime,timedelta
import os
import pandas_ta as ta
from IPython.display import clear_output
import warnings
import os

# Adjust display options
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', None)
# Suppress FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)

r_url = 'https://127.0.0.1'
p_url = 'https://129.0.0.1'
client_id = '5fcc7604-6e26-44f2-9af7-35c3d26d15f1'
secret = 'usqa72gqpy'
#url = urllib.parse.quote('http://0.0.0.0')
link = f'https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={client_id}&redirect_uri={r_url}'
link


class tradetowin:

    def __init__(self,token,symbols):

        self.logs = []
        self.length = 9
        self.position = False
        self.orderid = None
        self.trade = []
        self.data_list = []
        self.data_store = {}
        self.symbols = symbols
        self.last_order_time = datetime.now()


        #login details
        self.api_version = '2.0' # str | API Version Header
        self.token = token
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = token
        self.streamer = upstox_client.MarketDataStreamer(
            upstox_client.ApiClient(self.configuration))
        
    def log_update(self,type,msg,functionanem):
        self.logs.append(f"[{datetime.now()}] : [{type}] :: {functionanem}  -  {msg}")

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
            self.trade.append({'datetime':datetime.now,'order id':api_response.data.order_id,'price':price,'qty':qty,'type':transaction_type})
            self.log_update('INFO',f"Order Api Called.Placing Order at Price-{price}. {api_response}.",'place_order')
            return api_response.data.order_id

        except ApiException as e:
            
            self.log_update('Critical',"Exception when calling OrderApi->place_order: %s" % e,'place_order')
            


    def cancel_order(self,orderid): # create an instance of the API class
        api_instance = upstox_client.OrderApi(upstox_client.ApiClient(self.configuration))
        ''' str | The order ID for which the order must be cancelled'''


        try:
            # Cancel order
            api_response = api_instance.cancel_order(orderid, self.api_version)
            pprint(api_response)
            return api_response.data.order_id
        except ApiException as e:
            self.log_update('Critical',"Exception when calling OrderApi->cancel_order: %s" % e,'cancel_order')

    def order_book(self):
        # create an instance of the API class
        api_instance = upstox_client.OrderApi(upstox_client.ApiClient(self.configuration))


        try:
            # Get order book
            api_response = api_instance.get_order_book(self.api_version)
            pprint(api_response)
            return api_response

        except ApiException as e:
            self.log_update('Critical',"Exception when calling OrderApi->get_order_book: %s\n" % e,'order_book')

    def check_order_status(self, order_id, order_book):
        # Check if the order is filled using the order book data
        try :
            for order in order_book.data:
                if order.order_id == order_id:
                    return order.status == 'complete'
            return False
        except Exception as e:
            self.log_update('Critical',e,'check_order_status')
            return False


    def parse_timestamp(self, ts):
        return datetime.fromtimestamp(int(ts) / 1000)

    def process_data(self, data):

        try: 
            for instrument, details in data['feeds'].items():
                try:
                    ltp = details['ff']['marketFF']['ltpc']['ltp']
                    timestamp = details['ff']['marketFF']['ltpc']['ltt']
                    volume = details['ff']['marketFF']['ltpc'].get('ltq', None)

                except KeyError:
                    ltp = details['ff']['indexFF']['ltpc']['ltp']
                    timestamp = details['ff']['indexFF']['ltpc']['ltt']
                    volume = 0

                time = self.parse_timestamp(timestamp)

                if instrument not in self.data_store:
                    self.data_store[instrument] = []

                self.data_store[instrument].append([time, ltp, volume])
        except Exception as e:
            self.log_update("Error",e,'processing_data')

    def save_tick_data(self):
      
        try :
            for instrument, ticks in self.data_store.items():
                filename = f"{instrument.replace('|','_')}_{str(datetime.today().date())}_tick_data.csv"
                file_exists = os.path.isfile(filename)
                if not file_exists:
                    df = pd.DataFrame(ticks, columns=['time', 'ltp', 'volume'])
                    df.to_csv(filename, index=False)
                else:
                    df = pd.DataFrame(ticks, columns=['time', 'ltp', 'volume'])
                    df.to_csv(filename,mode='a',header=None, index=False)

        except Exception as e:
            self.log_update('Error',e,'save_tick_data')
    

    def aggregate_to_1min(self):
      

        try:
            aggregated_data = {}
            for instrument, ticks in self.data_store.items():
                df = pd.DataFrame(ticks, columns=['time', 'ltp', 'volume'])
                df.set_index('time', inplace=True)
                df['volume'] = df['volume'].astype(int)
                

                # Resample the OHLCV data to 30-second intervals
                #resampling data to 1 minute
                df_1min = df['ltp'].resample('1T').ohlc()

                df_1min['volume'] = df['volume'].resample('1T').sum()
                #print(ohlc)

                aggregated_data[instrument] = df_1min
            
            return aggregated_data
        except Exception as e:
            self.log_update('Error',e,'aggregate_to_1min')

    def on_message(self,message):

        
        os.system('cls')
        print('on_message')
        #print(self.logs)

        try : 
            self.process_data(message)
            #print(self.data_store)
            self.save_tick_data()
            aggregated_data = self.aggregate_to_1min()
          
        except Exception as e:
            print('Error')
            print(e)
        
        try:
            # Get the first instrument and calculate OHLC
            first_instrument = self.symbols[0]

            first_df = aggregated_data[first_instrument][['open', 'high', 'low', 'close']]
        except Exception as e:
            print('Error in second block')
            print(e)

        try:
            # Get the second instrument's close and volume
            second_instrument = self.symbols[1]
            second_df = aggregated_data[second_instrument][['close', 'volume']].rename(columns={'close': 'ce_close', 'volume': 'ce_volume'})

            # Get the third instrument's close and volume
            third_instrument = self.symbols[2]
            third_df = aggregated_data[third_instrument][['close', 'volume']].rename(columns={'close': 'pe_close', 'volume': 'pe_volume'})
        except Exception as e:
            print('Error in third block')
            print(e)

        try:
            # Combine all data into a single DataFrame
            df = first_df.join(second_df).join(third_df)
            
        except Exception as e:
            print('error in 4th block')
            print(e)
        

        if len(df)>self.length:
            super = ta.supertrend(df['high'],df['low'],df['close'],self.length,3)
            try:
                df = df.join(super[[f'SUPERT_{self.length}_3.0',f"SUPERTd_{self.length}_3.0"]])
            except Exception as e:
                print('can not join')

            
            print(df)
            print('\n'.join(self.logs))
            
            

            #defining latest variables
            candle_time = df.index[-1]
            diff = (candle_time - self.last_order_time) >= timedelta(minutes=3)
            close = df['close'][-1]
            ce_close = df['ce_close'][-1]
            ce_volume = df['ce_volume'][-1]
            pe_close = df['pe_close'][-1]
            pe_volume = df['pe_volume'][-1]
            super = df[f'SUPERT_{self.length}_3.0'][-1]


            #previuos candle variables
            close_prev = df['close'][-2]
            super_prev = df[f'SUPERT_{self.length}_3.0'][-2]

            if diff:

                #buy signal
                if super_prev > close_prev and super < close :

                    self.position = True
                    self.last_order_time = datetime.now()
                    self.log_update('INFO',f'Buy Condition Met. Buying at {ce_close}','Buy Signal')
                    orderid = self.place_order(self.symbols[1],ce_close,25,'BUY')
                    self.log_update('INFO',f'Placed a call buying order at Price = {ce_close},','Buy Signal')


                    while not self.check_order_status(orderid,self.order_book()):
                        
                        
                        self.logs.append('Order Not Filled yet') if self.logs[-1]!= 'Order Not Filled yet' else 0
                        os.system('cls')
                        
                        print(df)
                        pprint('\n'.join(self.logs))
                        time.sleep(0.1)
                    
                    else:
                        self.logs.pop()
                        self.log_update('INFO',f'Order Filled at Price {ce_close}','Buy While Else Loop')
                        self.place_order(self.symbols[1],ce_close+1,25,'SELL')
                        self.log_update('INFO',f'Placed a call Sell order at Target Price = {ce_close+1}','Buy Signal')
                        #os.system('cls')                  
                    

                #sell signal
                elif super_prev < close_prev and super > close :

                    self.position = True
                    self.last_order_time = datetime.now()
                    self.log_update('INFO',f'Sell Condition Met. Selling at {pe_close}','Sell Signal')
                    orderid = self.place_order(self.symbols[2],pe_close,25,'BUY')
                    self.log_update('INFO',f'Placed a put buying order at Price = {pe_close},','Buy Signal')

                    while not self.check_order_status(orderid,self.order_book()):
                        

                        self.logs.append('Order Not Filled yet') if self.logs[-1]!= 'Order Not Filled yet' else 0
                        os.system('cls')
                        
                        print(df)
                        pprint('\n'.join(self.logs))
                        time.sleep(0.1)
                    
                    else:
                        self.logs.pop()
                        self.log_update('INFO',f'Order Filled at Price {pe_close}','Sell While else loop')
                        self.place_order(self.symbols[2],pe_close+2,25,'SELL')
                        self.log_update('INFO',f'Placed a call Sell order at Target Price = {pe_close+2}','Buy Signal')   
                    

            
        
        else:
            
            print(df)
            pprint('\n'.join(self.logs))
            

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
ac = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzWUFRTFkiLCJqdGkiOiI2Njc0ZmM2ZDkzZDZhMjQ3YTExODE1MTUiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzE4OTQyODI5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3MTkwMDcyMDB9.g_hzM3QkuIxSByynz0wLn0YNdApo1rzUSyaXNVApWgE'
nifty_23700_ce = 'NSE_FO|64394'
nifty_23400_pe = 'NSE_FO|64371'
nifty = 'NSE_INDEX|Nifty 50'


demo = tradetowin(ac,[nifty,nifty_23700_ce,nifty_23400_pe])

demo.start()

