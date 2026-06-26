"""RFM分析モジュール。市民エンゲージメント版RFM（Recency/Frequency/Monetary）。"""
from __future__ import annotations
import pandas as pd
import numpy as np
from src.config import RFM_BINS


# ── RFMスコアリング ────────────────────────────────────────────

def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """
    activity_logs DataFrameからRFMスコアを計算する。

    Returns:
        citizen_id, r_score, f_score, m_score, rfm_total, segment_label,
        primary_category, age_group, churn_risk を含むDataFrame。
    """
    if df.empty:
        return pd.DataFrame()

    # 市民ごとに集計
    agg = (
        df.groupby("citizen_id", as_index=False)
        .agg(
            municipality_code=("municipality_code", "first"),
            recency_days=("recency_days", "min"),       # 最小 = 最近
            frequency_score=("frequency_score", "mean"),
            engagement_value=("engagement_value", "mean"),
            primary_category=("category", lambda x: x.mode().iloc[0] if len(x) > 0 else ""),
            age_group=("target_age_group", "first"),
            log_count=("log_id", "count"),
        )
    )

    # Rスコア: recency_daysが小さいほど高スコア（最近 = 高）
    agg["r_score"] = _qcut_score(agg["recency_days"], ascending=False)
    # Fスコア: frequency_scoreが大きいほど高スコア
    agg["f_score"] = _qcut_score(agg["frequency_score"], ascending=True)
    # Mスコア: engagement_valueが大きいほど高スコア
    agg["m_score"] = _qcut_score(agg["engagement_value"], ascending=True)

    agg["rfm_total"] = agg["r_score"] + agg["f_score"] + agg["m_score"]
    agg["segment_label"] = agg.apply(_assign_segment, axis=1)
    agg["churn_risk"] = agg.apply(_compute_churn_risk, axis=1)

    return agg.sort_values("rfm_total", ascending=False).reset_index(drop=True)


def _qcut_score(series: pd.Series, ascending: bool = True, n: int = RFM_BINS) -> pd.Series:
    """分位数で1〜nのスコアに変換する。ascending=Trueで大きいほど高スコア。"""
    try:
        labels = list(range(1, n + 1))
        if not ascending:
            labels = labels[::-1]
        return pd.qcut(series, q=n, labels=labels, duplicates="drop").astype(float).fillna(3).astype(int)
    except Exception:
        return pd.Series([3] * len(series), index=series.index)


def _assign_segment(row: pd.Series) -> str:
    """RFMスコアからセグメントラベルを付与する。"""
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    total = r + f + m
    if total >= 13:
        return "アクティブ市民"
    elif r >= 4 and f >= 4:
        return "高関与市民"
    elif r <= 2 and f <= 2:
        return "休眠層"
    elif r <= 2 and f >= 3:
        return "潜在離脱者"
    elif r >= 3 and f <= 2:
        return "再活性化可能"
    elif m >= 4:
        return "高価値市民"
    else:
        return "要注目層"


def _compute_churn_risk(row: pd.Series) -> float:
    """離脱リスクスコアを0〜1で計算する。"""
    r_risk = (5 - row["r_score"]) / 4
    f_risk = (5 - row["f_score"]) / 4
    # 年齢層による補正（20代若者は高リスク）
    age_factor = 1.3 if "20代" in str(row.get("age_group", "")) else 1.0
    raw = (r_risk * 0.5 + f_risk * 0.5) * age_factor
    return min(round(float(raw), 3), 1.0)


# ── セグメント集計 ─────────────────────────────────────────────

def segment_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """セグメント別の集計サマリーを返す。"""
    if rfm_df.empty:
        return pd.DataFrame()
    return (
        rfm_df.groupby("segment_label")
        .agg(
            citizen_count=("citizen_id", "count"),
            avg_rfm=("rfm_total", "mean"),
            avg_churn_risk=("churn_risk", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("avg_rfm", ascending=False)
    )


def age_group_rfm(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """年齢層別RFM平均スコアを返す。"""
    if rfm_df.empty:
        return pd.DataFrame()
    return (
        rfm_df.groupby("age_group")
        .agg(
            count=("citizen_id", "count"),
            avg_r=("r_score", "mean"),
            avg_f=("f_score", "mean"),
            avg_m=("m_score", "mean"),
            avg_churn=("churn_risk", "mean"),
        )
        .round(2)
        .reset_index()
    )


def high_churn_citizens(rfm_df: pd.DataFrame, threshold: float = 0.65) -> pd.DataFrame:
    """離脱リスクが高い市民のリストを返す。"""
    if rfm_df.empty:
        return pd.DataFrame()
    return rfm_df[rfm_df["churn_risk"] >= threshold].sort_values("churn_risk", ascending=False)


# ── k-meansペルソナ分類 ────────────────────────────────────────

_PERSONA_DEFINITIONS = [
    # (name, color, description) — rfm_totalの降順で割り当て
    ("地域の守り人",  "#2563EB", "高エンゲージメント・高頻度。村のコアを支える存在"),
    ("眠れる可能性",  "#7C3AED", "過去は活発だったが頻度が低下中。再活性化余地が大きい"),
    ("漂流する才能",  "#F59E0B", "能力はあるが定着していない。放置すると転出へ"),
    ("サイレント多数派", "#9CA3AF", "接点が少ない未開拓層。アウトリーチ戦略が必要"),
]


def segment_by_kmeans(rfm_df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """
    RFMスコアにk-meansを適用し、「市民ペルソナ」列を付与して返す。
    データが少ない場合はrfm_totalランクによる簡易分類にフォールバック。
    """
    if rfm_df.empty:
        return rfm_df

    result = rfm_df.copy()

    if len(result) < n_clusters * 2:
        # データ不足: rfm_totalで単純分位分類
        labels = pd.qcut(result["rfm_total"], q=n_clusters, labels=False, duplicates="drop")
        result["cluster"] = labels.fillna(0).astype(int)
        result["cluster_rank"] = result["cluster"]
    else:
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            result["persona"] = "要分析"
            result["persona_color"] = "#9CA3AF"
            result["persona_desc"] = ""
            return result

        X = result[["r_score", "f_score", "m_score"]].values.astype(float)
        X_scaled = StandardScaler().fit_transform(X)

        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        result["cluster"] = km.fit_predict(X_scaled)

        # クラスタ重心のrfm合計でランク付け → ペルソナを割り当て
        center_totals = (
            result.groupby("cluster")["rfm_total"]
            .mean()
            .sort_values(ascending=False)
        )
        rank_map = {cluster: rank for rank, cluster in enumerate(center_totals.index)}
        result["cluster_rank"] = result["cluster"].map(rank_map)

    # ペルソナラベルを付与
    def _assign_persona(rank):
        idx = min(int(rank), len(_PERSONA_DEFINITIONS) - 1)
        return _PERSONA_DEFINITIONS[idx]

    result["persona"] = result["cluster_rank"].apply(lambda r: _assign_persona(r)[0])
    result["persona_color"] = result["cluster_rank"].apply(lambda r: _assign_persona(r)[1])
    result["persona_desc"] = result["cluster_rank"].apply(lambda r: _assign_persona(r)[2])
    return result


def persona_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """ペルソナ別の集計サマリーを返す。segment_by_kmeansの結果が必要。"""
    if rfm_df.empty or "persona" not in rfm_df.columns:
        return pd.DataFrame()
    return (
        rfm_df.groupby(["persona", "persona_color", "persona_desc"], observed=True)
        .agg(
            citizen_count=("citizen_id", "count"),
            avg_rfm=("rfm_total", "mean"),
            avg_churn_risk=("churn_risk", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("avg_rfm", ascending=False)
    )


# ── デバッグ用 ─────────────────────────────────────────────────
if __name__ == "__main__":
    # サンプルデータで動作確認
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data.loader import load_activity_logs
    logs = load_activity_logs()
    if not logs.empty:
        rfm = compute_rfm(logs)
        print(rfm.head())
        print(segment_summary(rfm))
    else:
        print("activity_logs.csv が見つかりません。generate_sample_data.py を先に実行してください。")
