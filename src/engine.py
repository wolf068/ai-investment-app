from __future__ import annotations

import pandas as pd

IMPACT_MAP = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}

CONFIDENCE_MAP = {
    "Media": 1,
    "SupplyChain": 3,
    "Company": 5,
    "Official": 5,
}

ACTION_ZH = {
    "Review Position": "檢查部位",
    "Update Theme": "更新主題",
    "Ignore": "忽略",
}

IMPACT_ZH = {
    "Low": "低",
    "Medium": "中",
    "High": "高",
    "Critical": "關鍵",
}

TYPE_ZH = {
    "Product": "產品",
    "Capacity": "產能",
    "Customer": "客戶 / 訂單",
    "Technology": "技術",
    "Financial": "財務",
    "Policy": "政策",
    "SupplyChain": "供應鏈",
    "Competition": "競爭",
}


def calculate_score(impact: str, confidence_source: str) -> int:
    """Score = impact × confidence."""
    return IMPACT_MAP[impact] * CONFIDENCE_MAP[confidence_source]


def decide_action(score: int) -> str:
    if score >= 15:
        return "Review Position"
    if score >= 6:
        return "Update Theme"
    return "Ignore"


def enrich_signals(signals: pd.DataFrame, themes: pd.DataFrame | None = None) -> pd.DataFrame:
    df = signals.copy()
    if df.empty:
        return df
    df["score"] = df.apply(
        lambda r: calculate_score(r["impact"], r["confidence_source"]), axis=1
    )
    df["action"] = df["score"].apply(decide_action)
    df["action_zh"] = df["action"].map(ACTION_ZH)
    df["impact_zh"] = df["impact"].map(IMPACT_ZH)
    df["signal_type_zh"] = df["signal_type"].map(TYPE_ZH).fillna(df["signal_type"])
    if themes is not None and not themes.empty:
        theme_lookup = themes[["theme_id", "name"]].drop_duplicates()
        df = df.merge(theme_lookup, on="theme_id", how="left")
        df = df.rename(columns={"name": "theme_name"})
    return df


def theme_scores(signals: pd.DataFrame, themes: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame(columns=["theme_id", "主題", "訊號數", "總分", "最高分", "需檢查部位", "趨勢"])
    enriched = enrich_signals(signals, themes)
    out = (
        enriched.groupby(["theme_id", "theme_name"], dropna=False)
        .agg(
            訊號數=("signal_id", "count"),
            總分=("score", "sum"),
            最高分=("score", "max"),
            需檢查部位=("action", lambda s: int((s == "Review Position").sum())),
        )
        .reset_index()
        .rename(columns={"theme_name": "主題"})
        .sort_values(["需檢查部位", "總分"], ascending=False)
    )
    out["趨勢"] = out["最高分"].apply(lambda x: "↑" if x >= 15 else ("→" if x >= 6 else "↓"))
    return out[["theme_id", "主題", "訊號數", "總分", "最高分", "需檢查部位", "趨勢"]]


def today_actions(signals: pd.DataFrame, themes: pd.DataFrame, limit: int = 3) -> pd.DataFrame:
    enriched = enrich_signals(signals, themes)
    if enriched.empty:
        return enriched
    df = enriched[enriched["action"] == "Review Position"].copy()
    if df.empty:
        return df
    return df.sort_values(["date", "score"], ascending=[False, False]).head(limit)
