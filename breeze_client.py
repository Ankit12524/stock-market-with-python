# prompt: create a function which will return two variables start_date and end_date. function will two parameter period = which is the difference between start date and end date. period value can be 1y for years, 1m for months, 1d for days,,1h for hours. second parameter latest_date = which has default value of current date.
import pandas as pd
import backtesting as bt
import pandas_ta as ta
import numpy as np
import datetime as dt
from breeze_connect import BreezeConnect
import datetime as dt
import re




class icici_client:

  def __init__(self,apikey,secret_key,session_code):
    self.api_key = apikey
    self.secret_key = secret_key
    self.session_code = session_code
    
    # Initialize SDK
    self.breeze = BreezeConnect(api_key=self.api_key)

    self.breeze.generate_session(api_secret=secret_key,
                        session_token=session_code)

  def date_range(self,period, latest_date=dt.date.today()):
    """
    Returns a tuple of start_date and end_date based on the provided period and latest_date.

    Args:
      period: A string representing the period. Valid values are "1y", "1m", "1d", and "1h".
      latest_date: A datetime.date object representing the latest date. Defaults to today's date.

    Returns:
      A tuple of (start_date, end_date).
    """
    num = int(period[:-1])
    period = period[-1]
    #print(num,period)

    if period == "y":
      start_date = latest_date - dt.timedelta(days=num*365-1)
    elif period == "m":
      start_date = latest_date - dt.timedelta(days=num*30-1)
    elif period == "d":
      start_date = latest_date - dt.timedelta(days=num-1)
    elif period == "h":
      start_date = latest_date - dt.timedelta(hours=num)
    else:
      raise ValueError("Invalid period value. Should in format interger followed by [y,m,d,h]")

    end_date = latest_date + dt.timedelta(days=1)

    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

  def download(self,symbol,interval,period,exchange_code='NSE',product_type='cash',expiry_date=None,right=None,strike_price =None,latest_date=dt.date.today()):

    

    #values check
    if True:
      interval_list = ["1second","1minute","5minute","30minute","1day"]
      if interval not in interval_list:
        raise ValueError('Interval should be from "1second","1minute","5minute","30minute","1day"')

      exchange_code_list  = ["NSE", "NFO", "BSE","NDX","MCX"]
      if exchange_code not in exchange_code_list:
        raise ValueError('Exchange code should be from "NSE", "NFO", "BSE","NDX","MCX"')

      product_type_list = 	['cash', 'options',"futures"]
      if product_type not in product_type_list:
        raise ValueError('product_type should be Cash, Options,Futures (Required for NFO, NDX,MCX)' )

      if exchange_code == 'NFO':
        if expiry_date == None:
          raise ValueError('Expiry Date is required if exchange_code=NFO. Required if exchange code is NFO, NDX,MCX')

        if product_type == 'cash':
          raise ValueError('product_type is required if exchange_code = NFO. product_type can not be cash in case of exchange_code = NFO')

        if expiry_date!=None:
        
          signal = False
          try:
            day, month, year = map(int, expiry_date.split('-'))

            # Check for valid day, month, and year ranges
            if 1 <= day <= 31 and 1 <= month <= 12 and year >= 2000:
              signal = True
            
            else:
              raise ValueError(f'Enter a Valid Date in format yyyy-mm-dd. Entered Date =>  Day : {day}, Month : {month}, Year : {year}')
          except ValueError:
            raise ValueError(f"Enter date in Format dd-mm-yyyy. All dates should be in Number seprated by '-'.")
          
          if signal:
            expiry_date =  dt.date(year=year,month=month,day=day)
            expiry_date = expiry_date.strftime('%Y-%m-%d')
            print(expiry_date)

        if right == None:
          raise ValueError('"right" is rquired if exchange_code is NFO,NDX, MCX')
        
        else:
          right_list = ['call','put','others']
          if right not in right_list:
            raise ValueError('"right" should be from [call,put,others]')
        
        if strike_price == None:
          raise ValueError('"strike_price" is rquired if exchange_code is NFO,NDX, MCX. Enter "0" in case of future or where strike is not required in case product_type = NFO')
        
        else:
          try:
            strike = int(strike_price)
          except Exception as e:
            raise ValueError('strike_price should be numeric value in "" for example "5000"')
      #end of value checks


    #getting start date and end date from functions
    start_date, end_date = self.date_range(period=period,latest_date=latest_date)
    
    #returning date if exchange_code is nse
    data = []

    #candle_width = int(interval[-2:] if interval == '30minute' else interval[-1])
    def rows_calculator(interval,period):

      #["1second","1minute","5minute","30minute","1day"]
      #[y,m,d,h]
      

    
      i_unit = interval[2] if interval == '30minute' else interval[1]
      i_num = int(interval[:3]) if interval == '30minute' else int(interval[0])
      p_unit = period[-1]
      p_num = int(period[:-1])
      
      if i_unit == p_unit:
        return True
      elif i_unit == 'd':

        if p_unit =='y':
          total_rows = 365*p_num/i_num
          return total_rows

      elif i_unit == 'm':

        if p_unit == 'd':

          total_hours_in_day = 6.5
          total_hours_all_day = total_hours_in_day*p_num
          total_minutes = total_hours_all_day*60
          total_rows = (total_minutes/i_num)
          return total_rows
        
        elif p_unit == 'm':

          total_hours_in_day = 6.5
          total_hours_all_day = total_hours_in_day*p_num*30
          total_minutes = total_hours_all_day*60
          total_rows = (total_minutes/i_num)
          return total_rows
        
        elif p_unit == 'y':

          raise ValueError('minute data for year is not available currently. you can get by month for each month seprately then combine the data')
        
      elif i_unit == 's':

        if p_unit == 'd':

          hours_in_day = 6.5
          minute_in_day = 60*hours_in_day
          seconds_in_day = minute_in_day*60

          if p_num > 1:
            raise ValueError('For now maximum 1 day of data is available for 1 second tick')
        
          return seconds_in_day

        

      
        






    if exchange_code=='NSE':

      result = self.breeze.get_historical_data_v2(interval=interval,
                                from_date= f"{start_date}T07:00:00.000Z",
                                to_date= f"{end_date}T07:00:00.000Z",
                                stock_code= symbol,
                                exchange_code= exchange_code,
                                product_type=product_type,
                                )

    elif exchange_code == 'NFO':

      result = self.breeze.get_historical_data_v2(interval=interval,
                              from_date= f"{start_date}T07:00:00.000Z",
                              to_date= f"{end_date}T07:00:00.000Z",
                              stock_code=symbol,
                              exchange_code=exchange_code,
                              product_type=product_type,
                              expiry_date=f"{expiry_date}T07:00:00.000Z",
                              right=right,
                              strike_price=strike_price)





    if result['Error'] == None and result['Status']==200:
        data = result['Success']
    else:
        raise ValueError(result['Error'])

    data =  pd.DataFrame(data)
    data.rename(columns={'close': 'Close','open':'Open','high':'High','low':'Low','volume':'Volume'},inplace=True)

    return data
  
  def second_data(self,symbol,date=dt.datetime.today().strftime('%Y-%m-%d'),exchange_code='NSE',product_type ='cash',expiry_date=False,right=False,strike_price=False):
    
    #date value check:
    try:
      for x in date.split('-'):
        int(x)
    except Exception as e:
      print(f'Error : {e}')
      raise('Date Should be in format "YYYY-MM-DD" for Example : {date}')


    start_time = dt.datetime(year = 2024,month = 1, day = 1,hour=9,minute=0,second=0)

    dfs = []
    if exchange_code=='NSE':
      for x in range(1,27):
        
        end_time = start_time + dt.timedelta(minutes=15)

        s_time = start_time.strftime('%H:%M')
        e_time = end_time.strftime('%H:%M')
        

        result = self.breeze.get_historical_data_v2(interval='1second',
                                  from_date= f"{date}T{s_time}:00.000Z",
                                  to_date= f"{date}T{e_time}:00.000Z",
                                  stock_code= symbol,
                                  exchange_code= exchange_code,
                                  product_type=product_type,
                                  )
        
        start_time = end_time

        if result['Error'] == None and result['Status']==200:
          data = result['Success']

        else:
            raise ValueError(result['Error'])

        data =  pd.DataFrame(data)
        data.rename(columns={'close': 'Close','open':'Open','high':'High','low':'Low','volume':'Volume'},inplace=True)

        dfs.append(data)

        #printing progress 
        from IPython.display import clear_output

        clear_output()
        print(f"[{x*'*'+' '*(26-x)}]")
        print(f'{round((x+1)/27*100,2)} Completed')

    


    elif exchange_code == 'NFO':
      for x in range(1,27):
        result = self.breeze.get_historical_data_v2(interval='1second',
                                from_date= f"{date}T07:00:00.000Z",
                                to_date= f"{date}T07:00:00.000Z",
                                stock_code=symbol,
                                exchange_code=exchange_code,
                                product_type=product_type,
                                expiry_date=f"{expiry_date}T07:00:00.000Z",
                                right=right,
                                strike_price=strike_price)
    
    df = pd.concat(dfs,ignore_index=True)
    return df




def read_csv(filename):

  df = pd.read_csv(filename)
  df['datetime'] = pd.to_datetime(df['datetime'])
  df.set_index('datetime',inplace = True)
  
  return df