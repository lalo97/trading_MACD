import ccxt

import pandas as pd
pd.set_option('display.max_rows', None)

from datetime import datetime

from ta.trend import MACD
from ta.momentum import RSIIndicator
import warnings
warnings.filterwarnings('ignore')

import schedule as schedule
import time



#data retrival and order execution
exchange = ccxt.binance()


def technical_signals(df):
    '''
    this function will implement the technical indicator to the market DataFrame.
    the second par will define the logics with a bolean final.
    '''
    
    # Manual MACD
    # ShortEMA = df['close'].ewm(span=12, adjust=False).mean()
    # LongEMA = df['close'].ewm(span=26, adjust=False).mean()
    # MACD = ShortEMA - LongEMA
    # Signal = MACD.ewm(span=9, adjust=False).mean()
    # df['MACD'] = MACD
    # df['Signal'] = Signal
    
    # Get Indicators using libary MACD & RSI for the example
    # MACD
    indicator_macd = MACD(df['close'])
    df['MACD'] = indicator_macd.macd()
    df['Signal'] = indicator_macd.macd_signal()
    df['MACD Histogram'] = indicator_macd.macd_diff()
    
    df['MACD_Signal'] = False
    
    # RSI
    indicator_rsi = RSIIndicator(df['close'], window=14)
    df['RSI_Signal'] = False
    df['RSI'] = indicator_rsi.rsi()
    
    
    # Technical indicator strategy logics. We will use simple MACD to detect signals:
    # Crossover MACD over signal Below 0 == Buy Signal
    # Crossover MACD under Signal Above 0 == Sell Signal
    for current in range(1, len(df.index)):
        previous = current - 1
        if (df['MACD'][current] > df['Signal'][current] and df['MACD'][previous] < df['Signal'][previous] and df['MACD'][current] < 0):
            df['MACD_Signal'][current] = True
        elif (df['MACD'][current] < df['Signal'][current] and df['MACD'][previous] > df['Signal'][previous]):
            df['MACD_Signal'][current] = False
        else:
            df['MACD_Signal'][current] = df['MACD_Signal'][previous]
    return df
        


#  Defines if we're in hte market or not, to avoid submit orders once wwe've submited one
in_position = False
def reading_market(df):
    '''
    function to analize the market looking for signals according to our logics
    '''
    global in_position
    
    print("Looking for signals...")
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1
    
    if not df['MACD_Signal'][previous_row_index] and df['MACD_Signal'][last_row_index]:
        print('Uptrend activated according MACD, BUY SIGNAL triggered')
        if not in_position:
            order_buy = "Here goes BUY order" # exchange.create_market_buy_order('ETH/USDT', 1)
            print(order_buy)
            in_position = True
        else: 
            print("Already in position, skip BUY signal")
    
    if df['MACD_Signal'][previous_row_index] and not df['MACD_Signal'][last_row_index]:
        print('Downtrend activated according MACD, SELL SIGNAL triggered')
        if not in_position:
            order_sell = "Here goes SELL order" # exchange.create_market_sell_order('ETH/USDT', 1)
            print(order_sell)
            in_position = False
        else: 
            print("Not in position, skip SELL signal")


def execute_connection(symbol='ETH/USDT', timeframe='1m'):
    '''
        function for data retrival, processing and cleaning
    '''
    raw_data = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
    
    # print(raw_data)
    
    # skip todays date
    df = pd.DataFrame(raw_data[:-1], columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    df['date'] = pd.to_datetime(df['date'], unit='ms')
    print(f"Executing connection and data processing at... {datetime.now().isoformat()}")
    # print(df)
    complete_df = technical_signals(df)
    reading_market(complete_df)


schedule.every(10).seconds.do(execute_connection)

while True:
    schedule.run_pending()
    time.sleep(1)


