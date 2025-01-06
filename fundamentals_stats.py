from pandas import DataFrame
import pandas as pd
import os
import time
import re
from datetime import datetime
from utils import data_string_to_float
from tqdm import tqdm
from typing import Any, Dict, List

class FundamentalsStats:

    def __init__(self, features: List, statspath: str):

        self.features = features
        self.statspath = statspath

    def preprocess_price_data(self):
        """
        Currently, the sp500 and stock price datasets we downloaded do not have any data for
        days when the market was closed (weekends and public holidays). We need to amend this so that
        all rows are included. Doing this now saves a lot of effort when we actually create the
        keystats dataset, which requires that we have stock data every day.
        :return: SP500 and stock dataframes, with no missing rows.
        """
        # Read in SP500 data and stock data, parsing the dates.
        sp500_raw_data = pd.read_csv("stock_data/sp500_08_2003_to_01_2015_index.csv", index_col="Date", parse_dates=True)
        stock_raw_data = pd.read_csv("stock_data/stock_08_2003_to_01_2015_prices.csv", index_col="Date", parse_dates=True)
        sp_start_date, sp_end_date = str(sp500_raw_data.index[0]), str(sp500_raw_data.index[-1])
        stock_start_date, stock_end_date = str(stock_raw_data.index[0]), str(stock_raw_data.index[-1])
        sp_date_range = pd.date_range(start=sp_start_date, end=sp_end_date, freq="D")  # Include all days
        stock_date_range = pd.date_range(start=stock_start_date, end=stock_end_date, freq="D")
        sp500_raw_data = sp500_raw_data.reindex(sp_date_range)
        stock_raw_data = stock_raw_data.reindex(stock_date_range)
        sp500_raw_data = sp500_raw_data.reset_index()
        stock_raw_data = stock_raw_data.reset_index()
        sp500_raw_data.rename(columns={"index": "Date"}, inplace=True)
        stock_raw_data.rename(columns={"index": "Date"}, inplace=True)
        sp500_raw_data.ffill(inplace=True)
        stock_raw_data.ffill(inplace=True)
        sp500_raw_data["Date"] = sp500_raw_data["Date"].dt.date
        stock_raw_data["Date"] = stock_raw_data["Date"].dt.date
        stock_raw_data['Date'] = stock_raw_data['Date'].astype(str)
        sp500_raw_data['Date'] = sp500_raw_data['Date'].astype(str)
        sp500_raw_data.set_index('Date', inplace=True)
        stock_raw_data.set_index('Date', inplace=True)
        return sp500_raw_data, stock_raw_data

    def parse_keystats(self, sp500_df: DataFrame, stock_df: DataFrame):
        """
        We have downloaded a large number of html files, which are snapshots of a ticker at different times,
        containing the fundamental data (our features). To extract the key statistics, we use regex.
        For supervised machine learning, we also need the data that will form our dependent variable,
        the performance of the stock compared to the SP500.
        :sp500_df: dataframe containing SP500 prices
        :stock_df: dataframe containing stock prices
        :return: a dataframe of training data (i.e features and the components of our dependent variable)
        """
        stock_list = [x[0] for x in os.walk(self.statspath)]
        stock_list = stock_list[1:]
        df_columns = [
                 "Date",
                 "Unix",
                 "Ticker",
                 "Price",
                 "stock_p_change",
                 "SP500",
                 "SP500_p_change",
                     ] + self.features
        df = pd.DataFrame(columns=df_columns)
        # tqdm is a simple progress bar
        for stock_directory in tqdm(stock_list, desc="Parsing progress:", unit="tickers"):
            keystats_html_files = os.listdir(stock_directory)
            ticker = stock_directory.split(self.statspath)[1]
            for file in keystats_html_files:
                date_stamp = datetime.strptime(file, "%Y%m%d%H%M%S.html")
                unix_time = time.mktime(date_stamp.timetuple())
                full_file_path = stock_directory + "/" + file
                value_list = []

                with open(full_file_path, "r") as source:
                    source = source.read()
                    source = source.replace(",", "")
                    for variable in features:
                        try:
                            regex = (
                                    r">" + re.escape(variable) + r".*?(\-?\d+\.*\d*K?M?B?|N/A[\\n|\s]*|>0|NaN)%?"
                                                                 r"(</td>|</span>)"
                            )
                            value = re.search(regex, source, flags=re.DOTALL).group(1)
                            value_list.append(data_string_to_float(value))
                        except AttributeError:
                            if variable == "Avg Vol (3 month)":
                                try:
                                    new_variable = ">Average Volume (3 month)"
                                    regex = (
                                            re.escape(new_variable) + r".*?(\-?\d+\.*\d*K?M?B?|N/A[\\n|\s]*|>0)%?"
                    r"(</td>|</span>)"
                                    )
                                    value = re.search(regex, source, flags=re.DOTALL).group(1)
                                    value_list.append(data_string_to_float(value))
                                except AttributeError:
                                    value_list.append("N/A")
                            else:
                                value_list.append("N/A")

                current_date = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d")
                one_year_later = datetime.fromtimestamp(unix_time + 31536000).strftime("%Y-%m-%d")

                sp500_price = float(sp500_df.loc[current_date, "Close"])
                sp500_1y_price = float(sp500_df.loc[one_year_later, "Close"])
                sp500_p_change = round(
                    ((sp500_1y_price - sp500_price) / sp500_price * 100), 2)

                stock_price, stock_1y_price = "N/A", "N/A"
                try:
                    stock_price = float(stock_df.loc[current_date, ticker.upper()])
                    stock_1y_price = float(stock_df.loc[one_year_later, ticker.upper()])
                except KeyError:
                    continue

                stock_p_change = round(((stock_1y_price - stock_price) / stock_price * 100), 2)
                new_df_row = [date_stamp, unix_time, ticker, stock_price, stock_p_change, sp500_price,
                              sp500_p_change] + value_list
                df = pd.concat([df,pd.DataFrame(dict(zip(df_columns, new_df_row)), index=[0])], ignore_index=True)
        df.dropna(axis=0, subset=["Price", "stock_p_change"], inplace=True)
        df.to_csv("keystats.csv", index=False)


if __name__ == "__main__":

    features = [  # Valuation measures
        "Market Cap",
        "Enterprise Value",
        "Trailing P/E",
        "Forward P/E",
        "PEG Ratio",
        "Price/Sales",
        "Price/Book",
        "Enterprise Value/Revenue",
        "Enterprise Value/EBITDA",
        #  Financial highlights
        "Profit Margin",
        "Operating Margin",
        "Return on Assets",
        "Return on Equity",
        "Revenue",
        "Revenue Per Share",
        "Qtrly Revenue Growth",
        "Gross Profit",
        "EBITDA",
        "Net Income Avl to Common",
        "Diluted EPS",
        "Qtrly Earnings Growth",
        "Total Cash",
        "Total Cash Per Share",
        "Total Debt",
        "Total Debt/Equity",
        "Current Ratio",
        "Book Value Per Share",
        "Operating Cash Flow",
        "Levered Free Cash Flow",
        # Trading information
        "Beta",
        "50-Day Moving Average",
        "200-Day Moving Average",
        "Avg Vol (3 month)",
        "Shares Outstanding",
        "Float",
        "% Held by Insiders",
        "% Held by Institutions",
        "Shares Short (as of",
        "Short Ratio",
        "Short % of Float",
        "Shares Short (prior month",
    ]
    statspath = "intraQuarter/_KeyStats/"
    stats = FundamentalsStats(features, statspath)
    sp500_df, stock_df = stats.preprocess_price_data()
    stats.parse_keystats(sp500_df, stock_df)
