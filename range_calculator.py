import pandas as pd
import backtesting as bt
import pandas_ta as ta
import numpy as np
import datetime as dt
from IPython.display import clear_output
import breeze_client as bc
import yfinance as yf
import math
import matplotlib.pyplot as plt
import scipy.stats as stats


class probab_calculator:

    #including today
    including_today = False

    def __init__(self,symbol,interval,period):

        if self.including_today == False:
            print("****Attention Today is not included in days calculation if you want to include today please set 'including_today = True'.\n including_today variable is shared among all the instance of probab_calculator ****")
          
        
        #getting data
        self.data = yf.download(symbol,interval=interval,period=period)

        #updating data : Adding Daily Return[%]
        self.data['Return'] = np.log(self.data.Close/self.data.Open)

        #updating data : Adding previos stick change
        self.data['Day_Change'] = np.log(self.data["Close"]/self.data['Close'].shift(1))

        #getting_mean
        self.mean = round((self.data['Day_Change'].mean())*100,8)

        #getting sd
        self.sd = round((self.data['Day_Change'].std())*100,8)

        


        

        #Current Price 
        self.price = self.data.Close[-1]

    def days_calculation(self,expiry_date,additional_holidays=0):

              

        try:
            expiry_date = dt.datetime.strptime(expiry_date, '%d-%m-%Y')
            today_date = dt.datetime.now()
            days = (expiry_date - today_date).days

            # Count Saturdays and Sundays

            date_range = pd.date_range(start=today_date, end=expiry_date)
            num_saturdays = sum(1 for day in date_range if day.dayofweek == 5)  # Saturday is 5th day of the week
            num_sundays = sum(1 for day in date_range if day.dayofweek == 6)
            holidays = num_saturdays+num_sundays+additional_holidays
            today  = 0 if self.including_today == False else 1

            total_days = days+1-holidays+today
            print(f"total days = {total_days}")

            return total_days


        except Exception as e:
            raise ValueError (f"Date should be in DD-MM-YYYY format. Got the error  when trying 'expiry_date = dt.datetime.strptime(expiry_date, '%d-%m-%Y')' \n Error : {e}")
                

    

    def expiry_mean(self,days_to_expiry=None,expiry_date=None,additional_holidays=0):
        
        if days_to_expiry == None and expiry_date == None:
            raise ValueError("Either Expiry date or days_to_expiry is required. Only one Vairable is required ")
        elif days_to_expiry != None and expiry_date != None:
            raise ValueError("Use only days_to_expiry or expiry_date both can not be given at same time")
        
        else:
            if days_to_expiry != None and expiry_date == None:
                return self.mean*days_to_expiry
            elif days_to_expiry == None and expiry_date != None:
                
                

                total_days = self.days_calculation(expiry_date,additional_holidays=additional_holidays)

                return self.mean*total_days                  

                
            else:
                raise ValueError(f"Condiotions does not met problem with either :: Value of days_to_expiry : {days_to_expiry} or expiry_date : {expiry_date} ")
        


    def expiry_sd(self,days_to_expiry=None,expiry_date=None,additional_holidays=0
                    ):

        if days_to_expiry == None and expiry_date == None:
            raise ValueError("Either Expiry date or days_to_expiry is required. Only one Vairable is required ")
        elif days_to_expiry != None and expiry_date != None:
            raise ValueError("Use only days_to_expiry or expiry_date both can not be given at same time")
        
        else:
            if days_to_expiry != None and expiry_date == None:
                return self.sd*math.sqrt(days_to_expiry)
            elif days_to_expiry == None and expiry_date != None:

                total_days = self.days_calculation(expiry_date,additional_holidays=additional_holidays)

                return self.sd*math.sqrt(total_days)                  

                
            else:
                raise ValueError(f"Condiotions does not met problem with either :: Value of days_to_expiry : {days_to_expiry} or expiry_date : {expiry_date} ")

        return  

    def confidence_interval(self, confidence_level,expiry_date,holdiays=0):

        # Calculate the Z-value for the given confidence level
        z_value = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        print(z_value)
        
        # Calculate the margin of error
        expiry_mean = self.expiry_mean(expiry_date=expiry_date,additional_holidays=holdiays)/100
        expiry_sd = self.expiry_sd(expiry_date=expiry_date,additional_holidays=holdiays)/100
        margin_of_error = z_value * expiry_sd
        print(f"margin of error = {margin_of_error}")
        
        # Calculate the confidence interval
        ci_lower = expiry_mean - margin_of_error
        ci_upper = expiry_mean + margin_of_error
        print(f"ci_lower {ci_lower}")
        print(f"ci upper {ci_upper}")
        ci_lower_price = self.price * np.exp(ci_lower)
        ci_upper_price = self.price * np.exp(ci_upper)
        
        return ci_lower_price, ci_upper_price

    
