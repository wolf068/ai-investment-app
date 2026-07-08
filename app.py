from __future__ import annotations

from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

from src.engine import enrich_signals, theme_scores, calculate_score, decide_action, today_actions, ACTION_ZH

BASE = Path(__file__).parent
DATA = BASE / "data"

st.set_page_config(page_title="AI 投資研究 App MVP", layout="wide")
st.title("AI 投資研究 App MVP v0.3")
st.caption("新聞 → 訊號 → 主題 → 部位建議")


def load_csv(name: str) -> pd.DataFrame:
    path = DATA / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def save_csv(df: pd.DataFrame, name: str) -> None:
    df.to_csv(DATA / name, index=False)


def show_table(df: pd.DataFrame, height: int | None = None) -> None:
    st.dataframe(df, width="stretch", hide_index=True, height=height)


themes = load_csv("themes.csv")
companies = load_csv("companies.csv")
signals_raw = load_csv("signals.csv")
portfolio = load_csv("portfolio.csv")
trade_log = load_csv("trade_log.csv")

signals = enrich_signals(signals_raw, themes)
ranking = theme_scores(signals_raw, themes)
actions = today_actions(signals_raw, themes)

page = st.sidebar.radio(
    "頁面",
    ["儀表板", "新增訊號", "訊號資料庫", "主題", "投資組合", "交易紀錄"],
)

if page == "儀表板":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("訊號數", len(signals))
    c2.metric("需檢查部位", int((signals["action"] == "Review Position").sum()) if not signals.empty else 0)
    c3.metric("初始本金", "NT$1,500,000")
    cash_pct = 0.0
    if not portfolio.empty and "ticker" in portfolio.columns and "weight_pct" in portfolio.columns:
        cash_rows = portfolio.loc[portfolio["ticker"] == "CASH", "weight_pct"]
        if not cash_rows.empty:
            cash_pct = float(cash_rows.iloc[0])
    c4.metric("現金比例", f"{cash_pct:.0f}%")

    st.subheader("今日動作")
    if actions.empty:
        st.success("目前沒有需要調整部位的高分訊號。維持現金或原部位。")
    else:
        top = actions.iloc[0]
        st.warning(f"需要檢查部位：{top['theme_name']}｜分數 {top['score']}")
        st.write(f"**訊號：** {top['title']}")
        st.write(f"**投資意義：** {top['summary']}")
        st.write(f"**驅動因素：** {top['driver']}")
        st.write(f"**建議動作：** {top['action_zh']}")

        display_cols = ["date", "theme_name", "title", "driver", "score", "action_zh", "source"]
        st.markdown("#### 需檢查訊號清單")
        show_table(actions[display_cols].rename(columns={
            "date": "日期",
            "theme_name": "主題",
            "title": "訊號",
            "driver": "驅動因素",
            "score": "分數",
            "action_zh": "動作",
            "source": "來源",
        }))

    st.subheader("主題排名")
    show_table(ranking.rename(columns={"theme_id": "主題ID"}))

    st.subheader("最新訊號")
    latest_cols = ["date", "theme_name", "signal_type_zh", "title", "score", "action_zh", "source"]
    show_table(signals.sort_values("date", ascending=False).head(10)[latest_cols].rename(columns={
        "date": "日期",
        "theme_name": "主題",
        "signal_type_zh": "類型",
        "title": "訊號",
        "score": "分數",
        "action_zh": "動作",
        "source": "來源",
    }), height=320)

elif page == "新增訊號":
    st.subheader("新增回測訊號")
    st.write("一次新增一筆歷史訊號。系統會自動計算分數與建議動作。")

    theme_options = themes.apply(lambda r: f"{r['theme_id']}｜{r['name']}", axis=1).tolist()
    with st.form("add_signal_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            signal_date = st.date_input("日期", value=date(2025, 3, 19))
            source = st.text_input("來源", value="")
            source_quality = st.selectbox("來源品質", ["Official", "Company", "SupplyChain", "Media", "Internal"])
            title = st.text_input("標題", value="")
            source_url = st.text_input("來源連結", value="")
        with col2:
            signal_type = st.selectbox(
                "訊號類型",
                ["Product", "Capacity", "Customer", "Technology", "Financial", "Policy", "SupplyChain", "Competition"],
            )
            selected_theme = st.selectbox("主題", theme_options)
            theme_id = selected_theme.split("｜")[0]
            driver = st.text_input("驅動因素", value="")
            impact = st.selectbox("影響程度", ["Low", "Medium", "High", "Critical"], index=2)
            confidence_source = st.selectbox("信心來源", ["Media", "SupplyChain", "Company", "Official"], index=2)
        summary = st.text_area("一句話投資意義", value="")
        submitted = st.form_submit_button("新增訊號")

    if submitted:
        if not title.strip() or not summary.strip():
            st.error("標題與一句話投資意義為必填。")
        else:
            new_signal = {
                "signal_id": f"S{len(signals_raw) + 1:04d}",
                "date": signal_date.strftime("%Y-%m-%d"),
                "source": source.strip() or "Unknown",
                "source_quality": source_quality,
                "title": title.strip(),
                "signal_type": signal_type,
                "theme_id": theme_id,
                "driver": driver.strip() or "Unspecified",
                "impact": impact,
                "confidence_source": confidence_source,
                "summary": summary.strip(),
                "source_url": source_url.strip(),
            }
            updated = pd.concat([signals_raw, pd.DataFrame([new_signal])], ignore_index=True)
            save_csv(updated, "signals.csv")
            score = calculate_score(impact, confidence_source)
            action = ACTION_ZH[decide_action(score)]
            st.success(f"已新增訊號。分數={score}；動作={action}。請重新整理儀表板查看更新。")

elif page == "訊號資料庫":
    st.subheader("訊號資料庫")
    show_table(signals.sort_values("date"), height=640)

elif page == "主題":
    st.subheader("主題")
    show_table(themes)

    st.subheader("公司對應")
    show_table(companies)

elif page == "投資組合":
    st.subheader("投資組合")
    show_table(portfolio)
    st.info("MVP 規則：分數 >= 15 只觸發『檢查部位』，不會自動買進。")

elif page == "交易紀錄":
    st.subheader("交易紀錄")
    show_table(trade_log)
