# https://itnext.io/use-ccxt-to-calculate-cryptocurrency-trade-indicators-102a3ac1428e

import pandas as pd
from stockstats import StockDataFrame

class Indicators:
    """Take candles_array (ohlcv) data and prepare for calculating various indicators
    """
    def __init__(self, candles_array):
        header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = pd.DataFrame(candles_array, columns=header)
        self.sdf  = StockDataFrame.retype(df)
    
    @property
    def rsi(self):
        return self.sdf['rsi_14'].iloc[-1] 

    @property
    def macd(self):
        return self.sdf['macd'].iloc[-1] 
    
    @property    
    def macds(self):
        return self.sdf['macds'].iloc[-1] 
    
    @property    
    def macdh(self):
        return self.sdf['macdh'].iloc[-1]
        
    @property
    def buy_indicator(self):
        #return True only if RSI is above 35
        if pd.isna(self.rsi):
            #If RSI is invalid (NaN), allow buy
            return True
        return (self.rsi > 35)
    
    @property
    def sell_indicator(self):
        #return True only if RSI is below 65
        if pd.isna(self.rsi):
            #If RSI is invalid (NaN), allow sell
            return True
        return (self.rsi < 65)
    
    def __str__(self):
        return ("<Indicators rsi:%f b:%s s:%s macd:%f macds:%f macdh:%f>" % (self.rsi, self.buy_indicator, self.sell_indicator, self.macd, self.macds, self.macdh))
        