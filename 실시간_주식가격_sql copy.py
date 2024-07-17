import sys
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import QTimer, QDateTime, QFile
import datetime

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

        # 종목 코드 리스트
        self.stock_codes = [
            "005930",
            "000660",
            "035420",
            "452280",
            "092870",
            "002800",
            "373110",
            "003220",
            "014620",
            "024840",
            "053080",
            "290550",
            "214260",
            "175250",
            "291230",
            "220100",
            "018290"
        ]  # 삼성전자, SK하이닉스, NAVER 등

        # SQLite 연결 및 커서 생성
        self.conn = sqlite3.connect('실시간db.db')
        self.cur = self.conn.cursor()

        # 데이터 저장을 위한 변수 초기화
        self.data = {code: {} for code in self.stock_codes}  # 각 종목별로 딕셔너리로 데이터 관리

        # 타이머 설정 (3분마다 갱신)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.save_aggregated_data)
        self.timer.start(180000)  # 3 minutes in milliseconds

    def create_table_if_not_exists(self, table_name):
        try:
            self.cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT,
                    price INTEGER
                )
            ''')
            self.conn.commit()
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")

    def CommmConnect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.statusBar().showMessage("login 중 ...")

    def _handler_login(self, err_code):
        if err_code == 0:
            self.statusBar().showMessage("login 완료")
            # 구독 시작 (로그인 후에 설정)
            for code in self.stock_codes:
                self.SetRealReg("1000", code, "20;10", 0)
        else:
            self.statusBar().showMessage(f"login 실패: {err_code}")

    def _handler_real_data(self, code, real_type, data):
        print(f"Received real data: {code}, {real_type}, {data}")
        time_str = self.GetCommRealData(code, 20).strip()  # fid 20은 시간을 나타냄
        date = QDateTime.currentDateTime().toString("yyyy-MM-dd ")
        try:
            time = datetime.datetime.strptime(date + time_str, "%Y-%m-%d %H%M%S")
            price_str = self.GetCommRealData(code, 10).strip()  # fid 10은 가격을 나타냄
            price = int(price_str.replace('+', '').replace('-', '').replace(',', ''))

            if code not in self.data:
                self.data[code] = {}

            # 데이터 딕셔너리에 저장
            if real_type in self.data[code]:
                self.data[code][real_type].append((time, price))
            else:
                self.data[code][real_type] = [(time, price)]

            # 테이블 생성 및 데이터 저장
            table_name = f"stock_{code}_{real_type}"
            self.create_table_if_not_exists(table_name)
            self.cur.execute(f'''
                INSERT INTO {table_name} (time, price)
                VALUES (?, ?)
            ''', (time.strftime("%Y-%m-%d %H:%M:%S"), price))
            self.conn.commit()
            print(f"Saved data to {table_name} table: {time}, {price}")

        except Exception as e:
            print(f"Error handling real data for {code}: {e}")

    def save_aggregated_data(self):
        try:
            for code, data_dict in self.data.items():
                for real_type, data_list in data_dict.items():
                    if data_list:
                        for data_entry in data_list:
                            time, price = data_entry
                            table_name = f"stock_{code}_{real_type}"
                            self.create_table_if_not_exists(table_name)
                            self.cur.execute(f'''
                                INSERT INTO {table_name} (time, price)
                                VALUES (?, ?)
                            ''', (time.strftime("%Y-%m-%d %H:%M:%S"), price))
                            self.conn.commit()
                            print(f"Saved data to {table_name} table: {time}, {price}")

            # 데이터 저장 후 self.data 초기화
            self.data = {code: {} for code in self.stock_codes}

        except Exception as e:
            print(f"Error saving aggregated data: {e}")

    def SetRealReg(self, screen_no, code, fid_list, real_type):
        print(f"Setting real reg: {screen_no}, {code}, {fid_list}, {real_type}")
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                              screen_no, code, fid_list, real_type)

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid) 
        print(f"GetCommRealData: {code}, {fid} -> {data}")
        return data

    def closeEvent(self, event):
        self.save_aggregated_data()  # Save any remaining data before closing
        for code in self.stock_codes:
            self.ocx.dynamicCall("SetRealRemove(QString, QString)", "1000", code)  # Remove real-time data subscription
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()
