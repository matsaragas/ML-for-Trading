import os
import pandas as pd
import yfinance as yf
from typing import List


class DataLoader:

    def __init__(self, tickers: List, start_date: str, end_date: str):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date

    def build_stock_dataset(self) -> None:
        """
        Creates the dataset containing all stock prices
        :returns: stock_prices.csv
        """
        data = yf.download(self.tickers, self.start_date, self.end_date, auto_adjust=True)[['Close', 'Volume']]
        data_adj_close = data['Close'].reset_index()
        data_volume = data['Volume'].reset_index()
        data_path = os.path.join(os.getcwd(), "stock_data")
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        data_adj_close.to_csv(os.path.join(data_path, "stock_prices.csv"))
        data_volume.to_csv(os.path.join(data_path, "stock_volumes.csv"))

    def build_sp500_dataset(self) -> None:
        """
        Creates the dataset containing S&P500 prices
        :returns: sp500_index.csv
        """
        index_data = yf.download("SPY", start=START_DATE, end=END_DATE, auto_adjust=True)
        index_data.to_csv("stock_data/sp500_index.csv")


if __name__ == "__main__":

    START_DATE = "2018-08-01"
    END_DATE = "2025-01-01"
    tickers = ['MMM', "AOS", "GOOGL", "AMZN", "AEP", "AXP", "AIG", "AMP", "ADI", "AAPL"]

    stock_data = DataLoader(tickers, START_DATE, END_DATE)
    stock_data.build_stock_dataset()
    stock_data.build_sp500_dataset()
