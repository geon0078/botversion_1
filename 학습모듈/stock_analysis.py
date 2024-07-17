import sqlite3
import pandas as pd
import mplfinance as mpf
import re

class StockAnalyzer:
    def __init__(self, db_file):
        self.db_file = db_file
        self.date_str = self.extract_date_from_filename(db_file)
        self.conn = sqlite3.connect(db_file)
        self.tables = self.get_tables()

    def extract_date_from_filename(self, filename):
        match = re.search(r'\d{8}', filename)
        if match:
            date_str = match.group(0)
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            return formatted_date
        else:
            raise ValueError("Filename does not contain a valid date")

    def get_tables(self):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '3분%';"
        tables = pd.read_sql_query(query, self.conn)
        return tables['name'].tolist()

    def analyze_table(self, table_name):
        query = f'SELECT * FROM "{table_name}" WHERE date LIKE "{self.date_str}%";'
        df = pd.read_sql_query(query, self.conn)
        
        if df.empty:
            return

        # 날짜 형식을 datetime으로 변환
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # 1번째 봉의 시가와 종가
        first_open, first_close = df.iloc[0]['open'], df.iloc[0]['close']
        print(f"{table_name}: 1번째 봉 시가 = {first_open}, 종가 = {first_close}")
        
        # 첫 번째 봉부터 n번째 봉까지 (n은 1보다 크고 3보다 작음) 모두 양봉인지 확인
        all_bullish = True
        last_close = first_close
        for i in range(1, min(5, len(df))):
            if df.iloc[i]['close'] <= df.iloc[i]['open']:
                all_bullish = False
                print(f"{table_name}: {i+1}번째 봉은 양봉이 아닙니다. 시가 = {df.iloc[i]['open']}, 종가 = {df.iloc[i]['close']}")
                break
            last_close = df.iloc[i]['close']
            print(f"{table_name}: {i+1}번째 봉은 양봉입니다. 시가 = {df.iloc[i]['open']}, 종가 = {df.iloc[i]['close']}")
        
        # 두 번째 봉이 음봉이고, 두 번째 봉의 저가가 첫 번째 봉의 시가보다 낮은지 확인
        no_buy = False
        if len(df) > 1 and df.iloc[1]['close'] < df.iloc[1]['open'] and df.iloc[1]['low'] < first_open:
            no_buy = True
            print(f"{table_name}: 2번째 봉이 음봉이며, 저가가 1번째 봉의 시가보다 낮습니다. 매수하지 않습니다.")
        
        # 조건에 따른 가격 설정
        zero_price = first_open
        one_price = last_close
        
        addplots = [
            mpf.make_addplot(pd.Series([zero_price]*len(df), index=df.index), type='line', linestyle='--', color='b', label='0 Price'),
            mpf.make_addplot(pd.Series([one_price]*len(df), index=df.index), type='line', linestyle='--', color='g', label='1 Price')
        ]

        if no_buy:
            print(f"{table_name}: 매수 주문이 설정되지 않았습니다.")
        else:
            buy_price = zero_price + 0.382 * (one_price - zero_price)
            print(f"{table_name}: 매수 주문을 {buy_price}에 설정합니다.")
            
            # 0.786과 1.618 가격 계산
            price_0786 = zero_price + 0.786 * (one_price - zero_price)
            price_1618 = zero_price + 1.618 * (one_price - zero_price)
            
            addplots.append(mpf.make_addplot(pd.Series([buy_price]*len(df), index=df.index), type='line', linestyle='--', color='r', label='Buy Order (0.382)'))
            addplots.append(mpf.make_addplot(pd.Series([price_0786]*len(df), index=df.index), type='line', linestyle='--', color='purple', label='0.786 Price'))
            addplots.append(mpf.make_addplot(pd.Series([price_1618]*len(df), index=df.index), type='line', linestyle='--', color='orange', label='1.618 Price'))

        mpf.plot(df, type='candle', addplot=addplots, title=f"{table_name} - {self.date_str}", style='charles', ylabel='Price')

    def analyze_all(self):
        for table_name in self.tables:
            self.analyze_table(table_name)

    def close_connection(self):
        self.conn.close()

if __name__ == "__main__":
    db_file = '20240717_시가갭검색식_돌파.db'
    analyzer = StockAnalyzer(db_file)
    analyzer.analyze_all()
    analyzer.close_connection()
