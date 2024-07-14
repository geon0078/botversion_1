import sys
import requests
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from datetime import datetime

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle("Kiwoom 실시간 조건식 테스트")

        # 키움증권 OpenAPI 초기화
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)
        self.CommConnect()

        # GUI 요소 설정
        btn1 = QPushButton("시가갭 검색식 로드")
        btn1.clicked.connect(self.GetConditionLoad)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(btn1)
        self.setCentralWidget(widget)

    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")

    def _handler_login(self, err_code):
        print("로그인 결과:", err_code)

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        current_time = self.get_current_time()
        print(f"종목코드: {code}, 시간: {current_time}, 조건식명: {cond_name}")

    def GetConditionLoad(self):
        self.ocx.dynamicCall("GetConditionLoad()")

    def get_current_time(self):
        try:
            response = requests.get("http://time2.kriss.re.kr/timeSync.do")
            if response.status_code == 200:
                json_data = response.json()
                datetime_str = json_data['result']
                current_time = datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
                return current_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                print("시간 정보를 가져오는데 실패했습니다.")
                return ""
        except Exception as e:
            print(f"시간 정보를 가져오는 중 오류 발생: {str(e)}")
            return ""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
