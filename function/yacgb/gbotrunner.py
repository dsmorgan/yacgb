## https://github.com/dsmorgan/yacgb

import logging
import uuid

from model.gbot import Gbot, gbot_init
from model.gridline import GridLine

logger = logging.getLogger(__name__)


class GbotRunner:
    def __init__(self, gbotid=None, config={}, type='live'):
        #RESET
        #Gbot.delete_table()
        self.gbot = None
        gbot_init()
        
        if gbotid != None:
            try:
                self.gbot = Gbot.get(gbotid)
                #self.grid_array = jsonpickle.decode(self.gbot.grid)
                logger.info("Lookup existing gbot, gbotid: " + gbotid)
            except Gbot.DoesNotExist:
                logger.error('Unable to find gbot, gbotid: ' + gbotid)
                exit()
        else:
            # create a new bot
            self.gbot = Gbot(str(uuid.uuid1()), exchange=config['exchange'], market_symbol=config['market_symbol'],
                    type=type, last_ticker=config['start_ticker'], at_high_ticker=config['start_ticker'], at_low_ticker=config['start_ticker'], 
                    config=config, grid=[])

            logger.info("Created new gbot, gbotid: " + self.gbot.gbotid)
            # initalize new bot
            self.setup()
            # not clear if I should save now, but probably a good idea
            #self.gbot.save()
            self.save()
    
    def save(self):
        #self.gbot.grid = jsonpickle.encode(self.grid_array)
        self.gbot.save()
        
    def test_slortp(self, last_tick, high_tick, low_tick, ts=''):
        if self.gbot.state == 'active':
            #collect last, highest high, and lowest low
            self.gbot.last_ticker=last_tick
            if high_tick > self.gbot.at_high_ticker:
                self.gbot.at_high_ticker = high_tick
            if low_tick < self.gbot.at_low_ticker:
                self.gbot.at_low_ticker = low_tick
            #check for stop_loss or take_profit
            if self.gbot.config.stop_loss != None and self.gbot.config.stop_loss >= last_tick:
                self.gbot.state = 'stop_loss'
                logger.warning('%s changed state to: %s (%f)' %(ts, self.gbot.state, last_tick))
                return True
            if self.gbot.config.take_profit != None and self.gbot.config.take_profit <= last_tick:
                self.gbot.state = 'take_profit'
                logger.warning('%s changed state to: %s (%f)' %(ts, self.gbot.state, last_tick))
                return True
            if self.gbot.config.profit_protect_percent != None and ((1-self.gbot.config.profit_protect_percent)*self.gbot.at_high_ticker >= last_tick):
                self.gbot.state = 'profit_protect'
                logger.warning('%s changed state to: %s (%f) profit_protect_percent: %f at_high_ticker: %f' % 
                                    (ts, self.gbot.state, last_tick, self.gbot.config.profit_protect_percent, self.gbot.at_high_ticker))
                return True
            return False
        return True

    def backtest(self, tick=0, ts='empty'):
        if tick > 0 and not self.test_slortp(tick, tick, tick, ts):
            # find lowest sell and highest buy grids
            lowest_sell = 999999999
            highest_buy = 0
            sell_grid = -1
            buy_grid = -1
            #grid_below = -1
            #grid_above = -1
            reset_array = []
            for g in self.gbot.grid:
                if g.mode == 'sell' and g.ticker < lowest_sell:
                    lowest_sell = g.ticker
                    sell_grid = g.step
                if g.mode == 'sell' and g.ticker <= tick:
                    reset_array.append(g.step)
                if g.mode == 'buy' and g.ticker > highest_buy:
                    highest_buy = g.ticker
                    buy_grid = g.step
                if g.mode == 'buy' and g.ticker >= tick:
                    reset_array.insert(0,g.step)
            logger.debug("%s tick %.2f sell_grid %d @ %.2f buy_grid %d @ %.2f [%s]" %(ts, tick, sell_grid, lowest_sell, buy_grid, highest_buy, str(reset_array)))  
            
            for gg in reset_array:
                self.reset(self.gbot.grid[gg].ticker, ts)
        
        else:
            logger.info(ts + " skipped ticker: " + str(tick))
    
    
    def check_id(self, exchange, orderid):
        for g in self.gbot.grid:
            #logger.info("Grid: \n%s" %str(g))
            if g.ex_orderid == exchange + '_' + orderid:
                logger.info(">%d Matched %s" %(g.step, g.ex_orderid))
                return (g.step)
        return (None)

    def _new_none(self, grid_list=[]):
        
        return
    
    def reset(self, grid_ticker=-1, timestamp=''):
        #TODO: turn this into collecting a list, and then
        # used to take last Buy and setup the next Limit Sell
        temp_ticker = 0
        temp_quantity = 0
        
        if grid_ticker > 0:
            # Find the current grid to be reset, calculate buy or sell based on what it was
            for g in self.gbot.grid:
                if g.ticker == grid_ticker:
                    if g.mode == 'buy':
                        logger.info("[%s] Bought %.8f @ %.5f Total: %.2f" % (timestamp, g.buy_base_quantity, g.ticker, g.ticker*g.buy_base_quantity))
                        fee = g.ticker*g.buy_base_quantity*self.gbot.config.makerfee
                        self.gbot.total_fees += fee #TODO: what about using actual fee?
                        self.gbot.profit -= fee
                        self.gbot.step_profit -= fee
                        # take purchased amount (buy_base_quantity) and use to calculate sale and profit(s)
                        temp_ticker = g.ticker
                        temp_quantity = g.buy_base_quantity
                        self.gbot.transactions += 1
                        g.buy_count +=1
                        g.ex_orderid=None
                        g.mode = "NONE"
                    if g.mode == 'sell':
                        logger.info("[%s] Sold %.8f @ %.5f Total: %.2f" % (timestamp, g.sell_base_quantity, g.ticker, g.sell_quote_quantity))
                        fee = g.sell_quote_quantity*self.gbot.config.makerfee
                        self.gbot.total_fees += fee #TODO: what about using actual fee?
                        self.gbot.profit += g.take - fee
                        self.gbot.step_profit += g.step_take - fee
                        self.gbot.transactions += 1
                        g.sell_count +=1
                        g.ex_orderid=None
                        g.mode = "NONE"
                    break
        for g in self.gbot.grid:
            # Reset all NONE mode grids to buy or sell, depending on position from current grid being reset
            if g.mode ==  "NONE" and g.ticker != grid_ticker:
                if g.ticker < grid_ticker:
                    #buy
                    g.mode = "buy"
                    logger.info("Limit Buy %.8f @ %.5f Total: %.2f" % (g.buy_base_quantity, g.ticker, g.ticker*g.buy_base_quantity))
                else:
                    #sell
                    g.mode = "sell"
                    # reset the take to be the same as step_take going forward
                    g.take = g.step_take
                    logger.info("Limit Sell %.8f @ %.5f Total: %.2f" % (g.sell_base_quantity, g.ticker, g.sell_quote_quantity))
    
    
    def grids(self):
        return len(self.gbot.grid)
    
    def _create_grids(self):
        # used to determine closest grid to the current market price
        sell_quantity = -1
        closest_grid = -1
        closest = 9999999
        
        #Create each grid to figure out total number of grids
        now_ticker = self.gbot.config.min_ticker
        while now_ticker <= self.gbot.config.max_ticker:
            # add a new grid
            self.gbot.grid.append(GridLine(step=self.grids(), ticker=now_ticker))
            # find the closest grid to the current market price, in order to find which grid to mark as NONE   
            if abs(self.gbot.config.start_ticker - now_ticker) < closest:
                closest = abs(self.gbot.config.start_ticker - now_ticker)
                closest_grid = self.grids()-1 #step is 1 less then the length of the grid
            #print (x, now_ticker)
            now_ticker = now_ticker*(1+self.gbot.config.grid_spacing)
        return (closest_grid)
    
    def _fillin_grids(self, each_grid_buy, none_grid):
        #Determine total step and quote
        totalq = 0
        totalb = 0
        total_buy_q = 0
        total_sell_q = 0
        gs = self.gbot.config.grid_spacing
        last_grid_tick = self.gbot.config.min_ticker
        for g in self.gbot.grid:
            g.buy_quote_quantity = each_grid_buy
            g.buy_base_quantity = g.buy_quote_quantity/g.ticker
            g.sell_base_quantity = g.buy_base_quantity*(1+gs)
            g.sell_quote_quantity = g.sell_base_quantity*g.ticker
            g.step_take = (g.ticker-last_grid_tick)*g.sell_base_quantity
            #Traverse the grid and fill in details specific to mode
            if (none_grid == g.step):
                ###g.allocate(buy_quote_quantity, gs, "NONE", 0, (g.ticker-last_step))
                 g.mode = "NONE"
            elif g.ticker > self.gbot.config.start_ticker:
                ###g.allocate(buy_quote_quantity, gs, "sell", (g.ticker-self.gbot.config.start_ticker), (g.ticker-last_step))
                g.mode = "sell"
                g.take = (g.ticker-self.gbot.config.start_ticker)*g.sell_base_quantity
                
                total_sell_q += g.sell_quote_quantity
                totalq += g.buy_quote_quantity
                totalb += g.buy_base_quantity
            else:
                ###g.allocate(buy_quote_quantity, gs, "buy", 0, (g.ticker-last_step))
                g.mode = "buy"
                total_buy_q += g.buy_quote_quantity
                totalq += g.buy_quote_quantity
                totalb += g.buy_base_quantity
            last_grid_tick = g.ticker
        logger.info("Actual, based on current price in grid: total_buy_q %.2f total_sell_q %.8f" % (total_buy_q, total_sell_q)) 
        logger.info("Theoretical: totalq %.2f totalb %.8f @ %.5f = %.2f" % (totalq, totalb, self.gbot.config.start_ticker, self.gbot.config.start_ticker*totalb)) 
        logger.info("start_quote %.2f start_base: %.8f @ %.5f = %.2f" % (self.gbot.config.start_quote, self.gbot.config.start_base, 
                                                self.gbot.last_ticker, self.gbot.config.start_quote + (self.gbot.config.start_base*self.gbot.last_ticker)))
        
    def total_buy_q(self):
        q = 0
        for g in self.gbot.grid:
            if g.mode == "buy":
                q += g.buy_quote_quantity
        return (round(q,2))
        
    def total_sell_q(self):
        q = 0
        for g in self.gbot.grid:
            if g.mode == "sell":
                q += g.sell_quote_quantity
        return (round(q,2))
 
    def total_buy_b(self):
        b = 0
        for g in self.gbot.grid:
            if g.mode == "buy":
                b += g.buy_base_quantity
        return (round(b,4))
        
    def total_sell_b(self):
        b = 0
        for g in self.gbot.grid:
            if g.mode == "sell":
                b += g.sell_base_quantity
        return (round(b,4))
    
    def _check_base_quote(self):
        self.gbot.need_quote = 0
        self.gbot.need_base = 0
        total_buy_q = self.total_buy_q()
        total_sell_q = self.total_sell_q()
        total_sell_b = self.total_sell_b()
        extra_q = self.gbot.config.start_quote - total_buy_q
        extra_b = self.gbot.config.start_base - total_sell_b
        if extra_q < 0:
            self.gbot.need_quote = -extra_q
            self.gbot.balance_quote = 0
        else:
            self.gbot.balance_quote = extra_q 
        if extra_b < 0:
            self.gbot.need_base = -extra_b
            self.gbot.balance_base = 0
        else:
            self.gbot.balance_base = extra_b 

        #4 possible outcomes: 1) enough Q and B, 2) need to buy B (not enough), 3) need to sell B for more Q, 4) not enough B and Q
        if (self.gbot.need_quote == 0) and (self.gbot.need_base == 0):
            #enough Q and B
            return ("ok")
        elif (self.gbot.need_quote == 0) and (extra_q >= self.gbot.need_base*self.gbot.last_ticker):
            #extra Q, need to buy B
            return ("buy")
        elif (self.gbot.need_base == 0) and ((extra_b*self.gbot.last_ticker) >= self.gbot.need_quote):
            #extra B, need to sell B for more Q
            return ("sell")
        # Not enough base and/or quote
        self.gbot.state='error'
        return("error")
        
    def setup(self):
        closest_grid = self._create_grids()
        #leave some off for reserve
        usable_quote = self.gbot.config.total_quote* (1-self.gbot.config.reserve)
        #divide the usable amount evenly for each step, for buying 
        quote_step = usable_quote/(self.grids()-1) 
        #use the current ticker to split the quantity to sell at each step
        # TODO: this should instead be sell the previous grid step, close enought for now
        #sell_quantity = usable_quote/self.gbot.config.start_ticker/(self.gbot.grids-1) 
        
        #### _fillin_grids
        self._fillin_grids(quote_step, closest_grid)
        self.totals()
        #### Check here if we have enough, total_buy_q is the total of all grids that are tagged as buy (in quote currency)
        action = self._check_base_quote()
        logger.info("%s balance_base %.8f balance_quote %.2f need_base %.8f need_quote %.2f" % (action, self.gbot.balance_base, 
                            self.gbot.balance_quote, self.gbot.need_base, self.gbot.need_quote))
        if action == 'error':
            logger.error ("exit, unhandled condition. Not enough quote and/or base")
            #exit()

        ##TODO
        #self.start_timestamp = NumberAttribute(null=True)
        #self.start = UnicodeAttribute(null=True)
        #self.last_timestamp = NumberAttribute(null=True)
        #self.last = UnicodeAttribute(null=True)
        
    
    def totals(self):
        total_b = self.gbot.balance_base
        total_q = self.gbot.balance_quote
    
        for g in self.gbot.grid:
            logger.info(">%d %s %.5f (%.2f) <%d/%d> buybase %.8f sellbase %.8f [take %.2f/%.2f] %.2f %s" % (g.step, g.mode, g.ticker, g.buy_quote_quantity, 
                                    g.buy_count, g.sell_count, g.buy_base_quantity, g.sell_base_quantity, g.take, g.step_take, g.sell_quote_quantity, g.ex_orderid))
            if g.mode == 'buy':
                # add up the quote
                total_q += g.buy_quote_quantity
            elif g.mode == 'sell':
                # add up the base
                total_b += g.sell_base_quantity
        
        logger.info("Total Quote: %.5f Total Base: %.8f @ %.5f (%.2f) = %.2f" % (total_q, total_b, self.gbot.last_ticker, (total_b*self.gbot.last_ticker), 
                                                                            total_q + (total_b*self.gbot.last_ticker)))
        logger.info("Transactions %d (fees: %.2f) Profit %.2f/%.2f" % (self.gbot.transactions, self.gbot.total_fees, self.gbot.profit, self.gbot.step_profit))
        logger.info("state: %s" % self.gbot.state)
