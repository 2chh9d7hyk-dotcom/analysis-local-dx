"""
大玉村 × NES重点領域 EBPM ダッシュボード — メインエントリーポイント。
st.navigation を使用してページを管理する。
"""
import pandas as pd
import streamlit as st
from src.config import DEFAULT_MUNICIPALITY_CODE, DEFAULT_MUNICIPALITY_NAME
from src.data.loader import detect_table_type
from src.data.validators import validate_csv

# ── session_state 初期化 ────────────────────────────────────────
if "active_municipality_code" not in st.session_state:
    st.session_state["active_municipality_code"] = DEFAULT_MUNICIPALITY_CODE
if "active_municipality_name" not in st.session_state:
    st.session_state["active_municipality_name"] = DEFAULT_MUNICIPALITY_NAME
if "uploaded_tables" not in st.session_state:
    st.session_state["uploaded_tables"] = {}

# ── ページ定義 ──────────────────────────────────────────────
pages = [
    st.Page("pages/home.py",                  title="ホーム",           icon="🏠", default=True),
    st.Page("pages/nes_dashboard.py",         title="NES重点領域",      icon="📊"),
    st.Page("pages/improvement_proposal.py",  title="新発見と未来提案", icon="💡"),
    st.Page("pages/data_management.py",       title="データ管理",       icon="🗄️"),
]

pg = st.navigation(pages, position="sidebar")

# ── サイドバーの自治体情報 ─────────────────────────────────
with st.sidebar:
    muni_name = st.session_state["active_municipality_name"]
    muni_code = st.session_state["active_municipality_code"]
    is_sample = (muni_code == DEFAULT_MUNICIPALITY_CODE and not st.session_state["uploaded_tables"])

    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#1E3A5F 0%,#3B82F6 100%);border-radius:12px;padding:16px;margin-bottom:16px;text-align:center;">
<div style="font-size:1.5rem;margin-bottom:4px;">🏛️</div>
<div style="font-size:0.95rem;font-weight:700;color:#FFFFFF;letter-spacing:0.02em;">{muni_name}</div>
<div style="font-size:0.7rem;color:rgba(255,255,255,0.7);margin-top:2px;letter-spacing:0.04em;">コード: {muni_code}</div>
</div>""",
        unsafe_allow_html=True,
    )

    # ── 別の自治体データをアップロード ──────────────────────
    with st.expander("別の自治体を分析する", expanded=False):
        uploaded_files = st.file_uploader(
            "CSVを選択（複数可）",
            type=["csv"],
            accept_multiple_files=True,
            help="municipality_master / nes_focus_indicators / staff_time_allocation / activity_logs のいずれかを選択してください",
        )

        if uploaded_files:
            new_tables: dict[str, pd.DataFrame] = dict(st.session_state["uploaded_tables"])
            detected_names: list[str] = []
            errors: list[str] = []

            for f in uploaded_files:
                try:
                    try:
                        df = pd.read_csv(f, encoding="utf-8-sig")
                    except UnicodeDecodeError:
                        f.seek(0)
                        df = pd.read_csv(f, encoding="cp932")

                    key = detect_table_type(df)
                    if key:
                        new_tables[key] = df
                        detected_names.append(key)
                    else:
                        errors.append(f"{f.name}: テーブル種別を検出できませんでした")
                except Exception as e:
                    errors.append(f"{f.name}: 読み込みエラー ({e})")

            if detected_names:
                st.success(f"検出: {', '.join(detected_names)}")

            if errors:
                for err in errors:
                    st.warning(err)

            # municipality_master からコード・名を自動取得
            if "municipality_master" in new_tables:
                master_df = new_tables["municipality_master"]
                if "municipality_code" in master_df.columns and not master_df.empty:
                    new_code = str(master_df["municipality_code"].iloc[0]).strip().zfill(6)
                    new_name = str(master_df["name"].iloc[0]) if "name" in master_df.columns else new_code
                else:
                    new_code = DEFAULT_MUNICIPALITY_CODE
                    new_name = DEFAULT_MUNICIPALITY_NAME
            else:
                new_code = st.session_state["active_municipality_code"]
                new_name = st.session_state["active_municipality_name"]

            if detected_names:
                if st.button("この自治体データに切り替える", type="primary", use_container_width=True):
                    st.session_state["uploaded_tables"] = new_tables
                    st.session_state["active_municipality_code"] = new_code
                    st.session_state["active_municipality_name"] = new_name
                    st.rerun()

        # サンプルデータへのリセット
        if st.session_state["uploaded_tables"]:
            st.markdown("---")
            if st.button("大玉村サンプルに戻す", use_container_width=True):
                st.session_state["uploaded_tables"] = {}
                st.session_state["active_municipality_code"] = DEFAULT_MUNICIPALITY_CODE
                st.session_state["active_municipality_name"] = DEFAULT_MUNICIPALITY_NAME
                st.rerun()

    st.markdown(
        """<div style="font-size:0.75rem;color:#9CA3AF;letter-spacing:0.03em;margin-top:8px;line-height:1.5;">
<strong style="color:#6B7280;">NES重点領域</strong><br>
🌐 オンライン化<br>
🤖 AI/RPA<br>
📊 データ活用<br>
🌱 ポジティブ効果
</div>""",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("© 2024 NES EBPM System")

pg.run()
