import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, api_handler):
        self.api_handler = api_handler
        self.conn = None
        self.cursor = None

    def setup_database(self, condition_name):
        print("Setting up database...")
        current_date = datetime.now().strftime('%Y%m%d')
        db_filename = f"{current_date}_{condition_name}.db"
        self.conn = sqlite3.connect(db_filename)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracked_stocks (
                code TEXT PRIMARY KEY,
                first_seen TEXT,
                cond_name TEXT
            )
        ''')
        self.conn.commit()
        print(f"Database setup complete with filename: {db_filename}")

    def save_tracked_stocks_to_db(self):
        print("Saving tracked stocks to database...")
        for code, info in self.api_handler.tracked_stocks.items():
            self.cursor.execute('''
                INSERT OR REPLACE INTO tracked_stocks (code, first_seen, cond_name)
                VALUES (?, ?, ?)
            ''', (code, info['first_seen'], info['cond_name']))
        self.conn.commit()
        self.conn.close()
        print("Tracked stocks saved to database.")
