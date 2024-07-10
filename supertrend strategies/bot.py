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

    def __init__(self,token,symbol,name):
        
        
        #important variables
        self.name = name
        self.symbol_list = symbol
        self.symbol = symbol[0]
        

        #strategy variables
        self.length = 12
        self.multiplier = 4
        self.long_position = False
        self.short_position = False
        self.timeframe = '30S' #should be according to pandas resmaple function for minute use T
    
        self.orderid = None
        self.initial_qty = 250
        self.current_qty = self.initial_qty

        #data virables
        self.tick_data = []
        self.tick_df = None
        self.df = None
        self.trade = []
        


        #login details
        self.api_version = '2.0' # str | API Version Header
        self.token = token
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = token
        self.streamer = upstox_client.MarketDataStreamer(
            upstox_client.ApiClient(self.configuration))


    


    def parse_timestamp(self, ts):
        return datetime.fromtimestamp(int(ts) / 1000)


    #completed
    def save_tick_data(self,timestamp,ltp,ltq):
      
        try:
            filename = f"{self.name}_{str(datetime.today().date())}_tick_data.csv"
            file_exists = os.path.isfile(filename)
            with open(filename,mode='a') as file:
                
                if not file_exists:
                    file.write('time,price,volume\n')
                
                file.write(f'{timestamp},{ltp},{ltq}\n')


        except Exception as e:
            print(f'Error in saving data to file {e}')
            
    

    def process_data(self,ts,ltp,qty):
      

        try:
            ts= self.parse_timestamp(ts)
            #method 1
            '''new_data = [{'ltp' : float(ltp),'qty' : int(qty)}]
            new_dataframe = pd.DataFrame(new_data,index=ts)
        

            if self.df.empty:

                self.df = new_dataframe
            
            else:
                pd.concat([self.df,new_dataframe],ignore_index=True)'''
            
            #method 2 #method 3 try using diction instead of list
            self.tick_data.append([ts,ltp,qty])
            self.tick_df = pd.DataFrame(self.tick_data,columns=['datetime','ltp','qty']).set_index('datetime')
            self.df = self.tick_df['ltp'].resample(self.timeframe).ohlc()
            self.df['volume'] = self.tick_df['qty'].resample(self.timeframe).sum()         

            
            print('dataframe : ',self.df)
        
        except Exception as e:
            print(f'Error in processing data : {e}')
                
            
    def savetrade(self,ts,ltp,qty,trade_type,position_type):
        total = qty*ltp
        last_trade = self.trade[-1] if len(self.trade)>0 else None
        if len(self.trade) !=0 and last_trade['position'] in ['long','short']:
            profit =  total - last_trade['total']
        else:
            profit = None
            

        self.trade.append({
            'datetime':datetime.now(),
            'ltp_time':ts,
            'price' : ltp,
            'qty':qty,
            'type':trade_type,
            'total': total,
            'position' :position_type  #can be long short or close
            
        })
        
    
    def superstrategy(self,df):

        if len(self.df) > self.length:
            super = ta.supertrend(df.high,df.low,df.close,self.length,self.multiplier)[f'SUPERTd_{self.length}_{self.multiplier}.0']

            current_super = super.iloc[-1]
            last_super = super.iloc[-2]
            if current_super == 1 and last_super == -1:
                return 1
            elif current_super == -1 and last_super == 1:
                return -1
            else:
                return 0
        else:
            return 0
            



    


    def on_message(self,message):
        
        
        #getting info from stream
        try : 
            ltp = message['feeds'][self.symbol]['ff']['marketFF']['ltpc']['ltp']
            qty = message['feeds'][self.symbol]['ff']['marketFF']['ltpc']['ltq']
            ts = message['feeds'][self.symbol]['ff']['marketFF']['ltpc']['ltt']
            ltt = self.parse_timestamp(ts)

        except Exception as e:
            print(f'erroe in getting info : {e}')
            raise(ValueError(f'Error in getting info from stream : {e}'))
        
        #saving data to file
        self.save_tick_data(ts,ltp,qty)

        #processing data
        self.process_data(ts,ltp,qty)

        #getting signal from strategy
        signal = self.superstrategy(self.df)



        if signal == 1 :

            #closign short trade if open
            if self.short_position:
                self.place_order(self.symbol,ltp,self.current_qty,"BUY")
                self.savetrade(ltt,ltp,self.current_qty,'BUY','close')
                self.short_position = False

            #taking fresh long trade
            if not self.long_position:
                self.place_order(self.symbol,ltp,self.current_qty,"BUY")
                self.savetrade(ltt,ltp,self.current_qty,'BUY','long')
                self.long_position = True
        elif signal ==-1:

            #closing long trade if open
            if self.long_position:
                self.place_order(self.symbol,ltp,self.current_qty,"SELL")
                self.savetrade(ltt,ltp,-self.current_qty,'SELL','close')
                self.long_position = False

            #taking fresh short trade
            if not self.short_position:
                self.place_order(self.symbol,ltp,self.current_qty,"SELL")
                self.savetrade(ltt,ltp,-self.current_qty,'SELL','short')
                self.short_position = True

    def backtest(self,df):

        #provided should have "ltp","qty" and "datetime" as column
        for index,row in df.iterrows():
            ltp = row['ltp']
            qty = row['qty']
            ts = row['datetime']
            ltt = self.parse_timestamp(ts)

            #saving data to file
            self.save_tick_data(ts,ltp,qty)

            #processing data
            self.process_data(ts,ltp,qty)

            #getting signal from strategy
            signal = self.superstrategy(self.df)



            if signal == 1 :

                #closign short trade if open
                if self.short_position:
                    
                    self.savetrade(ltt,ltp,self.current_qty,'BUY','close')
                    self.short_position = False

                #taking fresh long trade
                if not self.long_position:
                    
                    self.savetrade(ltt,ltp,self.current_qty,'BUY','long')
                    self.long_position = True
            elif signal ==-1:

                #closing long trade if open
                if self.long_position:
                    
                    self.savetrade(ltt,ltp,-self.current_qty,'SELL','close')
                    self.long_position = False
                    

                #taking fresh short trade
                if not self.short_position:
                    
                    
                    self.savetrade(ltt,ltp,-self.current_qty,'SELL','short')
                    self.short_position = True

            

                

        

        
            

    def on_open(self):
            print(self.symbol)
            self.streamer.subscribe(
                    self.symbol_list, "full")

    def start(self):

        # Handle incoming market data messages\
        self.streamer.on('open',self.on_open)
        self.streamer.on("message", self.on_message)
        self.streamer.connect()

    def stop(self,symbol=False):

        if symbol == False:
            self.streamer.unsubscribe(self.symbol_list)
        else:
            self.streamer.unsubscribe(symbol)
    
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
            return api_response.data.order_id

        except ApiException as e:
            
            self.log_update('Critical',"Exception when calling OrderApi->place_order: %s" % e,'place_order')
            


    def cancel_order(self,orderid): # create an instance of the API class
        api_instance = upstox_client.OrderApi(upstox_client.ApiClient(self.configuration))
        ''' str | The order ID for which the order must be cancelled'''


        try:
            # Cancel order
            api_response = api_instance.cancel_order(orderid, self.api_version)
            return api_response.data.order_id
        except ApiException as e:
            self.log_update('Critical',"Exception when calling OrderApi->cancel_order: %s" % e,'cancel_order')

    def order_book(self):
        # create an instance of the API class
        api_instance = upstox_client.OrderApi(upstox_client.ApiClient(self.configuration))


        try:
            # Get order book
            api_response = api_instance.get_order_book(self.api_version)
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


#symbols
ac = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzWUFRTFkiLCJqdGkiOiI2NjdjZGNhNTNjOGJhNDE5NWJhMzU4ZTEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzE5NDU4OTgxLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3MTk1MjU2MDB9.m9b7eUJtFKZD9Gw2opJk_YgCvTSHHbYTnJGtY7xI7sc'
insturment_code = 'NSE_FO|64371'
instrument_name = 'NIFTY_23500_pe'



demo = tradetowin(ac,[insturment_code],instrument_name)

demo.start()

