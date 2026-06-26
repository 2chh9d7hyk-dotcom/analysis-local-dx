"""NES重点領域指標の計算・集計モジュール。"""
from __future__ import annotations
import pandas as pd
import numpy as np
from src.config import NES_AREAS


def get_latest_indicators(df: pd.DataFrame) -> dict[str, float] | None:
    """最新年度のNES指標を辞書形式で返す。"""
    if df.empty:
        return None
    latest = df.loc[df["target_year"].idxmax()]
    return {
        "online": float(latest.get("online_score", 0)),
        "ai_rpa": float(latest.get("ai_rpa_score", 0)),
        "data": float(latest.get("data_utilization_score", 0)),
        "total": float(latest.get("total_score", 0)),
        "year": int(latest.get("target_year", 0)),
    }


def compute_yoy_change(df: pd.DataFrame) -> dict[str, float]:
    """前年比変化量を計算する（最新年 - 前年）。"""
    if df.empty or len(df) < 2:
        return {}
    df_sorted = df.sort_values("target_year")
    latest = df_sorted.iloc[-1]
    prev = df_sorted.iloc[-2]
    return {
        "online": round(float(latest.get("online_score", 0)) - float(prev.get("online_score", 0)), 1),
        "ai_rpa": round(float(latest.get("ai_rpa_score", 0)) - float(prev.get("ai_rpa_score", 0)), 1),
        "data": round(float(latest.get("data_utilization_score", 0)) - float(prev.get("data_utilization_score", 0)), 1),
        "total": round(float(latest.get("total_score", 0)) - float(prev.get("total_score", 0)), 1),
    }


def benchmark_comparison(
    indicator_df: pd.DataFrame,
    national_avg: dict[str, float] | None = None,
    prefecture_avg: dict[str, float] | None = None,
) -> pd.DataFrame:
    """
    全国平均・県平均との比較DataFrameを返す。
    """
    national_avg = national_avg or {"online": 55.0, "ai_rpa": 42.0, "data": 38.0, "total": 45.0}
    prefecture_avg = prefecture_avg or {"online": 48.0, "ai_rpa": 35.0, "data": 30.0, "total": 38.0}

    latest = get_latest_indicators(indicator_df)
    if not latest:
        return pd.DataFrame()

    rows = []
    for key, area_info in NES_AREAS.items():
        if key == "positive":
            continue
        rows.append({
            "area": area_info["label"],
            "大玉村": latest.get(key, 0),
            "全国平均": national_avg.get(key, 0),
            "県平均": prefecture_avg.get(key, 0),
        })

    return pd.DataFrame(rows)


def score_trend_df(indicator_df: pd.DataFrame) -> pd.DataFrame:
    """スコア推移をPlotly用に整形する。"""
    if indicator_df.empty:
        return pd.DataFrame()
    return indicator_df[
        ["target_year", "online_score", "ai_rpa_score", "data_utilization_score", "total_score"]
    ].sort_values("target_year")


def priority_matrix(indicator_df: pd.DataFrame) -> list[dict]:
    """
    各NES領域の優先度マトリクス（改善余地 × 成長速度）を返す。
    改善提案ページのロードマップ表示に使用。
    """
    latest = get_latest_indicators(indicator_df)
    changes = compute_yoy_change(indicator_df)
    if not latest:
        return []

    items = [
        {
            "area": "オンライン化",
            "key": "online",
            "score": latest.get("online", 0),
            "yoy": changes.get("online", 0),
            "improvement_room": 100 - latest.get("online", 0),
            "color": "#3B82F6",
        },
        {
            "area": "AI/RPA",
            "key": "ai_rpa",
            "score": latest.get("ai_rpa", 0),
            "yoy": changes.get("ai_rpa", 0),
            "improvement_room": 100 - latest.get("ai_rpa", 0),
            "color": "#7C3AED",
        },
        {
            "area": "データ活用",
            "key": "data",
            "score": latest.get("data", 0),
            "yoy": changes.get("data", 0),
            "improvement_room": 100 - latest.get("data", 0),
            "color": "#06B6D4",
        },
    ]

    for item in items:
        # 優先度: 改善余地が大きく、成長が遅い領域を最優先
        room = item["improvement_room"]
        growth_speed = max(item["yoy"], 0.1)
        item["priority_score"] = room / growth_speed
        if item["priority_score"] >= 8:
            item["priority_level"] = "highest"
        elif item["priority_score"] >= 5:
            item["priority_level"] = "high"
        elif item["priority_score"] >= 3:
            item["priority_level"] = "medium"
        else:
            item["priority_level"] = "low"

    return sorted(items, key=lambda x: x["priority_score"], reverse=True)


# ── デバッグ用 ─────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data.loader import load_nes_indicators
    ind = load_nes_indicators()
    print(get_latest_indicators(ind))
    print(compute_yoy_change(ind))
    print(priority_matrix(ind))
