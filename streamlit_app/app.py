"""
Dragon King - LPPLS分析ツール (Streamlit版)
元のスクリプトの入力・出力形式を忠実に再現
"""

import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from yahooquery import Ticker
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.backends.backend_agg
from lppls import lppls
import warnings
import sys
import time
from io import StringIO

# Streamlit設定
st.set_page_config(
    page_title="Dragon King LPPLS分析ツール",
    page_icon="📈",
    layout="wide"
)

# Streamlit用のmatplotlibバックエンド設定
matplotlib.use('Agg')

# matplotlibの設定を最適化
plt.ioff()  # インタラクティブモードを無効化

# 日本語フォント設定（シンプル化）
matplotlib.rcParams['font.family'] = ['DejaVu Sans']
matplotlib.rcParams['figure.max_open_warning'] = 0  # 警告を抑制

# 警告を非表示
warnings.filterwarnings('ignore')

# ページ設定
st.set_page_config(
    page_title="Dragon King - LPPLS分析ツール",
    page_icon="📈",
    layout="wide"
)

@st.cache_data(ttl=300)  # 5分間キャッシュ
def fetch_stock_data(ticker_symbol, start_date_str, end_date_str):
    """株価データを取得（キャッシュ付き）"""
    try:
        # リクエスト間隔を空ける
        time.sleep(0.5)
        
        ticker = Ticker(ticker_symbol)
        data = ticker.history(start=start_date_str, end=end_date_str)
        
        if data.empty:
            return None, f"ティッカーシンボル '{ticker_symbol}' のデータが見つかりません。"
            
        data.reset_index(inplace=True)
        data.rename(columns={"date": "Date", "adjclose": "Adj Close"}, inplace=True)
        
        # タイムゾーン情報を削除
        data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
        data = data.sort_values('Date')
        
        return data, None
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "too many" in error_msg.lower():
            return None, "❌ データ取得エラー: アクセス頻度が高すぎます。しばらく待ってから再試行してください。"
        else:
            return None, f"❌ データ取得エラー: {error_msg}"

def main():
    # セッション状態の初期化
    if 'analysis_completed' not in st.session_state:
        st.session_state.analysis_completed = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
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
    
    # タイトル表示（元のスクリプトと同じ形式）
    st.text("=" * 60)
    st.text("Dragon King - LPPLS分析ツール")
    st.text("=" * 60)
    st.text("【省略入力対応】")
    st.text("  Nikkei → ^N225 (日経平均)")
    st.text("  SP500  → ^GSPC (S&P500)")
    st.text("  Nas    → ^IXIC (NASDAQ)")
    st.text("  USDJPY → JPY=X (ドル円)")
    st.text("  DAX    → ^GDAXI (ドイツDAX)")
    st.text("  JREIT  → 1345.T (日本REIT)")
    st.text("  Nifty  → ^NSEI (インドNifty50)")
    st.text("【その他】直接ティッカーシンボルを入力")
    st.text("  例: AAPL, MSFT, 7203.T など")
    st.text("-" * 60)
    
    # ティッカーシンボル入力
    ticker_input = st.text_input(
        "解析対象のティッカーシンボルを入力してください:",
        key="ticker_input"
    )
    
    if ticker_input:
        # 省略入力をチェックして変換
        ticker_input_lower = ticker_input.lower()
        if ticker_input_lower in ticker_shortcuts:
            ticker_symbol = ticker_shortcuts[ticker_input_lower]
            st.success(f"省略入力 '{ticker_input}' → '{ticker_symbol}' に変換しました")
        else:
            ticker_symbol = ticker_input.upper()
        
        st.text("")
        st.text("-" * 60)
        st.text("分析期間の入力方式を選択してください:")
        st.text("1. 開始日と終了日を両方指定 (現行方式)")
        st.text("2. 終了日から何年前までかを指定")
        st.text("-" * 60)
        
        # 入力方式選択
        input_method = st.radio(
            "入力方式を選択:",
            options=["1", "2"],
            format_func=lambda x: "1. 開始日と終了日を両方指定" if x == "1" else "2. 終了日から何年前までかを指定",
            key="input_method"
        )
        
        start_date_str = None
        end_date_str = None
        years_back = None
        
        if input_method == "1":
            # 現行方式: 開始日と終了日を両方入力
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "解析開始日:",
                    value=datetime.now() - timedelta(days=365),
                    key="start_date"
                )
                start_date_str = start_date.strftime('%Y-%m-%d')
            
            with col2:
                end_date = st.date_input(
                    "解析終了日:",
                    value=datetime.now(),
                    key="end_date"
                )
                end_date_str = end_date.strftime('%Y-%m-%d')
                
        else:
            # 新方式: 終了日から何年前まで
            end_date = st.date_input(
                "解析終了日:",
                value=datetime.now(),
                key="end_date_new"
            )
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            st.text("")
            st.text("分析期間を選択してください:")
            st.text("1. 1年前まで")
            st.text("2. 2年前まで") 
            st.text("3. 3年前まで")
            st.text("4. 5年前まで")
            st.text("5. 10年前まで")
            st.text("6. カスタム期間")
            
            period_choice = st.selectbox(
                "期間を選択:",
                options=["1", "2", "3", "4", "5", "6"],
                format_func=lambda x: {
                    "1": "1. 1年前まで",
                    "2": "2. 2年前まで", 
                    "3": "3. 3年前まで",
                    "4": "4. 5年前まで",
                    "5": "5. 10年前まで",
                    "6": "6. カスタム期間"
                }[x],
                key="period_choice"
            )
            
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
                years_back = st.number_input(
                    "何年前まで分析しますか? (小数点可):",
                    min_value=0.1,
                    max_value=50.0,
                    value=2.0,
                    step=0.1,
                    key="custom_years"
                )
            
            # 開始日を計算
            days_back = int(years_back * 365.25)
            start_date = datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=days_back)
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            st.info(f"✓ 計算された分析期間: {start_date_str} ～ {end_date_str} ({years_back}年間)")
        
        # 分析実行ボタン
        if st.button("🚀 LPPLS分析を実行", type="primary", key="run_analysis"):
            # セッション状態をリセット
            st.session_state.analysis_completed = False
            st.session_state.analysis_results = None
            
            # 分析実行
            with st.spinner("分析を実行中..."):
                run_lppls_analysis(ticker_symbol, ticker_input, ticker_input_lower, ticker_shortcuts, 
                                 start_date_str, end_date_str, input_method, years_back)
        
        # 結果表示
        if st.session_state.analysis_completed and st.session_state.analysis_results:
            # 結果が既にセッション状態に保存されているので、
            # ここでは何もしない（結果は既に表示されている）
            pass

def run_lppls_analysis(ticker_symbol, ticker_input, ticker_input_lower, ticker_shortcuts, 
                      start_date_str, end_date_str, input_method, years_back):
    """LPPLS分析を実行"""
    
    # 出力コンテナ
    output_container = st.container()
    
    with output_container:
        # 分析開始の表示（元のスクリプトと同じ形式）
        st.text("")
        st.text("=" * 60)
        st.text("Dragon King - LPPLS分析")
        st.text("=" * 60)
        
        if ticker_input_lower in ticker_shortcuts:
            st.text(f"対象銘柄: {ticker_symbol} (入力: {ticker_input})")
        else:
            st.text(f"対象銘柄: {ticker_symbol}")
            
        if input_method == "1":
            st.text(f"分析期間: {start_date_str} ～ {end_date_str} (手動指定)")
        else:
            st.text(f"分析期間: {start_date_str} ～ {end_date_str} ({years_back}年間)")
            
        st.text("=" * 60)
        st.text("データ取得中...")
        
        # 🔍 デバッグ: 環境情報を表示
        st.write("🔍 **環境情報**")
        st.write(f"- Python version: {sys.version}")
        st.write(f"- Streamlit version: {st.__version__}")
        st.write(f"- Matplotlib version: {matplotlib.__version__}")
        st.write(f"- Matplotlib backend: {matplotlib.get_backend()}")
        
        # データ取得
        st.write("🔍 **データ取得開始**")
        data, error = fetch_stock_data(ticker_symbol, start_date_str, end_date_str)
        st.write("🔍 **データ取得完了**")
        
        if error:
            st.error(error)
            return
            
        if data is None or data.empty:
            st.error(f"❌ ティッカーシンボル '{ticker_symbol}' のデータが取得できませんでした。")
            return
            
        # タイムゾーン情報を削除
        data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
        data = data.sort_values('Date')
        
        # データの基本情報を表示
        actual_start = data['Date'].min().strftime('%Y-%m-%d')
        actual_end = data['Date'].max().strftime('%Y-%m-%d')
        data_points = len(data)
        price_min = data['Adj Close'].min()
        price_max = data['Adj Close'].max()
        
        st.text("✓ データ取得完了")
        st.text(f"  実際の期間: {actual_start} ～ {actual_end}")
        st.text(f"  データ数: {data_points:,} 件")
        st.text(f"  価格範囲: ${price_min:.2f} - ${price_max:.2f}")
        st.text("-" * 60)
        
        # LPPLS分析実行
        st.text("LPPLS分析を開始します...")
        st.write("🔍 **LPPLS処理開始**")
        
        # 日付をordinal形式（数値）に変換
        time = [pd.Timestamp.toordinal(date) for date in data['Date']]
        st.write(f"- 時系列データ変換完了: {len(time)} points")
        
        # 調整後終値をlog変換
        price = np.log(data['Adj Close'].values)
        st.write(f"- 価格データlog変換完了: min={price.min():.4f}, max={price.max():.4f}")
        
        # LPPLSモデル用の観測データを作成
        observations = np.array([time, price])
        st.write(f"- 観測データ作成完了: shape={observations.shape}")
        
        # LPPLSモデルを初期化
        lppls_model = lppls.LPPLS(observations=observations)
        st.write("- LPPLSモデル初期化完了")
        
        # モデルをフィッティング
        MAX_SEARCHES = 25
        st.text(f"モデルフィッティング中... (最大試行回数: {MAX_SEARCHES})")
        st.write("🔍 **フィッティング開始**")
        
        with st.spinner("フィッティング実行中..."):
            tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(MAX_SEARCHES)
            
        st.write("🔍 **フィッティング完了**")
        st.write(f"- 取得されたパラメータ: tc={tc:.4f}, m={m:.4f}, w={w:.4f}")
        st.write(f"- オシレーション指標: O={O:.4f}")
        st.write(f"- ダミアン指標: D={D:.4f}")
        
        # fit()の結果があるか確認
        if not lppls_model.coef_:
            st.text("")
            st.text("❌ LPPLSモデルで有効な解が得られませんでした。解析をスキップします。")
            st.text("=" * 60)
            return
        
        # 結果表示
        st.text("✓ LPPLS分析完了")
        st.text("")
        st.text("=" * 60)
        st.text("LPPLS分析結果")
        st.text("=" * 60)
        
        if ticker_input_lower in ticker_shortcuts:
            st.text(f"対象銘柄: {ticker_symbol} (入力: {ticker_input})")
        else:
            st.text(f"対象銘柄: {ticker_symbol}")
            
        if input_method == "1":
            st.text(f"指定期間: {start_date_str} ～ {end_date_str} (手動指定)")
        else:
            st.text(f"指定期間: {start_date_str} ～ {end_date_str} ({years_back}年間)")
            
        st.text(f"分析期間: {actual_start} ～ {actual_end}")
        st.text(f"データ数: {data_points:,} 件")
        st.text("-" * 60)
        
        # パラメータ結果を表示
        st.text("フィットパラメータ:")
        tc_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')
        st.text(f"  臨界時点 (tc): {tc_date} ({tc:.2f})")
        st.text(f"  指数パラメータ (m): {m:.6f}")
        st.text(f"  角周波数 (w): {w:.6f}")
        st.text(f"  線形係数 (a): {a:.6f}")
        st.text(f"  非線形係数 (b): {b:.6f}")
        st.text(f"  周期係数 (c): {c:.6f}")
        st.text(f"  コサイン成分 (c1): {c1:.6f}")
        st.text(f"  サイン成分 (c2): {c2:.6f}")
        st.text(f"  残差平方和 (O): {O:.6f}")
        st.text(f"  ダミアン指標 (D): {D:.6f}")
        st.text("-" * 60)
        
        # 解釈を追加
        st.text("解釈:")
        if 0 < m < 1:
            st.text("  ⚠️  指数パラメータ (m) がバブル領域 (0 < m < 1) にあります")
        elif m >= 1:
            st.text("  🔴 指数パラメータ (m) が強いバブル領域 (m >= 1) にあります")
        else:
            st.text("  ✅ 指数パラメータ (m) は正常範囲です")
            
        current_date = pd.Timestamp.now()
        tc_timestamp = pd.Timestamp.fromordinal(int(tc))
        days_to_tc = (tc_timestamp - current_date).days
        
        if days_to_tc > 0:
            st.text(f"  📅 予測される臨界時点まで約 {days_to_tc} 日")
        elif days_to_tc == 0:
            st.text("  ⚡ 臨界時点は今日です")
        else:
            st.text(f"  📅 臨界時点は約 {abs(days_to_tc)} 日前でした")
            
        if D < 0.5:
            st.text("  ✅ ダミアン指標が良好 (D < 0.5) - 高い信頼性")
        elif D < 1.0:
            st.text("  ⚠️  ダミアン指標が中程度 (0.5 <= D < 1.0)")
        else:
            st.text("  🔴 ダミアン指標が高い (D >= 1.0) - 注意が必要")
        
        st.text("=" * 60)
        
        # フィット結果をプロット
        st.text("")
        st.text("フィット結果をプロット中...")
        
        # デバッグ情報の表示
        st.write("🔍 **デバッグ情報 (プロット前)**")
        st.write(f"- matplotlib backend: {matplotlib.get_backend()}")
        st.write(f"- matplotlib version: {matplotlib.__version__}")
        st.write(f"- streamlit version: {st.__version__}")
        st.write(f"- 現在のfigure数: {len(plt.get_fignums())}")
        
        try:
            # 全ての既存のfigureをクリア
            plt.close('all')
            st.write(f"- figure クリア後: {len(plt.get_fignums())}")
            
            # 新しいFigureオブジェクトを明示的に作成
            fig, ax = plt.subplots(figsize=(12, 8))
            st.write(f"- 新しいfigure作成後: {len(plt.get_fignums())}")
            st.write(f"- figure サイズ: {fig.get_size_inches()}")
            st.write(f"- figure number: {fig.number}")
            
            # LPPLSのplot_fitを実行
            st.write("- LPPLSのplot_fit実行中...")
            lppls_model.plot_fit()
            st.write("- plot_fit完了")
            
            # 現在のfigureの状態を確認
            current_fig = plt.gcf()
            st.write(f"- 現在のfigure number: {current_fig.number}")
            st.write(f"- axes数: {len(current_fig.axes)}")
            
            # タイトルを設定
            plt.title(f'{ticker_symbol} - LPPLS フィット結果 ({actual_start} ～ {actual_end})')
            plt.tight_layout()
            
            st.write("- グラフをStreamlitに表示中...")
            
            # 複数の表示方法を試行
            try:
                # 方法1: 作成したfigureを使用
                st.pyplot(fig, clear_figure=False)
                st.write("✅ 方法1成功: 作成したfigureで表示")
            except Exception as e1:
                st.write(f"❌ 方法1失敗: {str(e1)}")
                
                try:
                    # 方法2: 現在のfigureを使用
                    st.pyplot(current_fig, clear_figure=False)
                    st.write("✅ 方法2成功: 現在のfigureで表示")
                except Exception as e2:
                    st.write(f"❌ 方法2失敗: {str(e2)}")
                    
                    try:
                        # 方法3: パラメータなしで表示
                        st.pyplot()
                        st.write("✅ 方法3成功: パラメータなしで表示")
                    except Exception as e3:
                        st.write(f"❌ 方法3失敗: {str(e3)}")
                        raise e1
            
        except Exception as e:
            st.error(f"⚠️ グラフの表示でエラーが発生しました: {str(e)}")
            # 詳細なデバッグ情報を追加
            st.write("🔍 **エラー詳細情報**")
            st.write(f"- エラー型: {type(e).__name__}")
            st.write(f"- エラーメッセージ: {str(e)}")
            st.write(f"- matplotlib backend: {matplotlib.get_backend()}")
            st.write(f"- matplotlib version: {matplotlib.__version__}")
            st.write(f"- streamlit version: {st.__version__}")
            st.write(f"- Python version: {sys.version}")
            st.write(f"- 現在のfigure数: {len(plt.get_fignums())}")
            
            # トレースバックも表示
            import traceback
            st.code(traceback.format_exc(), language="python")
        finally:
            plt.close('all')  # 全てのfigureを確実に閉じる
        
        # 信頼指標を計算してプロット
        st.text("")
        st.text("信頼指標を計算中... (この処理には時間がかかる場合があります)")
        
        with st.spinner("信頼指標計算中..."):
            try:
                res = lppls_model.mp_compute_nested_fits(
                    workers=4,  # Streamlitでは少なめに設定
                    window_size=120,
                    smallest_window_size=30,
                    outer_increment=1,
                    inner_increment=5,
                    max_searches=MAX_SEARCHES,
                )
                
                st.text("信頼指標をプロット中...")
                
                try:
                    st.write("🔍 **信頼指標プロット デバッグ情報**")
                    
                    # 信頼指標用の新しいfigureを作成
                    fig2, ax2 = plt.subplots(figsize=(15, 10))
                    st.write(f"- 信頼指標用figure作成: number={fig2.number}")
                    
                    # 信頼指標をプロット
                    st.write("- 信頼指標プロット実行中...")
                    lppls_model.plot_confidence_indicators(res)
                    st.write("- 信頼指標プロット完了")
                    
                    # タイトルを設定
                    plt.suptitle(f'{ticker_symbol} - LPPLS 信頼指標 ({actual_start} ～ {actual_end})', y=0.98)
                    plt.tight_layout()
                    
                    st.write("- 信頼指標グラフをStreamlitに表示中...")
                    # Streamlit 1.50.0対応: widthパラメータを使用
                    st.pyplot(fig2, clear_figure=False)
                    st.write("✅ 信頼指標グラフ表示成功")
                    
                except Exception as plot_error:
                    st.error(f"⚠️ 信頼指標グラフの表示でエラーが発生しました: {str(plot_error)}")
                    # デバッグ情報を追加
                    st.write("デバッグ情報:")
                    st.write(f"- matplotlib version: {matplotlib.__version__}")
                    st.write(f"- Python version: {sys.version}")
                finally:
                    plt.close('all')  # 全てのfigureを確実に閉じる
                
            except Exception as e:
                st.warning(f"⚠️ 信頼指標の計算でエラーが発生しました: {str(e)}")
        
        st.text("")
        st.text("✅ 全ての分析が完了しました。")
        st.text("=" * 60)

if __name__ == "__main__":
    main()
