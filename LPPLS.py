# %%
# 必要なライブラリをインポート
from lppls import lppls
import numpy as np
import pandas as pd
from datetime import datetime as dt

if __name__ == '__main__':
    # データをCSVから読み込む（ファイルパスを適宜修正）
    file_path = 'nikkei_data.csv'
    data = pd.read_csv(file_path)

    # 日付列をdatetime型に変換
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')

    # 日付をordinal形式（数値）に変換
    time = [pd.Timestamp.toordinal(date) for date in data['Date']]

    # 調整後終値をlog変換
    price = np.log(data['Adj Close'].values)

    # LPPLSモデル用の観測データを作成
    observations = np.array([time, price])

    # LPPLSモデルを初期化
    lppls_model = lppls.LPPLS(observations=observations)

    # モデルをフィッティング
    MAX_SEARCHES = 25  # 最大試行回数（推奨値: 25）
    tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(MAX_SEARCHES)

    # フィット結果をプロット
    import matplotlib.pyplot as plt # プロット用ライブラリ
    lppls_model.plot_fit()
    plt.show()

    # 信頼指標を計算してプロット
    res = lppls_model.mp_compute_nested_fits(
        workers=8,
        window_size=120,  # ウィンドウサイズ
        smallest_window_size=30,
        outer_increment=1,
        inner_increment=5,
        max_searches=MAX_SEARCHES,
    )
    lppls_model.plot_confidence_indicators(res)
    plt.show()
    
