from PyQt5.QAxContainer import QAxWidget

class KiwoomAPI:
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)
        self.connected = False

    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")

    def GetConnectState(self):
        return self.ocx.dynamicCall("GetConnectState()")

    def GetConditionLoad(self):
        self.ocx.dynamicCall("GetConditionLoad()")

    def _handler_login(self, err_code):
        if err_code == 0:
            self.connected = True
        else:
            self.connected = False

    def _handler_real_condition(self, code, type, cond_name, cond_index):
        pass  # 실시간 조건식 처리 로직을 추가해야 함

    def SendCondition(self, screen, cond_name, cond_index, search):
        return self.ocx.dynamicCall("SendCondition(QString, QString, int, int)", screen, cond_name, cond_index, search)

    def SendConditionStop(self, screen, cond_name, cond_index):
        return self.ocx.dynamicCall("SendConditionStop(QString, QString, int)", screen, cond_name, cond_index)
