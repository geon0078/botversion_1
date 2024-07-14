import sys
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtChart import QChart, QChartView, QCandlestickSeries, QCandlestickSet
from PyQt5.QtChart import QDateTimeAxis, QValueAxis
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QApplication

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import QTimer, QTime, QDateTime
from datetime import datetime
import time

class DataProcessor(QThread):
    capture_signal = pyqtSignal(str, str)  # 시간과 종목코드를 전달하기 위한 시그널
    chart_signal = pyqtSignal(str)  # 차트 데이터베이스 파일 이름을 전달하기 위한 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)
        self.connected = False

    def run(self):
        self.CommConnect()

    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")

    def _handler_login(self, err_code):
        if err_code == 0:
            self.connected = True
            self.capture_signal.emit("connected", "서버에 연결됨")
        else:
            self.connected = False
            self.capture_signal.emit("disconnected", f"서버 연결 실패 (에러코드: {err_code})")

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        current_time = self.get_current_time()
        capture_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"갭상승_{capture_time}_{code}.db"
        self.chart_signal.emit(file_name)
        self.save_to_sqlite(file_name, code)

    def save_to_sqlite(self, file_name, code):
        conn = sqlite3.connect(file_name)
        c = conn.cursor()
        # 테이블 생성 예시 (종목코드, 시간, open, high, low, close, volume)
        c.execute('''CREATE TABLE IF NOT EXISTS ohlcv (
                     code TEXT,
                     time TEXT,
                     open REAL,
                     high REAL,
                     low REAL,
                     close REAL,
                     volume INTEGER)''')
        # 여기서 데이터를 가져와서 삽입하는 로직을 구현해야 함
        # 예를 들어 키움증권 API를 사용하여 1분봉 데이터를 가져와서 SQLite에 삽입하는 코드

        conn.commit()
        conn.close()

    def get_current_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class ChartWindow(QMainWindow):
    def __init__(self, file_name):
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle(f"Gap Chart - {file_name}")

        # 차트 초기화
        self.chart = QChart()
        self.chart.setTitle(f"Gap Chart - {file_name}")
        self.chart.legend().hide()

        self.chart_view = QChartView(self.chart)
        self.setCentralWidget(self.chart_view)

        # 차트 데이터 로드 및 설정
        self.load_data(file_name)

    def load_data(self, file_name):
        # SQLite에서 데이터 불러오는 예시 코드
        # 여기서는 데이터를 가져와서 QCandlestickSeries에 추가하는 로직을 구현해야 함
        series = QCandlestickSeries()
        # 데이터를 series에 추가하는 로직 필요
        self.chart.addSeries(series)

        # 축 설정
        axis_x = QDateTimeAxis()
        axis_x.setFormat("hh:mm")
        axis_x.setTitleText("Time")
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Price")
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        # 차트 뷰 설정
        self.chart_view.setChart(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 연결 중")

        # GUI 요소 설정
        self.label_time = QLabel(self)
        self.label_status = QLabel(self)
        self.label_capture = QLabel(self)

        btn1 = QPushButton("시가갭 검색식 로드", self)
        btn1.clicked.connect(self.on_btn_load_clicked)

        layout = QVBoxLayout()
        layout.addWidget(btn1)
        layout.addWidget(self.label_time)
        layout.addWidget(self.label_status)
        layout.addWidget(self.label_capture)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 타이머 설정 (현재 시간 업데이트용)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 1초마다 현재 시간 업데이트

        # 서버 연결 상태 체크용 타이머
        self.server_status_timer = QTimer(self)
        self.server_status_timer.timeout.connect(self.check_server_status)
        self.server_status_timer.start(10000)  # 10초마다 서버 연결 상태 체크

        # 데이터 프로세서 초기화 및 시그널 연결
        self.data_processor = DataProcessor()
        self.data_processor.capture_signal.connect(self.update_capture_label)
        self.data_processor.chart_signal.connect(self.show_chart_window)

        # 데이터 프로세서 스레드 실행
        self.data_processor.start()

        # QAxWidget 초기화
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)

    def on_btn_load_clicked(self):
        self.GetConditionLoad()
        self.label_status.setText("데이터 로딩 중...")

    def GetConditionLoad(self):
        self.ocx.dynamicCall("GetConditionLoad()")

    def _handler_login(self, err_code):
        if err_code == 0:
            self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 연결 완료")
            self.label_status.setText("서버에 연결됨")
        else:
            self.setWindowTitle(f"Kiwoom 실시간 조건식 테스트 - 연결 실패 (에러코드: {err_code})")
            self.label_status.setText(f"서버 연결 실패 (에러코드: {err_code})")

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        current_time = self.get_current_time()
        capture_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"갭상승_{capture_time}_{code}.db"
        self.save_to_sqlite(file_name, code)

    def save_to_sqlite(self, file_name, code):
        conn = sqlite3.connect(file_name)
        c = conn.cursor()
        # 테이블 생성 예시 (종목코드, 시간, open, high, low, close, volume)
        c.execute('''CREATE TABLE IF NOT EXISTS ohlcv (
                     code TEXT,
                     time TEXT,
                     open REAL,
                     high REAL,
                     low REAL,
                     close REAL,
                     volume INTEGER)''')
        # 여기서 데이터를 가져와서 삽입하는 로직을 구현해야 함
        # 예를 들어 키움증권 API를 사용하여 1분봉 데이터를 가져와서 SQLite에 삽입하는 코드

        conn.commit()
        conn.close()

    def get_current_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_time(self):
        current_time = QTime.currentTime()
        display_text = current_time.toString('hh:mm:ss')
        self.label_time.setText(f"현재시간: {display_text}")

    def update_capture_label(self, status, message):
        self.label_capture.setText(f"{status} - {message}")

    def check_server_status(self):
        state = self.ocx.dynamicCall("GetConnectState()")
        if state == 1:
            self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 서버 연결 중")
            self.label_status.setText("서버에 연결 중입니다.")
        else:
            self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 서버 연결 끊김")
            self.label_status.setText("서버 연결이 끊어졌습니다.")

    def show_chart_window(self, file_name):
        chart_window = ChartWindow(file_name)
        chart_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
