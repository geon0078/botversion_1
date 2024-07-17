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

                # 구독 시작 (로그인 후에 설정)
                self.SetRealReg("1000", ";".join(self.tracked_stocks), "20;10", 0)

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
  