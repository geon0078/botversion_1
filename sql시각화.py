import sqlite3
import pandas as pd
import mplfinance as mpf
import os

class DBVisualizer:
    def __init__(self, db_name):
        self.db_name = db_name
        self.db_path = f'{db_name}.db'
        self.charts_folder = db_name

    def fetch_table_names(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [name[0] for name in cursor.fetchall()]
        conn.close()
        return tables

    def visualize_all(self):
        tables = self.fetch_table_names()
        for selected_table in tables:
            conn = sqlite3.connect(self.db_path)
            query = f'SELECT * FROM "{selected_table}"'
            try:
                df = pd.read_sql_query(query, conn, parse_dates=['date'], index_col='date')
            except KeyError as e:
                print(f"Error with table {selected_table}: {e}")
                continue
            finally:
                conn.close()
            
            df_filtered = df.between_time('09:00', '10:00')
            
            prev_day = df.index.max() - pd.Timedelta(days=1)
            prev_day_df = df.loc[df.index.date == prev_day.date(), 'close']
            
            if not prev_day_df.empty:
                prev_day_close = prev_day_df.iloc[-1]
            else:
                prev_day_close = "N/A"
            
            title = f'Candlestick chart for {selected_table} (9-10 AM)'
            if prev_day_close != "N/A":
                title += f"\nPrevious day's close: {prev_day_close}"
            
            save_path = f'./{self.charts_folder}/{selected_table}.jpg'
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            savefig_options = {'fname': save_path, 'dpi': 100}
            mpf.plot(df_filtered, type='candle', style='charles', title=title, volume=True, savefig=savefig_options)

# Example usage
db_name = '20240715_90%이상 주장 단타'
visualizer = DBVisualizer(db_name)
visualizer.visualize_all()