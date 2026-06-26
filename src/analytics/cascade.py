"""
人口カスケード分析モジュール。

若者の離脱が引き起こす自己強化的な人口減少ループを定量化する。
「19%が危機的状態」という数字を「学校が閉まるのは2032年」という
具体的な未来に変換することで、職員の行動を促す。

カスケードのメカニズム:
  若者の転出 → 出生数の減少 → 学童数の減少
    → 学校統廃合 → 残った若者もさらに転出（自己強化ループ）

このモジュールは Streamlit に一切依存しない純粋な分析層。
"""
from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


# ── 定数 ─────────────────────────────────────────────────────

# 日本の地方農村部の人口動態ベースライン（総務省・厚労省統計参照）
_ANNUAL_BIRTH_RATE    = 0.0060  # 出生率: 1000人に6人（地方平均）
_ANNUAL_DEATH_RATE    = 0.0130  # 死亡率: 1000人に13人（高齢化考慮）
_SCHOOL_CHILDREN_RATE = 0.055   # 小学校児童（6-11歳）の人口比
_SCHOOL_VIABILITY_MIN = 120     # 全学年合計でこれを下回ると教育環境悪化リスク（1学年20人相当）
_YOUTH_RATIO_OF_WORKING_AGE = 0.38  # 20-39歳は生産年齢人口の約38%


@dataclass
class CascadeInput:
    """人口カスケード分析の入力パラメータ。"""
    population: int              # 現在人口
    aging_rate: float            # 高齢化率（0-1）
    youth_annual_churn_rate: float   # 若者の年間転出率（0-1）
    base_year: int = 2024
    projection_years: int = 15
    # DX介入でチャーン率をどれだけ削減できるか（0-100%）
    intervention_reduction_pct: float = 40.0
    # 1人あたり年間税収（円）
    per_capita_tax: int = 280_000


def estimate_churn_rate_from_logs(churn_df: pd.DataFrame) -> float:
    """
    churn.compute_churn_trends() の結果から若者の年間転出率を推定する。

    churn_flag はエンゲージメント低下の警告シグナル（実際の転出率より高く出る）。
    地方農村部の実績データ（総務省統計）をベースに:
      - ベース転出率: 3% / 年（地方自治体平均）
      - エンゲージメント低下フラグが立つほど転出リスク増加
      - 上限: 20%（非常に深刻な状態でも現実的な上限）
    """
    if churn_df.empty:
        return 0.10  # データなしのデフォルト: 10%

    youth_df = churn_df[churn_df["age_group"].str.contains("20代", na=False)]
    if youth_df.empty:
        flag_rate = float(churn_df["churn_flag"].mean())
    else:
        flag_rate = float(youth_df["churn_flag"].mean())

    # 実績ベースの換算: ベース3% + フラグ率に比例した追加リスク
    annual_rate = 0.03 + flag_rate * 0.15
    return min(annual_rate, 0.20)


def _estimate_youth_population(population: int, aging_rate: float) -> float:
    """20-39歳の若者人口を推定する。"""
    working_age_rate = max(1.0 - aging_rate - 0.12, 0.20)  # 高齢者 + 子ども(12%)を除く
    return population * working_age_rate * _YOUTH_RATIO_OF_WORKING_AGE


def project_population_cascade(params: CascadeInput) -> pd.DataFrame:
    """
    3シナリオの人口推移を15年分投影する。

    Scenarios:
      現状維持  — チャーン率が変わらず継続する
      DX介入    — 提案システムがチャーン率をN%削減する
      危機加速  — 学校閉鎖を契機にチャーン率が連鎖的に悪化する

    Returns columns:
      year, scenario, population, youth_population, school_children,
      scenario_color, school_closed
    """
    youth_pop_0      = _estimate_youth_population(params.population, params.aging_rate)
    school_children_0 = params.population * _SCHOOL_CHILDREN_RATE

    scenarios = [
        {
            "name":  "現状維持シナリオ",
            "color": "#EF4444",
            "base_churn": params.youth_annual_churn_rate,
            "accelerate": False,
        },
        {
            "name":  "DX介入シナリオ",
            "color": "#22C55E",
            "base_churn": params.youth_annual_churn_rate * (1 - params.intervention_reduction_pct / 100),
            "accelerate": False,
        },
        {
            "name":  "危機加速シナリオ",
            "color": "#F97316",
            "base_churn": params.youth_annual_churn_rate,
            "accelerate": True,
        },
    ]

    rows: list[dict] = []

    for sc in scenarios:
        pop         = float(params.population)
        youth_pop   = float(youth_pop_0)
        school_ch   = float(school_children_0)
        churn_rate  = sc["base_churn"]
        closed      = False

        for yr in range(params.projection_years + 1):
            rows.append({
                "year":           params.base_year + yr,
                "scenario":       sc["name"],
                "population":     round(pop),
                "youth_population": round(youth_pop),
                "school_children":  round(school_ch),
                "scenario_color": sc["color"],
                "school_closed":  closed,
            })

            if yr < params.projection_years:
                # 出生: 若者人口の減少とともに出生も減少
                birth_factor = max(youth_pop / youth_pop_0, 0.0)
                births  = pop * _ANNUAL_BIRTH_RATE * birth_factor
                deaths  = pop * _ANNUAL_DEATH_RATE
                youth_out = youth_pop * churn_rate

                # 危機加速シナリオ: 学校閉鎖トリガー
                if sc["accelerate"] and school_ch < _SCHOOL_VIABILITY_MIN and not closed:
                    closed = True
                    churn_rate = min(churn_rate * 1.6, 0.50)

                pop       = max(pop + births - deaths - youth_out, 0)
                youth_pop = max(youth_pop - youth_out + births * 0.4, 0)
                school_ch = max(pop * _SCHOOL_CHILDREN_RATE, 0)

    return pd.DataFrame(rows)


def find_critical_year(
    cascade_df: pd.DataFrame,
    scenario: str = "現状維持シナリオ",
    threshold: int = _SCHOOL_VIABILITY_MIN,
) -> int | None:
    """
    指定シナリオで学校存続の限界点（school_children < threshold）に
    達する最初の年を返す。達しない場合は None。
    """
    sc_df = cascade_df[cascade_df["scenario"] == scenario]
    below = sc_df[sc_df["school_children"] < threshold]
    return int(below["year"].min()) if not below.empty else None


def compute_lost_potential(
    cascade_df: pd.DataFrame,
    per_capita_tax: int = 280_000,
) -> pd.DataFrame:
    """
    現状維持 vs DX介入の人口差から、DX介入によって守られる累積人口・税収を試算する。

    Returns columns: year, population_saved, cumulative_tax_saved
    """
    sq = cascade_df[cascade_df["scenario"] == "現状維持シナリオ"].set_index("year")["population"]
    dx = cascade_df[cascade_df["scenario"] == "DX介入シナリオ"].set_index("year")["population"]
    common = sq.index.intersection(dx.index)

    rows = []
    cumulative = 0
    for year in sorted(common):
        saved = max(int(dx[year]) - int(sq[year]), 0)
        cumulative += saved * per_capita_tax
        rows.append({
            "year": year,
            "population_saved": saved,
            "cumulative_tax_saved": cumulative,
        })
    return pd.DataFrame(rows)


def cascade_summary(params: CascadeInput, cascade_df: pd.DataFrame) -> dict:
    """
    カスケード分析のサマリーをdict形式で返す（UIでのKPIカード表示用）。
    """
    critical_status_quo = find_critical_year(cascade_df, "現状維持シナリオ")
    critical_dx         = find_critical_year(cascade_df, "DX介入シナリオ")
    lost_df             = compute_lost_potential(cascade_df, params.per_capita_tax)

    sq_df = cascade_df[cascade_df["scenario"] == "現状維持シナリオ"]
    dx_df = cascade_df[cascade_df["scenario"] == "DX介入シナリオ"]

    pop_end_sq = int(sq_df["population"].iloc[-1])
    pop_end_dx = int(dx_df["population"].iloc[-1])
    pop_decline_pct = round((params.population - pop_end_sq) / params.population * 100, 1)

    # 累積人口差（「守られた人口・年数」の積分）
    sq_series = sq_df.set_index("year")["population"]
    dx_series = dx_df.set_index("year")["population"]
    cumulative_pop_saved = int(sum(
        max(dx_series.get(y, 0) - sq_series.get(y, 0), 0)
        for y in sq_series.index
    ))

    return {
        "current_population":       params.population,
        "current_youth_pop":        round(_estimate_youth_population(params.population, params.aging_rate)),
        "youth_churn_rate_pct":     round(params.youth_annual_churn_rate * 100, 1),
        "school_viability_year":    critical_status_quo,
        "dx_school_year":           critical_dx,
        "pop_end_sq":               pop_end_sq,
        "pop_end_dx":               pop_end_dx,
        "pop_decline_pct_sq":       pop_decline_pct,
        "pop_decline_pct_dx":       round((params.population - pop_end_dx) / params.population * 100, 1),
        "pop_saved_at_end":         max(pop_end_dx - pop_end_sq, 0),
        "cumulative_pop_saved":     cumulative_pop_saved,
        "cumulative_tax_saved":     int(lost_df["cumulative_tax_saved"].iloc[-1]) if not lost_df.empty else 0,
        "projection_years":         params.projection_years,
    }
