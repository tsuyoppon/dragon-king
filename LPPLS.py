# %%
# 必要なライブラリをインポート
from lppls import lppls
import numpy as np
import pandas as pd
from datetime import datetime as dt
from yahooquery import Ticker
import streamlit as st

if __name__ == '__main__':
    st.title("LPPLS Analysis")

    # ティッカーシンボルをユーザーから入力
    ticker_symbol = st.text_input("解析対象のティッカーシンボルを入力してください", value="AAPL")
    start_date = st.date_input("解析開始日", value=dt(2020, 1, 1))
    end_date = st.date_input("解析終了日", value=dt.today())

    run_analysis = st.button("解析を実行")

    if run_analysis:
        if not ticker_symbol:
            st.error("ティッカーシンボルを入力してください。")
        elif start_date > end_date:
            st.error("解析開始日は解析終了日より前の日付にしてください。")
        else:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            data = Ticker(ticker_symbol).history(start=start_date_str, end=end_date_str)
            if data is None or data.empty:
                st.error("指定された期間のデータを取得できませんでした。")
            else:
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
                lppls_model.fit(MAX_SEARCHES)

                # fit() の結果があるか確認
                if not lppls_model.coef_:
                    st.error("LPPLSモデルで有効な解が得られませんでした。解析をスキップします。")
                else:
                    # フィット結果をプロット
                    import matplotlib.pyplot as plt  # プロット用ライブラリ
                    lppls_model.plot_fit()
                    st.pyplot(plt.gcf())
                    plt.close()

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
                    st.pyplot(plt.gcf())
                    plt.close()
    
# %%
