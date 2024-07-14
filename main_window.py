import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, QTime, pyqtSignal, QObject
from kiwoom_api import KiwoomAPI
from data_processor import DataProcessor
from chart_window import ChartWindow

class Communicate(QObject):
    capture_signal = pyqtSignal(str, str)  # 시간과 종목코드를 전달하기 위한 시그널

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 서버 연결 중")

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
        self.kiwoom_api = KiwoomAPI()
        self.data_processor = DataProcessor(self.kiwoom_api)
        self.communicate = Communicate()
        self.data_processor.capture_signal.connect(self.update_capture_label)

        # 데이터 프로세서 스레드 실행
        self.data_processor.start()

    def on_btn_load_clicked(self):
        self.kiwoom_api.GetConditionLoad()
        self.label_status.setText("데이터 로딩 중...")

    def update_time(self):
        current_time = QTime.currentTime()
        display_text = current_time.toString('hh:mm:ss')
        self.label_time.setText(f"현재시간: {display_text}")

    def update_capture_label(self, status, message):
        self.label_capture.setText("")
        self.label_capture.setText("========= 현재 조건을 만족하는 주식 코드 =========")
        for line in message.split("\n"):
            self.label_capture.setText(f"{self.label_capture.text()}\n{line}")

    def check_server_status(self):
        state = self.kiwoom_api.GetConnectState()
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
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
