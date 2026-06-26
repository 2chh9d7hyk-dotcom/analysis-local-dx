"""離脱・転出予測モジュール。直近エンゲージメントトレンドから転出リスクを計算する。"""
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.config import CHURN_THRESHOLD_DAYS, CHURN_DECLINE_RATE


def compute_churn_trends(df: pd.DataFrame, reference_date: date | None = None) -> pd.DataFrame:
    """
    市民ごとの直近エンゲージメントトレンドを計算し、転出リスクを推定する。

    Args:
        df: activity_logs DataFrame
        reference_date: 基準日（Noneの場合は最新アクション日を使用）

    Returns:
        citizen_id, age_group, category, freq_3m, freq_6m,
        freq_change_rate, churn_flag, churn_probability を含むDataFrame。
    """
    if df.empty:
        return pd.DataFrame()

    if "action_date" not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["action_date"] = pd.to_datetime(df["action_date"], errors="coerce")
    df = df.dropna(subset=["action_date"])

    ref = pd.Timestamp(reference_date or df["action_date"].max().date())

    cutoff_3m = ref - pd.Timedelta(days=90)
    cutoff_6m = ref - pd.Timedelta(days=180)

    results = []
    for citizen_id, group in df.groupby("citizen_id"):
        recent_3m = group[group["action_date"] >= cutoff_3m]
        prev_3m = group[(group["action_date"] >= cutoff_6m) & (group["action_date"] < cutoff_3m)]

        freq_3m = recent_3m["frequency_score"].mean() if not recent_3m.empty else 0.0
        freq_6m = prev_3m["frequency_score"].mean() if not prev_3m.empty else 0.0
        engagement_3m = recent_3m["engagement_value"].mean() if not recent_3m.empty else 0.0

        # 前期比変化率
        if freq_6m > 0:
            change_rate = (freq_3m - freq_6m) / freq_6m
        else:
            change_rate = 0.0

        # 離脱フラグ: 30%以上減少 または 直近90日間に行動なし
        churn_flag = (change_rate <= -CHURN_DECLINE_RATE) or (recent_3m.empty)

        # 離脱確率（ロジスティック回帰の代替シミュレーション）
        age_group = group["target_age_group"].mode().iloc[0] if len(group) > 0 else ""
        age_penalty = 0.25 if "20代" in age_group else 0.10

        base_risk = max(0.0, -change_rate) * 0.6  # 減少率をリスクに変換
        recency_risk = min(group["recency_days"].max() / 180, 1.0) * 0.3
        churn_prob = min(base_risk + recency_risk + (age_penalty if churn_flag else 0), 1.0)

        results.append({
            "citizen_id": citizen_id,
            "age_group": age_group,
            "primary_category": group["category"].mode().iloc[0] if len(group) > 0 else "",
            "freq_3m": round(freq_3m, 2),
            "freq_6m": round(freq_6m, 2),
            "engagement_3m": round(engagement_3m, 2),
            "freq_change_rate": round(change_rate * 100, 1),  # %表示
            "churn_flag": churn_flag,
            "churn_probability": round(churn_prob, 3),
        })

    result_df = pd.DataFrame(results)
    if result_df.empty:
        return result_df

    return result_df.sort_values("churn_probability", ascending=False).reset_index(drop=True)


def churn_by_age_group(churn_df: pd.DataFrame) -> pd.DataFrame:
    """年齢層別の離脱リスク集計。"""
    if churn_df.empty:
        return pd.DataFrame()
    return (
        churn_df.groupby("age_group")
        .agg(
            citizen_count=("citizen_id", "count"),
            churn_flag_count=("churn_flag", "sum"),
            avg_churn_prob=("churn_probability", "mean"),
            avg_freq_change=("freq_change_rate", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("avg_churn_prob", ascending=False)
    )


def churn_by_category(churn_df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ別の離脱リスク集計。"""
    if churn_df.empty:
        return pd.DataFrame()
    return (
        churn_df.groupby("primary_category")
        .agg(
            citizen_count=("citizen_id", "count"),
            churn_rate=("churn_flag", "mean"),
            avg_churn_prob=("churn_probability", "mean"),
        )
        .round(3)
        .reset_index()
        .sort_values("churn_rate", ascending=False)
    )


def simulate_time_quality_improvement(
    routine_before: float,
    creative_before: float,
    system_hours_saved_per_month: float,
    total_months: int = 12,
) -> pd.DataFrame:
    """
    システム導入による「時間の質」改善シミュレーション。
    定型業務削減→クリエイティブ業務増加の推移を返す。
    """
    rows = []
    routine = routine_before
    creative = creative_before
    monthly_saving = system_hours_saved_per_month / total_months

    for month in range(total_months + 1):
        rows.append({
            "month": month,
            "label": f"{month}ヶ月後" if month > 0 else "導入前",
            "routine_hours": round(max(routine - monthly_saving * month, 0), 1),
            "creative_hours": round(creative + monthly_saving * month * 0.8, 1),
        })

    return pd.DataFrame(rows)


# ── ロジスティック回帰チャーンモデル ──────────────────────────

def train_churn_model(activity_logs: pd.DataFrame):
    """
    ロジスティック回帰で転出リスクモデルを訓練する。

    「何が転出を引き起こすのか」を係数として可視化することで、
    職員が「なぜ」危険なのかを理解しやすくする。

    Returns:
        (model_bundle, importance_df, metrics_dict)
        model_bundle: None or (model, scaler) のタプル
        importance_df: feature, feature_label, coefficient, importance 列
        metrics_dict: accuracy, auc, n_churners, n_total
    """
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import accuracy_score, roc_auc_score
    except ImportError:
        return None, pd.DataFrame(), {}

    churn_df = compute_churn_trends(activity_logs)
    if churn_df.empty or len(churn_df) < 15:
        return None, pd.DataFrame(), {}

    # 市民レベルの集計特徴量
    citizen_stats = (
        activity_logs.groupby("citizen_id")
        .agg(
            recency_days=("recency_days", "min"),
            frequency_score=("frequency_score", "mean"),
            engagement_value=("engagement_value", "mean"),
        )
        .reset_index()
    )
    merged = churn_df.merge(citizen_stats, on="citizen_id", how="left")

    merged["is_youth"]     = merged["age_group"].str.contains("20代", na=False).astype(int)
    merged["is_childcare"] = merged["primary_category"].str.contains("育児", na=False).astype(int)
    merged["is_new_resident"] = merged["primary_category"].str.contains("移住|UIターン", na=False).astype(int)

    features = ["recency_days", "frequency_score", "engagement_value", "is_youth", "is_childcare", "is_new_resident"]
    feature_labels = ["最終行動からの経過日数", "利用頻度スコア", "エンゲージメント値", "20代若者フラグ", "育児利用者フラグ", "移住者フラグ"]

    X = merged[features].fillna(0).values
    y = merged["churn_flag"].astype(int).values

    if len(np.unique(y)) < 2:
        return None, pd.DataFrame(), {}

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(class_weight="balanced", random_state=42, max_iter=300, solver="lbfgs")
    model.fit(X_scaled, y)

    importance_df = pd.DataFrame({
        "feature": features,
        "feature_label": feature_labels,
        "coefficient": model.coef_[0],
        "importance": np.abs(model.coef_[0]),
        "direction": ["転出リスク増" if c > 0 else "転出リスク減" for c in model.coef_[0]],
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    y_pred = model.predict(X_scaled)
    y_prob = model.predict_proba(X_scaled)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y, y_pred)), 3),
        "auc": round(float(roc_auc_score(y, y_prob)), 3),
        "n_churners": int(y.sum()),
        "n_total": len(y),
        "churn_rate": round(float(y.mean()) * 100, 1),
    }

    return (model, scaler), importance_df, metrics


def predict_churn_proba(activity_logs: pd.DataFrame, model_bundle) -> pd.DataFrame:
    """
    訓練済みモデルで各市民の転出確率を予測する。
    model_bundle は train_churn_model() の第1戻り値。
    """
    if model_bundle is None:
        return pd.DataFrame()

    model, scaler = model_bundle

    citizen_stats = (
        activity_logs.groupby("citizen_id")
        .agg(
            age_group=("target_age_group", "first"),
            primary_category=("category", lambda x: x.mode().iloc[0] if len(x) > 0 else ""),
            recency_days=("recency_days", "min"),
            frequency_score=("frequency_score", "mean"),
            engagement_value=("engagement_value", "mean"),
        )
        .reset_index()
    )

    citizen_stats["is_youth"]       = citizen_stats["age_group"].str.contains("20代", na=False).astype(int)
    citizen_stats["is_childcare"]   = citizen_stats["primary_category"].str.contains("育児", na=False).astype(int)
    citizen_stats["is_new_resident"] = citizen_stats["primary_category"].str.contains("移住|UIターン", na=False).astype(int)

    features = ["recency_days", "frequency_score", "engagement_value", "is_youth", "is_childcare", "is_new_resident"]
    X = citizen_stats[features].fillna(0).values
    X_scaled = scaler.transform(X)

    citizen_stats["churn_proba"] = model.predict_proba(X_scaled)[:, 1].round(3)
    return citizen_stats[["citizen_id", "age_group", "primary_category", "churn_proba"]].sort_values(
        "churn_proba", ascending=False
    )


# ── デバッグ用 ─────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data.loader import load_activity_logs
    logs = load_activity_logs()
    if not logs.empty:
        churn = compute_churn_trends(logs)
        print(churn.head(10))
        print("\n年齢層別リスク:")
        print(churn_by_age_group(churn))
    else:
        print("activity_logs.csv が見つかりません。")
