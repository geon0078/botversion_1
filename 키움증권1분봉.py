from pykiwoom.kiwoom import *
import time
import pandas as pd

# 로그인
kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

df = kiwoom.block_request("opt10080",
                          종목코드="005930",
                          기준일자="20200424",
                          수정주가구분=1,
                          output="주식일봉차트조회",
                          next=0)