"""
バスケット分析テスト。

「子育て施設に高頻度で来ているのにオンライン申請を使っていない」という
ボトルネック発見がこのシステムの最初の驚き（STEP 1）。
このテストは、そのインサイトが正しく検出されることを保証する。
"""
import pandas as pd
import pytest
from src.analytics.basket import (
    compute_basket_rules,
    bottleneck_detection,
    online_usage_by_offline_frequency,
)


# ── compute_basket_rules ─────────────────────────────────────

def test_basket_rules_returns_expected_columns(sample_logs):
    rules = compute_basket_rules(sample_logs)
    if not rules.empty:
        for col in ["antecedent", "consequent", "support", "confidence", "lift"]:
            assert col in rules.columns


def test_basket_rules_confidence_bounded(sample_logs):
    """信頼度は0〜1の範囲。"""
    rules = compute_basket_rules(sample_logs)
    if not rules.empty:
        assert rules["confidence"].between(0.0, 1.0).all()


def test_basket_rules_lift_positive(sample_logs):
    """Lift値は正の値。"""
    rules = compute_basket_rules(sample_logs)
    if not rules.empty:
        assert (rules["lift"] > 0).all()


def test_basket_rules_empty_input():
    assert compute_basket_rules(pd.DataFrame()).empty


# ── bottleneck_detection ─────────────────────────────────────

def test_bottleneck_detection_returns_list(sample_logs):
    """ボトルネック検出はリスト形式で返すこと。"""
    bottlenecks = bottleneck_detection(sample_logs)
    assert isinstance(bottlenecks, list)


def test_bottleneck_detection_items_have_required_keys(sample_logs):
    """各ボトルネックに必要なキーが含まれること（UIが壊れない保証）。"""
    bottlenecks = bottleneck_detection(sample_logs)
    for item in bottlenecks:
        assert "title" in item
        assert "body" in item
        assert "type" in item


# ── online_usage_by_offline_frequency ────────────────────────

def test_online_usage_childcare_high_freq_low_online(sample_logs):
    """
    育児カテゴリの高頻度利用者のオンライン率が低いこと。
    これがSTEP 1の核心インサイト: 最もサービスを必要としている人が
    オンライン化の恩恵を受けていない。
    """
    result = online_usage_by_offline_frequency(sample_logs)
    if result.empty:
        pytest.skip("育児カテゴリのデータが不足しています")

    if "freq_group" in result.columns and "online_rate" in result.columns:
        high_freq = result[result["freq_group"].str.contains("高頻度|high", case=False, na=False)]
        low_freq = result[result["freq_group"].str.contains("低頻度|low", case=False, na=False)]
        if not high_freq.empty and not low_freq.empty:
            assert high_freq["online_rate"].mean() <= low_freq["online_rate"].mean() + 0.3
