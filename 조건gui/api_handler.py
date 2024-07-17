from PyQt5.QAxContainer import QAxWidget
from datetime import datetime
from PyQt5.QtWidgets import QTableWidgetItem


class APIHandler():
    def __init__(self, parent):
        self.parent = parent
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveConditionVer.connect(self._handler_condition_load)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)
        self.ocx.OnReceiveRealData.connect(self._receive_real_data)

        self.tracked_stocks = {}
        self.current_condition_name = ""

    def CommConnect(self):
        print("Attempting to connect...")
        self.parent.status_bar.showMessage("Connecting...")
        self.ocx.dynamicCall("CommConnect()")

    def _handler_login(self, err_code):
        print(f"Login handler called with error code: {err_code}")
        if err_code == 0:
            self.parent.status_bar.showMessage("Login successful")
        else:
            self.parent.status_bar.showMessage(f"Login failed: {err_code}")

    def _handler_condition_load(self, ret, msg):
        print(f"Condition load handler called with ret: {ret}, msg: {msg}")
        self.parent.status_bar.showMessage(f"Condition Load - ret: {ret}, msg: {msg}")

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        print(f"Real condition handler called with code: {code}, type: {type}, cond_name: {cond_name}, cond_index: {cond_index}")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if type == 'I':
            if code not in self.tracked_stocks:
                self.tracked_stocks[code] = {'first_seen': current_time, 'cond_name': cond_name}
                print(f"Inserted: {current_time} - {cond_name} {code} {type}")
                self.update_table_widget()
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
        self.current_condition_name = cond_name  # Save the current condition name for database filename
        ret = self.ocx.dynamicCall("SendCondition(QString, QString, int, int)", screen, cond_name, cond_index, search)
        if ret == 1:
            self.parent.status_bar.showMessage(f"Condition {cond_name} sent successfully")
            self.parent.db.setup_database(self.current_condition_name)
        else:
            self.parent.status_bar.showMessage(f"Failed to send condition {cond_name}")

    def SendConditionStop(self, screen, cond_name, cond_index):
        print(f"Stopping condition: screen={screen}, cond_name={cond_name}, cond_index={cond_index}")
        ret = self.ocx.dynamicCall("SendConditionStop(QString, QString, int)", screen, cond_name, cond_index)

    def update_table_widget(self):
        self.parent.table_widget.setRowCount(len(self.tracked_stocks))
        for row, (code, info) in enumerate(self.tracked_stocks.items()):
            self.parent.table_widget.setItem(row, 0, QTableWidgetItem(code))
            self.parent.table_widget.setItem(row, 1, QTableWidgetItem(info['first_seen']))
            self.parent.table_widget.setItem(row, 2, QTableWidgetItem(info['cond_name']))

    def print_tracked_stocks(self):
        print("\nCurrent tracked stocks:")
        if not self.tracked_stocks:
            print("No tracked stocks.")
        else:
            for code, info in self.tracked_stocks.items():
                print(f"  Code: {code}, First Seen: {info['first_seen']}, Condition Name: {info['cond_name']}")
        print("-" * 40)

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