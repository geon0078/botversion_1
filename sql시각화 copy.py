import sqlite3
import pandas as pd
import mplfinance as mpf
import os
import logging
import re
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc 
import matplotlib.font_manager as fm  # 폰트 관리




font_path = 'C:\\Users\\euphoria\\AppData\\Local\\Microsoft\\Windows\\Fonts\\Malgun Gothic.ttf'  # 사용자의 시스템에 맞는 경로로 변경
if os.path.exists(font_path):
    font_name = font_manager.FontProperties(fname=font_path).get_name()

    rc('font', family=font_name)
    print(f"Font {font_name} has been set successfully.")


class DBVisualizer:
    def __init__(self, db_name, num_records=400):
        self.db_name = db_name
        self.db_path = f'{db_name}.db'
        self.num_records = num_records
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fetch_table_names(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [name[0] for name in cursor.fetchall() if re.match(r'(1분|3분|30분)_\d{6}$', name[0])]
            conn.close()
            self.logger.info(f"Found tables: {tables}")
            return tables
        except sqlite3.Error as e:
            self.logger.error(f"Failed to fetch table names: {e}")
            return []

    def get_output_path(self, table_name):
        match = re.match(r'(1분|3분|30분)_(\d{6})$', table_name)
        if match:
            interval = match.group(1)
            stock_name = match.group(2)
            return os.path.join(self.db_name, interval, stock_name)
        else:
            self.logger.error(f"Table name {table_name} does not match the expected pattern")
            return None

    def visualize_all(self):
        tables = self.fetch_table_names()
        for selected_table in tables:
            try:
                conn = sqlite3.connect(self.db_path)
                query = f'SELECT * FROM "{selected_table}" ORDER BY date DESC LIMIT {self.num_records}'
                df = pd.read_sql_query(query, conn, parse_dates=['date'], index_col='date')
                conn.close()
                
                df = df.sort_index()  # Sorting back to ascending order for plotting

                prev_day = df.index.max() - pd.Timedelta(days=1)
                prev_day_df = df.loc[df.index.date == prev_day.date(), 'close']
                prev_day_close = prev_day_df.iloc[-1] if not prev_day_df.empty else "N/A"

                title = f'{self.db_name} : {selected_table} (Last {self.num_records} records)'
                if prev_day_close != "N/A":
                    title += f"\nPrevious close: {prev_day_close}"
                    print("title:", title)

                save_path = self.get_output_path(selected_table)
                if save_path:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    savefig_options = {'fname': f'{save_path}.jpg', 'dpi': 800}

                    fig, ax = mpf.plot(df, type='candle', style='charles', title=title, volume=True, returnfig=True)
                    fig.set_size_inches(10, 6)
                    fig.savefig(**savefig_options)
                    plt.close(fig)
                    self.logger.info(f"Saved chart for {selected_table} at {save_path}.jpg")
            except KeyError as e:
                self.logger.error(f"Error with table {selected_table}: {e}")
            except sqlite3.Error as e:
                self.logger.error(f"Database error with table {selected_table}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error with table {selected_table}: {e}")

# Example usage
if __name__ == "__main__":
    db_name = '20240716_시가갭검색식_돌파'
    visualizer = DBVisualizer(db_name)
    visualizer.visualize_all()
