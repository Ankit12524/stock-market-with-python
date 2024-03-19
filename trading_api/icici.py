import json
import hashlib
from datetime import datetime
from breeze_connect import BreezeConnect
import urllib
import pandas as pd
import numpy as np
import math


class icici:
    defalut_key = '73=63fT44781tY4C42L0i3491201v23A'
    default_secret = '11331XF5fm6c5&Y3K2Q99lp28347480+'

    def __init__(self,api_session,key=defalut_key,secret = default_secret):
        self.Key = key
        self.Secret = secret
        self.api_session = api_session
        self.breeze = BreezeConnect(api_key=self.Key)

    
    def login(self):
        
        self.breeze.generate_session(api_secret=self.Secret,session_token=self.api_session)
        # Generate ISO8601 Date/DateTime String
        import datetime
        iso_date_string = datetime.datetime.strptime("07/12/2023","%d/%m/%Y").isoformat()[:10] + 'T05:30:00.000Z'
        iso_date_time_string = datetime.datetime.strptime("07/12/2023 23:59:59","%d/%m/%Y %H:%M:%S").isoformat()[:19] + '.000Z'

    def get_histroy_data_stock(self,stock_code,from_date,to_date,interval='1day',exchange='NSE'):
        data = self.breeze.get_historical_data(interval=interval,
                                    from_date= f"{from_date}T07:00:00.000Z",
                                    to_date= f"{to_date}T07:00:00.000Z",
                                    stock_code=stock_code,
                                    exchange_code=exchange,
                                    product_type="cash")
        if data['Status']==200:
            df = pd.DataFrame(data['Success'])[['datetime','stock_code','open','close','high','low']]
            for x in df.columns:
                try:
                    df[x]=df[x].astype(float)
                    print(x,'complete')
                except Exception as e:
                    print('couldnt perform on',x)
                    print('Error',e)
            return df
        else:
            print('got error')
            return data