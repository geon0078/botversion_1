from pykiwoom.kiwoom import *
import time
import pandas as pd
import sqlite3

class RealTimeStockDataUpdater:
    def __init__(self, db_path, tick_ranges, update_interval=1):
        self.db_path = db_path
        self.tick_ranges = tick_ranges
        self.update_interval = update_interval
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)
        self.stock_codes = self._get_tracked_stock_codes()

    def _get_tracked_stock_codes(self):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT code FROM tracked_stocks"
        stock_codes_df = pd.read_sql_query(query, conn)
        conn.close()
        return stock_codes_df['code'].tolist()

    def _fetch_stock_data(self, code, tick_range):
        df = self.kiwoom.block_request("opt10080",
                                       종목코드=code,
                                       틱범위=tick_range,
                                       output="주식분봉차트조회",
                                       next=0)
        df['종목코드'] = code
        return df

    def _format_datetime(self, dt_str):
        return pd.to_datetime(dt_str, format='%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')

    def _save_data_to_db(self, data, tick_range):
        conn = sqlite3.connect(self.db_path)
        for stock_code, df in data.items():
            table_name = f"{tick_range}분_{stock_code}"
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()

    def update_stock_data(self):
        while True:
            for tick_range in self.tick_ranges:
                all_data = pd.DataFrame()
                for code in self.stock_codes:
                    df = self._fetch_stock_data(code, tick_range)
                    all_data = pd.concat([all_data, df], ignore_index=True)
                    time.sleep(1)  # Avoid hitting the API rate limit
                
                # Get only the current date data
                current_date = pd.Timestamp.now().strftime('%Y%m%d')
                all_data = all_data[all_data['체결시간'].str.startswith(current_date)]
                
                all_data.rename(columns={
                    '현재가': 'close',
                    '거래량': 'volume',
                    '체결시간': 'date',
                    '시가': 'open',
                    '고가': 'high',
                    '저가': 'low',
                    '종목코드': 'stock_code'
                }, inplace=True)
                
                reordered_columns = ['stock_code', 'date', 'open', 'high', 'close', 'low', 'volume']
                reordered_df = all_data[reordered_columns]
                
                reordered_df.loc[:, 'date'] = reordered_df['date'].apply(self._format_datetime)
                
                grouped_data = reordered_df.groupby('stock_code')
                stock_data_dict = {stock_code: data for stock_code, data in grouped_data}
                
                for stock_code in stock_data_dict.keys():
                    stock_data_dict[stock_code] = stock_data_dict[stock_code].sort_values(by='date')
                    stock_data_dict[stock_code][['open', 'high', 'close', 'low', 'volume']] = stock_data_dict[stock_code][['open', 'high', 'close', 'low', 'volume']].apply(pd.to_numeric, errors='coerce').abs()
                
                self._save_data_to_db(stock_data_dict, tick_range)
            
            time.sleep(self.update_interval)  # Wait before fetching data again

# Usage example
db_path = '20240717_시가갭검색식_돌파.db'
tick_ranges = [3]
updater = RealTimeStockDataUpdater(db_path, tick_ranges, update_interval=0.2)
updater.update_stock_data()
