from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, QTime, QThread, pyqtSignal
import socket

class MessageReceiver(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        while self.running:
            message = self.sock.recv(1024).decode('utf-8')
            if message:
                self.message_received.emit(message)

    def stop(self):
        self.running = False
        self.sock.close()

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("Server Message Receiver")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.current_time_label = QLabel()
        self.status_bar.addPermanentWidget(self.current_time_label)

        self.message_display = QPlainTextEdit(self)
        self.message_display.setReadOnly(True)

        btn1 = QPushButton("Connect to Server")
        btn2 = QPushButton("Disconnect from Server")

        btn1.clicked.connect(self.connect_to_server)
        btn2.clicked.connect(self.disconnect_from_server)

        layout = QVBoxLayout()
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(self.message_display)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 1초마다 타이머 작동

        self.message_receiver = None

    def connect_to_server(self):
        if self.message_receiver is None:
            self.message_receiver = MessageReceiver('localhost', 12345)
            self.message_receiver.message_received.connect(self.display_message)
            self.message_receiver.start()
            self.status_bar.showMessage("Connected to server")

    def disconnect_from_server(self):
        if self.message_receiver is not None:
            self.message_receiver.stop()
            self.message_receiver = None
            self.status_bar.showMessage("Disconnected from server")

    def update_time(self):
        current_time = QTime.currentTime().toString("hh:mm:ss")
        self.current_time_label.setText(current_time)

    def display_message(self, message):
        self.message_display.appendPlainText(message)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    sys.exit(app.exec_())
