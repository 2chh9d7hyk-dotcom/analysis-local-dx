"""ホーム画面 — エモーショナルランディング + 自治体サマリー + データインジェスト。"""
import base64 as _b64
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _svg_uri(inner: str, color: str, size: int = 38) -> str:
    """SVGパスを base64 data URI に変換して <img src="..."> で安全に利用できるようにする。"""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        f'{inner}</svg>'
    )
    return "data:image/svg+xml;base64," + _b64.b64encode(svg.encode()).decode()


_ICON_BULB = _svg_uri(
    '<line x1="9" y1="18" x2="15" y2="18"/>'
    '<line x1="10" y1="22" x2="14" y2="22"/>'
    '<path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8'
    'c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>',
    "#2563EB",
)
_ICON_CLOCK = _svg_uri(
    '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 16 14"/>',
    "#7C3AED",
)
_ICON_GLOBE = _svg_uri(
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="2" y1="12" x2="22" y2="12"/>'
    '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10'
    ' 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "#10B981",
)
_ICON_UPLOAD = _svg_uri(
    '<polyline points="16 16 12 12 8 16"/>'
    '<line x1="12" y1="12" x2="12" y2="21"/>'
    '<path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>',
    "#9CA3AF",
    36,
)

from src.ui.theme import inject_theme, set_page_config
from src.ui.components import (
    hero_section, section_header, metric_card,
    alert_future, spacer, divider, info_table,
)
from src.ui.charts import donut_chart
from src.data.loader import get_active_master, active_municipality_name, active_municipality_code, get_latest_year

set_page_config("ホーム", "🏠")
inject_theme()

# ── データ読み込み ────────────────────────────────────────────
muni_df = get_active_master()
muni_name = active_municipality_name()
muni_code = active_municipality_code()
latest_year = get_latest_year(muni_df)
latest = muni_df[muni_df["target_year"] == latest_year].iloc[0] if not muni_df.empty and latest_year else None

# ── ヒーローセクション ────────────────────────────────────────
hero_section(
    title="若者の可能性を、絶対に時代の波に飲み込ませない。",
    subtitle=(
        "地方の若者職員が、自分に何でも選択肢があると気づき、"
        "失敗を恐れずに主役として挑戦できる最高の環境を構築したい。"
        "DXの本質は単なるコスト削減や時間の削減ではない。"
        "職員が地域課題を解決・創造するクリエイティブな時間を生み出すことにある。"
    ),
    badge=f"{muni_name} × NES重点領域 EBPM ダッシュボード",
)

# ── 3つの魂（ランディングページ的タイポグラフィ） ─────────────
_CARD_STYLE = (
    "background:#FFFFFF;border-radius:16px;padding:28px 28px 28px 24px;"
    "border:1px solid #E5E7EB;box-shadow:0 2px 10px rgba(0,0,0,0.05);"
)
st.markdown(
    f"""
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:36px;">
  <div style="{_CARD_STYLE}border-left:4px solid #2563EB;">
    <img src="{_ICON_BULB}" width="38" height="38" alt="" style="display:block;margin-bottom:18px;">
    <div style="font-size:1.1rem;font-weight:700;color:#1E3A8A;letter-spacing:-0.01em;line-height:1.45;margin-bottom:10px;">若者の可能性を<br>引き出す</div>
    <div style="font-size:0.875rem;color:#4B5563;line-height:1.7;letter-spacing:0.04em;">まだ気づいていない選択肢に自ら気づき、失敗を恐れずに主役として挑戦できる最高の環境を構築</div>
  </div>
  <div style="{_CARD_STYLE}border-left:4px solid #7C3AED;">
    <img src="{_ICON_CLOCK}" width="38" height="38" alt="" style="display:block;margin-bottom:18px;">
    <div style="font-size:1.1rem;font-weight:700;color:#4C1D95;letter-spacing:-0.01em;line-height:1.45;margin-bottom:10px;">時間の質を<br>根本から変える</div>
    <div style="font-size:0.875rem;color:#4B5563;line-height:1.7;letter-spacing:0.04em;">つまらない定型的な予定外作業から職員を徹底的に解放し、創造・挑戦・学びに使える「時間の質」を変える</div>
  </div>
  <div style="{_CARD_STYLE}border-left:4px solid #10B981;">
    <img src="{_ICON_GLOBE}" width="38" height="38" alt="" style="display:block;margin-bottom:18px;">
    <div style="font-size:1.1rem;font-weight:700;color:#064E3B;letter-spacing:-0.01em;line-height:1.45;margin-bottom:10px;">都市と地方の壁を<br>本質的に打ち破る</div>
    <div style="font-size:0.875rem;color:#4B5563;line-height:1.7;letter-spacing:0.04em;">情報の非対称性を解消し、選択肢の多様性を増やすことで、誰もが自分を輝ける環境からの大脱走を証明</div>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

# ── 自治体サマリーカード ───────────────────────────────────────
if latest is not None:
    section_header(f"{muni_name} 基本情報", f"対象年度: {latest_year}年")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(
            value=f"{latest['population_total']:,}人",
            label="総人口",
            delta=None,
        )
    with col2:
        metric_card(
            value=f"{latest['aging_rate']*100:.1f}%",
            label="高齢化率",
            delta=None,
        )
    with col3:
        metric_card(
            value=f"{latest['fiscal_health_index']:.2f}",
            label="財政健全度指数",
            delta=None,
        )
    with col4:
        import json
        ind = latest.get("industry_structure", "{}")
        if isinstance(ind, str):
            try:
                ind_dict = json.loads(ind)
            except Exception:
                ind_dict = {}
        else:
            ind_dict = ind
        tertiary = ind_dict.get("tertiary", 0)
        metric_card(
            value=f"{tertiary*100:.0f}%",
            label="第3次産業比率",
            delta=None,
        )

    spacer(16)

    # 産業構造ドーナツグラフ
    col_chart, col_info = st.columns([1, 1])
    with col_chart:
        if ind_dict:
            labels = ["第1次産業", "第2次産業", "第3次産業"]
            values = [
                ind_dict.get("primary", 0) * 100,
                ind_dict.get("secondary", 0) * 100,
                ind_dict.get("tertiary", 0) * 100,
            ]
            from src.config import COLORS
            fig = donut_chart(
                labels=labels,
                values=values,
                colors=[COLORS["positive"], COLORS["ai_rpa"], COLORS["online"]],
                title="産業構造（2024年）",
                height=280,
                center_text="産業構造",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_info:
        spacer(32)
        info_table([
            ("自治体名", muni_name, False),
            ("自治体コード", muni_code, False),
            ("総人口", f"{latest['population_total']:,}人", False),
            ("高齢化率", f"{latest['aging_rate']*100:.1f}%", True),
            ("財政健全度", f"{latest['fiscal_health_index']:.2f}", False),
        ])

else:
    st.info(
        "サンプルデータが見つかりません。"
        "`python data/sample/generate_sample_data.py` を実行してください。",
    )

divider()

# ── データインジェスト（スタイリッシュCSVアップロード） ─────────
section_header("データを読み込む", "CSVファイルをアップロードして分析を開始します")

st.markdown(
    f"""
<div style="background:#FFFFFF;border-radius:16px;padding:32px;border:1px solid #E5E7EB;box-shadow:0 1px 3px rgba(0,0,0,0.05);margin-bottom:16px;">
  <div style="text-align:center;">
    <img src="{_ICON_UPLOAD}" width="36" height="36" alt="" style="display:block;margin:0 auto 12px;">
    <div style="font-size:1rem;font-weight:600;color:#1F2937;letter-spacing:0.02em;">CSVデータをドロップ</div>
    <div style="font-size:0.85rem;color:#6B7280;margin-top:6px;line-height:1.7;letter-spacing:0.04em;">または下のボタンからファイルを選択してください</div>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

with st.expander("データアップロード（自治体CSVを読み込む）", expanded=False):
    import pandas as pd
    from src.data.loader import load_from_uploaded, detect_table_type
    from src.data.validators import validate_csv, show_validation_result

    uploaded = st.file_uploader(
        "CSVファイルを選択",
        type=["csv"],
        help="UTF-8またはShift-JIS(CP932)のCSVファイルに対応しています。",
    )

    if uploaded:
        table_options = {
            "自動検出": None,
            "自治体マスター (municipality_master)": "municipality_master",
            "NES重点領域指標 (nes_focus_indicators)": "nes_focus_indicators",
            "職員時間配分 (staff_time_allocation)": "staff_time_allocation",
            "アクションログ (activity_logs)": "activity_logs",
        }
        table_choice = st.selectbox("テーブル種別を選択", list(table_options.keys()))
        table_key = table_options[table_choice]

        try:
            df_preview = pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded.seek(0)
            df_preview = pd.read_csv(uploaded, encoding="cp932")

        if table_key is None:
            table_key = detect_table_type(df_preview)

        if table_key:
            result = validate_csv(df_preview, table_key)
            show_validation_result(result)

        st.subheader("プレビュー（先頭5行）")
        st.dataframe(df_preview.head(5), use_container_width=True)

# ── ページナビゲーション ──────────────────────────────────────
divider()

col_spacer, col_next = st.columns([5, 1])
with col_next:
    if st.button("NES分析へ →", type="primary", use_container_width=True):
        st.switch_page("pages/nes_dashboard.py")

divider()

# ── フッターメッセージ ────────────────────────────────────────
alert_future(
    title="このシステムの唯一無二の存在意義",
    body=(
        "過去のデータから「だけ」発見するのではなく、データ分析の本来の力を追求し、"
        "「職員が自治体にいながらこんなことができるのか？」という新しい発見をもたらし、"
        "具体的なシステム開発や政策提案への一歩を踏み出させる。"
        "若者職員が自分たちの手で改善できる領域（教育・育児・若者支援・人口減少対策など）を"
        "自ら発見し、具体的なシステム開発・政策提案への一歩を踏み出せるようにすること。"
        "それがこのシステムの使命です。"
    ),
)
