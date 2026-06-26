"""データ管理画面 — CSVアップロード・スキーマ認識・バリデーション・マスター確認。"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.theme import inject_theme, set_page_config
from src.ui.auth import login_gate, logout_button
from src.ui.components import hero_section, section_header, divider, spacer, alert_future
from src.data.loader import (
    load_from_uploaded, detect_table_type,
    get_active_master, get_active_indicators, get_active_staff_time, get_active_activity_logs,
    active_municipality_name,
)
from src.data.validators import validate_csv, show_validation_result
from src.data.db import (
    upsert_df, list_municipalities_in_db, list_tables_in_db, delete_municipality_from_db,
)
from src.data.api_client import EStatClient, RESASClient, build_municipality_master
from src.config import EXPECTED_SCHEMAS, SAMPLE_DIR

set_page_config("データ管理", "🗄️")
inject_theme()

if not login_gate():
    st.stop()

logout_button()

# ── ヒーロー ──────────────────────────────────────────────────
hero_section(
    title="データ管理",
    subtitle=(
        "パブリック公開を見据えた、アップロードされたCSVデータのスキーマ自動認識と"
        "バリデーション。一般公開データと庁内限定データを厳格に分離・管理します。"
    ),
    badge="🗄️ データインジェスト・マネジメント",
)

# ── タブ構成 ──────────────────────────────────────────────────
tab_upload, tab_current, tab_db, tab_api, tab_schema = st.tabs([
    "📤 CSVアップロード",
    "📊 現在のデータ確認",
    "💾 SQLite保存済みデータ",
    "🌐 APIから取得",
    "📋 スキーマリファレンス",
])

# ─────────────────────────────────────────────────────────────
# Tab1: アップロード
# ─────────────────────────────────────────────────────────────
with tab_upload:
    section_header("CSVファイルのアップロード", "自治体のCSVデータを読み込みます")

    col_upload, col_guide = st.columns([3, 2])

    with col_upload:
        table_options = {
            "自動検出（推奨）": None,
            "自治体マスター": "municipality_master",
            "NES重点領域指標": "nes_focus_indicators",
            "職員時間配分": "staff_time_allocation",
            "アクションログ": "activity_logs",
        }
        table_choice = st.selectbox(
            "テーブル種別",
            list(table_options.keys()),
            help="不明な場合は「自動検出」を選択してください",
        )
        table_key = table_options[table_choice]

        uploaded = st.file_uploader(
            "CSVファイルを選択（UTF-8またはShift-JIS対応）",
            type=["csv"],
        )

        if uploaded:
            # 読み込み試行
            try:
                df = pd.read_csv(uploaded, encoding="utf-8-sig")
            except UnicodeDecodeError:
                uploaded.seek(0)
                try:
                    df = pd.read_csv(uploaded, encoding="cp932")
                except Exception as e:
                    st.error(f"ファイルの読み込みに失敗しました: {e}")
                    st.stop()

            # テーブル種別の自動検出
            detected_key = table_key or detect_table_type(df)

            if detected_key:
                st.info(f"テーブル種別: **{detected_key}** を検出しました")
                result = validate_csv(df, detected_key)
                show_validation_result(result)
            else:
                st.warning(
                    "テーブル種別を自動検出できませんでした。"
                    "手動でテーブル種別を選択してください。"
                )
                detected_key = "activity_logs"

            st.subheader("プレビュー（先頭10行）")
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"総行数: {len(df):,}行 / カラム数: {len(df.columns)}列")

            # 基本統計
            with st.expander("📊 基本統計"):
                st.dataframe(df.describe(include="all"), use_container_width=True)

            # ── アクションボタン ──
            if detected_key:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("このデータを分析に使う", type="primary", use_container_width=True):
                        from src.config import DEFAULT_MUNICIPALITY_CODE, DEFAULT_MUNICIPALITY_NAME
                        tables = dict(st.session_state.get("uploaded_tables", {}))
                        tables[detected_key] = df
                        st.session_state["uploaded_tables"] = tables
                        if detected_key == "municipality_master" and "municipality_code" in df.columns and not df.empty:
                            new_code = str(df["municipality_code"].iloc[0]).strip().zfill(6)
                            new_name = str(df["name"].iloc[0]) if "name" in df.columns else new_code
                            st.session_state["active_municipality_code"] = new_code
                            st.session_state["active_municipality_name"] = new_name
                        st.success(f"「{detected_key}」を分析データとして保存しました。")
                        st.rerun()
                with btn_col2:
                    if st.button("SQLiteに保存（永続化）", use_container_width=True, help="ブラウザを閉じても残ります"):
                        saved = upsert_df(detected_key, df)
                        if detected_key == "municipality_master" and "municipality_code" in df.columns and not df.empty:
                            new_code = str(df["municipality_code"].iloc[0]).strip().zfill(6)
                            new_name = str(df["name"].iloc[0]) if "name" in df.columns else new_code
                            st.session_state["active_municipality_code"] = new_code
                            st.session_state["active_municipality_name"] = new_name
                            tables = dict(st.session_state.get("uploaded_tables", {}))
                            tables[detected_key] = df
                            st.session_state["uploaded_tables"] = tables
                        st.success(f"「{detected_key}」を SQLite に保存しました（{saved:,}行）。")
                        st.rerun()

    with col_guide:
        spacer(32)
        st.markdown(
            """
            <div class="dx-card">
                <div style="font-size: 0.875rem; font-weight: 700; color: #1F2937; margin-bottom: 12px;">
                    📋 アップロードガイド
                </div>
                <div style="font-size: 0.8rem; color: #4B5563; line-height: 1.8;">
                    <strong>対応ファイル形式</strong><br>
                    • UTF-8（推奨）<br>
                    • Shift-JIS（CP932）<br><br>
                    <strong>必須フィールド</strong><br>
                    • municipality_code（自治体コード）<br>
                    • target_year（対象年度）<br><br>
                    <strong>セキュリティ</strong><br>
                    • 個人を特定できる情報は匿名化してください<br>
                    • citizen_id は匿名化ID（例: C0001）<br><br>
                    <strong>将来対応</strong><br>
                    • e-Stat / RESAS API自動連携<br>
                    • トークン管理・認証フロー
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────
# Tab2: 現在のデータ確認
# ─────────────────────────────────────────────────────────────
with tab_current:
    muni_name = active_municipality_name()
    section_header(f"現在読み込まれているデータ（{muni_name}）", "サンプルデータまたはアップロード済みデータ")

    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "自治体マスター",
        "NES指標",
        "職員時間配分",
        "アクションログ",
    ])

    with sub_tab1:
        df_muni = get_active_master()
        if df_muni.empty:
            st.warning("データなし（サンプルデータを生成してください）")
        else:
            st.dataframe(df_muni, use_container_width=True, hide_index=True)

    with sub_tab2:
        df_nes = get_active_indicators()
        if df_nes.empty:
            st.warning("データなし")
        else:
            st.dataframe(df_nes, use_container_width=True, hide_index=True)

    with sub_tab3:
        df_staff = get_active_staff_time()
        if df_staff.empty:
            st.warning("データなし")
        else:
            st.dataframe(df_staff, use_container_width=True, hide_index=True)

    with sub_tab4:
        df_logs = get_active_activity_logs()
        if df_logs.empty:
            st.warning("データなし（generate_sample_data.pyを実行してください）")
        else:
            st.caption(f"総レコード数: {len(df_logs):,}件")

            # フィルター
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                categories = ["すべて"] + sorted(df_logs["category"].unique().tolist())
                sel_cat = st.selectbox("カテゴリ", categories)
            with col_f2:
                age_groups = ["すべて"] + sorted(df_logs["target_age_group"].unique().tolist())
                sel_age = st.selectbox("年齢層", age_groups)
            with col_f3:
                freq_min = st.slider("最小頻度スコア", 1, 5, 1)

            filtered = df_logs.copy()
            if sel_cat != "すべて":
                filtered = filtered[filtered["category"] == sel_cat]
            if sel_age != "すべて":
                filtered = filtered[filtered["target_age_group"] == sel_age]
            filtered = filtered[filtered["frequency_score"] >= freq_min]

            st.dataframe(filtered.head(200), use_container_width=True, hide_index=True)
            st.caption(f"表示件数: {min(len(filtered), 200):,}件（最大200件）")

# ─────────────────────────────────────────────────────────────
# Tab3: SQLite保存済みデータ管理
# ─────────────────────────────────────────────────────────────
with tab_db:
    section_header("SQLite保存済みデータ", "セッションをまたいで永続化されたデータを管理します")

    table_counts = list_tables_in_db()
    total_rows = sum(table_counts.values())

    if total_rows == 0:
        st.info("まだSQLiteにデータが保存されていません。「CSVアップロード」タブから「SQLiteに保存」を実行してください。")
    else:
        # テーブル別の行数サマリー
        st.markdown("**テーブル別保存状況**")
        summary_cols = st.columns(len(table_counts))
        table_labels = {
            "municipality_master": "自治体マスター",
            "nes_focus_indicators": "NES指標",
            "staff_time_allocation": "職員時間配分",
            "activity_logs": "アクションログ",
        }
        for col, (key, count) in zip(summary_cols, table_counts.items()):
            with col:
                st.metric(table_labels.get(key, key), f"{count:,}行")

        spacer(12)

        # 自治体別一覧
        df_munis = list_municipalities_in_db()
        if not df_munis.empty:
            section_header("保存済み自治体一覧", "")
            st.dataframe(
                df_munis.rename(columns={
                    "municipality_code": "自治体コード",
                    "name": "自治体名",
                    "latest_year": "最新年度",
                }),
                use_container_width=True,
                hide_index=True,
            )

            spacer(12)
            st.markdown("**自治体データの削除**")
            del_col1, del_col2 = st.columns([2, 1])
            with del_col1:
                muni_options = {
                    f"{row['name']} ({row['municipality_code']})": row["municipality_code"]
                    for _, row in df_munis.iterrows()
                }
                selected_label = st.selectbox("削除する自治体を選択", list(muni_options.keys()))
                selected_code = muni_options[selected_label]
            with del_col2:
                spacer(28)
                if st.button("DBから削除", type="secondary", use_container_width=True):
                    delete_municipality_from_db(selected_code)
                    st.warning(f"{selected_label} のデータをDBから削除しました。")
                    st.rerun()

        # DBからアクティブ自治体に切り替えるボタン
        if not df_munis.empty:
            spacer(8)
            st.markdown("**DBのデータをアクティブにする**")
            load_col1, load_col2 = st.columns([2, 1])
            with load_col1:
                load_options = {
                    f"{row['name']} ({row['municipality_code']})": (row["municipality_code"], row["name"])
                    for _, row in df_munis.iterrows()
                }
                load_label = st.selectbox("読み込む自治体を選択", list(load_options.keys()), key="db_load_select")
                load_code, load_name = load_options[load_label]
            with load_col2:
                spacer(28)
                if st.button("この自治体に切り替え", type="primary", use_container_width=True):
                    st.session_state["active_municipality_code"] = load_code
                    st.session_state["active_municipality_name"] = load_name
                    st.session_state["uploaded_tables"] = {}
                    st.success(f"{load_name} に切り替えました。DBのデータを使用します。")
                    st.rerun()

# ─────────────────────────────────────────────────────────────
# Tab4: e-Stat / RESAS APIから取得
# ─────────────────────────────────────────────────────────────
with tab_api:
    section_header("e-Stat / RESAS APIから自動取得", "自治体コードを入力するだけで、公的統計データから基本情報を自動生成")

    resas = RESASClient()
    estat = EStatClient()

    # API設定状況
    col_st1, col_st2 = st.columns(2)
    with col_st1:
        if resas.is_configured:
            st.markdown('<div class="dx-card-sm" style="border-left:4px solid #22C55E;"><span style="font-weight:700;color:#166534;">✅ RESAS API: 設定済み</span><br><span style="font-size:0.8rem;color:#6B7280;">人口構成・産業構造・社会増減データを取得できます</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="dx-card-sm" style="border-left:4px solid #D1D5DB;"><span style="font-weight:700;color:#6B7280;">⬜ RESAS API: 未設定</span><br><span style="font-size:0.8rem;color:#9CA3AF;">設定すると全国どの市区町村でも人口・産業データを自動取得できます</span></div>', unsafe_allow_html=True)
    with col_st2:
        if estat.is_configured:
            st.markdown('<div class="dx-card-sm" style="border-left:4px solid #22C55E;"><span style="font-weight:700;color:#166534;">✅ e-Stat API: 設定済み</span><br><span style="font-size:0.8rem;color:#6B7280;">国勢調査・住民基本台帳データを取得できます</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="dx-card-sm" style="border-left:4px solid #D1D5DB;"><span style="font-weight:700;color:#6B7280;">⬜ e-Stat API: 未設定</span><br><span style="font-size:0.8rem;color:#9CA3AF;">設定すると年齢別詳細人口データを取得できます</span></div>', unsafe_allow_html=True)

    spacer(12)

    with st.expander(
        "🔑 APIキーの設定方法" + ("（未設定 — まずここから）" if not resas.is_configured and not estat.is_configured else ""),
        expanded=not resas.is_configured and not estat.is_configured,
    ):
        st.markdown(
            """
**Step 1: プロジェクトルートに `.env` ファイルを作成**
```
# .env.example をコピーして .env にリネームしてください
cp .env.example .env
```

**Step 2: APIキーを取得してファイルに記入**

| API | 登録先 | 料金 |
|-----|--------|------|
| **RESAS** | https://opendata.resas-portal.go.jp/ | 無料 |
| **e-Stat** | https://www.e-stat.go.jp/api/ | 無料 |

```ini
# .env の内容
RESAS_API_KEY=your_resas_api_key_here
ESTAT_API_KEY=your_estat_api_key_here
```

**Streamlit Cloud にデプロイする場合は Secrets を使用**
```toml
# .streamlit/secrets.toml
RESAS_API_KEY = "your_key"
ESTAT_API_KEY = "your_key"
```

**Step 3: アプリを再起動（Ctrl+C → streamlit run app.py）**
            """
        )

    divider()

    # 自治体データ取得フォーム
    section_header("自治体データを自動取得", "自治体コードを入力して公的統計データを取り込みます")

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        api_code = st.text_input(
            "自治体コード（6桁）", value="073229", max_chars=6,
            help="総務省の自治体コード。大玉村=073229、盛岡市=032011 など",
        )
    with col_f2:
        api_name = st.text_input("自治体名", value="大玉村")
    with col_f3:
        api_year = st.selectbox("基準年", [2020, 2015, 2010], index=0)

    col_btn, col_hint = st.columns([1, 3])
    with col_btn:
        fetch_clicked = st.button(
            "🔍 APIからデータを取得",
            type="primary",
            use_container_width=True,
            disabled=not resas.is_configured,
        )
    with col_hint:
        if not resas.is_configured:
            spacer(8)
            st.caption("※ RESAS APIキーを設定すると有効になります（上の設定方法を参照）")

    if fetch_clicked and resas.is_configured:
        with st.spinner(f"RESAS APIから {api_name}（{api_code}）のデータを取得中..."):
            master_row = build_municipality_master(api_code, api_name, target_year=api_year, resas=resas)
            comp_data  = resas.fetch_population_composition(api_code)
            migration  = resas.fetch_net_migration(api_code)

        if master_row:
            st.session_state["api_fetch_result"] = {
                "master": master_row,
                "composition": comp_data,
                "migration": migration,
                "municipality_code": api_code,
                "municipality_name": api_name,
            }
            st.success(f"✅ {api_name} のデータを取得しました")
        else:
            st.error(
                "データの取得に失敗しました。"
                "自治体コードが正しいか確認してください（RESAS形式は5桁の市区町村コードを使用します）。"
            )

    # 取得結果の表示
    if "api_fetch_result" in st.session_state:
        result = st.session_state["api_fetch_result"]
        master = result["master"]
        comp   = result.get("composition") or []

        spacer(8)
        st.markdown(
            f'<div class="dx-card" style="border-left:4px solid #3B82F6;">'
            f'<div style="font-size:0.9rem;font-weight:700;color:#1F2937;margin-bottom:12px;">取得結果: {master["name"]}（{master["municipality_code"]}）</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;">'
            f'<div><div style="font-size:0.72rem;color:#9CA3AF;">総人口</div><div style="font-size:1.4rem;font-weight:700;color:#1F2937;">{master["population_total"]:,}</div><div style="font-size:0.72rem;color:#6B7280;">人（{master["target_year"]}年）</div></div>'
            f'<div><div style="font-size:0.72rem;color:#9CA3AF;">高齢化率</div><div style="font-size:1.4rem;font-weight:700;color:#EF4444;">{master["aging_rate"]:.1%}</div><div style="font-size:0.72rem;color:#6B7280;">65歳以上の割合</div></div>'
            f'<div><div style="font-size:0.72rem;color:#9CA3AF;">財政健全度</div><div style="font-size:1.4rem;font-weight:700;color:#6B7280;">{master["fiscal_health_index"]:.2f}</div><div style="font-size:0.72rem;color:#6B7280;">デフォルト値（要更新）</div></div>'
            f'<div><div style="font-size:0.72rem;color:#9CA3AF;">産業構造</div><div style="font-size:0.85rem;font-weight:600;color:#1F2937;">{master["industry_structure"][:40]}...</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if comp:
            comp_df = pd.DataFrame(comp).rename(columns={
                "year": "年", "total": "総人口", "young": "年少(0-14)",
                "working": "生産(15-64)", "elderly": "老年(65+)", "aging_rate": "高齢化率",
            })
            spacer(8)
            st.caption("年齢3区分別人口推移（RESASより）")
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

        spacer(12)
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
        with btn_col1:
            if st.button("このデータを分析に使う", type="primary", use_container_width=True):
                mdf = pd.DataFrame([master])
                tables = dict(st.session_state.get("uploaded_tables", {}))
                tables["municipality_master"] = mdf
                st.session_state["uploaded_tables"] = tables
                st.session_state["active_municipality_code"] = master["municipality_code"]
                st.session_state["active_municipality_name"] = master["name"]
                st.success(f"「{master['name']}」を分析データにセットしました")
                st.rerun()
        with btn_col2:
            if st.button("SQLiteに保存（永続化）", use_container_width=True):
                mdf = pd.DataFrame([master])
                n = upsert_df("municipality_master", mdf)
                st.session_state["active_municipality_code"] = master["municipality_code"]
                st.session_state["active_municipality_name"] = master["name"]
                st.success(f"SQLiteに保存しました（{n}行）")
                st.rerun()

    divider()

    # API活用の可能性をビジョンとして示す
    st.markdown(
        '<div class="dx-card" style="border-left:4px solid #7C3AED;background:linear-gradient(135deg,#FAF5FF 0%,#F5F3FF 100%);">'
        '<div style="font-size:0.9rem;font-weight:700;color:#5B21B6;margin-bottom:8px;">🌐 これが「任意の自治体」対応の核心です</div>'
        '<div style="font-size:0.85rem;color:#4B5563;line-height:1.8;">'
        '自治体コードを入力するだけで、全国1,741市区町村の人口・産業データが即座に取り込まれます。<br>'
        '各自治体が独自に収集したアクションログ（activity_logs）をアップロードすれば、<br>'
        '<strong>RFM分析 × バスケット分析 × チャーン予測 × 人口カスケード</strong>がどの自治体でも動きます。<br>'
        'これが「地方創生DXのプラットフォーム」としての本質的な価値です。'
        '</div></div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
# Tab5: スキーマリファレンス
# ─────────────────────────────────────────────────────────────
with tab_schema:
    section_header("スキーマリファレンス", "各CSVファイルの必須フィールド定義")

    schema_docs = {
        "municipality_master": {
            "title": "自治体マスター",
            "desc": "自治体の基本統計情報を管理します。",
            "fields": [
                ("municipality_code", "str", "自治体コード（主キー）", "073229"),
                ("name", "str", "自治体名", "大玉村"),
                ("population_total", "int", "総人口", "7821"),
                ("aging_rate", "float", "高齢化率（0〜1）", "0.312"),
                ("industry_structure", "JSON str", "産業構造割合", '{"primary": 0.15, ...}'),
                ("fiscal_health_index", "float", "財政健全度指数", "0.48"),
                ("target_year", "int", "対象年度", "2024"),
            ],
        },
        "nes_focus_indicators": {
            "title": "NES重点領域指標",
            "desc": "オンライン化・AI/RPA・データ活用の年度別スコア（0〜100）。",
            "fields": [
                ("municipality_code", "str", "自治体コード（外部キー）", "073229"),
                ("target_year", "int", "対象年度", "2024"),
                ("online_score", "float", "オンライン化スコア（0〜100）", "62.0"),
                ("ai_rpa_score", "float", "AI/RPAスコア（0〜100）", "45.0"),
                ("data_utilization_score", "float", "データ活用スコア（0〜100）", "38.0"),
                ("total_score", "float", "総合スコア（0〜100）", "48.3"),
            ],
        },
        "staff_time_allocation": {
            "title": "職員の時間配分",
            "desc": "DX推進による定型業務削減とクリエイティブ業務増加の記録。",
            "fields": [
                ("municipality_code", "str", "自治体コード", "073229"),
                ("target_year", "int", "対象年度", "2024"),
                ("routine_hours", "float", "定型業務時間（時間/月・人平均）", "142.0"),
                ("creative_hours", "float", "クリエイティブ業務（時間/月・人平均）", "38.0"),
                ("total_workforce_hours", "float", "月間総稼働時間", "180.0"),
            ],
        },
        "activity_logs": {
            "title": "住民・行政アクションログ ★コア",
            "desc": "RFM分析・バスケット分析・チャーン予測の源泉データ。匿名化必須。",
            "fields": [
                ("log_id", "str", "ログ識別ユニークID（主キー）", "L00001"),
                ("municipality_code", "str", "自治体コード", "073229"),
                ("citizen_id", "str", "匿名化市民ID", "C0001"),
                ("category", "str", "分析対象領域（教育/育児/若者支援/etc.）", "育児"),
                ("action_type", "str", "具体的な行動ログ", "子育て施設チェックイン"),
                ("target_age_group", "str", "対象年齢層", "30代子育て層"),
                ("action_date", "date", "行動日（YYYY-MM-DD形式）", "2024-06-15"),
                ("frequency_score", "int", "直近3ヶ月の頻度スコア（1〜5）", "4"),
                ("recency_days", "int", "直近行動からの経過日数", "7"),
                ("engagement_value", "float", "エンゲージメント価値（1〜10）", "7.5"),
            ],
        },
    }

    for key, doc in schema_docs.items():
        with st.expander(f"📋 {doc['title']} (`{key}.csv`)", expanded=(key == "activity_logs")):
            st.markdown(f"**{doc['desc']}**")
            spacer(8)
            rows_html = ""
            for fname, ftype, fdesc, fex in doc["fields"]:
                is_key = "コード" in fdesc or "主キー" in fdesc or "ID" in fdesc
                bg = "background:#EFF6FF;" if is_key else ""
                rows_html += f"""
                <tr style="{bg}">
                    <td style="padding:8px 12px;font-size:0.85rem;color:#1F2937;font-weight:600;
                               border-bottom:1px solid #F3F4F6;font-family:monospace;">{fname}</td>
                    <td style="padding:8px 12px;font-size:0.8rem;color:#7C3AED;
                               border-bottom:1px solid #F3F4F6;">{ftype}</td>
                    <td style="padding:8px 12px;font-size:0.85rem;color:#4B5563;
                               border-bottom:1px solid #F3F4F6;">{fdesc}</td>
                    <td style="padding:8px 12px;font-size:0.8rem;color:#6B7280;
                               border-bottom:1px solid #F3F4F6;font-family:monospace;">{fex}</td>
                </tr>
                """
            st.markdown(
                f"""
                <table style="width:100%;border-collapse:collapse;border-radius:8px;overflow:hidden;">
                    <thead>
                        <tr style="background:#F9FAFB;">
                            <th style="padding:8px 12px;font-size:0.75rem;color:#6B7280;text-align:left;
                                       border-bottom:2px solid #E5E7EB;letter-spacing:0.04em;">フィールド名</th>
                            <th style="padding:8px 12px;font-size:0.75rem;color:#6B7280;text-align:left;
                                       border-bottom:2px solid #E5E7EB;">型</th>
                            <th style="padding:8px 12px;font-size:0.75rem;color:#6B7280;text-align:left;
                                       border-bottom:2px solid #E5E7EB;">説明</th>
                            <th style="padding:8px 12px;font-size:0.75rem;color:#6B7280;text-align:left;
                                       border-bottom:2px solid #E5E7EB;">例</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

divider()

alert_future(
    title="次のステップ: 認証・公開制御（フェーズ4）",
    body=(
        "e-Stat / RESAS API連携は実装済み（「APIから取得」タブ）。"
        "次フェーズでは streamlit-authenticator によるログイン機能と、"
        "一般公開データと庁内限定データのルーティング分離に対応します。"
    ),
)
