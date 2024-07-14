import sqlite3
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime

class DataProcessor(QThread):
    capture_signal = pyqtSignal(str, str)  # 시간과 종목코드를 전달하기 위한 시그널
    chart_signal = pyqtSignal(str)  # 차트 데이터베이스 파일 이름을 전달하기 위한 시그널

    def __init__(self, kiwoom_api, parent=None):
        super().__init__(parent)
        self.kiwoom_api = kiwoom_api

    def run(self):
        self.kiwoom_api.CommConnect()

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        current_time = self.get_current_time()
        capture_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"갭상승_{capture_time}_{code}.db"
        self.chart_signal.emit(file_name)
        self.save_to_sqlite(file_name, code)

    def save_to_sqlite(self, file_name, code):
        conn = sqlite3.connect(file_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS ohlcv (
                    code TEXT,
                    time TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER)''')

        # 키움증권 API를 이용하여 실시간 데이터를 받아와 SQLite에 삽입하는 예시 코드
        data = self.kiwoom_api.GetRealData(code)  # GetRealData 함수는 키움 API에서 실시간 데이터를 받아오는 것으로 가정
        if data:
            time = data['time']  # 시간 정보가 있는 키움 API 데이터에서 시간을 추출
            open_price = data['open']
            high_price = data['high']
            low_price = data['low']
            close_price = data['close']
            volume = data['volume']

            c.execute("INSERT INTO ohlcv VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (code, time, open_price, high_price, low_price, close_price, volume))

        conn.commit()
        conn.close()


    def get_current_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
