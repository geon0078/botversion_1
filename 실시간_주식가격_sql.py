import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import QTimer
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sqlite3

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real")
        self.setGeometry(300, 300, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Initialize SQLite connection and cursor
        self.conn = sqlite3.connect('실시간db.db')
        self.cur = self.conn.cursor()

        # 종목 코드 리스트
        self.stock_codes = [
            "005930", "000660", "035420", "452280", "092870", 
            "002800", "373110", "003220", "014620", "024840", 
            "053080", "290550", "214260", "175250", "291230", 
            "220100", "018290"
        ]  # 삼성전자, SK하이닉스, NAVER 예시

        # Matplotlib Figure와 Canvas 설정
        self.figures = {}
        self.axes = {}
        self.canvases = {}
        self.data = {code: [] for code in self.stock_codes}

        for code in self.stock_codes:
            fig, ax = plt.subplots()
            canvas = FigureCanvas(fig)
            self.layout.addWidget(canvas)

            self.figures[code] = fig
            self.axes[code] = ax
            self.canvases[code] = canvas

            ax.set_title(f"Stock Code: {code}")
            ax.set_xlabel("Time")
            ax.set_ylabel("Price")

        # 타이머 설정 (3분마다 갱신)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_charts)
        self.timer.start(180000)  # 3 minutes in milliseconds

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveRealData.connect(self._handler_real_data)
        self.CommmConnect()

        # Create tables for each stock code in SQLite
        self.create_tables()

    def CommmConnect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.statusBar().showMessage("login 중 ...")

    def _handler_login(self, err_code):
        if err_code == 0:
            self.statusBar().showMessage("login 완료")
            # 구독 시작 (로그인 후에 설정)
            self.SetRealReg("1000", ";".join(self.stock_codes), "20;10", 0)
        else:
            self.statusBar().showMessage(f"login 실패: {err_code}")

    def _handler_real_data(self, code, real_type, data):
        print(f"Received real data: {code}, {real_type}, {data}")
        if real_type == "주식체결":
            # 체결 시간
            time_str = self.GetCommRealData(code, 20).strip()
            date = datetime.datetime.now().strftime("%Y-%m-%d ")
            try:
                time = datetime.datetime.strptime(date + time_str, "%Y-%m-%d %H%M%S")

                # 현재가
                price_str = self.GetCommRealData(code, 10).strip()
                price = int(price_str.replace('+', '').replace('-', '').replace(',', ''))

                # 가격이 숫자인지 확인하고 변환
                if isinstance(price, int):
                    price = int(price)
                else:
                    print(f"Invalid price data for {code}: {price}")
                    return  # 유효하지 않은 데이터는 무시

                # 데이터 추가
                self.data[code].append((time, price))

                # Check if 3 minutes have passed
                if len(self.data[code]) >= 3:
                    self.save_data_to_db(code, self.data[code])

            except Exception as e:
                print(f"Error parsing data for {code}: {e}")


    def save_data_to_db(self, code, data):
        try:
            table_name = f"stock_{code}"
            
            # Compute OHLC values
            if data:
                times, prices = zip(*data)
                open_price = prices[0]
                high_price = max(prices)
                low_price = min(prices)
                close_price = prices[-1]

                # Save OHLC data to database
                self.cur.execute(f'''
                    INSERT OR REPLACE INTO {table_name} (time, open, high, low, close)
                    VALUES (?, ?, ?, ?, ?)
                ''', (times[0].strftime("%Y-%m-%d %H:%M:%S"), open_price, high_price, low_price, close_price))
                self.conn.commit()
                print(f"Saved OHLC data to {table_name} table: {times[0]}, {open_price}, {high_price}, {low_price}, {close_price}")

                # Clear data list after saving OHLC
                data.clear()

        except Exception as e:
            print(f"Error saving data to {table_name} table: {e}")


    def update_charts(self):
        for code in self.stock_codes:
            ax = self.axes[code]
            ax.clear()
            ax.set_title(f"Stock Code: {code}")
            ax.set_xlabel("Time")
            ax.set_ylabel("Price")

            if self.data[code]:
                times, prices = zip(*self.data[code])
                ax.plot(times, prices, 'b-')

            self.canvases[code].draw()

    def SetRealReg(self, screen_no, code_list, fid_list, real_type):
        print(f"Setting real reg: {screen_no}, {code_list}, {fid_list}, {real_type}")
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                              screen_no, code_list, fid_list, real_type)

    def DisConnectRealData(self, screen_no):
        print(f"Disconnecting real data: {screen_no}")
        self.ocx.dynamicCall("DisConnectRealData(QString)", screen_no)

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid) 
        print(f"GetCommRealData: {code}, {fid} -> {data}")
        return data

    def create_tables(self):
        # Create tables for each stock code in SQLite database
        for code in self.stock_codes:
            table_name = f"stock_{code}"
            self.cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    time TEXT PRIMARY KEY,
                    open INTEGER,
                    high INTEGER,
                    low INTEGER,
                    close INTEGER
                )
            ''')
        self.conn.commit()

    def closeEvent(self, event):
        self.DisConnectRealData("1000")
        self.conn.close()  # Close SQLite connection
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()
