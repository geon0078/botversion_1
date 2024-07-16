from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop
import sys
import subprocess

class KiwoomAPI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._event_connect)
        self.ocx.OnReceiveRealData.connect(self._receive_real_data)
        self.login_event_loop = QEventLoop()
        self.run_main_script()

    def comm_connect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공")
        else:
            print("로그인 실패")
        self.login_event_loop.exit()

    def subscribe_market_start(self):
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", "1000", "", "215", "0")

    def _receive_real_data(self, jongmok_code, real_type, real_data):
        if real_type == "장시작시간":
            market_start_time = self.ocx.dynamicCall("GetCommRealData(QString, int)", jongmok_code, 215).strip()
            if market_start_time == "0":
                print("장 시작 전")
            elif market_start_time == "2":
                print("장 종료, 시간 외 매매 시작")
            elif market_start_time == "3":
                print("시간 외 매매 종료")
            elif market_start_time == "1":
                print("장이 시작되었습니다!")
                self.run_main_script()

    def run_main_script(self):
        try:
            subprocess.Popen(["python", "조건gui/main.py"])
            print("조건gui파일/main.py 스크립트가 실행되었습니다.")
        except Exception as e:
            print(f"스크립트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    api = KiwoomAPI()
    api.comm_connect()
    api.subscribe_market_start()
    api.app.exec_()
