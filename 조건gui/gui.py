from PyQt5.QtWidgets import *
from api_handler import APIHandler
from database import DatabaseManager

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("Kiwoom 실시간 조건식 테스트")

        self.api_handler = APIHandler(self)
        self.db = DatabaseManager(self.api_handler)

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

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Code", "First Seen", "Condition Name"])

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addLayout(form_layout)
        layout.addWidget(btn3)
        layout.addWidget(self.table_widget)
        self.setCentralWidget(widget)

        # event
        btn1.clicked.connect(self.api_handler.GetConditionLoad)
        btn2.clicked.connect(self.api_handler.GetConditionNameList)
        btn3.clicked.connect(self.send_condition)

        self.api_handler.CommConnect()

    def closeEvent(self, event):
        self.db.save_tracked_stocks_to_db()
        print("\nTracked stocks at program close:")
        if not self.api_handler.tracked_stocks:
            print("No tracked stocks.")
        else:
            for code, info in self.api_handler.tracked_stocks.items():
                print(f"Code: {code}, First Seen: {info['first_seen']}, Condition Name: {info['cond_name']}")
        event.accept()

    def send_condition(self):
        cond_name = self.cond_name_input.text()
        cond_index = self.cond_index_input.text()
        print(f"Preparing to send condition: cond_name={cond_name}, cond_index={cond_index}")
        if cond_name and cond_index:
            self.api_handler.SendCondition("100", cond_name, int(cond_index), 1)
        else:
            self.status_bar.showMessage("Please enter both condition name and index")
