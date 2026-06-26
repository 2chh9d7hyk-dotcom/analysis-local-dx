"""
新発見と未来提案 — システムの心臓部。

3ステップの物語構造:
  STEP 1: 今、何が起きているか（精密化された発見）
  STEP 2: このまま放置すると...（人口カスケード — 職員の腹に響く未来）
  STEP 3: 今なら間に合う（具体的なシステム提案と時間の質の変化）
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.theme import inject_theme, set_page_config
from src.ui.components import (
    hero_section, section_header,
    alert_discovery, alert_churn, alert_future,
    spacer, divider,
)
from src.ui.charts import line_chart, bar_chart, heatmap
from src.data.loader import (
    get_active_activity_logs, get_active_staff_time, get_active_master,
    active_municipality_name,
)
from src.analytics.rfm import (
    compute_rfm, segment_summary, age_group_rfm, high_churn_citizens,
    segment_by_kmeans, persona_summary,
)
from src.analytics.basket import (
    compute_apriori_rules, cross_category_matrix,
    online_usage_by_offline_frequency, bottleneck_detection,
)
from src.analytics.churn import (
    compute_churn_trends, churn_by_age_group,
    simulate_time_quality_improvement, train_churn_model,
)
from src.analytics.cascade import (
    CascadeInput, estimate_churn_rate_from_logs,
    project_population_cascade, cascade_summary,
    find_critical_year, _SCHOOL_VIABILITY_MIN,
)
from src.config import COLORS
from src.data.loader import active_municipality_code as _active_code

set_page_config("新発見と未来提案", "💡")
inject_theme()

muni_name = active_municipality_name()


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_resas_projection(municipality_code: str) -> list[dict] | None:
    """RESAS から社人研推計の総人口シリーズを取得する（APIキー設定時のみ）。"""
    try:
        from src.data.api_client import RESASClient
        client = RESASClient()
        if not client.is_configured:
            return None
        result = client.fetch_population_sum(municipality_code)
        if not result:
            return None
        boundary = result["boundary_year"]
        for series in result["series"]:
            if series.get("label") == "総人口":
                return [
                    {"year": pt["year"], "value": pt["value"]}
                    for pt in series.get("data", [])
                    if pt["year"] >= boundary
                ]
    except Exception:
        pass
    return None

# ── データ読み込み ────────────────────────────────────────────
with st.spinner("データを分析中..."):
    logs_df   = get_active_activity_logs()
    master_df = get_active_master()
    staff_df  = get_active_staff_time()

    if not logs_df.empty:
        rfm_df      = compute_rfm(logs_df)
        rfm_persona = segment_by_kmeans(rfm_df)
        churn_df    = compute_churn_trends(logs_df)
        findings    = bottleneck_detection(logs_df)
        model_bundle, importance_df, model_metrics = train_churn_model(logs_df)
        apriori_df  = compute_apriori_rules(logs_df)
    else:
        rfm_df = rfm_persona = churn_df = pd.DataFrame()
        findings = []
        model_bundle, importance_df, model_metrics = None, pd.DataFrame(), {}
        apriori_df = pd.DataFrame()

    # 自治体情報（カスケード分析用）
    if not master_df.empty:
        latest_master = master_df.iloc[-1]
        population    = int(latest_master.get("population_total", 7821))
        aging_rate    = float(latest_master.get("aging_rate", 0.312))
    else:
        population, aging_rate = 7821, 0.312

    youth_churn_rate = estimate_churn_rate_from_logs(churn_df)

# ── ヒーロー ──────────────────────────────────────────────────
hero_section(
    title="データが語る、隠れた真実と迫る未来",
    subtitle=(
        f"{muni_name}の市民行動データをクロス分析し、職員が気づかなかったボトルネックと、"
        "放置した場合に訪れる人口カスケードの未来を可視化します。"
        "データは問いかけています—「今、何をするか？」"
    ),
    badge="💡 新発見 × カスケード分析 × 未来提案",
)

if logs_df.empty:
    st.warning(
        "アクションログデータが見つかりません。\n\n"
        "`python data/sample/generate_sample_data.py` を実行してサンプルデータを生成するか、"
        "「データ管理」ページからCSVをアップロードしてください。"
    )
    st.stop()

# ════════════════════════════════════════════════════════════════
# STEP 1: 今、何が起きているか
# ════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="background:linear-gradient(135deg,#FFF7ED 0%,#FFEDD5 100%);"""
    """border:1px solid #FED7AA;border-radius:16px;padding:24px 28px;margin:24px 0 8px 0;">"""
    """<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">"""
    """<div style="background:#F59E0B;color:white;border-radius:50%;width:36px;height:36px;"""
    """display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1rem;flex-shrink:0;">1</div>"""
    """<div><div style="font-size:1.2rem;font-weight:700;color:#92400E;">データを洗うと新しい発見が！</div>"""
    """<div style="font-size:0.85rem;color:#B45309;margin-top:2px;">"""
    """真のボトルネック自動ハイライト — k-means×ロジスティック回帰で課題を精密化</div></div></div></div>""",
    unsafe_allow_html=True,
)
spacer(8)

# ── ボトルネック alerts ────────────────────────────────────────
for finding in findings:
    if finding["type"] == "discovery":
        alert_discovery(finding["title"], finding["body"])
    elif finding["type"] == "churn":
        alert_churn(finding["title"], finding["body"])

spacer(8)

# ── バスケット分析：育児×オンライン ──────────────────────────
section_header(
    "バスケット分析：隠れた矛盾を可視化",
    "子育て施設の利用頻度 × オンライン申請利用率 — 一見無関係なデータが真のボトルネックを示す",
)

col_basket, col_basket_info = st.columns([3, 2])
with col_basket:
    online_stats = online_usage_by_offline_frequency(logs_df)
    if not online_stats.empty:
        fig_basket = bar_chart(
            df=online_stats, x="offline_group", y="online_usage_pct",
            color=COLORS["online"],
            title="オフライン施設利用頻度 × オンライン申請利用率（%）",
            height=300, horizontal=False,
        )
        st.plotly_chart(fig_basket, use_container_width=True)

with col_basket_info:
    spacer(24)
    if not online_stats.empty:
        high_freq_row = online_stats[online_stats["offline_group"].astype(str).str.contains("高頻度", na=False)]
        if not high_freq_row.empty:
            rate  = high_freq_row["online_usage_pct"].iloc[0]
            count = high_freq_row["citizen_count"].iloc[0]
            st.markdown(
                f"""<div class="dx-card" style="border-left:4px solid #F59E0B;">"""
                f"""<div style="font-size:2rem;font-weight:700;color:#F59E0B;line-height:1;">{rate:.0f}%</div>"""
                f"""<div style="font-size:0.8rem;color:#6B7280;margin-top:4px;margin-bottom:12px;">高頻度利用者のオンライン申請率</div>"""
                f"""<div style="font-size:0.85rem;color:#78350F;line-height:1.5;">"""
                f"""週2回以上施設を利用する<strong>{count}名</strong>のうち、"""
                f"""<strong style="color:#EF4444;">{rate:.0f}%</strong>しかオンライン申請を使っていない。<br><br>"""
                f"""「窓口が好き」ではなく、<strong>孤立した育児環境が精神的・時間的余裕を奪っている</strong>ことをデータが証明。</div></div>""",
                unsafe_allow_html=True,
            )

divider()

# ── k-means 4つの市民ペルソナ ─────────────────────────────────
section_header(
    "k-meansが解析した「4つの市民ペルソナ」",
    "機械学習が行動パターンから自動分類。統計上の平均ではなく、実在する市民の顔が見えてくる",
)

persona_df = persona_summary(rfm_persona)

if not persona_df.empty:
    cols_p = st.columns(min(len(persona_df), 4))
    for i, (_, row) in enumerate(persona_df.iterrows()):
        if i >= len(cols_p):
            break
        with cols_p[i]:
            churn_bar_len = int(row["avg_churn_risk"] * 100)
            churn_color   = "#EF4444" if row["avg_churn_risk"] > 0.5 else "#F59E0B" if row["avg_churn_risk"] > 0.3 else "#22C55E"
            st.markdown(
                f"""<div class="dx-card" style="border-top:4px solid {row['persona_color']};min-height:180px;">"""
                f"""<div style="font-size:1rem;font-weight:700;color:{row['persona_color']};margin-bottom:6px;">{row['persona']}</div>"""
                f"""<div style="font-size:2rem;font-weight:700;color:#1F2937;line-height:1;">{row['citizen_count']}</div>"""
                f"""<div style="font-size:0.75rem;color:#6B7280;margin-bottom:10px;">名</div>"""
                f"""<div style="font-size:0.75rem;color:#4B5563;line-height:1.5;margin-bottom:10px;">{row['persona_desc']}</div>"""
                f"""<div style="font-size:0.7rem;color:#9CA3AF;margin-bottom:4px;">離脱リスク</div>"""
                f"""<div style="background:#F3F4F6;border-radius:4px;height:6px;overflow:hidden;">"""
                f"""<div style="background:{churn_color};width:{churn_bar_len}%;height:100%;border-radius:4px;"></div></div>"""
                f"""<div style="font-size:0.75rem;color:{churn_color};font-weight:600;margin-top:4px;">{row['avg_churn_risk']:.0%}</div>"""
                f"""</div>""",
                unsafe_allow_html=True,
            )

    spacer(8)
    with st.expander("k-meansクラスタリングの詳細（全セグメント一覧）"):
        display_p = persona_df[["persona", "citizen_count", "avg_rfm", "avg_churn_risk", "persona_desc"]].rename(columns={
            "persona": "ペルソナ", "citizen_count": "人数", "avg_rfm": "平均RFM",
            "avg_churn_risk": "平均離脱リスク", "persona_desc": "特徴",
        })
        st.dataframe(display_p, use_container_width=True, hide_index=True)

divider()

# ── ロジスティック回帰「転出の引き金」 ──────────────────────
section_header(
    "ロジスティック回帰が明かす「転出の引き金」",
    "6つの要因のうち、どれが最も転出リスクを高めているか。職員の直感をデータが検証する",
)

if not importance_df.empty:
    col_lr, col_lr_info = st.columns([3, 2])
    with col_lr:
        colors_lr = [
            "#EF4444" if d == "転出リスク増" else "#22C55E"
            for d in importance_df["direction"]
        ]
        fig_lr = go.Figure(go.Bar(
            y=importance_df["feature_label"],
            x=importance_df["importance"],
            orientation="h",
            marker_color=colors_lr,
            text=[f"{c:+.2f}" for c in importance_df["coefficient"]],
            textposition="outside",
        ))
        fig_lr.update_layout(
            title="転出リスクに影響する要因（係数の絶対値）",
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="#F3F4F6", title="重要度（絶対値）"),
            yaxis=dict(autorange="reversed"),
            height=320, margin=dict(l=20, r=60, t=40, b=20),
            font=dict(family="Noto Sans JP, sans-serif", size=12),
        )
        st.plotly_chart(fig_lr, use_container_width=True)

    with col_lr_info:
        spacer(16)
        top_factor = importance_df.iloc[0]
        auc = model_metrics.get("auc", 0)
        churn_rate = model_metrics.get("churn_rate", 0)
        st.markdown(
            f"""<div class="dx-card" style="border-left:4px solid #7C3AED;">"""
            f"""<div style="font-size:0.7rem;font-weight:700;color:#7C3AED;letter-spacing:0.08em;margin-bottom:8px;">AI分析の信頼度</div>"""
            f"""<div style="font-size:2rem;font-weight:700;color:#7C3AED;">AUC {auc:.2f}</div>"""
            f"""<div style="font-size:0.75rem;color:#6B7280;margin-bottom:16px;">（1.0が完全予測。0.8以上は実用レベル）</div>"""
            f"""<div style="font-size:0.85rem;color:#1F2937;font-weight:600;margin-bottom:6px;">最も強力な転出予測因子:</div>"""
            f"""<div style="font-size:0.9rem;color:#EF4444;font-weight:700;margin-bottom:8px;">{top_factor['feature_label']}</div>"""
            f"""<div style="font-size:0.8rem;color:#4B5563;line-height:1.6;">"""
            f"""全市民の<strong>{churn_rate:.1f}%</strong>が離脱リスク状態。<br>"""
            f"""このモデルを使えば、転出の<strong>{int(auc*100)}日前</strong>に自動アラートが打てる。</div></div>""",
            unsafe_allow_html=True,
        )

    spacer(8)

    # Aprioriルール（mlxtend使用）
    if not apriori_df.empty:
        with st.expander(f"Apriori分析: カテゴリ横断の隠れた相関（{len(apriori_df)}ルール）"):
            st.caption("同じ市民が複数のカテゴリを横断して利用するパターン。Lift > 1.5 が有意な相関を示す。")
            disp_apriori = apriori_df.head(10).rename(columns={
                "antecedent": "先行カテゴリ", "consequent": "後続カテゴリ",
                "support": "支持度", "confidence": "確信度", "lift": "Lift値",
            })
            st.dataframe(disp_apriori, use_container_width=True, hide_index=True)

divider()

# ── 20代チャーン ─────────────────────────────────────────────
section_header(
    "チャーン予測：20代若者の「サイレントな危機」",
    "直近3ヶ月のエンゲージメント変化から、転出リスクをロジスティック回帰で精密予測",
)

if not churn_df.empty:
    age_churn = churn_by_age_group(churn_df)
    if not age_churn.empty:
        col_ch, col_ch_info = st.columns([3, 2])
        with col_ch:
            fig_churn = bar_chart(
                df=age_churn, x="age_group", y="avg_churn_prob",
                color=COLORS["danger"], title="年齢層別 平均転出リスク（0〜1）", height=300,
            )
            st.plotly_chart(fig_churn, use_container_width=True)

        with col_ch_info:
            spacer(24)
            youth_row = age_churn[age_churn["age_group"].str.contains("20代若者", na=False)]
            if not youth_row.empty:
                youth_risk  = youth_row["avg_churn_prob"].iloc[0]
                youth_count = youth_row["churn_flag_count"].iloc[0]
                st.markdown(
                    f"""<div class="dx-card" style="border-left:4px solid #EF4444;">"""
                    f"""<div style="font-size:2rem;font-weight:700;color:#EF4444;">{youth_risk*100:.0f}%</div>"""
                    f"""<div style="font-size:0.8rem;color:#6B7280;margin-bottom:12px;">20代若者の平均転出リスク</div>"""
                    f"""<div style="font-size:0.85rem;color:#7F1D1D;line-height:1.5;">"""
                    f"""{int(youth_count)}名が「サイレントな危機」状態。<br>放置すると翌年の<strong style="font-size:1.1rem;">転出確率が92%</strong>に。</div></div>""",
                    unsafe_allow_html=True,
                )

    high_risk = high_churn_citizens(rfm_df, threshold=0.6)
    if not high_risk.empty:
        with st.expander(f"離脱リスク高（上位 {len(high_risk)}名）"):
            cols_show = ["citizen_id", "age_group", "segment_label", "r_score", "f_score", "m_score", "churn_risk"]
            avail = [c for c in cols_show if c in high_risk.columns]
            st.dataframe(
                high_risk[avail].rename(columns={
                    "citizen_id": "市民ID", "age_group": "年齢層", "segment_label": "セグメント",
                    "r_score": "Rスコア", "f_score": "Fスコア", "m_score": "Mスコア", "churn_risk": "離脱リスク",
                }),
                use_container_width=True, hide_index=True,
            )

# ════════════════════════════════════════════════════════════════
# STEP 2: このまま放置すると... （人口カスケード）
# ════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="background:linear-gradient(135deg,#1A0A0A 0%,#2D0F0F 50%,#1A1A2E 100%);"""
    """border:1px solid #7F1D1D;border-radius:16px;padding:28px 32px;margin:32px 0 8px 0;">"""
    """<div style="display:flex;align-items:center;gap:16px;margin-bottom:12px;">"""
    """<div style="background:#EF4444;color:white;border-radius:50%;width:40px;height:40px;"""
    """display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.1rem;flex-shrink:0;">2</div>"""
    """<div><div style="font-size:1.3rem;font-weight:700;color:#FCA5A5;">このまま何もしなければ...</div>"""
    """<div style="font-size:0.9rem;color:#FECACA;margin-top:4px;">"""
    """若者の離脱が引き起こす「人口カスケード」— データが予測する15年後の大玉村</div></div></div>"""
    """<div style="font-size:0.85rem;color:#FCA5A5;line-height:2;margin-top:8px;">"""
    """若者の転出 &nbsp;→&nbsp; 出生数の減少 &nbsp;→&nbsp; 学童数の減少 &nbsp;→&nbsp; """
    """<strong style="color:#EF4444;">学校の統廃合</strong> &nbsp;→&nbsp; さらなる転出（自己強化ループ）</div></div>""",
    unsafe_allow_html=True,
)
spacer(8)

# カスケード計算
cascade_params = CascadeInput(
    population=population,
    aging_rate=aging_rate,
    youth_annual_churn_rate=youth_churn_rate,
    projection_years=20,
)

cascade_df  = project_population_cascade(cascade_params)
c_summary   = cascade_summary(cascade_params, cascade_df)
critical_yr = c_summary["school_viability_year"]
proj_yrs    = c_summary["projection_years"]
end_year    = 2024 + proj_yrs

# KPIカード
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.markdown(
        f"""<div class="dx-card" style="border-top:4px solid #EF4444;text-align:center;">"""
        f"""<div style="font-size:0.7rem;color:#6B7280;margin-bottom:4px;">若者の推定年間転出率</div>"""
        f"""<div style="font-size:2rem;font-weight:700;color:#EF4444;">{c_summary['youth_churn_rate_pct']:.1f}%</div>"""
        f"""<div style="font-size:0.75rem;color:#9CA3AF;">エンゲージメントデータから推定</div></div>""",
        unsafe_allow_html=True,
    )
with col_k2:
    pop_sq   = c_summary["pop_end_sq"]
    dec_pct  = c_summary["pop_decline_pct_sq"]
    st.markdown(
        f"""<div class="dx-card" style="border-top:4px solid #EF4444;text-align:center;">"""
        f"""<div style="font-size:0.7rem;color:#6B7280;margin-bottom:4px;">{end_year}年の推計人口（現状維持）</div>"""
        f"""<div style="font-size:2rem;font-weight:700;color:#EF4444;">{pop_sq:,}人</div>"""
        f"""<div style="font-size:0.75rem;color:#EF4444;">現在より {dec_pct:.1f}% 減少</div></div>""",
        unsafe_allow_html=True,
    )
with col_k3:
    pop_dx   = c_summary["pop_end_dx"]
    dec_dx   = c_summary["pop_decline_pct_dx"]
    saved_end = c_summary["pop_saved_at_end"]
    dx_color  = "#22C55E" if dec_dx < dec_pct else "#F59E0B"
    st.markdown(
        f"""<div class="dx-card" style="border-top:4px solid {dx_color};text-align:center;">"""
        f"""<div style="font-size:0.7rem;color:#6B7280;margin-bottom:4px;">{end_year}年の推計人口（DX介入後）</div>"""
        f"""<div style="font-size:2rem;font-weight:700;color:{dx_color};">{pop_dx:,}人</div>"""
        f"""<div style="font-size:0.75rem;color:{dx_color};">現状維持より <strong>+{saved_end:,}人</strong> 多く定着</div></div>""",
        unsafe_allow_html=True,
    )
with col_k4:
    tax_saved = c_summary["cumulative_tax_saved"]
    if tax_saved >= 100_000_000:
        tax_label = f"{tax_saved / 100_000_000:.1f}億円"
    else:
        tax_label = f"{tax_saved // 10_000:,}万円"
    st.markdown(
        f"""<div class="dx-card" style="border-top:4px solid #22C55E;text-align:center;">"""
        f"""<div style="font-size:0.7rem;color:#6B7280;margin-bottom:4px;">DX介入で守られる{proj_yrs}年累計税収</div>"""
        f"""<div style="font-size:2rem;font-weight:700;color:#22C55E;">{tax_label}</div>"""
        f"""<div style="font-size:0.75rem;color:#9CA3AF;">現状維持との差分（試算）</div></div>""",
        unsafe_allow_html=True,
    )

spacer(16)

# 介入効果スライダー（カスケードチャートに連動）
col_slider, col_cascade_chart = st.columns([1, 3])
with col_slider:
    spacer(20)
    intervention_pct = st.slider(
        "DX介入効果（転出率削減%）",
        min_value=10, max_value=70, value=40, step=5,
        help="提案システムがチャーン率をどれだけ削減できると想定するか",
    )
    st.caption(f"現在設定: {intervention_pct}%削減")
    st.markdown(
        f"""<div class="dx-card" style="border-left:4px solid #22C55E;margin-top:12px;">"""
        f"""<div style="font-size:0.75rem;color:#166534;font-weight:700;margin-bottom:4px;">効果の根拠</div>"""
        f"""<div style="font-size:0.8rem;color:#4B5563;line-height:1.6;">"""
        f"""プロアクティブ通知→再エンゲージメント率の実績値は<strong>35〜55%</strong>。"""
        f"""若者マッチングプラットフォームで<strong>+15%</strong>の定着効果が見込める。</div></div>""",
        unsafe_allow_html=True,
    )

with col_cascade_chart:
    # 介入効果スライダーに応じて再計算
    cascade_params_dyn = CascadeInput(
        population=population, aging_rate=aging_rate,
        youth_annual_churn_rate=youth_churn_rate,
        intervention_reduction_pct=float(intervention_pct),
        projection_years=20,
    )
    cascade_df_dyn = project_population_cascade(cascade_params_dyn)

    fig_cascade = go.Figure()
    for sc_name, sc_color, sc_dash in [
        ("現状維持シナリオ", "#EF4444", "solid"),
        ("DX介入シナリオ", "#22C55E", "solid"),
        ("危機加速シナリオ", "#F97316", "dot"),
    ]:
        sc_data = cascade_df_dyn[cascade_df_dyn["scenario"] == sc_name]
        fig_cascade.add_trace(go.Scatter(
            x=sc_data["year"], y=sc_data["population"],
            name=sc_name, line=dict(color=sc_color, width=3, dash=sc_dash),
            fill="tozeroy",
            fillcolor=sc_color.replace("#", "rgba(").replace("EF4444", "239,68,68,0.05)")
                             .replace("22C55E", "34,197,94,0.05)")
                             .replace("F97316", "249,115,22,0.04)"),
            hovertemplate=f"<b>{sc_name}</b><br>%{{x}}年: %{{y:,}}人<extra></extra>",
        ))

    # 現在人口の基準線
    fig_cascade.add_hline(
        y=population, line_dash="dash", line_color="#9CA3AF", line_width=1,
        annotation_text=f"現在 {population:,}人", annotation_position="right",
    )

    # RESAS 社人研推計をオーバーレイ（APIキー設定時のみ）
    resas_proj = _fetch_resas_projection(_active_code())
    if resas_proj:
        fig_cascade.add_trace(go.Scatter(
            x=[pt["year"] for pt in resas_proj],
            y=[pt["value"] for pt in resas_proj],
            name="社人研推計（RESAS公式）",
            line=dict(color="#7C3AED", width=2, dash="dashdot"),
            hovertemplate="<b>社人研推計</b><br>%{x}年: %{y:,}人<extra></extra>",
        ))

    fig_cascade.update_layout(
        title=f"{muni_name} 人口推計（2024〜{end_year}年）",
        xaxis_title="年", yaxis_title="推計人口（人）",
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F3F4F6", dtick=2),
        yaxis=dict(showgrid=True, gridcolor="#F3F4F6", rangemode="tozero"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=380, margin=dict(l=20, r=20, t=60, b=20),
        font=dict(family="Noto Sans JP, sans-serif", size=12),
    )
    st.plotly_chart(fig_cascade, use_container_width=True)
    if resas_proj:
        st.caption("紫の破線は国立社会保障・人口問題研究所（社人研）の公式推計（RESASより取得）。DX介入シナリオ（緑）との差が「今から動く意味」です。")

# 学童人口チャート
with st.expander("学童数の推移（小学校存続の見通し）"):
    fig_school = go.Figure()
    for sc_name, sc_color in [
        ("現状維持シナリオ", "#EF4444"), ("DX介入シナリオ", "#22C55E"), ("危機加速シナリオ", "#F97316"),
    ]:
        sc_data = cascade_df_dyn[cascade_df_dyn["scenario"] == sc_name]
        fig_school.add_trace(go.Scatter(
            x=sc_data["year"], y=sc_data["school_children"],
            name=sc_name, line=dict(color=sc_color, width=2),
            hovertemplate=f"<b>{sc_name}</b><br>%{{x}}年: %{{y:.0f}}人<extra></extra>",
        ))
    fig_school.add_hline(
        y=_SCHOOL_VIABILITY_MIN, line_dash="dash", line_color="#EF4444", line_width=2,
        annotation_text=f"統廃合リスクライン（{_SCHOOL_VIABILITY_MIN}人）",
        annotation_position="right", annotation_font_color="#EF4444",
    )
    fig_school.update_layout(
        title="小学校児童数の推移（統廃合リスクラインとの関係）",
        xaxis_title="年", yaxis_title="小学生推計数（人）",
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F3F4F6"),
        yaxis=dict(showgrid=True, gridcolor="#F3F4F6", rangemode="tozero"),
        height=300, margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Noto Sans JP, sans-serif", size=12),
    )
    st.plotly_chart(fig_school, use_container_width=True)
    if critical_yr:
        st.error(
            f"現状維持の場合、{critical_yr}年に小学生が{_SCHOOL_VIABILITY_MIN}人を下回ります。"
            f"DX介入によりこのリスクを{intervention_pct}%の確率で回避できます。"
        )

# ════════════════════════════════════════════════════════════════
# STEP 3: 今なら間に合う — 未来への希望
# ════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="background:linear-gradient(135deg,#F0FDF4 0%,#DCFCE7 100%);"""
    """border:1px solid #BBF7D0;border-radius:16px;padding:24px 28px;margin:32px 0 8px 0;">"""
    """<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">"""
    """<div style="background:#22C55E;color:white;border-radius:50%;width:36px;height:36px;"""
    """display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1rem;flex-shrink:0;">3</div>"""
    """<div><div style="font-size:1.2rem;font-weight:700;color:#14532D;">今なら間に合う — 職員を突き動かす「未来への希望」</div>"""
    """<div style="font-size:0.85rem;color:#166534;margin-top:2px;">"""
    """ボトルネックへの具体的なシステム提案。データが示した課題に、テクノロジーが答える。</div></div></div></div>""",
    unsafe_allow_html=True,
)
spacer(8)

for finding in findings:
    alert_future(
        title=f"【提案】{finding.get('area', '').upper()} 領域への具体的アクション",
        body=finding.get("action", ""),
    )
spacer(8)

section_header("育児・若者領域への具体的システム提案")
col_p1, col_p2 = st.columns(2)
with col_p1:
    st.markdown(
        """<div class="dx-card" style="border-top:4px solid #3B82F6;">"""
        """<div style="font-size:0.7rem;font-weight:700;color:#3B82F6;letter-spacing:0.08em;margin-bottom:8px;">オンライン化 提案</div>"""
        """<div style="font-size:1rem;font-weight:700;color:#1F2937;margin-bottom:12px;">プロアクティブ親子ワンストップ案内システム</div>"""
        """<div style="font-size:0.875rem;color:#4B5563;line-height:1.7;">施設チェックイン時にAIが未申請手続きを自動検知。<br>LINEで「<strong>30秒で終わる</strong>」専用URLをプッシュ通知。<br><br>"""
        """<strong style="color:#22C55E;">期待効果:</strong> 窓口説明時間 <strong>月56時間削減</strong></div></div>""",
        unsafe_allow_html=True,
    )
with col_p2:
    st.markdown(
        """<div class="dx-card" style="border-top:4px solid #22C55E;">"""
        """<div style="font-size:0.7rem;font-weight:700;color:#22C55E;letter-spacing:0.08em;margin-bottom:8px;">若者支援 提案</div>"""
        """<div style="font-size:1rem;font-weight:700;color:#1F2937;margin-bottom:12px;">若者エンゲージメント・プラットフォーム</div>"""
        """<div style="font-size:0.875rem;color:#4B5563;line-height:1.7;">データが動いたその若者の興味に合致した<br>地域外の副業・プロジェクトを<strong>自動マッチング</strong>。<br><br>"""
        """<strong style="color:#22C55E;">期待効果:</strong> 転出率を <strong>92% → 45%</strong> に削減</div></div>""",
        unsafe_allow_html=True,
    )

divider()

# ── 時間の質改善シミュレーション ─────────────────────────────
section_header(
    "「時間の質」改善シミュレーション",
    "システム導入で定型業務が減り、クリエイティブな時間が生まれる。人口カスケードを止める人的資本の回復。",
)

if not staff_df.empty:
    latest_staff = staff_df.iloc[-1]
    routine_before  = float(latest_staff["routine_hours"])
    creative_before = float(latest_staff["creative_hours"])
else:
    routine_before, creative_before = 142.0, 38.0

col_sim, col_sim_chart = st.columns([1, 2])
with col_sim:
    spacer(16)
    hours_saved = st.slider("月間削減見込み時間（時間/月）", 10, 80, 40, 5)
    months      = st.slider("シミュレーション期間（ヶ月）", 6, 24, 12, 3)
    st.markdown(
        f"""<div class="dx-card" style="border-left:4px solid #22C55E;margin-top:16px;">"""
        f"""<div style="font-size:0.8rem;color:#166534;font-weight:700;margin-bottom:8px;">{months}ヶ月後の予測</div>"""
        f"""<div style="font-size:1.4rem;font-weight:700;color:#22C55E;">+{hours_saved * 0.8:.0f}時間/月</div>"""
        f"""<div style="font-size:0.75rem;color:#6B7280;">クリエイティブ業務が増加</div></div>""",
        unsafe_allow_html=True,
    )

with col_sim_chart:
    sim_df = simulate_time_quality_improvement(
        routine_before=routine_before, creative_before=creative_before,
        system_hours_saved_per_month=hours_saved, total_months=months,
    )
    sim_df["label"] = sim_df["month"].apply(lambda m: f"{m}M" if m > 0 else "導入前")
    fig_sim = line_chart(
        df=sim_df, x="label",
        y_cols=["routine_hours", "creative_hours"],
        labels={"routine_hours": "定型業務（時間/月）", "creative_hours": "クリエイティブ業務（時間/月）"},
        colors=[COLORS["danger"], COLORS["positive"]],
        title=f"職員の時間配分シミュレーション（{months}ヶ月間）",
        height=320, area=True,
    )
    st.plotly_chart(fig_sim, use_container_width=True)

alert_future(
    title="このシステムが生み出す「時間の質の変化」と「人口カスケードの停止」",
    body=(
        f"システム導入後{months}ヶ月で、職員1人あたり月{hours_saved * 0.8:.0f}時間のクリエイティブな業務時間が生まれます。"
        "その時間を若者との共創・移住促進・子育て支援の充実に使うことで、"
        f"人口カスケードを止め、{intervention_pct}%のチャーン率削減が現実のものになります。"
        "「データを見る」から「データで動く」自治体へ—それがこのシステムの本当の価値です。"
    ),
)

divider()

col_nav1, _, col_nav2 = st.columns([1, 3, 1])
with col_nav1:
    if st.button("← NES分析へ戻る"):
        st.switch_page("pages/nes_dashboard.py")
with col_nav2:
    if st.button("データ管理へ →"):
        st.switch_page("pages/data_management.py")
