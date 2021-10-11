# https://itnext.io/use-ccxt-to-calculate-cryptocurrency-trade-indicators-102a3ac1428e

from collections import OrderedDict
import jsonpickle
import pandas as pd
from stockstats import StockDataFrame

from yacgb.lookup import Candles

class Indicators(Candles):
    """Take candles_array (ohlcv) data and prepare for calculating various indicators
    """
    def __init__(self, candlesObj):
        super().__init__(timeframe=candlesObj.timeframe, candles_array=candlesObj.candles_array, last=candlesObj.last)
        header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = pd.DataFrame(self.candles_array, columns=header)
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

    @property    
    def jsonp(self):
        i='Indicator'
        c='Candles'
        d = OrderedDict()
        
        d[i]=OrderedDict()
        d[i]['rsi']=self.rsi
        d[i]['buy_indicator']=self.buy_indicator
        d[i]['sell_indicator']=self.sell_indicator
        d[i]['macd']=self.macd
        d[i]['macds']=self.macds
        d[i]['macdh']=self.macdh
        
        d[c]=OrderedDict()
        dts = datetime.datetime.fromtimestamp(int(self.candles_array[0][0]/1000), tz=timezone.utc)
        dts_st = dts.strftime('%Y%m%d %H:%M')
        dte = datetime.datetime.fromtimestamp(int(self.candles_array[-1][0]/1000), tz=timezone.utc)
        dte_st = dte.strftime('%Y%m%d %H:%M')
        d[c]['start']=dts_st
        d[c]['end']=dte_st
        d[c]['timeframe']=self.timeframe
        d[c]['open']=self.open
        d[c]['high']=self.high 
        d[c]['low']=self.low
        d[c]['close']=self.close
        d[c]['wavg_close']=self.wavg_close
        d[c]['volume']=self.volume
        d[c]['avg_volume']=self.avg_volume()
        d[c]['change']=self.change
        d[c]['amplitude']=self.amplitude
        d[c]['valid']=self.valid
        
        return(jsonpickle.encode(d))
        
    def __str__(self):
        return ("<Indicators rsi:%f b:%s s:%s macd:%f macds:%f macdh:%f>" % (self.rsi, self.buy_indicator, self.sell_indicator, self.macd, self.macds, self.macdh))
    
