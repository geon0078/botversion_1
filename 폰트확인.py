import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import os

def set_korean_font():
    try:
        font_path = 'C:\\Users\\euphoria\\AppData\\Local\\Microsoft\\Windows\\Fonts\\NanumGothic.ttf'  # 사용자의 시스템에 맞는 경로로 변경
        if os.path.exists(font_path):
            font_name = font_manager.FontProperties(fname=font_path).get_name()
            rc('font', family=font_name)
            print(f"Font {font_name} has been set successfully.")
        else:
            print(f"Font path {font_path} does not exist.")
    except Exception as e:
        print(f"Failed to set Korean font: {e}")

# 폰트를 설정합니다.
set_korean_font()

# 간단한 그래프를 그려 폰트 설정이 잘 되었는지 확인합니다.
plt.figure(figsize=(6, 4))
plt.plot([0, 1, 2, 3], [0, 1, 4, 9])
plt.title('테스트 그래프')
plt.xlabel('시간')
plt.ylabel('값')
plt.show()
