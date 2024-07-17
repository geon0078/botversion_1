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

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveRealData.connect(self._handler_real_data)
        self.CommmConnect()

        # Fetch stock codes from database
        self.stock_codes = self.fetch_stock_codes_from_db("20240717_시가갭검색식_돌파.db")

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

        # 타이머 설정 (1초마다 갱신)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_charts)
        self.timer.start(1000)

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
            time = self.GetCommRealData(code, 20).strip()
            date = datetime.datetime.now().strftime("%Y-%m-%d ")
            try:
                time = datetime.datetime.strptime(date + time, "%Y-%m-%d %H%M%S")

                # 현재가
                price = self.GetCommRealData(code, 10).strip()
                price = price.replace('+', '').replace('-', '').replace(',', '')

                # 가격이 숫자인지 확인하고 변환
                if price.isdigit():
                    price = int(price)
                else:
                    print(f"Invalid price data for {code}: {price}")
                    return  # 유효하지 않은 데이터는 무시

                # 데이터 추가
                self.data[code].append((time, price))
                if len(self.data[code]) > 100:  # 데이터 포인트가 100개를 넘으면 오래된 것부터 제거
                    self.data[code].pop(0)

                print(f"Data updated for {code}: {time}, {price}")
            except Exception as e:
                print(f"Error parsing data for {code}: {e}")

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

    def closeEvent(self, event):
        self.DisConnectRealData("1000")
        event.accept()

    def fetch_stock_codes_from_db(self, db_file):
        stock_codes = []
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT code FROM tracked_stocks")
            stock_codes = [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching stock codes from database: {e}")
        finally:
            if conn:
                conn.close()
        return stock_codes

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()
