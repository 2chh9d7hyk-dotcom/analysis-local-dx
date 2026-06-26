"""
RFM分析テスト。

「どんな市民がいるか」を正確に把握できなければ、職員は正しい施策を打てない。
このテストは、市民ペルソナ分類と離脱リスクスコアの信頼性を保証する。
"""
import pandas as pd
import pytest
from src.analytics.rfm import (
    compute_rfm,
    segment_by_kmeans,
    persona_summary,
    high_churn_citizens,
    segment_summary,
)

REQUIRED_COLUMNS = {"citizen_id", "r_score", "f_score", "m_score", "rfm_total", "churn_risk"}
PERSONA_NAMES = {"地域の守り人", "眠れる可能性", "漂流する才能", "サイレント多数派"}


# ── compute_rfm ───────────────────────────────────────────────

def test_compute_rfm_returns_required_columns(sample_logs):
    rfm = compute_rfm(sample_logs)
    assert not rfm.empty
    assert REQUIRED_COLUMNS.issubset(rfm.columns)


def test_compute_rfm_empty_input():
    assert compute_rfm(pd.DataFrame()).empty


def test_churn_risk_is_bounded(sample_logs):
    """離脱リスクは必ず0〜1の範囲。グラフ軸が壊れないことを保証。"""
    rfm = compute_rfm(sample_logs)
    assert rfm["churn_risk"].between(0.0, 1.0).all()


def test_rfm_total_equals_sum_of_scores(sample_logs):
    rfm = compute_rfm(sample_logs)
    expected = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
    assert (rfm["rfm_total"] == expected).all()


def test_citizen_count_matches_unique_ids(sample_logs):
    """1市民1行になっていること（集計漏れ・重複がないこと）。"""
    rfm = compute_rfm(sample_logs)
    assert len(rfm) == sample_logs["citizen_id"].nunique()


# ── segment_by_kmeans ────────────────────────────────────────

def test_segment_by_kmeans_assigns_known_persona_names(sample_logs):
    """4つのペルソナ名が正しく使われていること（職員が読む名前が壊れていない保証）。"""
    rfm = compute_rfm(sample_logs)
    segmented = segment_by_kmeans(rfm)
    assert "persona" in segmented.columns
    assert set(segmented["persona"].unique()).issubset(PERSONA_NAMES)


def test_segment_by_kmeans_no_null_personas(sample_logs):
    rfm = compute_rfm(sample_logs)
    segmented = segment_by_kmeans(rfm)
    assert segmented["persona"].notna().all()


def test_segment_by_kmeans_empty_input():
    assert segment_by_kmeans(pd.DataFrame()).empty


# ── high_churn_citizens ──────────────────────────────────────

def test_high_churn_citizens_all_above_threshold(sample_logs):
    rfm = compute_rfm(sample_logs)
    threshold = 0.65
    high_risk = high_churn_citizens(rfm, threshold=threshold)
    if not high_risk.empty:
        assert (high_risk["churn_risk"] >= threshold).all()


def test_high_churn_citizens_sorted_descending(sample_logs):
    rfm = compute_rfm(sample_logs)
    high_risk = high_churn_citizens(rfm)
    if len(high_risk) > 1:
        assert high_risk["churn_risk"].is_monotonic_decreasing


# ── persona_summary ──────────────────────────────────────────

def test_persona_summary_counts_sum_to_total(sample_logs):
    rfm = compute_rfm(sample_logs)
    segmented = segment_by_kmeans(rfm)
    summary = persona_summary(segmented)
    assert summary["citizen_count"].sum() == len(segmented)
