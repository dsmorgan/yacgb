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
    
    def rsi(self):
        return self.sdf['rsi_14'].iloc[-1] 
        
    def macds(self):
        return self.sdf['macds'].iloc[-1] 
    
    def macd(self):
        return self.sdf['macd'].iloc[-1] 
        
        
