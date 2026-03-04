"""
Dragon King - LPPLS分析ツール (Streamlit版)
"""

# matplotlib のバックエンドを pyplot インポート前に設定（必須）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import io
import warnings
import time

import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from yahooquery import Ticker
from lppls import lppls

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────
# ページ設定（スクリプト内で1回だけ呼び出す）
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Dragon King LPPLS分析ツール",
    page_icon="📈",
    layout="wide",
)

# matplotlib グローバル設定
plt.ioff()
matplotlib.rcParams["font.family"] = ["DejaVu Sans"]
matplotlib.rcParams["figure.max_open_warning"] = 0

# ──────────────────────────────────────────────
# 定数
# ──────────────────────────────────────────────
TICKER_SHORTCUTS: dict[str, str] = {
    "nikkei": "^N225",
    "sp500": "^GSPC",
    "nas": "^IXIC",
    "usdjpy": "JPY=X",
    "dax": "^GDAXI",
    "jreit": "1345.T",
    "nifty": "^NSEI",
}

SHORTCUT_LABELS: dict[str, str] = {
    "nikkei": "日経平均",
    "sp500": "S&P500",
    "nas": "NASDAQ",
    "usdjpy": "ドル円",
    "dax": "ドイツDAX",
    "jreit": "日本REIT",
    "nifty": "インドNifty50",
}

MAX_SEARCHES = 25


# ──────────────────────────────────────────────
# データ取得
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_stock_data(
    ticker_symbol: str, start_date_str: str, end_date_str: str
) -> tuple:
    """株価データを取得してキャッシュする（5分間）。

    Returns:
        (DataFrame, None)  : 成功時
        (None, error_msg)  : 失敗時
    """
    try:
        time.sleep(0.5)  # レート制限対策
        ticker = Ticker(ticker_symbol)
        data = ticker.history(start=start_date_str, end=end_date_str)

        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return None, f"ティッカー '{ticker_symbol}' のデータが見つかりません。"

        data = data.reset_index()
        data = data.rename(columns={"date": "Date", "adjclose": "Adj Close"})

        # タイムゾーン除去・ソート（ここで1回だけ実施）
        data["Date"] = pd.to_datetime(data["Date"]).dt.tz_localize(None)
        data = data.sort_values("Date").reset_index(drop=True)

        if data["Adj Close"].isna().all():
            return None, f"ティッカー '{ticker_symbol}' の終値データがありません。"

        return data, None

    except Exception as exc:
        msg = str(exc)
        if "429" in msg or "too many" in msg.lower():
            return None, "アクセス頻度が高すぎます。しばらく待ってから再試行してください。"
        return None, f"データ取得エラー: {msg}"


# ──────────────────────────────────────────────
# LPPLS 補助関数
# ──────────────────────────────────────────────
def _fig_to_st_image(fig, caption: str = "") -> None:
    """matplotlib Figure を st.image() で表示する。"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    st.image(buf, caption=caption, use_container_width=True)


def _run_fit(lppls_model):
    """フィッティングを実行し、結果タプルを返す。失敗時は None。"""
    try:
        result = lppls_model.fit(MAX_SEARCHES)
        if not lppls_model.coef_:
            return None
        return result
    except Exception as exc:
        st.error(f"フィッティングエラー: {exc}")
        return None


def _display_params(
    ticker_symbol: str,
    actual_start: str,
    actual_end: str,
    data_points: int,
    fit_result: tuple,
) -> None:
    """フィットパラメータを Streamlit ネイティブコンポーネントで表示する。"""
    tc, m, w, a, b, c, c1, c2, O, D = fit_result
    tc_date = pd.Timestamp.fromordinal(int(tc)).strftime("%Y-%m-%d")

    st.subheader("フィットパラメータ")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("臨界時点 tc", tc_date)
    col2.metric("指数パラメータ m", f"{m:.4f}")
    col3.metric("角周波数 w", f"{w:.4f}")
    col4.metric("ダミアン指標 D", f"{D:.4f}")
    col5.metric("残差平方和 O", f"{O:.4f}")

    with st.expander("詳細パラメータ"):
        params_df = pd.DataFrame(
            {
                "パラメータ": ["tc (ordinal)", "m", "w", "a", "b", "c", "c1", "c2", "O (残差)", "D (ダミアン)"],
                "値": [f"{tc:.2f}", f"{m:.6f}", f"{w:.6f}", f"{a:.6f}",
                       f"{b:.6f}", f"{c:.6f}", f"{c1:.6f}", f"{c2:.6f}",
                       f"{O:.6f}", f"{D:.6f}"],
                "説明": [
                    "臨界時点（ordinal）", "指数パラメータ", "角周波数",
                    "線形係数", "非線形係数", "周期係数",
                    "コサイン成分", "サイン成分", "残差平方和", "ダミアン指標"
                ],
            }
        )
        st.dataframe(params_df, hide_index=True, use_container_width=True)

    st.subheader("解釈")
    if 0 < m < 1:
        st.warning(f"⚠️ 指数パラメータ (m={m:.4f}) がバブル領域 (0 < m < 1) にあります。")
    elif m >= 1:
        st.error(f"🔴 指数パラメータ (m={m:.4f}) が強いバブル領域 (m ≥ 1) にあります。")
    else:
        st.success(f"✅ 指数パラメータ (m={m:.4f}) は正常範囲です。")

    tc_timestamp = pd.Timestamp.fromordinal(int(tc))
    days_to_tc = (tc_timestamp - pd.Timestamp.now()).days
    if days_to_tc > 0:
        st.info(f"📅 予測される臨界時点まで約 **{days_to_tc}** 日（{tc_date}）")
    elif days_to_tc == 0:
        st.error("⚡ 臨界時点は今日です。")
    else:
        st.info(f"📅 臨界時点は約 **{abs(days_to_tc)}** 日前でした（{tc_date}）")

    if D < 0.5:
        st.success(f"✅ ダミアン指標 (D={D:.4f}) が良好 < 0.5 — 高い信頼性")
    elif D < 1.0:
        st.warning(f"⚠️ ダミアン指標 (D={D:.4f}) が中程度 (0.5 ≤ D < 1.0)")
    else:
        st.error(f"🔴 ダミアン指標 (D={D:.4f}) が高い ≥ 1.0 — 注意が必要")


def _plot_fit(lppls_model, ticker_display: str, actual_start: str, actual_end: str) -> None:
    """フィット結果グラフを描画して st.image() で表示する。"""
    try:
        plt.close("all")
        lppls_model.plot_fit()
        fig = plt.gcf()
        if fig.axes:
            fig.suptitle(
                f"{ticker_display} — LPPLS フィット結果  ({actual_start} ～ {actual_end})",
                fontsize=13,
            )
            plt.tight_layout()
            _fig_to_st_image(fig)
        else:
            st.warning("フィットグラフの生成に失敗しました。")
    except Exception as exc:
        st.error(f"フィットグラフ描画エラー: {exc}")
    finally:
        plt.close("all")


def _plot_confidence(
    lppls_model,
    ticker_display: str,
    actual_start: str,
    actual_end: str,
    max_searches: int,
) -> None:
    """信頼指標グラフを計算・描画して st.image() で表示する。"""
    with st.spinner("信頼指標を計算中… (数十秒かかる場合があります)"):
        try:
            res = lppls_model.mp_compute_nested_fits(
                workers=4,
                window_size=120,
                smallest_window_size=30,
                outer_increment=1,
                inner_increment=5,
                max_searches=max_searches,
            )
        except Exception as exc:
            st.warning(f"信頼指標の計算でエラーが発生しました: {exc}")
            return

    try:
        plt.close("all")
        lppls_model.plot_confidence_indicators(res)
        fig = plt.gcf()
        if fig.axes:
            fig.suptitle(
                f"{ticker_display} — LPPLS 信頼指標  ({actual_start} ～ {actual_end})",
                fontsize=13,
                y=1.01,
            )
            plt.tight_layout()
            _fig_to_st_image(fig)
        else:
            st.warning("信頼指標グラフの生成に失敗しました。")
    except Exception as exc:
        st.error(f"信頼指標グラフ描画エラー: {exc}")
    finally:
        plt.close("all")


# ──────────────────────────────────────────────
# 分析メイン処理
# ──────────────────────────────────────────────
def run_lppls_analysis(
    ticker_symbol: str,
    ticker_display: str,
    start_date_str: str,
    end_date_str: str,
    period_label: str,
) -> None:
    """LPPLS 分析を実行し、結果を Streamlit に描画する。"""

    # ── データ取得 ──────────────────────────────
    with st.spinner("データを取得中…"):
        data, error = fetch_stock_data(ticker_symbol, start_date_str, end_date_str)

    if error:
        st.error(f"❌ {error}")
        return
    if data is None or data.empty:
        st.error(f"❌ '{ticker_symbol}' のデータを取得できませんでした。")
        return

    actual_start = data["Date"].min().strftime("%Y-%m-%d")
    actual_end = data["Date"].max().strftime("%Y-%m-%d")
    data_points = len(data)

    st.success(
        f"✅ データ取得完了 — **{data_points:,}** 件  "
        f"（{actual_start} ～ {actual_end}）"
    )

    # データプレビュー
    preview_cols = [c for c in ["Date", "open", "high", "low", "close", "Adj Close", "volume"] if c in data.columns]
    with st.expander("取得データのプレビュー（直近20件）"):
        st.dataframe(data[preview_cols].tail(20), hide_index=True, use_container_width=True)

    # ── LPPLS セットアップ ──────────────────────
    time_ord = [pd.Timestamp.toordinal(d) for d in data["Date"]]
    price_log = np.log(data["Adj Close"].values)
    observations = np.array([time_ord, price_log])
    lppls_model = lppls.LPPLS(observations=observations)

    # ── フィッティング ──────────────────────────
    st.subheader("モデルフィッティング")
    with st.spinner(f"フィッティング実行中… (最大試行: {MAX_SEARCHES})"):
        fit_result = _run_fit(lppls_model)

    if fit_result is None:
        st.error("❌ LPPLS モデルで有効な解が得られませんでした。")
        st.info("💡 分析期間を変更するか、別のティッカーシンボルをお試しください。")
        return

    st.success("✅ フィッティング完了")

    # ── パラメータ表示 ───────────────────────────
    _display_params(ticker_symbol, actual_start, actual_end, data_points, fit_result)

    # ── フィットグラフ ──────────────────────────
    st.subheader("フィット結果グラフ")
    _plot_fit(lppls_model, ticker_display, actual_start, actual_end)

    # ── 信頼指標グラフ ──────────────────────────
    st.subheader("信頼指標グラフ")
    _plot_confidence(lppls_model, ticker_display, actual_start, actual_end, MAX_SEARCHES)

    st.success("✅ すべての分析が完了しました。")


# ──────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────
def main() -> None:
    st.title("📈 Dragon King — LPPLS 分析ツール")
    st.caption("Log-Periodic Power Law Singularity (LPPLS) モデルによるバブル・崩壊予測")

    # ── ティッカー入力 ───────────────────────────
    st.header("1. 銘柄選択")

    with st.expander("省略入力ガイド"):
        shortcut_df = pd.DataFrame(
            [
                {"省略キー": k, "ティッカー": v, "市場": SHORTCUT_LABELS[k]}
                for k, v in TICKER_SHORTCUTS.items()
            ]
        )
        st.dataframe(shortcut_df, hide_index=True, use_container_width=True)
        st.caption("上記以外は AAPL、MSFT、7203.T など公式ティッカーを直接入力してください。")

    ticker_input = st.text_input(
        "ティッカーシンボル（例: nikkei / sp500 / AAPL）",
        placeholder="nikkei",
        key="ticker_input",
    )

    if not ticker_input:
        st.info("ティッカーシンボルを入力してください。")
        return

    ticker_lower = ticker_input.lower()
    if ticker_lower in TICKER_SHORTCUTS:
        ticker_symbol = TICKER_SHORTCUTS[ticker_lower]
        ticker_display = f"{ticker_symbol} ({SHORTCUT_LABELS[ticker_lower]})"
        st.success(f"省略入力 → **{ticker_symbol}** ({SHORTCUT_LABELS[ticker_lower]})")
    else:
        ticker_symbol = ticker_input.upper()
        ticker_display = ticker_symbol

    # ── 分析期間 ─────────────────────────────────
    st.header("2. 分析期間")

    input_method = st.radio(
        "入力方式",
        options=["dates", "years"],
        format_func=lambda x: "開始日と終了日を指定" if x == "dates" else "終了日から遡る年数を指定",
        horizontal=True,
        key="input_method",
    )

    start_date_str = None
    end_date_str = None
    period_label = ""

    if input_method == "dates":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "開始日",
                value=datetime.now() - timedelta(days=365),
                key="start_date",
            )
        with col2:
            end_date = st.date_input(
                "終了日",
                value=datetime.now(),
                key="end_date",
            )
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        period_label = "手動指定"

    else:
        end_date = st.date_input(
            "終了日",
            value=datetime.now(),
            key="end_date_years",
        )
        end_date_str = end_date.strftime("%Y-%m-%d")

        years_option = st.selectbox(
            "遡る年数",
            options=["1年", "2年", "3年", "5年", "10年", "カスタム"],
            index=1,
            key="years_back",
        )

        years_map = {"1年": 1, "2年": 2, "3年": 3, "5年": 5, "10年": 10}

        if years_option == "カスタム":
            years_back = st.number_input(
                "年数（小数可）",
                min_value=0.1,
                max_value=50.0,
                value=2.0,
                step=0.1,
                key="custom_years",
            )
        else:
            years_back = years_map[years_option]

        days_back = int(float(years_back) * 365.25)
        start_date = datetime.strptime(end_date_str, "%Y-%m-%d") - timedelta(days=days_back)
        start_date_str = start_date.strftime("%Y-%m-%d")
        period_label = f"{years_back}年間"
        st.info(f"分析期間: **{start_date_str}** ～ **{end_date_str}** ({period_label})")

    # 日付バリデーション
    if start_date_str and end_date_str and start_date_str >= end_date_str:
        st.error("開始日は終了日より前に設定してください。")
        return

    # ── 実行ボタン ───────────────────────────────
    st.header("3. 分析実行")
    st.markdown(
        f"**銘柄:** {ticker_display}　　**期間:** {start_date_str} ～ {end_date_str}　　**方式:** {period_label}"
    )

    if st.button("🚀 LPPLS 分析を実行", type="primary", key="run_btn"):
        st.divider()
        run_lppls_analysis(
            ticker_symbol=ticker_symbol,
            ticker_display=ticker_display,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            period_label=period_label,
        )


if __name__ == "__main__":
    main()
