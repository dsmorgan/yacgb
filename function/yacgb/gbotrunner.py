## https://github.com/dsmorgan/yacgb

import logging
import uuid

from model.gbot import Gbot, gbot_init
from model.gridline import GridLine
from yacgb.orderscapture import OrdersCapture
from yacgb.bdt import BacktestDateTime

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
                logger.info("Lookup existing gbot, gbotid: " + gbotid + " state: " + self.gbot.state)
            except Gbot.DoesNotExist:
                logger.error('Unable to find gbot, gbotid: ' + gbotid)
                #We probably should do something better then exit, so that we can continue exiting other bots
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
            self.save()
    
    def save(self):
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
            # returning False is the normal case when we are still active, yet not past stop_loss, take_profit, or profit_protect thresholds
            return False
        return True

    def backtest(self, tick=0, ts=BacktestDateTime().dtstf(), indicator=None):
        self.dynamic_set_triggers()
        if tick > 0 and not self.test_slortp(tick, tick, tick, ts):
            # find lowest sell and highest buy grids
            lowest_sell = 999999999
            highest_buy = 0
            sell_grid = -1
            buy_grid = -1
            #grid_below = -1
            #grid_above = -1
            closed_dict = {}
            timestamp = BacktestDateTime(ts).ccxt_timestamp()
            for g in self.gbot.grid:
                pts = []
                if g.mode == 'sell' and g.ticker < lowest_sell:
                    # For debug
                    lowest_sell = g.ticker
                    sell_grid = g.step
                if g.mode == 'sell' and g.type == 'limit' and g.ticker <= tick:
                    # static grid, use the g.ticker (limit price)
                    pts.append(g.ticker)
                    pts.append(timestamp)
                    closed_dict[g.step] = pts
                if self.gbot.config.dynamic_grid and g.mode == 'sell' and g.type == 'trigger' and g.ticker <= tick:
                    if indicator == None or indicator.sell_indicator:
                        # For a dynamic grid, use tick instead of g.ticker
                        pts.append(tick)
                        pts.append(timestamp)
                        closed_dict[g.step] = pts
                    else:
                        logger.info("step [%d] delayed trigger tick: %.5f %s" % (g.step, tick, indicator))
                if g.mode == 'buy' and g.ticker > highest_buy:
                    # For debug
                    highest_buy = g.ticker
                    buy_grid = g.step
                if g.mode == 'buy' and g.type != None and g.ticker >= tick:
                    # static grid, use the g.ticker (limit price)
                    pts.append(g.ticker)
                    pts.append(timestamp)
                    closed_dict[g.step] = pts
                if self.gbot.config.dynamic_grid and g.mode == 'buy' and g.type == 'trigger' and g.ticker >= tick:
                    if indicator == None or indicator.buy_indicator:
                        # For a dynamic grid, use tick instead of g.ticker
                        pts.append(tick)
                        pts.append(timestamp)
                        closed_dict[g.step] = pts
                    else:
                        logger.info("step [%d] delayed trigger tick: %.5f %s" % (g.step, tick, indicator))
                
            logger.debug("%s tick %.2f sell_grid %d @ %.2f buy_grid %d @ %.2f [%s]" %(ts, tick, sell_grid, lowest_sell, buy_grid, highest_buy, str(closed_dict)))  
            
            self.closed_adjust(self.stepsmatch(closed_dict), ts)
        
        else:
            logger.info(ts + " skipped ticker: " + str(tick))
    
    def stepsmatch(self, steps):
        #generate a dictionary that emulates what a closed order looks like (minimally populated), with a key of the grid step
        odict={}
        for step, average_ts in steps.items():
            average = average_ts[0]
            ts = average_ts[1]
            order={}
            order['side'] = self.gbot.grid[step].mode
            order['type'] = self.gbot.grid[step].type
            # we attach the price that is passed to us here, instead of what ticker is
            order['timestamp'] = ts
            #average represents the actual order price. price represents what the (original) grid price is
            order['average'] = average
            order['price'] = self.gbot.grid[step].ticker
            order['status'] = 'closed'
            order['symbol'] = self.gbot.config.market_symbol
            #TODO
            #order['timestamp'] = ...
            if self.gbot.grid[step].mode == 'buy':
                order['amount'] = self.gbot.grid[step].buy_base_quantity
                order['cost'] = self.gbot.grid[step].buy_quote_quantity
            if self.gbot.grid[step].mode == 'sell':
                order['amount'] = self.gbot.grid[step].sell_base_quantity
                order['cost'] = self.gbot.grid[step].sell_quote_quantity
            odict[step] = order
            
        return (odict)
    
    def ordersmatch(self, orders_array):
        #generate a dictionary that represents all orders that match, with a key of the grid step
        odict={}
        for o in orders_array:
            logger.debug("closed order: %s, timestamp: %d" % (o['id'], o['timestamp']))
            exord = self.gbot.config.exchange + '_' + o['id']
            for g in self.gbot.grid:
                if g.ex_orderid == exord:
                    logger.info("[%d] Matched %s" %(g.step, g.ex_orderid))
                    odict[g.step] = o
        return (odict)
    
    #TODO: replace this with ordersmatch() for live and stepsmatch() for backtesting
    #def check_id(self, exchange, orderid):
    #    for g in self.gbot.grid:
    #        #logger.info("Grid: \n%s" %str(g))
    #        if g.ex_orderid == exchange + '_' + orderid:
    #            logger.info(">%d Matched %s" %(g.step, g.ex_orderid))
    #            return (g.step)
    #    return (None)

    def _current_none(self):
        ret = -1
        valid = 0
        for g in self.gbot.grid:
            if g.mode == "NONE":
                ret = g.step
                valid += 1
        if valid == 1:
            return (ret)
        else:
            return (-1)

    def _new_none(self, none_index, grid_list=[]):
        if (none_index < 0):
            return (none_index)
        up = 0
        down = 0
        
        for g in self.gbot.grid:
            if g.step in grid_list:
                if g.mode == "buy":
                    down += 1
                elif g.mode == "sell":
                    up += 1
        return (none_index + up - down)
    
    def closed_adjust(self, closed={}, timestamp=''):
        #use orderscap to parse and seperate reset from closed lists orders
        orderscap = OrdersCapture(self.gbot.gbotid, self.gbot.exchange, self.gbot.config.makerfee, self.gbot.config.takerfee)
        
        for step,order in closed.items():
            orderscap.add(step, order)
        
        if len(orderscap.closed_list_steps)+len(orderscap.reset_list_steps) > 0:
            logger.info("closed_list %s reset_list %s" % (str(orderscap.closed_list_steps), str(orderscap.reset_list_steps)))
        
        cindex = self._current_none()
        nindex = self._new_none(cindex, orderscap.closed_list_steps)
        #grab this value now, as it will change as we adjust the grid
        #bc = self.base_cost()
        total_b = self.total_sell_b()
        #print ("cost_basis", self.gbot.cost_basis)
        #print("total_b", total_b)
        #print ("bc", bc)
 
        for r in orderscap.reset_list:
            logger.info("Reset %d (%s)" %(r.step, self.gbot.grid[r.step].ex_orderid))
            self.gbot.grid[r.step].ex_orderid = None
             
        for c in orderscap.closed_list: 
            for g in self.gbot.grid:
                if c.step == g.step:
                    if g.mode == 'buy':
                        #logger.info("[%s] Bought %.8f @ %.5f Total: %.2f" % (timestamp, g.buy_base_quantity, g.ticker, g.ticker*g.buy_base_quantity))
                        # use c.average instead of c.price, since that refelects the actual buy/sell price
                        logger.info("[%s] Bought %.8f @ %.5f Total: %.2f (grid ticker: %.5f)" % (timestamp, c.amount, c.average, c.cost, g.ticker))
                        #fee = g.ticker*g.buy_base_quantity*self.gbot.config.makerfee
                        self.gbot.total_fees += c.fee_cost
                        self.gbot.profit -= c.fee_cost
                        self.gbot.step_profit -= c.fee_cost
                        #self.gbot.cost_basis += c.fee_cost + (g.ticker*g.buy_base_quantity)
                        self.gbot.cost_basis += c.fee_cost + c.cost
                        # take purchased amount (buy_base_quantity) and use to calculate sale and profit(s)
                        self.gbot.transactions += 1
                        g.buy_count +=1
                        g.ex_orderid=None
                        g.mode = "NONE"
                    if g.mode == 'sell':
                        #logger.info("[%s] Sold %.8f @ %.5f Total: %.2f" % (timestamp, g.sell_base_quantity, g.ticker, g.sell_quote_quantity))
                        # use c.average instead of c.price, since that refelects the actual buy/sell price
                        logger.info("[%s] Sold %.8f @ %.5f Total: %.2f (grid ticker: %.5f)" % (timestamp, c.amount, c.average, c.cost, g.ticker))
                        #fee = g.sell_quote_quantity*self.gbot.config.makerfee
                        self.gbot.total_fees += c.fee_cost
                        #take = g.sell_quote_quantity - (g.sell_base_quantity/total_b * self.gbot.cost_basis)
                        #step_take = g.sell_quote_quantity - self.gbot.grid[g.step-1].buy_quote_quantity
                        take = c.cost - (c.amount/total_b * self.gbot.cost_basis)
                        step_take = c.cost - self.gbot.grid[g.step-1].buy_quote_quantity
                        #print ("c.cost %f c.amount %f total_b %f cost_basis %f take %f step_take %f" %(c.cost, c.amount, total_b, self.gbot.cost_basis, take, step_take))
                        self.gbot.profit += take - c.fee_cost
                        self.gbot.step_profit += step_take - c.fee_cost
                        self.gbot.cost_basis += c.fee_cost - (c.amount/total_b * self.gbot.cost_basis)
                        self.gbot.transactions += 1
                        g.sell_count +=1
                        g.ex_orderid=None
                        g.mode = "NONE"
        
        for g in self.gbot.grid:
            # Reset all NONE mode grids to buy or sell, depending on position from current grid being reset
            if g.mode ==  "NONE" and g.step != nindex:
                if g.ticker < self.gbot.grid[nindex].ticker:
                    #buy
                    g.mode = "buy"
                    logger.info("Limit Buy %.8f @ %.5f Total: %.2f" % (g.buy_base_quantity, g.ticker, g.ticker*g.buy_base_quantity))
                else:
                    #sell
                    g.mode = "sell"
                    # reset the take to be the same as step_take going forward
                    #g.take = g.step_take
                    logger.info("Limit Sell %.8f @ %.5f Total: %.2f" % (g.sell_base_quantity, g.ticker, g.sell_quote_quantity))
            elif g.step == nindex:
                if g.mode != "NONE":
                    logger.error("step %d, ticker %.5f, mode should be NONE, but was %s, resetting" % (g.step, g.ticker, g.mode))
                    g.mode = "NONE"
        
        if len(orderscap.closed_list) > 0:
            # usage average instead of price, since that reflects actual value. Assuming just 1 order possible for now
            self.dynamic_grid_adjust(orderscap.closed_list[0].average)
        
        
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
            now_ticker = now_ticker*(1+self.gbot.config.grid_spacing)
        return (closest_grid)
    
    def _fillin_grids(self, each_grid_buy, none_grid, order_type='limit'):
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
            g.type = order_type
            #g.step_take = (g.ticker-last_grid_tick)*g.sell_base_quantity
            #Traverse the grid and fill in details specific to mode
            if (none_grid == g.step):
                ###g.allocate(buy_quote_quantity, gs, "NONE", 0, (g.ticker-last_step))
                 g.mode = "NONE"
            elif g.ticker > self.gbot.config.start_ticker:
                ###g.allocate(buy_quote_quantity, gs, "sell", (g.ticker-self.gbot.config.start_ticker), (g.ticker-last_step))
                g.mode = "sell"
                #g.take = (g.ticker-self.gbot.config.start_ticker)*g.sell_base_quantity
                ##self.gbot.cost_basis += self.gbot.config.start_ticker*g.sell_base_quantity
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
        self.gbot.cost_basis = self.gbot.config.start_ticker*self.total_sell_b()
        logger.info("Actual, based on current price in grid: total_buy_q %.2f total_sell_q %.8f" % (total_buy_q, total_sell_q)) 
        #logger.info("Theoretical: totalq %.2f totalb %.8f @ %.5f = %.2f" % (totalq, totalb, self.gbot.config.start_ticker, self.gbot.config.start_ticker*totalb)) 
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
        return (round(b,5))
        
    def total_sell_b(self):
        b = 0
        for g in self.gbot.grid:
            if g.mode == "sell":
                b += g.sell_base_quantity
        return (round(b,5))
        
    def base_cost(self):
        if self.total_sell_b() <= 0:
            return (0)
        return (self.gbot.cost_basis/self.total_sell_b())
    
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
            self.gbot.state='buy_base'
            return ("buy_base")
        elif (self.gbot.need_base == 0) and ((extra_b*self.gbot.last_ticker) >= self.gbot.need_quote):
            #extra B, need to sell B for more Q
            self.gbot.state='sell_base'
            return ("sell_base")
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
            logger.info(">%d %s/%s %.5f <%d/%d> buybase %.8f (%.2f) sellbase %.8f (%.2f) %s" % (g.step, g.type, g.mode, g.ticker, g.buy_count, g.sell_count, 
                        g.buy_base_quantity, g.buy_quote_quantity, g.sell_base_quantity, g.sell_quote_quantity, g.ex_orderid))
            if g.mode == 'buy':
                # add up the quote
                total_q += g.buy_quote_quantity
            elif g.mode == 'sell':
                # add up the base
                total_b += g.sell_base_quantity
        
        logger.info("Total Quote: %.5f Total Base: %.8f @ %.5f (%.2f) = %.2f" % (total_q, total_b, self.gbot.last_ticker, (total_b*self.gbot.last_ticker), 
                                                                            total_q + (total_b*self.gbot.last_ticker)))
        logger.info("Base Held Cost Basis: %.2f (%.2f)" % (self.gbot.cost_basis, self.base_cost()))                                                                    
        logger.info("Transactions %d (fees: %.2f) Profit %.2f (step: %.2f)" % (self.gbot.transactions, self.gbot.total_fees, self.gbot.profit, self.gbot.step_profit))
        logger.info("state: %s" % self.gbot.state)
        
    def dynamic_set_triggers(self):
        if self.gbot.config.dynamic_grid:
            n = self._current_none()
            f = []
            f.append(n-1)
            #f.append(n)
            f.append(n+1)
            for g in self.gbot.grid:
                if g.step in f:
                    g.type = 'trigger'
                else:
                    g.type = None
        else:
            for g in self.gbot.grid:
                g.type = 'limit'
                
    def dynamic_check_triggers(self, tick, indicator):
        #This is only need for live (not backtesting), where we need to change a trigger to limit to initative a new order
        if  self.gbot.config.dynamic_grid and tick > 0:
            for g in self.gbot.grid:
                if g.mode == 'sell' and g.type == 'trigger' and g.ticker <= tick:
                    if indicator.sell_indicator:
                        #toggle type from trigger to limit, so that it triggers an order
                        g.type = 'limit'
                        logger.info("[%d] %.5f triggered @ tick: %.5f %s" % (g.step, g.ticker, tick, indicator))
                    else:
                       logger.info("[%d] delayed trigger tick: %.5f %s" % (g.step, tick, indicator))
                if g.mode == 'buy' and g.type == 'trigger' and g.ticker >= tick:
                    if indicator.buy_indicator:
                        #toggle type from trigger to limit, so that it triggers an order
                        g.type = 'limit'
                        logger.info("[%d] %.5f triggered @ tick: %.5f %s" % (g.step, g.ticker, tick, indicator))
                    else:
                       logger.info("[%d] delayed trigger tick: %.5f %s" % (g.step, tick, indicator))
                    
    def dynamic_grid_adjust(self, new_ticker):
        if not self.gbot.config.dynamic_grid:
            #skip this function if we aren't in dynamic mode
            return
        #TODO: check no open orders 1st?
        sell_amt = self.total_sell_b()
        # reset none line grid ticker
        none = self._current_none()
        logger.info("dynamic_grid_adjust [%d] old:%.5f new:%.5f" %(none, self.gbot.grid[none].ticker, new_ticker))
        
        self.gbot.grid[none].ticker = new_ticker
        
        # reset grid tickers below none line
        t_ticker = new_ticker
        for i in range(none-1, -1, -1):
            t_ticker = t_ticker / (1+self.gbot.config.grid_spacing)
            self.gbot.grid[i].ticker = t_ticker
        
        # reset grids tickers above none line
        t_ticker = new_ticker
        for i in range(none+1, self.grids()):
            t_ticker = t_ticker * (1+self.gbot.config.grid_spacing)
            self.gbot.grid[i].ticker = t_ticker
        
        #recalculate each grid    
        for g in self.gbot.grid:
            #should NOT change
            #g.buy_quote_quantity = each_grid_buy 
            #g.sell_quote_quantity = g.sell_base_quantity*g.ticker
            #g.step_take = (g.ticker-last_grid_tick)*g.sell_base_quantity
            g.buy_base_quantity = g.buy_quote_quantity/g.ticker
            g.sell_base_quantity = g.buy_base_quantity*(1+self.gbot.config.grid_spacing)
            if g.mode == 'sell':
                if sell_amt >= g.sell_base_quantity:
                    sell_amt -= g.sell_base_quantity
                else:
                    g.sell_base_quantity = sell_amt
                    sell_amt = 0
                g.sell_quote_quantity = g.sell_base_quantity*g.ticker    
            #if sell_amt != 0:
            #if its zero, won't hurt to add it to the last grid
            self.gbot.grid[-1].sell_base_quantity += sell_amt
            self.gbot.grid[-1].sell_quote_quantity = g.sell_base_quantity*g.ticker
    
    @property        
    def open_orders(self):
        ret = False
        for g in self.gbot.grid:
            if g.ex_orderid != None:
                ret = True
                break
        return (ret)
            