import sys
import requests
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import QTimer, QTime
from datetime import datetime

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 연결 중")

        # 키움증권 OpenAPI 초기화
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)
        self.CommConnect()

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

    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")

    def _handler_login(self, err_code):
        if err_code == 0:
            self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 연결 완료")
            self.label_status.setText("서버에 연결됨")
        else:
            self.setWindowTitle(f"Kiwoom 실시간 조건식 테스트 - 연결 실패 (에러코드: {err_code})")
            self.label_status.setText(f"서버 연결 실패 (에러코드: {err_code})")

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        current_time = self.get_current_time()
        capture_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        capture_info = f"{capture_time} // {code} // {cond_name}"
        self.update_capture_label(capture_info)

    def on_btn_load_clicked(self):
        self.GetConditionLoad()
        self.label_status.setText("데이터 로딩 중...")

    def GetConditionLoad(self):
        self.ocx.dynamicCall("GetConditionLoad()")

    def get_current_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_time(self):
        current_time = QTime.currentTime()
        display_text = current_time.toString('hh:mm:ss')
        self.label_time.setText(f"현재시간: {display_text}")

    def update_capture_label(self, text):
        self.label_capture.setText(text)

    def check_server_status(self):
        if not self.ocx.dynamicCall("GetConnectState()"):
            self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 서버 연결 끊김")
            self.label_status.setText("서버 연결이 끊어졌습니다.")
            # 여기서 추가적인 처리를 하거나 사용자에게 알림을 보낼 수 있음
            # 예를 들어 자동으로 재접속 시도 등을 구현할 수 있음
        else:
            self.setWindowTitle("Kiwoom 실시간 조건식 테스트 - 서버에 연결됨")
            self.label_status.setText("서버에 연결됨")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
