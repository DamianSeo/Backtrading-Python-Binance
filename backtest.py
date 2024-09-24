from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import backtrader as bt

# Define the strategies (SMA and RSI) as they were defined in your original code
class SMAStrategy(bt.Strategy):
    params = (('maperiod', None), ('quantity', None))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.amount = None
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.buy(size=self.amount)
        else:
            if self.dataclose[0] < self.sma[0]:
                self.order = self.sell(size=self.amount)

class RSIStrategy(bt.Strategy):
    params = (('maperiod', None), ('quantity', None))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.amount = None
        self.rsi = bt.talib.RSI(self.datas[0], timeperiod=self.params.maperiod)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.rsi < 30:
                self.amount = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.order = self.buy(size=self.amount)
        else:
            if self.rsi > 70:
                self.order = self.sell(size=self.amount)

# Helper functions to manage timeframes and analyze results
def timeFrame(datapath):
    sepdatapath = datapath[5:-4].split(sep='-')
    tf = sepdatapath[3]

    timeframes = {
        '1mth': (1, bt.TimeFrame.Months),
        '12h': (720, bt.TimeFrame.Minutes),
        '15m': (15, bt.TimeFrame.Minutes),
        '30m': (30, bt.TimeFrame.Minutes),
        '1d': (1, bt.TimeFrame.Days),
        '1h': (60, bt.TimeFrame.Minutes),
        '3m': (3, bt.TimeFrame.Minutes),
        '2h': (120, bt.TimeFrame.Minutes),
        '3d': (3, bt.TimeFrame.Days),
        '1w': (1, bt.TimeFrame.Weeks),
        '4h': (240, bt.TimeFrame.Minutes),
        '5m': (5, bt.TimeFrame.Minutes),
        '6h': (360, bt.TimeFrame.Minutes),
        '8h': (480, bt.TimeFrame.Minutes)
    }

    return timeframes.get(tf, (None, None))

def getWinLoss(analyzer):
    return analyzer.won.total, analyzer.lost.total, analyzer.pnl.net.total

def getSQN(analyzer):
    return round(analyzer.sqn, 2)

def runbacktest(datapath, start, end, period, strategy, commission_val=None, portofolio=10000.0, stake_val=1, quantity=0.01, plt=False):
    cerebro = bt.Cerebro()
    cerebro.addsizer(bt.sizers.FixedSize, stake=stake_val)
    cerebro.broker.setcash(portofolio)

    if commission_val:
        cerebro.broker.setcommission(commission=commission_val/100)

    if strategy == 'SMA':
        cerebro.addstrategy(SMAStrategy, maperiod=period, quantity=quantity)
    elif strategy == 'RSI':
        cerebro.addstrategy(RSIStrategy, maperiod=period, quantity=quantity)
    else:
        print('no strategy')
        exit()

    compression, timeframe = timeFrame(datapath)

    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        dtformat=2,
        compression=compression,
        timeframe=timeframe,
        fromdate=datetime.datetime.strptime(start, '%Y-%m-%d'),
        todate=datetime.datetime.strptime(end, '%Y-%m-%d'),
        reverse=False
    )

    cerebro.adddata(data)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    strat = cerebro.run()
    stratexe = strat[0]

    try:
        totalwin, totalloss, pnl_net = getWinLoss(stratexe.analyzers.ta.get_analysis())
    except KeyError:
        totalwin, totalloss, pnl_net = 0, 0, 0

    sqn = getSQN(stratexe.analyzers.sqn.get_analysis())

    if plt:
        cerebro.plot()

    return cerebro.broker.getvalue(), totalwin, totalloss, pnl_net, sqn

# Main function to run backtesting for all coins and strategies
def main():
    coins = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
    strategies = ['SMA', 'RSI']
    period_range = range(10, 31)  # Range of periods to test
    start_date = '2022-01-01'
    end_date = '2024-08-31'

    # Adjust file paths to your CSV data location
    data_paths = {
        'BTCUSDT': 'BTCUSDT-2022-2024-1mth.csv',
        'ETHUSDT': 'ETHUSDT-2022-2024-1mth.csv',
        'XRPUSDT': 'XRPUSDT-2022-2024-1mth.csv'
    }

    for coin in coins:
        for strategy in strategies:
            for period in period_range:
                data_path = data_paths[coin]
                final_value, totalwin, totalloss, pnl_net, sqn = runbacktest(
                    data_path, start_date, end_date, period, strategy,
                    commission_val=0.04, portofolio=10000.0, stake_val=1, quantity=0.10, plt=False
                )

                print(f"{coin} | {strategy} | Period: {period}")
                print(f"Final Value: {final_value}, Total Wins: {totalwin}, Total Losses: {totalloss}, Net PnL: {pnl_net}, SQN: {sqn}\n")

if __name__ == '__main__':
    main()
