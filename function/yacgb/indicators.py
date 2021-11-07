# https://itnext.io/use-ccxt-to-calculate-cryptocurrency-trade-indicators-102a3ac1428e

import pandas as pd
from stockstats import StockDataFrame
import json

from yacgb.lookup import Candles

class Indicators(Candles):
    """Take candles_array (ohlcv) data and prepare for calculating various indicators
    """
    def __init__(self, candlesObj):
        super().__init__(timeframe=candlesObj.timeframe, candles_array=candlesObj.candles_array, last=candlesObj.last)
        header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = pd.DataFrame(self.candles_array, columns=header)
        self.sdf  = StockDataFrame.retype(df)

    # @property
    # def i_close(self):
    #     #return self.sdf.loc[10].at['timestamp'] 
    #     #return len(self.sdf) + len(self.candles_array)
    #     return self.sdf.iloc[-1].at['rsi_14']
       
   
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
        i='Indicators'
        c='Candles'
        d = {}
        
        d[i]={}
        d[i]['rsi']=float(self.rsi)
        d[i]['buy_indicator']=bool(self.buy_indicator)
        d[i]['sell_indicator']=bool(self.sell_indicator)
        d[i]['macd']=float(self.macd)
        d[i]['macds']=float(self.macds)
        d[i]['macdh']=float(self.macdh)
        
        d[c]={}
        d[c]['start']=self.dts_st
        d[c]['end']=self.dte_st
        d[c]['timeframe']=self.timeframe
        d[c]['open']=self.open
        d[c]['high']=self.high 
        d[c]['low']=self.low
        d[c]['close']=self.close
        d[c]['dejitter_close']=self.dejitter_close()
        d[c]['wavg_close']=self.wavg_close
        d[c]['volume']=self.volume
        d[c]['avg_volume']=self.avg_volume()
        d[c]['change']=self.change
        d[c]['amplitude']=self.amplitude
        d[c]['last_candle_age']=self.last_candle_age
        d[c]['ohlcv_age']=self.ohlcv_age
        d[c]['valid']=self.valid
        
        return(json.dumps(d))
    
    @property    
    def ca_dict(self):
        r = {}
        inc = self.sdf.close >= self.sdf.open
        dec = self.sdf.open > self.sdf.close
        
        r['g_ts'] = self.sdf.timestamp[inc].to_list()
        r['g_o'] = self.sdf.open[inc].to_list()
        r['g_h'] = self.sdf.high[inc].to_list()
        r['g_l'] = self.sdf.low[inc].to_list()
        r['g_c'] = self.sdf.close[inc].to_list()
        r['g_v'] = self.sdf.volume[inc].to_list()
        #r['g_rsi'] = self.sdf.rsi_14[inc].to_list()
        
        r['r_ts'] = self.sdf.timestamp[dec].to_list()
        r['r_o'] = self.sdf.open[dec].to_list()
        r['r_h'] = self.sdf.high[dec].to_list()
        r['r_l'] = self.sdf.low[dec].to_list()
        r['r_c'] = self.sdf.close[dec].to_list()
        r['r_v'] = self.sdf.volume[dec].to_list()
        #r['r_rsi'] = self.sdf.rsi_14[dec].to_list()
        
        r['high'] = self.high
        r['low'] = self.low
        r['width'] = int((self.sdf.timestamp.iloc[-1] - self.sdf.timestamp.iloc[-2])*2/3)
        r['start'] = int(self.sdf.timestamp.iloc[0])
        r['end'] = int(self.sdf.timestamp.iloc[-1])
        
        return (r)
        
    def __str__(self):
        return ("<Indicators rsi:%f b:%s s:%s macd:%f macds:%f macdh:%f>" % (self.rsi, self.buy_indicator, self.sell_indicator, self.macd, self.macds, self.macdh))