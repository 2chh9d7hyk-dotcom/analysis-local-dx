"""NES重点領域ダッシュボード — スコア推移・レーダーチャート・比較分析。"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.theme import inject_theme, set_page_config
from src.ui.components import (
    hero_section, section_header, score_card,
    alert_discovery, spacer, divider,
)
from src.ui.charts import (
    radar_chart, line_chart, grouped_bar_chart,
    stacked_bar_time_allocation,
)
from src.data.loader import (
    get_active_indicators, get_active_staff_time, active_municipality_name,
    get_latest_year, get_year_delta, load_reference_avg,
)
from src.analytics.indicators import (
    get_latest_indicators, compute_yoy_change,
    benchmark_comparison, score_trend_df, priority_matrix,
)
from src.ui.components import priority_badge, nes_area_badge
from src.config import COLORS, NES_AREAS

set_page_config("NES重点領域ダッシュボード", "📊")
inject_theme()

# ── データ読み込み ────────────────────────────────────────────
muni_name = active_municipality_name()
ind_df = get_active_indicators()
staff_df = get_active_staff_time()
latest = get_latest_indicators(ind_df)
yoy = compute_yoy_change(ind_df)
latest_year = get_latest_year(ind_df) or 2024
ref_avg = load_reference_avg(latest_year)

# ── ヒーロー ──────────────────────────────────────────────────
hero_section(
    title="NES重点領域ダッシュボード",
    subtitle=(
        f"オンライン化・AI/RPA・データ活用の各領域で{muni_name}がどこにいるのか。"
        "全国平均・県平均と比較しながら、真の課題を客観的に可視化します。"
    ),
    badge="📊 Evidence-Based Policy Making",
)

# ── スコアカード（最新年度） ──────────────────────────────────
if latest:
    section_header(f"{latest_year}年度 NESスコアサマリー", "各領域のスコア（0〜100）")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        score_card(latest["online"], "オンライン化", COLORS["online"])
    with col2:
        score_card(latest["ai_rpa"], "AI/RPA", COLORS["ai_rpa"])
    with col3:
        score_card(latest["data"], "データ活用", COLORS["data"])
    with col4:
        score_card(latest["total"], "総合スコア", COLORS["positive"])

    spacer(8)

    # 前年比デルタ表示
    if yoy:
        delta_cols = st.columns(4)
        deltas = [
            ("オンライン化", yoy.get("online", 0), COLORS["online"]),
            ("AI/RPA", yoy.get("ai_rpa", 0), COLORS["ai_rpa"]),
            ("データ活用", yoy.get("data", 0), COLORS["data"]),
            ("総合", yoy.get("total", 0), COLORS["positive"]),
        ]
        for col, (label, delta, color) in zip(delta_cols, deltas):
            with col:
                arrow = "▲" if delta > 0 else "▼" if delta < 0 else "―"
                delta_color = COLORS["positive"] if delta > 0 else COLORS["danger"] if delta < 0 else COLORS["text_muted"]
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 8px;">
                        <span style="font-size: 1.1rem; font-weight: 700; color: {delta_color};">
                            {arrow} {abs(delta):.1f}pt
                        </span>
                        <div style="font-size: 0.72rem; color: #9CA3AF; margin-top: 2px;">前年比 ({label})</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
else:
    st.info("NES指標データが見つかりません。データ管理ページからCSVをアップロードしてください。")

divider()

# ── レーダーチャート + 全国比較 ───────────────────────────────
section_header("全国・県平均との比較", "現在地の客観的把握")

col_radar, col_bar = st.columns([1, 1])

with col_radar:
    if not ind_df.empty:
        national_avg = ref_avg["national"]
        pref_avg = ref_avg["pref"]
        bench_df = benchmark_comparison(ind_df, national_avg=national_avg, prefecture_avg=pref_avg)
        categories = ["オンライン化", "AI/RPA", "データ活用"]

        otama_vals = [
            latest["online"] if latest else 0,
            latest["ai_rpa"] if latest else 0,
            latest["data"] if latest else 0,
        ]

        fig_radar = radar_chart(
            categories=categories,
            values_list=[
                (muni_name, otama_vals, COLORS["online"]),
                ("全国平均", [national_avg["online"], national_avg["ai_rpa"], national_avg["data"]], "#9CA3AF"),
                ("県平均", [pref_avg["online"], pref_avg["ai_rpa"], pref_avg["data"]], COLORS["warning"]),
            ],
            title="NES重点領域 レーダーチャート",
            height=380,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

with col_bar:
    if not ind_df.empty and latest:
        national_avg = ref_avg["national"]
        pref_avg = ref_avg["pref"]
        bench_df = benchmark_comparison(ind_df, national_avg=national_avg, prefecture_avg=pref_avg)
        if not bench_df.empty:
            fig_bar = grouped_bar_chart(
                df=bench_df,
                x="area",
                y_cols=["大玉村", "全国平均", "県平均"],
                labels={"大玉村": muni_name, "全国平均": "全国平均", "県平均": "県平均"},
                colors=[COLORS["online"], "#9CA3AF", COLORS["warning"]],
                title="NES領域別スコア比較",
                height=380,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

divider()

# ── スコア推移折れ線グラフ ────────────────────────────────────
section_header("スコア推移（時系列）", "2021年からの4ヵ年変化")

if not ind_df.empty:
    trend_df = score_trend_df(ind_df)
    trend_df["target_year"] = trend_df["target_year"].astype(str) + "年"

    fig_line = line_chart(
        df=trend_df,
        x="target_year",
        y_cols=["online_score", "ai_rpa_score", "data_utilization_score", "total_score"],
        labels={
            "online_score": "オンライン化",
            "ai_rpa_score": "AI/RPA",
            "data_utilization_score": "データ活用",
            "total_score": "総合スコア",
        },
        colors=[COLORS["online"], COLORS["ai_rpa"], COLORS["data"], COLORS["positive"]],
        title="NES重点領域スコア推移",
        height=360,
        area=True,
    )
    st.plotly_chart(fig_line, use_container_width=True)

divider()

# ── 職員の時間配分 ─────────────────────────────────────────────
section_header("職員の時間配分の変化", "DX推進が「時間の質」をどう変えたか")

if not staff_df.empty:
    col_stack, col_text = st.columns([3, 2])
    with col_stack:
        fig_stack = stacked_bar_time_allocation(staff_df)
        st.plotly_chart(fig_stack, use_container_width=True)
    with col_text:
        spacer(24)
        latest_staff = staff_df.iloc[-1]
        routine_pct = latest_staff["routine_hours"] / latest_staff["total_workforce_hours"] * 100
        creative_pct = latest_staff["creative_hours"] / latest_staff["total_workforce_hours"] * 100

        st.markdown(
            f"""
            <div class="dx-card">
                <div style="font-size: 0.85rem; font-weight: 700; color: #1F2937; margin-bottom: 16px;">
                    {int(latest_staff['target_year'])}年度の時間配分
                </div>
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-size: 0.8rem; color: #6B7280;">定型業務</span>
                        <span style="font-size: 0.9rem; font-weight: 700; color: #EF4444;">
                            {latest_staff['routine_hours']:.0f}時間/月 ({routine_pct:.0f}%)
                        </span>
                    </div>
                    <div class="score-bar-track">
                        <div class="score-bar-fill" style="width:{routine_pct}%; background:#EF4444;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-size: 0.8rem; color: #6B7280;">クリエイティブ業務</span>
                        <span style="font-size: 0.9rem; font-weight: 700; color: #22C55E;">
                            {latest_staff['creative_hours']:.0f}時間/月 ({creative_pct:.0f}%)
                        </span>
                    </div>
                    <div class="score-bar-track">
                        <div class="score-bar-fill" style="width:{creative_pct}%; background:#22C55E;"></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

divider()

# ── 優先度マトリクス ──────────────────────────────────────────
section_header("改善優先度マトリクス", "どの領域から取り組むべきか")

if not ind_df.empty:
    priorities = priority_matrix(ind_df)
    for p in priorities:
        badge_html = priority_badge(p["priority_level"])
        area_badge = nes_area_badge(p["key"])
        yoy_val = p.get("yoy", 0)
        yoy_color = COLORS["positive"] if yoy_val >= 0 else COLORS["danger"]
        st.markdown(
            f"""
            <div class="dx-card-sm" style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                <div style="min-width: 120px;">{area_badge}</div>
                <div style="flex: 1;">
                    <div style="font-size: 0.9rem; font-weight: 600; color: #1F2937;">
                        現在スコア: <span style="color: {p['color']};">{p['score']:.0f}pt</span>
                        &nbsp;|&nbsp;
                        改善余地: <strong>{p['improvement_room']:.0f}pt</strong>
                        &nbsp;|&nbsp;
                        前年比: <span style="color: {yoy_color};">
                            {"▲" if yoy_val >= 0 else "▼"}{abs(yoy_val):.1f}pt
                        </span>
                    </div>
                </div>
                <div>{badge_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    weakest = min(priorities, key=lambda x: x["score"])
    alert_discovery(
        title=f"最重点改善領域: {weakest['area']}（スコア {weakest['score']:.0f}pt）",
        body=(
            f"「{weakest['area']}」は改善余地が{weakest['improvement_room']:.0f}ptと最大であり、"
            f"年間成長率も他領域と比較して低い水準にあります。"
            "次ページ「新発見と未来提案」で、具体的なシステム・政策の提案を確認できます。"
        ),
    )

divider()

col_prev, col_spacer, col_next = st.columns([1, 4, 1])
with col_prev:
    if st.button("← ホームへ戻る", use_container_width=True):
        st.switch_page("pages/home.py")
with col_next:
    if st.button("新発見へ →", type="primary", use_container_width=True):
        st.switch_page("pages/improvement_proposal.py")
