from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import backtrader as bt
import os
import pandas as pd  # Import pandas for data handling
from myBinance import GetMACD, GetStoch  # Import the required functions

# Define the Custom Strategy with additional indicators for exit conditions
class CustomStrategy(bt.Strategy):
    params = (('ma_period', 5), ('rsi_period', 14), ('quantity', 0.01), ('fee_rate', 0.0004), ('leverage', 3))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.ma_period)
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.params.rsi_period)
        self.long_position = 0
        self.short_position = 0
        self.entry_price_long = 0
        self.entry_price_short = 0

    def next(self):
        # Convert Backtrader data to a DataFrame for compatibility with GetMACD and GetStoch
        ohlcv = pd.DataFrame({
            'close': self.dataclose.get(size=len(self.dataclose)),
            'high': self.datas[0].high.get(size=len(self.datas[0].high)),
            'low': self.datas[0].low.get(size=len(self.datas[0].low))
        })

        # Get MACD and Stochastic values
        macd_values = GetMACD(ohlcv, 0)
        stoch_values = GetStoch(ohlcv, 14, 0)

        # Skip if order is pending
        if self.order:
            return

        # Long Position Handling
        if not self.position:
            if self.dataclose[0] > self.sma[0] and self.rsi[0] > 50:
                self.long_position = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.entry_price_long = self.dataclose[0]
                self.order = self.buy(size=self.long_position)
                print(f"Entering Long: Price {self.dataclose[0]}, Size {self.long_position}")

            elif self.dataclose[0] < self.sma[0] and self.rsi[0] < 50:
                self.short_position = (self.broker.getvalue() * self.params.quantity) / self.dataclose[0]
                self.entry_price_short = self.dataclose[0]
                self.order = self.sell(size=self.short_position)
                print(f"Entering Short: Price {self.dataclose[0]}, Size {self.short_position}")

        # Manage Long Position
        elif self.position.size > 0:
            revenue_rate = self.calculate_revenue_rate(self.dataclose[0], self.entry_price_long, self.position.size)
            if revenue_rate > 3.0 or (macd_values['macd'] < macd_values['macd_siginal']) or stoch_values['fast_k'] > 80:
                self.order = self.sell(size=self.position.size)
                print(f"Exiting Long: Price {self.dataclose[0]}, Total Size {self.position.size}")

        # Manage Short Position
        elif self.position.size < 0:
            revenue_rate = self.calculate_revenue_rate(self.dataclose[0], self.entry_price_short, -self.position.size)
            if revenue_rate > 3.0 or (macd_values['macd'] > macd_values['macd_siginal']) or stoch_values['fast_k'] < 20:
                self.order = self.buy(size=abs(self.position.size))
                print(f"Exiting Short: Price {self.dataclose[0]}, Total Size {abs(self.position.size)}")

    def calculate_revenue_rate(self, current_price, entry_price, size):
        if entry_price == 0 or size == 0:
            return 0
        pnl = (current_price - entry_price) * size if size > 0 else (entry_price - current_price) * abs(size)
        fees = abs(entry_price * size * self.params.fee_rate) + abs(current_price * size * self.params.fee_rate)
        revenue_rate = ((pnl - fees) / (entry_price * abs(size))) * 100 * self.params.leverage
        return revenue_rate

# Updated backtesting function to accept 10 parameters
def run_custom_backtest(datapath, start, end, period, strategy, commission_val, portofolio, stake_val, quantity, plot):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(CustomStrategy, ma_period=period, rsi_period=14, quantity=quantity, fee_rate=commission_val/100, leverage=3)

    # Load 5-minute data for testing
    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        dtformat=2,
        compression=5,  # 5-minute bars
        timeframe=bt.TimeFrame.Minutes,
        fromdate=datetime.datetime.strptime(start, '%Y-%m-%d'),
        todate=datetime.datetime.strptime(end, '%Y-%m-%d'),
        reverse=False
    )

    cerebro.adddata(data)
    cerebro.broker.setcash(portofolio)
    cerebro.broker.setcommission(commission=commission_val/100)

    # Performance indicators
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    # Run backtest
    print(f"\nStarting Portfolio Value for {strategy}: {cerebro.broker.getvalue():.2f}")
    results = cerebro.run()
    stratexe = results[0]
    end_value = cerebro.broker.getvalue()

    # Extract performance metrics
    try:
        totalwin = stratexe.analyzers.ta.get_analysis().won.total
        totalloss = stratexe.analyzers.ta.get_analysis().lost.total
        pnl_net = stratexe.analyzers.ta.get_analysis().pnl.net.total
        sqn = stratexe.analyzers.sqn.get_analysis().sqn
    except KeyError:
        totalwin = totalloss = pnl_net = sqn = 0

    print(f"Ending Portfolio Value for {strategy}: {end_value:.2f}")

    # Plotting if enabled
    if plot:
        cerebro.plot()

    return end_value, totalwin, totalloss, pnl_net, sqn

# Main function to execute the backtest
def main():
    # Get the list of CSV files in the 'data' directory
    data_dir = './data'
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    # Display available files to the user
    print("Available data files:")
    for i, file in enumerate(csv_files):
        print(f"{i + 1}. {file}")

    # Prompt user to select files
    selected_indices = input("Select the files to test (e.g., 1,2,3): ")
    selected_indices = [int(idx) - 1 for idx in selected_indices.split(',')]

    # Execute backtest for each selected file
    for idx in selected_indices:
        selected_file = csv_files[idx]
        data_path = os.path.join(data_dir, selected_file)
        run_custom_backtest(data_path, '2022-01-01', '2024-08-31', 5, 'CustomStrategy', 0.04, 10000.0, 1, 0.1, False)

if __name__ == '__main__':
    main()
