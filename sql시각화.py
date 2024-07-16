import sqlite3
import pandas as pd
import mplfinance as mpf
import os
import logging
import re
import matplotlib.pyplot as plt

class DBVisualizer:
    def __init__(self, db_name, num_records=400):
        self.db_name = db_name
        self.db_path = f'{db_name}.db'
        self.charts_folder = db_name
        self.num_records = num_records
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fetch_table_names(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [name[0] for name in cursor.fetchall() if re.match(r'.*\d{6}$', name[0])]
            conn.close()
            self.logger.info(f"Found tables: {tables}")
            return tables
        except sqlite3.Error as e:
            self.logger.error(f"Failed to fetch table names: {e}")
            return []

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

                save_path = f'./{self.charts_folder}/{selected_table}.jpg'
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                savefig_options = {'fname': save_path, 'dpi': 100}

                fig, ax = mpf.plot(df, type='candle', style='charles', title=title, volume=True, returnfig=True)
                fig.set_size_inches(10, 6)
                fig.savefig(**savefig_options)
                plt.close(fig)
                self.logger.info(f"Saved chart for {selected_table} at {save_path}")
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
