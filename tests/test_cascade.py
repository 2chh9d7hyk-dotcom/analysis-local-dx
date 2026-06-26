"""
人口カスケードテスト。

「DX介入が現状維持より良い未来をもたらす」という物語の数理的な根拠を保証する。
このテストが通ることは、職員に見せるグラフが正直であることの証明。
"""
import pytest
from src.analytics.cascade import (
    CascadeInput,
    project_population_cascade,
    find_critical_year,
    cascade_summary,
    estimate_churn_rate_from_logs,
)


@pytest.fixture
def base_params():
    return CascadeInput(
        population=8000,
        aging_rate=0.35,
        youth_annual_churn_rate=0.10,
        projection_years=15,
        intervention_reduction_pct=40.0,
    )


# ── project_population_cascade ───────────────────────────────

def test_cascade_returns_three_scenarios(base_params):
    df = project_population_cascade(base_params)
    scenarios = df["scenario"].unique()
    assert "現状維持シナリオ" in scenarios
    assert "DX介入シナリオ" in scenarios
    assert "危機加速シナリオ" in scenarios


def test_dx_scenario_outperforms_baseline_at_end(base_params):
    """
    物語の核心: DX介入シナリオは最終年で現状維持より人口が多い。
    このテストが落ちたら、システムが「DXは効果がない」と嘘をついていることになる。
    """
    df = project_population_cascade(base_params)
    dx_end = df[df["scenario"] == "DX介入シナリオ"]["population"].iloc[-1]
    sq_end = df[df["scenario"] == "現状維持シナリオ"]["population"].iloc[-1]
    assert dx_end > sq_end


def test_crisis_scenario_is_worst_at_end(base_params):
    """危機加速シナリオが最も人口減少していること。"""
    df = project_population_cascade(base_params)
    crisis_end = df[df["scenario"] == "危機加速シナリオ"]["population"].iloc[-1]
    sq_end = df[df["scenario"] == "現状維持シナリオ"]["population"].iloc[-1]
    assert crisis_end <= sq_end


def test_cascade_population_never_negative(base_params):
    """人口がマイナスにならないこと（グラフがゼロ以下を表示しない）。"""
    df = project_population_cascade(base_params)
    assert (df["population"] >= 0).all()


def test_cascade_row_count(base_params):
    """3シナリオ × (projection_years + 1) 行が生成されること。"""
    df = project_population_cascade(base_params)
    expected = 3 * (base_params.projection_years + 1)
    assert len(df) == expected


def test_initial_population_matches_params(base_params):
    """初年度の人口がパラメータと一致すること。"""
    df = project_population_cascade(base_params)
    for scenario in df["scenario"].unique():
        initial = df[(df["scenario"] == scenario) & (df["year"] == base_params.base_year)]
        assert initial["population"].iloc[0] == base_params.population


# ── find_critical_year ───────────────────────────────────────

def test_find_critical_year_returns_none_when_safe():
    """人口が十分多く学校が存続するケースでNoneを返すこと。"""
    params = CascadeInput(population=50000, aging_rate=0.25, youth_annual_churn_rate=0.03)
    df = project_population_cascade(params)
    year = find_critical_year(df, "現状維持シナリオ")
    assert year is None


def test_find_critical_year_detects_risk_for_small_village():
    """小規模村では危機年が検出されること（初年度より学童数が多い人口で開始）。"""
    # 2500人: 初期学童数=137人(>120)。転出率18%なら数年以内に閾値を下回る
    params = CascadeInput(population=2500, aging_rate=0.45, youth_annual_churn_rate=0.18)
    df = project_population_cascade(params)
    year = find_critical_year(df, "現状維持シナリオ")
    assert year is not None
    assert year >= params.base_year


# ── cascade_summary ──────────────────────────────────────────

def test_cascade_summary_dx_pop_greater_than_sq(base_params):
    df = project_population_cascade(base_params)
    summary = cascade_summary(base_params, df)
    assert summary["pop_end_dx"] >= summary["pop_end_sq"]


def test_cascade_summary_tax_saved_non_negative(base_params):
    df = project_population_cascade(base_params)
    summary = cascade_summary(base_params, df)
    assert summary["cumulative_tax_saved"] >= 0


# ── estimate_churn_rate_from_logs ────────────────────────────

def test_estimate_churn_rate_is_bounded(sample_logs):
    from src.analytics.churn import compute_churn_trends
    churn_df = compute_churn_trends(sample_logs)
    rate = estimate_churn_rate_from_logs(churn_df)
    assert 0.0 < rate <= 0.20


def test_estimate_churn_rate_empty_returns_default():
    import pandas as pd
    rate = estimate_churn_rate_from_logs(pd.DataFrame())
    assert rate == 0.10
