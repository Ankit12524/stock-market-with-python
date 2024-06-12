import pandas as pd
import numpy as np
from breeze_connect import BreezeConnect
import datetime as dt
import base64 
import socketio
from IPython.display import clear_output


#keys
Key = '73=63fT44781tY4C42L0i3491201v23A'
Secret = '11331XF5fm6c5&Y3K2Q99lp28347480+'
api_session = '42126408'



# Initialize SDK

breeze = BreezeConnect(api_key=Key)

# Obtain your session key from https://api.icicidirect.com/apiuser/login?api_key=YOUR_API_KEY
# Incase your api-key has special characters(like +,=,!) then encode the api key before using in the url as shown below.

#print("https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus("your_api_key"))

# Generate Session
breeze.generate_session(api_secret=Secret,
                        session_token=api_session)


# Generate ISO8601 Date/DateTime String
import datetime
iso_date_string = datetime.datetime.strptime("07/12/2023","%d/%m/%Y").isoformat()[:10] + 'T05:30:00.000Z'
iso_date_time_string = datetime.datetime.strptime("07/12/2023 23:59:59","%d/%m/%Y %H:%M:%S").isoformat()[:19] + '.000Z'


#stock details
stock = 'NIFTY'
s_type = 'options'
exp = '13-Jun-2024'
strike = '23300'


#initializing tick
breeze.ws_connect()
tick_data = []

def on_ticks(ticks):
    print(ticks)

#assigning function tick function to stream
breeze.on_ticks = on_ticks

#breeze.subscribe_feeds(exchange_code="NFO", stock_code=stock, product_type=s_type, expiry_date=exp, strike_price=strike, right="Call",get_exchange_quotes=False,get_market_depth=False)


breeze.subscribe_feeds(exchange_code="NFO", stock_code="ZEEENT", product_type="options", expiry_date="31-Mar-2022", strike_price="350", right="Call", get_exchange_quotes=True, get_market_depth=True)


