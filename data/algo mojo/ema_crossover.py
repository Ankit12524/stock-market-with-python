#For Complete Algomojo Python Documentation Visit - https://pypi.org/project/algomojo/

#Algomojo - ema_crossover
#Website : www.algomojo.com



from algomojo.pyapi import *
import yfinance as yf
import time
import threading
import pandas_ta as ta
import pandas as pd

#set the StrategyName, broker code, Trading symbol, exchange
strategy = "EMA Crossover"
broker = "an"
symbol = "RELIANCE-EQ"
exchange = "NSE"
quantity = 10

# Set the API Key and API Secret key obtained from Algomojo MyAPI Section
algomojo = api(api_key="8ddfc3bd01a4c8eedcbf9157c0cf4ce8", api_secret="9f9a9f7ca5488a67b320f7464dd7af55")

# Define function to run the strategy
def ema_crossover():
    # Get historical data for the stock using Yahoo Finance API
    stock = yf.Ticker("^NSEI.")
   
     # Set initial values for variables
    position = 0
    

    # Main loop
    while True:
        # Get historical price data from 5min timeframe 


        df = stock.history(period="1d", interval="1m")
        close = df.Close.round(2)

        # Calculate SuperTrend
        
        df['super'] = ta.supertrend(df.High,df.Low,df.Close)['SUPERT_7_3.0']

        # Determine the crossover point
        current_price = df.Close[-1]
        last_price = df.Close[-2]
        current_trend = df.super[-1]
        last_trend = df.super[-2]
        
        positive_crossover = (last_trend > last_price) and (current_trend < current_price)
        negative_crossover = (last_trend < last_price) and (current_trend > current_price)




        # Place an order if there's a crossover and we don't already have a position
        if positive_crossover and position<=0:

            # Update position variable
            position = quantity

            # Place Smart market buy order
            response = algomojo.PlaceSmartOrder(broker=broker ,
                                strategy=strategy,
                                exchange=exchange,
                                symbol=symbol,
                                action="BUY",
                                product="MIS",
                                pricetype="MARKET",
                                quantity=quantity,
                                price="0",
                                position_size=position,
                                trigger_price="0",
                                disclosed_quantity="0",
                                amo="NO",
                                splitorder="NO",
                                split_quantity="1") 

            print ("Buy Order Response :",response)
            
            

        # Close position if there's a crossover and we already have a position
        elif negative_crossover and position>=0:

            # Update position variable
            position = quantity*-1
            
            # Place Smart market sell order
            response = algomojo.PlaceSmartOrder(broker=broker,
                                strategy=strategy,
                                exchange=exchange,
                                symbol=symbol,
                                action="SELL",
                                product="MIS",
                                pricetype="MARKET",
                                quantity=quantity,
                                price="0",
                                position_size=position,
                                trigger_price="0",
                                disclosed_quantity="0",
                                amo="NO",
                                splitorder="NO",
                                split_quantity="1") 

            print ("Sell Order Response :",response)
            
            

        # Print current position and price data
        print("Position:", position)
        print("LTP:", close[-1])
        print("Short EMA:", df.super[-1])
        
        print("Positive crossover:", positive_crossover)
        print("Negative crossover:", negative_crossover)

        # Wait for 15 seconds before checking again
        time.sleep(1)

# Create and start a new thread to run the strategy
t = threading.Thread(target=ema_crossover)
t.start()
