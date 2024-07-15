import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from datetime import datetime

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 300, 400)
        self.setWindowTitle("Kiwoom 실시간 조건식 테스트")

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveConditionVer.connect(self._handler_condition_load)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        btn1 = QPushButton("Load Conditions")
        btn2 = QPushButton("List Conditions")
        btn3 = QPushButton("Send Condition")

        self.cond_name_input = QLineEdit(self)
        self.cond_index_input = QLineEdit(self)

        form_layout = QFormLayout()
        form_layout.addRow("Condition Name:", self.cond_name_input)
        form_layout.addRow("Condition Index:", self.cond_index_input)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addLayout(form_layout)
        layout.addWidget(btn3)
        self.setCentralWidget(widget)

        # event
        btn1.clicked.connect(self.GetConditionLoad)
        btn2.clicked.connect(self.GetConditionNameList)
        btn3.clicked.connect(self.send_condition)

        self.tracked_stocks = {}

        self.CommConnect()  # Move this call to the end of __init__

    def closeEvent(self, event):
        # This method is called when the window is closed.
        print("\nTracked stocks at program close:")
        if not self.tracked_stocks:
            print("No tracked stocks.")
        else:
            for code, info in self.tracked_stocks.items():
                print(f"Code: {code}, First Seen: {info['first_seen']}, Condition Name: {info['cond_name']}")
        event.accept()  # Ensure the application exits properly

    def CommConnect(self):
        print("Attempting to connect...")
        self.status_bar.showMessage("Connecting...")
        self.ocx.dynamicCall("CommConnect()")

    def _handler_login(self, err_code):
        print(f"Login handler called with error code: {err_code}")
        if err_code == 0:
            self.status_bar.showMessage("Login successful")
        else:
            self.status_bar.showMessage(f"Login failed: {err_code}")

    def _handler_condition_load(self, ret, msg):
        print(f"Condition load handler called with ret: {ret}, msg: {msg}")
        self.status_bar.showMessage(f"Condition Load - ret: {ret}, msg: {msg}")

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        print(f"Real condition handler called with code: {code}, type: {type}, cond_name: {cond_name}, cond_index: {cond_index}")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if type == 'I':
            if code not in self.tracked_stocks:
                self.tracked_stocks[code] = {'first_seen': current_time, 'cond_name': cond_name}
                print(f"Inserted: {current_time} - {cond_name} {code} {type}")
        elif type == 'D':
            if code in self.tracked_stocks:
                del self.tracked_stocks[code]
                print(f"Deleted: {current_time} - {cond_name} {code} {type}")
        self.print_tracked_stocks()

    def GetConditionLoad(self):
        print("Loading conditions...")
        self.ocx.dynamicCall("GetConditionLoad()")

    def GetConditionNameList(self):
        print("Getting condition name list...")
        data = self.ocx.dynamicCall("GetConditionNameList()")
        conditions = data.split(";")[:-1]
        for condition in conditions:
            index, name = condition.split('^')
            print(index, name)

    def SendCondition(self, screen, cond_name, cond_index, search):
        print(f"Sending condition: screen={screen}, cond_name={cond_name}, cond_index={cond_index}, search={search}")
        ret = self.ocx.dynamicCall("SendCondition(QString, QString, int, int)", screen, cond_name, cond_index, search)
        if ret == 1:
            self.status_bar.showMessage(f"Condition {cond_name} sent successfully")
        else:
            self.status_bar.showMessage(f"Failed to send condition {cond_name}")

    def SendConditionStop(self, screen, cond_name, cond_index):
        print(f"Stopping condition: screen={screen}, cond_name={cond_name}, cond_index={cond_index}")
        ret = self.ocx.dynamicCall("SendConditionStop(QString, QString, int)", screen, cond_name, cond_index)

    def send_condition(self):
        cond_name = self.cond_name_input.text()
        cond_index = self.cond_index_input.text()
        print(f"Preparing to send condition: cond_name={cond_name}, cond_index={cond_index}")
        if cond_name and cond_index:
            self.SendCondition("100", cond_name, int(cond_index), 1)
        else:
            self.status_bar.showMessage("Please enter both condition name and index")

    def print_tracked_stocks(self):
        print("\nCurrent tracked stocks:")
        if not self.tracked_stocks:
            print("No tracked stocks.")
        else:
            for code, info in self.tracked_stocks.items():
                print(f"  Code: {code}, First Seen: {info['first_seen']}, Condition Name: {info['cond_name']}")
        print("-" * 40)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()
