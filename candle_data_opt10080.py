import sqlite3
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QLabel, QListWidget
from PyQt5.QtCore import Qt
from datetime import datetime

class CandleDataRetrieverOpt10080(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("1분봉 데이터 조회 (opt10080)")

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_receive_tr_data)

        self.stock_codes = []

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels(["Stock Code", "Date", "Time", "Open", "High", "Low", "Close", "Volume"])

        self.file_label = QLabel("No file selected")
        self.status_label = QLabel("Status: Not connected")

        btn_select_file = QPushButton("Select SQLite File")
        btn_get_data = QPushButton("Get 1-minute Candlestick Data")
        btn_save_data = QPushButton("Save Data to SQLite")

        btn_select_file.clicked.connect(self.select_file)
        btn_get_data.clicked.connect(self.get_candlestick_data)
        btn_save_data.clicked.connect(self.save_data_to_sqlite)

        self.stock_list_widget = QListWidget()
        self.stock_list_widget.setSelectionMode(QListWidget.MultiSelection)

        layout = QVBoxLayout()
        layout.addWidget(btn_select_file)
        layout.addWidget(self.file_label)
        layout.addWidget(QLabel("Select Stock Codes:"))
        layout.addWidget(self.stock_list_widget)
        layout.addWidget(btn_get_data)
        layout.addWidget(btn_save_data)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table_widget)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.conn = None
        self.cursor = None

        self.CommConnect()

    def CommConnect(self):
        self.status_label.setText("Status: Connecting...")
        self.ocx.dynamicCall("CommConnect()")

    def _handler_login(self, err_code):
        if err_code == 0:
            self.status_label.setText("Status: Login successful")
        else:
            self.status_label.setText(f"Status: Login failed: {err_code}")

    def select_file(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Select SQLite File", "", "SQLite Files (*.db);;All Files (*)", options=options)
        if file:
            self.file_label.setText(f"Selected File: {file}")
            self.conn = sqlite3.connect(file)
            self.cursor = self.conn.cursor()
            self.load_stock_codes()

    def load_stock_codes(self):
        if self.conn:
            self.cursor.execute("SELECT code FROM tracked_stocks")
            rows = self.cursor.fetchall()
            self.stock_codes = [row[0] for row in rows]
            self.stock_list_widget.clear()
            for code in self.stock_codes:
                self.stock_list_widget.addItem(code)
            print("Loaded stock codes:", self.stock_codes)

    def get_candlestick_data(self):
        selected_items = self.stock_list_widget.selectedItems()
        if not selected_items:
            self.status_label.setText("Status: No stock codes selected")
            return

        self.table_widget.setRowCount(0)
        self.selected_stock_codes = [item.text() for item in selected_items]
        self.current_stock_index = 0
        self.request_candlestick_data(self.selected_stock_codes[self.current_stock_index])

    def request_candlestick_data(self, stock_code):
        print(f"Requesting candlestick data for {stock_code}")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10080_req", "opt10080", 0, "0101")

    def _handler_receive_tr_data(self, screen_no, rqname, trcode, recordname, prevnext, data_len, err_code, msg1, msg2):
        if rqname == "opt10080_req":
            count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            stock_code = self.selected_stock_codes[self.current_stock_index]
            for i in range(count):
                date = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip()
                time = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결시간").strip()
                open_price = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip()))
                high_price = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip()))
                low_price = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip()))
                close_price = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()))
                volume = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip()))
                datetime_str = f"{date} {time}"
                datetime_obj = datetime.strptime(datetime_str, "%Y%m%d %H%M%S")
                formatted_datetime = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
                self.add_table_row(stock_code, date, formatted_datetime, open_price, high_price, low_price, close_price, volume)

            if prevnext == '2':
                self.request_candlestick_data(stock_code)
            else:
                self.current_stock_index += 1
                if self.current_stock_index < len(self.selected_stock_codes):
                    self.request_candlestick_data(self.selected_stock_codes[self.current_stock_index])
                else:
                    self.status_label.setText("Status: Completed retrieving data")

    def add_table_row(self, stock_code, date, time, open_price, high_price, low_price, close_price, volume):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        self.table_widget.setItem(row_position, 0, QTableWidgetItem(stock_code))
        self.table_widget.setItem(row_position, 1, QTableWidgetItem(date))
        self.table_widget.setItem(row_position, 2, QTableWidgetItem(time))
        self.table_widget.setItem(row_position, 3, QTableWidgetItem(str(open_price)))
        self.table_widget.setItem(row_position, 4, QTableWidgetItem(str(high_price)))
        self.table_widget.setItem(row_position, 5, QTableWidgetItem(str(low_price)))
        self.table_widget.setItem(row_position, 6, QTableWidgetItem(str(close_price)))
        self.table_widget.setItem(row_position, 7, QTableWidgetItem(str(volume)))

    def save_data_to_sqlite(self):
        if self.conn is None:
            self.status_label.setText("Status: No SQLite file selected")
            return
        
        cursor = self.conn.cursor()
        for stock_code in self.selected_stock_codes:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS "{stock_code}" (
                    time TEXT,
                    open INTEGER,
                    high INTEGER,
                    low INTEGER,
                    close INTEGER,
                    volume INTEGER
                )
            ''')

        for row in range(self.table_widget.rowCount()):
            stock_code = self.table_widget.item(row, 0).text()
            time = self.table_widget.item(row, 2).text()
            open_price = int(self.table_widget.item(row, 3).text())
            high_price = int(self.table_widget.item(row, 4).text())
            low_price = int(self.table_widget.item(row, 5).text())
            close_price = int(self.table_widget.item(row, 6).text())
            volume = int(self.table_widget.item(row, 7).text())
            cursor.execute(f'''
                INSERT INTO "{stock_code}" (time, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (time, open_price, high_price, low_price, close_price, volume))

        self.conn.commit()
        self.status_label.setText(f"Status: Data saved to selected SQLite file")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = CandleDataRetrieverOpt10080()
    window.show()
    app.exec_()
