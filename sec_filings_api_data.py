import requests
import json
import pandas as pd
from pandas import DataFrame
from sec_api import QueryApi
import time
import os
from datetime import datetime
from typing import Any, Dict, List

from utils import num


class SecApiFilings:

    def __init__(self, api_key: str, xbrl_converter_api_endpoint: str, save_dir: str):
        self.api_key = api_key
        self.xbrl_converter_api_endpoint = xbrl_converter_api_endpoint
        self.save_dir = save_dir

    def get_income_statement(self, xbrl_json) -> DataFrame:
        income_statement_store = {}
        # iterate over each US GAAP item in the income statement
        for usGaapItem in xbrl_json['StatementsOfIncome']:
            values = []
            indices = []
            for fact in xbrl_json['StatementsOfIncome'][usGaapItem]:
                # only consider items without segment. not required for our analysis.
                if 'segment' not in fact:
                    index = fact['period']['startDate'] + '-' + fact['period']['endDate']
                    # ensure no index duplicates are created
                    if index not in indices:
                        values.append(fact['value'])
                        indices.append(index)

            income_statement_store[usGaapItem] = pd.Series(values, index=indices)

        income_statement = pd.DataFrame(income_statement_store)
        return income_statement.T

    def get_balance_sheet(self, xbrl_json: Dict[str, Any]) -> DataFrame:
        balance_sheet_store = {}
        for usGaapItem in xbrl_json['BalanceSheets']:
            values = []
            indices = []
            for fact in xbrl_json['BalanceSheets'][usGaapItem]:
                if 'segment' not in fact:
                    index = fact['period']['instant']
                    if index in indices:
                        continue

                    if "value" not in fact:
                        values.append(0)
                    else:
                        values.append(fact['value'])

                    indices.append(index)

                balance_sheet_store[usGaapItem] = pd.Series(values, index=indices)
        balance_sheet = pd.DataFrame(balance_sheet_store)
        return balance_sheet.T

    def get_cash_flow_statement(self, xbrl_json: Dict[str, Any]) -> DataFrame:

        cash_flows_store = {}
        for usGaapItem in xbrl_json['StatementsOfCashFlows']:
            values = []
            indices = []
            for fact in xbrl_json['StatementsOfCashFlows'][usGaapItem]:
                if 'segment' not in fact:
                    if "instant" in fact['period']:
                        index = fact['period']['instant']
                    else:
                        index = fact['period']['startDate'] + '-' + fact['period']['endDate']
                    if index in indices:
                        continue
                    if "value" not in fact:
                        values.append(0)
                    else:
                        values.append(fact['value'])
                    indices.append(index)
            cash_flows_store[usGaapItem] = pd.Series(values, index=indices)
        cash_flows = pd.DataFrame(cash_flows_store)
        return cash_flows.T

    def accession_number_generator(self, query: Dict[str, Any]) -> List:

        #get your API key at https://sec-api.i
        query_api = QueryApi(api_key=self.api_key)
        query_result = query_api.get_filings(query)
        accession_numbers = []
        # extract accession numbers of each filing
        for filing in query_result['filings']:
            accession_numbers.append(filing['accessionNo'])

        return accession_numbers

    def get_xbrl_json(self, accession_no: str, retry=0) -> Dict[str, Any]:

        request_url = self.xbrl_converter_api_endpoint + "?accession-no=" + accession_no + "&token=" + self.api_key
        try:
            response_tmp = requests.get(request_url)
            xbrl_json = json.loads(response_tmp.text)
        except:
            if retry > 5:
                raise Exception('API error')
            time.sleep(0.5)
            return self.get_xbrl_json(accession_no, retry + 1)
        return xbrl_json

    def clean_income_statement(self, statement: DataFrame) -> DataFrame:

        for column in statement:
            is_nan_column = statement[column].isna().sum() > 5
            if column.endswith('_left') or column == 'key_0' or is_nan_column:
                statement = statement.drop(column, axis=1)

        sorted_columns = sorted(statement.columns.values)
        return statement[sorted_columns]

    def merge_income_statements(self, statement_a: DataFrame, statement_b: DataFrame) -> DataFrame:
        return statement_a.merge(statement_b,
                                 how="outer",
                                 right_on=statement_b.index,
                                 left_index=True,
                                 suffixes=('_left', ''))

    def add_fourth_quarter_results(self, statement: DataFrame) -> DataFrame:

        for column in statement:
            date_strings = [a for a in column.split('-')]
            d0 = datetime.strptime(date_strings[0] + date_strings[1] + date_strings[2], '%Y%m%d')
            d1 = datetime.strptime(date_strings[3] + date_strings[4] + date_strings[5], '%Y%m%d')
            delta = d1 - d0

            if delta.days > 350:
                for column_1 in statement:
                    date_strings_1 = [a for a in column_1.split('-')]
                    d1_0 = datetime.strptime(date_strings_1[0] + date_strings_1[1] + date_strings_1[2], '%Y%m%d')
                    d1_1 = datetime.strptime(date_strings_1[3] + date_strings_1[4] + date_strings_1[5], '%Y%m%d')
                    delta_1 = d1_1 - d1_0

                    if (d1_0 == d0) and (delta_1.days > 200) and (delta_1.days < 350):
                        fourth_quarter_column_name = column_1[11:] + column[10:]
                        fourth_quarter_values = []

                        for row_key, row_value in statement[column].items():
                            print('Number:', statement[column][row_key])
                            value = num(statement[column][row_key]) - num(statement[column_1][row_key])
                            if isinstance(value, float):
                                value = round(value, 2)

                            fourth_quarter_values.append(str(value))

                        statement[fourth_quarter_column_name] = fourth_quarter_values
                        statement[fourth_quarter_column_name]["WeightedAverageNumberOfSharesOutstandingBasic"] = statement[column]["WeightedAverageNumberOfSharesOutstandingBasic"]
                        statement[fourth_quarter_column_name]["WeightedAverageNumberOfDilutedSharesOutstanding"] = statement[column]["WeightedAverageNumberOfDilutedSharesOutstanding"]
                        statement[fourth_quarter_column_name]["EarningsPerShareBasic"] = round(num(statement[fourth_quarter_column_name]["NetIncomeLoss"]) /
                                                                                           num(statement[fourth_quarter_column_name]["WeightedAverageNumberOfSharesOutstandingBasic"]), 2)

                        statement[fourth_quarter_column_name]["EarningsPerShareDiluted"] = round(num(statement[fourth_quarter_column_name]["NetIncomeLoss"]) /
                                                                                                 num(statement[fourth_quarter_column_name]["WeightedAverageNumberOfDilutedSharesOutstanding"]), 2)

        sorted_columns = sorted(statement.columns.values)
        return statement[sorted_columns]

    def retrieve_income_statement(self, ticker: str) -> DataFrame:
        query = {
            "query": {
                "query_string": {
                    "query": f"(formType:\"10-Q\" OR formType:\"10-K\") AND ticker:{ticker}"
                }
            },
            "from": "0",
            "size": "30",
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        previous_income_statement_set = False
        income_statement_final = None
        accession_numbers = self.accession_number_generator(query)
        for accession_no in accession_numbers:
            print('Processing: ' + accession_no)
            xbrl_json_data = self.get_xbrl_json(accession_no)
            income_statement_uncleaned = self.get_income_statement(xbrl_json_data)
            income_statement_cleaned = self.clean_income_statement(income_statement_uncleaned)
            if previous_income_statement_set:
                income_statement_final = self.clean_income_statement(
                    self.merge_income_statements(income_statement_final, income_statement_cleaned))
            else:
                income_statement_final = income_statement_cleaned
                previous_income_statement_set = True

        income_statement_final = income_statement_final.dropna()
        income_statement_final = self.add_fourth_quarter_results(income_statement_final)
        return income_statement_final

    def get_ticker_income_statements(self, ticker: str, save=False) -> DataFrame:
        income_statement = self.retrieve_income_statement(ticker)
        if save:
            file_name = f"{ticker}_Quarterly_Income_Statement.xlsx"
            save_path = os.path.join(self.save_dir, file_name)
            income_statement.to_csv(save_path)

        return income_statement


if __name__ == "__main__":
    api_key = '8c04a5be4b815aeb0d6de32c9c7f4ff894ad8b2e4b366c8ee6c779254ee3a3f7'
    ticker_list = ["AAPL"]
    save_dir = "sec_api_data"
    xbrl_converter_api_endpoint = "https://api.sec-api.io/xbrl-to-json"
    sec_filings = SecApiFilings(api_key, xbrl_converter_api_endpoint, save_dir)
    for ticker in ticker_list:
        sec_filings.get_ticker_income_statements(ticker, save=True)







