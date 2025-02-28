# %%
# 必要なライブラリをインポート
from lppls import lppls
import numpy as np
import pandas as pd
from datetime import datetime as dt
from yahooquery import Ticker

if __name__ == '__main__':
    # ティッカーシンボルをユーザーから入力
    ticker_symbol = input("解析対象のティッカーシンボルを入力してください: ")
    start_date_str = input("解析開始日(YYYY-MM-DD)を入力してください: ")
    end_date_str = input("解析終了日(YYYY-MM-DD)を入力してください: ")

    data = Ticker(ticker_symbol).history(start=start_date_str, end=end_date_str)
    data.reset_index(inplace=True)
    data.rename(columns={"date": "Date", "adjclose": "Adj Close"}, inplace=True)

    # タイムゾーン情報を削除
    data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)

    data = data.sort_values('Date')  # 日付順にソート

    subset_data = data

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
