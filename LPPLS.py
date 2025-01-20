# %%
# 必要なライブラリをインポート
from lppls import lppls
import numpy as np
import pandas as pd
from datetime import datetime as dt

if __name__ == '__main__':
    # データをCSVから読み込む（ファイルパスを適宜修正）
    file_path = input("CSVファイルのパスを入力してください: ")
    data = pd.read_csv(file_path)

    # 日付列をdatetime型に変換
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')

    # 解析開始日と終了日をユーザーから入力
    start_date_str = input("解析開始日(YYYY-MM-DD)を入力してください: ")
    end_date_str = input("解析終了日(YYYY-MM-DD)を入力してください: ")
    start_date = pd.to_datetime(start_date_str, format='%Y-%m-%d', errors='coerce')
    end_date = pd.to_datetime(end_date_str, format='%Y-%m-%d', errors='coerce')

    data = data.sort_values('Date')  # 日付順にソート

    # 開始日・終了日に近い日付を探索
    closest_start = data[data['Date'] >= start_date]['Date'].min()
    closest_end = data[data['Date'] <= end_date]['Date'].max()

    # 取得できない場合の簡易処理（データが範囲外ならスキップ／全体解析など）
    if pd.isnull(closest_start) or pd.isnull(closest_end):
        print("指定した期間に該当するデータがありません。全期間で解析を実行します。")
        subset_data = data
    else:
        subset_data = data[(data['Date'] >= closest_start) & (data['Date'] <= closest_end)]

    # 日付をordinal形式（数値）に変換
    time = [pd.Timestamp.toordinal(date) for date in subset_data['Date']]

    # 調整後終値をlog変換
    price = np.log(subset_data['Adj Close'].values)

    # LPPLSモデル用の観測データを作成
    observations = np.array([time, price])

    # LPPLSモデルを初期化
    lppls_model = lppls.LPPLS(observations=observations)

    # モデルをフィッティング
    MAX_SEARCHES = 25  # 最大試行回数（推奨値: 25）
    tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(MAX_SEARCHES)

    # fit() の結果があるか確認
    if not lppls_model.coef_:
        print("LPPLSモデルで有効な解が得られませんでした。解析をスキップします。")
    else:
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
    
# %%
