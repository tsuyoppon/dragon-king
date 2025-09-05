# %%
# 必要なライブラリをインポート
from lppls import lppls
import numpy as np
import pandas as pd
from datetime import datetime as dt, datetime, timedelta
from yahooquery import Ticker
import matplotlib.pyplot as plt
import matplotlib
# 日本語フォント設定
matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']

if __name__ == '__main__':
    # ティッカーシンボル省略入力の定義
    ticker_shortcuts = {
        'nikkei': '^N225',
        'sp500': '^GSPC', 
        'nas': '^IXIC',
        'usdjpy': 'JPY=X',
        'dax': '^GDAXI',
        'jreit': '1345.T',
        'nifty': '^NSEI'
    }
    
    # ティッカーシンボルをユーザーから入力
    print("=" * 60)
    print("Dragon King - LPPLS分析ツール")
    print("=" * 60)
    print("【省略入力対応】")
    print("  Nikkei → ^N225 (日経平均)")
    print("  SP500  → ^GSPC (S&P500)")
    print("  Nas    → ^IXIC (NASDAQ)")
    print("  USDJPY → JPY=X (ドル円)")
    print("  DAX    → ^GDAXI (ドイツDAX)")
    print("  JREIT  → 1345.T (日本REIT)")
    print("  Nifty  → ^NSEI (インドNifty50)")
    print("【その他】直接ティッカーシンボルを入力")
    print("  例: AAPL, MSFT, 7203.T など")
    print("-" * 60)
    ticker_input = input("解析対象のティッカーシンボルを入力してください: ").strip()
    
    # 省略入力をチェックして変換
    ticker_input_lower = ticker_input.lower()
    if ticker_input_lower in ticker_shortcuts:
        ticker_symbol = ticker_shortcuts[ticker_input_lower]
        print(f"省略入力 '{ticker_input}' → '{ticker_symbol}' に変換しました")
    else:
        ticker_symbol = ticker_input.upper()
    
    # 期間入力方式の選択
    print("\n" + "-" * 60)
    print("分析期間の入力方式を選択してください:")
    print("1. 開始日と終了日を両方指定 (現行方式)")
    print("2. 終了日から何年前までかを指定")
    print("-" * 60)
    
    while True:
        input_method = input("入力方式を選択 (1 または 2): ").strip()
        if input_method in ['1', '2']:
            break
        print("❌ 1 または 2 を入力してください")
    
    if input_method == '1':
        # 現行方式: 開始日と終了日を両方入力
        start_date_str = input("解析開始日(YYYY-MM-DD)を入力してください: ")
        end_date_str = input("解析終了日(YYYY-MM-DD)を入力してください: ")
    else:
        # 新方式: 終了日から何年前まで
        end_date_str = input("解析終了日(YYYY-MM-DD)を入力してください: ")
        
        print("\n分析期間を選択してください:")
        print("1. 1年前まで")
        print("2. 2年前まで") 
        print("3. 3年前まで")
        print("4. 5年前まで")
        print("5. 10年前まで")
        print("6. カスタム期間")
        
        while True:
            period_choice = input("期間を選択 (1-6): ").strip()
            if period_choice in ['1', '2', '3', '4', '5', '6']:
                break
            print("❌ 1-6 の数字を入力してください")
        
        # 終了日をパース
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            print("❌ 日付形式が正しくありません。YYYY-MM-DD形式で入力してください。")
            exit(1)
        
        # 期間に応じて開始日を計算
        if period_choice == '1':
            years_back = 1
        elif period_choice == '2':
            years_back = 2
        elif period_choice == '3':
            years_back = 3
        elif period_choice == '4':
            years_back = 5
        elif period_choice == '5':
            years_back = 10
        else:  # カスタム期間
            while True:
                try:
                    years_back = float(input("何年前まで分析しますか? (小数点可): "))
                    if years_back > 0:
                        break
                    else:
                        print("❌ 正の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
        
        # 開始日を計算
        days_back = int(years_back * 365.25)  # うるう年を考慮
        start_date = end_date - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        print(f"✓ 計算された分析期間: {start_date_str} ～ {end_date_str} ({years_back}年間)")

    print("\n" + "="*60)
    print(f"Dragon King - LPPLS分析")
    print("="*60)
    if ticker_input_lower in ticker_shortcuts:
        print(f"対象銘柄: {ticker_symbol} (入力: {ticker_input})")
    else:
        print(f"対象銘柄: {ticker_symbol}")
    if input_method == '1':
        print(f"分析期間: {start_date_str} ～ {end_date_str} (手動指定)")
    else:
        print(f"分析期間: {start_date_str} ～ {end_date_str} ({years_back}年間)")
    print("="*60)
    print("データ取得中...")

    data = Ticker(ticker_symbol).history(start=start_date_str, end=end_date_str)
    data.reset_index(inplace=True)
    data.rename(columns={"date": "Date", "adjclose": "Adj Close"}, inplace=True)

    # タイムゾーン情報を削除
    data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)

    data = data.sort_values('Date')  # 日付順にソート

    # データの基本情報を表示
    actual_start = data['Date'].min().strftime('%Y-%m-%d')
    actual_end = data['Date'].max().strftime('%Y-%m-%d')
    data_points = len(data)
    price_min = data['Adj Close'].min()
    price_max = data['Adj Close'].max()
    
    print(f"✓ データ取得完了")
    print(f"  実際の期間: {actual_start} ～ {actual_end}")
    print(f"  データ数: {data_points:,} 件")
    print(f"  価格範囲: ${price_min:.2f} - ${price_max:.2f}")
    print("-"*60)

    subset_data = data

    # 日付をordinal形式（数値）に変換
    time = [pd.Timestamp.toordinal(date) for date in subset_data['Date']]

    # 調整後終値をlog変換
    price = np.log(subset_data['Adj Close'].values)

    # LPPLSモデル用の観測データを作成
    observations = np.array([time, price])

    # LPPLSモデルを初期化
    print("LPPLS分析を開始します...")
    lppls_model = lppls.LPPLS(observations=observations)

    # モデルをフィッティング
    MAX_SEARCHES = 25  # 最大試行回数（推奨値: 25）
    print(f"モデルフィッティング中... (最大試行回数: {MAX_SEARCHES})")
    tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(MAX_SEARCHES)

    # fit() の結果があるか確認
    if not lppls_model.coef_:
        print("\n❌ LPPLSモデルで有効な解が得られませんでした。解析をスキップします。")
        print("="*60)
    else:
        print("✓ LPPLS分析完了")
        print("\n" + "="*60)
        print("LPPLS分析結果")
        print("="*60)
        if ticker_input_lower in ticker_shortcuts:
            print(f"対象銘柄: {ticker_symbol} (入力: {ticker_input})")
        else:
            print(f"対象銘柄: {ticker_symbol}")
        if input_method == '1':
            print(f"指定期間: {start_date_str} ～ {end_date_str} (手動指定)")
        else:
            print(f"指定期間: {start_date_str} ～ {end_date_str} ({years_back}年間)")
        print(f"分析期間: {actual_start} ～ {actual_end}")
        print(f"データ数: {data_points:,} 件")
        print("-"*60)
        
        # パラメータ結果を表示
        print("フィットパラメータ:")
        tc_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')
        print(f"  臨界時点 (tc): {tc_date} ({tc:.2f})")
        print(f"  指数パラメータ (m): {m:.6f}")
        print(f"  角周波数 (w): {w:.6f}")
        print(f"  線形係数 (a): {a:.6f}")
        print(f"  非線形係数 (b): {b:.6f}")
        print(f"  周期係数 (c): {c:.6f}")
        print(f"  コサイン成分 (c1): {c1:.6f}")
        print(f"  サイン成分 (c2): {c2:.6f}")
        print(f"  残差平方和 (O): {O:.6f}")
        print(f"  ダミアン指標 (D): {D:.6f}")
        print("-"*60)
        
        # 解釈を追加
        print("解釈:")
        if 0 < m < 1:
            print("  ⚠️  指数パラメータ (m) がバブル領域 (0 < m < 1) にあります")
        elif m >= 1:
            print("  🔴 指数パラメータ (m) が強いバブル領域 (m >= 1) にあります")
        else:
            print("  ✅ 指数パラメータ (m) は正常範囲です")
            
        current_date = pd.Timestamp.now()
        tc_timestamp = pd.Timestamp.fromordinal(int(tc))
        days_to_tc = (tc_timestamp - current_date).days
        
        if days_to_tc > 0:
            print(f"  📅 予測される臨界時点まで約 {days_to_tc} 日")
        elif days_to_tc == 0:
            print("  ⚡ 臨界時点は今日です")
        else:
            print(f"  📅 臨界時点は約 {abs(days_to_tc)} 日前でした")
            
        if D < 0.5:
            print("  ✅ ダミアン指標が良好 (D < 0.5) - 高い信頼性")
        elif D < 1.0:
            print("  ⚠️  ダミアン指標が中程度 (0.5 <= D < 1.0)")
        else:
            print("  🔴 ダミアン指標が高い (D >= 1.0) - 注意が必要")
        
        print("="*60)
        
        # フィット結果をプロット
        print("\nフィット結果をプロット中...")
        plt.figure(figsize=(12, 8))
        lppls_model.plot_fit()
        plt.title(f'{ticker_symbol} - LPPLS フィット結果 ({actual_start} ～ {actual_end})')
        plt.show()

        # 信頼指標を計算してプロット
        print("\n信頼指標を計算中... (この処理には時間がかかる場合があります)")
        res = lppls_model.mp_compute_nested_fits(
            workers=8,
            window_size=120,  # ウィンドウサイズ
            smallest_window_size=30,
            outer_increment=1,
            inner_increment=5,
            max_searches=MAX_SEARCHES,
        )
        print("信頼指標をプロット中...")
        plt.figure(figsize=(12, 10))
        lppls_model.plot_confidence_indicators(res)
        plt.suptitle(f'{ticker_symbol} - LPPLS 信頼指標 ({actual_start} ～ {actual_end})', y=0.98)
        plt.show()
        
        print("\n✅ 全ての分析が完了しました。")
        print("="*60)
    
# %%
