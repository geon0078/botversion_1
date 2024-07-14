import sqlite3
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QWidget
from PyQt5.QtChart import QChart, QChartView, QCandlestickSeries, QCandlestickSet, QDateTimeAxis, QValueAxis
from PyQt5.Qt import Qt
from PyQt5.QtGui import QPainter
from datetime import datetime

class ChartWindow(QMainWindow):
    def __init__(self, file_name):
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle(f"Gap Chart - {file_name}")

        # 차트 초기화
        self.chart = QChart()
        self.chart.setTitle(f"Gap Chart - {file_name}")
        self.chart.legend().hide()

        self.chart_view = QChartView(self.chart)
        self.setCentralWidget(self.chart_view)

        # 차트 데이터 로드 및 설정
        self.load_data(file_name)

    def load_data(self, file_name):
        # SQLite에서 데이터 불러오는 예시 코드
        conn = sqlite3.connect(file_name)
        c = conn.cursor()
        c.execute("SELECT * FROM ohlcv")
        data = c.fetchall()
        conn.close()

        series = QCandlestickSeries()
        for row in data:
            time_str = row[1]  # 시간 정보가 있는 컬럼에 따라 수정 필요
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            candle = QCandlestickSet(dt.timestamp() * 1000, row[2], row[3], row[4], row[5])
            series.append(candle)

        # 축 설정
        axis_x = QDateTimeAxis()
        axis_x.setFormat("hh:mm")
        axis_x.setTitleText("Time")
        self.chart.addSeries(series)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Price")
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        # 차트 뷰 설정
        self.chart_view.setChart(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
