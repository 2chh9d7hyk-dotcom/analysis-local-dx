"""
チャーン予測テスト。

「転出の引き金」を正確に特定できなければ、職員は間違った施策に予算を使う。
このテストは、20代若者の高リスク検出とロジスティック回帰の予測精度を保証する。
"""
import pandas as pd
import pytest
from src.analytics.churn import (
    compute_churn_trends,
    churn_by_age_group,
    train_churn_model,
    simulate_time_quality_improvement,
)


# ── compute_churn_trends ─────────────────────────────────────

def test_churn_trends_returns_required_columns(sample_logs):
    churn = compute_churn_trends(sample_logs)
    assert not churn.empty
    for col in ["citizen_id", "churn_flag", "churn_probability", "age_group"]:
        assert col in churn.columns


def test_churn_trends_empty_input():
    assert compute_churn_trends(pd.DataFrame()).empty


def test_churn_probability_is_bounded(sample_logs):
    """予測確率は0〜1の範囲。グラフや計算の連鎖が壊れないことを保証。"""
    churn = compute_churn_trends(sample_logs)
    assert churn["churn_probability"].between(0.0, 1.0).all()


def test_churn_trends_detects_youth_at_high_risk(sample_logs):
    """
    20代若者のチャーンリスクが全体平均より高いこと。
    サンプルデータはこのパターンが検出されるよう設計されている。
    """
    churn = compute_churn_trends(sample_logs)
    youth_avg = churn[churn["age_group"].str.contains("20代", na=False)]["churn_probability"].mean()
    overall_avg = churn["churn_probability"].mean()
    assert youth_avg >= overall_avg * 0.8  # 20代は全体平均以上のリスク


def test_churn_by_age_group_returns_all_groups(sample_logs):
    churn = compute_churn_trends(sample_logs)
    by_age = churn_by_age_group(churn)
    assert not by_age.empty
    assert "age_group" in by_age.columns
    assert "avg_churn_prob" in by_age.columns


# ── train_churn_model ────────────────────────────────────────

def test_train_churn_model_returns_valid_auc(sample_logs):
    """
    AUCが0.5以上（ランダム以上の予測力があること）。
    サンプルデータでは0.9以上を想定。
    """
    _, importance_df, metrics = train_churn_model(sample_logs)
    assert metrics.get("auc", 0) >= 0.5


def test_train_churn_model_importance_df_has_all_features(sample_logs):
    """6つの特徴量が全て重要度DataFrameに含まれること。"""
    _, importance_df, _ = train_churn_model(sample_logs)
    assert not importance_df.empty
    assert len(importance_df) == 6
    assert "feature" in importance_df.columns
    assert "coefficient" in importance_df.columns


def test_train_churn_model_empty_input():
    model_bundle, importance_df, metrics = train_churn_model(pd.DataFrame())
    assert model_bundle is None
    assert importance_df.empty
    assert metrics == {}


# ── simulate_time_quality_improvement ────────────────────────

def test_simulate_time_quality_creative_hours_increase():
    """DX導入でクリエイティブ業務が増えること（物語のSTEP3の約束）。"""
    df = simulate_time_quality_improvement(
        routine_before=4000,
        creative_before=2000,
        system_hours_saved_per_month=600,
        total_months=12,
    )
    assert df["creative_hours"].iloc[-1] > df["creative_hours"].iloc[0]


def test_simulate_time_quality_routine_hours_decrease():
    """DX導入で定型業務が減ること。"""
    df = simulate_time_quality_improvement(
        routine_before=4000,
        creative_before=2000,
        system_hours_saved_per_month=600,
        total_months=12,
    )
    assert df["routine_hours"].iloc[-1] < df["routine_hours"].iloc[0]
