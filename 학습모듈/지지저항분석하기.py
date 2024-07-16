import sqlite3
import pandas as pd
import numpy as np
import hdbscan
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

# SQLite 데이터베이스 파일 연결
db_path = '20240716_시가갭검색식_돌파.db'
conn = sqlite3.connect(db_path)

# 테이블 목록 가져오기
query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '30분%';"
tables = pd.read_sql_query(query, conn)['name'].tolist()

if not tables:
    print("No tables found that start with '30분'")
else:
    print(f"Found tables: {tables}")

# 현재 테이블 인덱스 추적
current_table_index = 0

# 키보드 이벤트 처리 함수
def on_key(event):
    global current_table_index
    if event.key == 'right':
        current_table_index = (current_table_index + 1) % len(tables)
    elif event.key == 'left':
        current_table_index = (current_table_index - 1) % len(tables)
    update_plot()

# 차트 업데이트 함수
def update_plot():
    global current_table_index
    table = tables[current_table_index]
    print(f"Processing table: {table}")
    
    # 데이터 로드
    df = pd.read_sql_query(f'SELECT date, close FROM [{table}]', conn)
    if df.empty:
        print(f"No data found in table {table}")
        return

    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    if df['close'].isnull().all():
        print(f"All 'close' values are NaN in table {table}")
        return

    # 데이터 정규화
    scaler = MinMaxScaler()
    data_normalized = scaler.fit_transform(df['close'].values.reshape(-1, 1))
    
    # 지지선과 저항선을 찾기 위한 클러스터링
    clusterer = hdbscan.HDBSCAN(min_cluster_size=5)
    cluster_labels = clusterer.fit_predict(data_normalized)
    
    if len(set(cluster_labels)) <= 1:
        print(f"No clusters found in table {table}")
        return

    # 각 클러스터의 중앙값을 지지선/저항선으로 사용
    unique_labels = set(cluster_labels)
    support_resistance_lines_normalized = []
    for label in unique_labels:
        if label != -1:
            support_resistance_lines_normalized.append(np.median(data_normalized[cluster_labels == label]))
    
    if not support_resistance_lines_normalized:
        print(f"No support/resistance lines found in table {table}")
        return

    # 정규화된 지지선/저항선을 원래 스케일로 변환
    support_resistance_lines = scaler.inverse_transform(np.array(support_resistance_lines_normalized).reshape(-1, 1)).flatten()
    
    # 신뢰도 계산 (클러스터 크기와 반비례)
    cluster_sizes = [np.sum(cluster_labels == label) for label in unique_labels if label != -1]
    confidence = [size / np.max(cluster_sizes) for size in cluster_sizes]
    
    # 신뢰도 임계값 설정
    confidence_threshold = 0.8
    high_confidence_lines = [(line, conf) for line, conf in zip(support_resistance_lines, confidence) if conf >= confidence_threshold]
    
    if not high_confidence_lines:
        print(f"No high confidence lines found in table {table}")
        return

    # 결과 시각화
    plt.clf()
    plt.plot(df.index, df['close'], label='Close Price')
    for line, conf in high_confidence_lines:
        plt.axhline(line, linestyle='--', linewidth=2, color=(1 - conf, 0, conf), alpha=0.7)
        plt.text(df.index[-1], line, f'{line:.2f}', verticalalignment='bottom', horizontalalignment='right', color='black', fontsize=10)
    
    # 범례 추가
    import matplotlib.patches as mpatches
    red_patch = mpatches.Patch(color='red', label='Low Confidence')
    blue_patch = mpatches.Patch(color='blue', label='High Confidence')
    plt.legend(handles=[red_patch, blue_patch])
    
    plt.title(f'{table} High Confidence Support and Resistance Lines')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.draw()

# 이벤트 핸들러 연결
fig, ax = plt.subplots()
fig.canvas.mpl_connect('key_press_event', on_key)

# 첫 번째 플롯 업데이트
update_plot()
plt.show()

# 데이터베이스 연결 닫기
conn.close()