# 大玉村 × NES重点領域 EBPM ダッシュボード — CLAUDE.md

> **このファイルの目的**: `/clear` 後の新しいセッションが、直前までの作業状況を完全に把握して即座に続きを始められるようにするための詳細仕様書。

---

## 0. 新セッション開始時のチェックリスト

```bash
# 1. アプリが起動するか確認
cd c:\analysis_local_dx
streamlit run app.py

# 2. サンプルデータが存在するか確認（なければ再生成）
ls data/sample/*.csv
python data/sample/generate_sample_data.py

# 3. SQLite DBが存在するか確認（任意）
ls data/local.db
```

アプリURL: http://localhost:8501

---

## 1. プロジェクト概要・背景・目的

### 何を作っているか
**大玉村（福島県安達郡、自治体コード: 073229）× NES重点領域 EBPM ダッシュボード**

Streamlitで作られた多ページWebアプリ。民間企業のPOS・ポイントカード分析手法（RFM分析・バスケット分析・チャーン予測・k-means・ロジスティック回帰）を自治体データに適用し、「職員が気づかなかった地域の真の課題」を自動発見するシステム。

### フェーズロードマップ
- **フェーズ1（完了）**: ローカル環境（CSV/SQLite）での検証・デモ
- **フェーズ2（完了）**: パブリックWebアプリ化（Streamlit Cloud）← S7で完了
- **フェーズ3（完了）**: e-Stat / RESAS APIとの自動連携 ← S6で先行実装
- **フェーズ4（完了）**: 認証・アクセス制御（データ管理ページのみ職員認証）← S7で完了
- **フェーズ5（現在）**: ブラッシュアップ — 本質（感情の設計・汎用化）をさらに磨く

### プロジェクトの背景・価値観
- NES（NECソリューションイノベータ）への面接・提案用ポートフォリオ
- 「単なる効率化DXではなく、地方若者の可能性を引き出し、時間の質を変える」という思想を体現するシステム
- **エモーショナルなストーリーライン**が重要（グラフを見て「へえ」で終わるのではなく、「これは何とかしなければ」と職員が動きたくなるUI）
- 大玉村はあくまで例示。最終的には任意の自治体のオープンデータをアップロードして分析できる汎用システム

---

## 2. ディレクトリ構成（2026-06-27 セッション7 完了時点）

```
c:\analysis_local_dx\
├── CLAUDE.md                              ← このファイル
├── requirements.txt                       ← 本番依存（Streamlit Cloud用）
├── requirements-dev.txt                   ← 開発依存（pytest等）★S7追加
├── .env.example                           ← APIキーテンプレート
├── .gitignore                             ← local.db / .env / __pycache__ 除外 ★S7追加
├── .gitattributes                         ← LF統一（Windows↔Linux対応）★S7追加
├── app.py                                 ← Streamlit メインエントリー・サイドバー
├── .streamlit/
│   └── config.toml
├── .github/
│   └── workflows/
│       └── ci.yml                         ← GitHub Actions CI（pytest + 構文チェック）★S7追加
├── pages/
│   ├── __init__.py
│   ├── home.py                            ← ホーム画面
│   ├── nes_dashboard.py                   ← NES重点領域ダッシュボード（全国/県平均は動的CSV参照）
│   ├── improvement_proposal.py            ← 新発見と未来提案（★コア・3ステップ物語）
│   └── data_management.py                ← データ管理（5タブ）★S7で職員認証ゲート追加
├── src/
│   ├── __init__.py
│   ├── config.py                          ← カラー・定数・スキーマ定義
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── theme.py                       ← CSS注入・ハンバーガーメニュー・ファビコン
│   │   ├── components.py                  ← 再利用UIコンポーネント
│   │   ├── charts.py                      ← Plotlyチャートファクトリー
│   │   └── auth.py                        ← 職員認証ゲート（login_gate / logout_button）★S7追加
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models.py                      ← dataclass型定義
│   │   ├── loader.py                      ← CSV/DB読み込み・load_reference_avg()・session_state
│   │   ├── validators.py                  ← スキーマバリデーション
│   │   ├── db.py                          ← SQLite永続化レイヤー
│   │   └── api_client.py                  ← e-Stat / RESAS APIクライアント
│   └── analytics/
│       ├── __init__.py
│       ├── rfm.py                         ← RFM分析 + k-meansペルソナ分類
│       ├── basket.py                      ← バスケット分析 + mlxtend Apriori
│       ├── churn.py                       ← チャーン予測 + ロジスティック回帰
│       ├── indicators.py                  ← NES指標スコア計算
│       └── cascade.py                     ← 人口カスケード投影モデル
├── tests/                                 ← ★S7追加
│   ├── __init__.py
│   ├── conftest.py                        ← 共有フィクスチャ（sample_logs等）
│   ├── test_rfm.py                        ← 13テスト（ペルソナ分類・離脱リスク）
│   ├── test_churn.py                      ← 10テスト（20代高リスク検出・AUC検証）
│   ├── test_cascade.py                    ← 11テスト（DX>現状維持の数理保証）
│   └── test_basket.py                     ← 7テスト（ボトルネック検出・信頼度境界）
└── data/
    ├── local.db                           ← SQLite永続DB（自動生成・gitignore済み）
    ├── reference/
    │   └── national_avg.csv              ← 全国・県平均参照データ（2021〜2024年）
    └── sample/
        ├── generate_sample_data.py        ← サンプルデータ生成スクリプト
        ├── municipality_master.csv        ← 4行（2021〜2024年）
        ├── nes_focus_indicators.csv       ← 4行（2021〜2024年）
        ├── staff_time_allocation.csv      ← 4行（2021〜2024年）
        └── activity_logs.csv             ← 2081行（3つのインサイトが埋め込まれた設計）
```

---

## 3. 各ページの実装内容（最新版）

### `pages/home.py` — ホーム画面
- ネイビー→ブルーの深いグラデーションヒーローセクション
- 「3つの魂」カード: 白背景 + 左4px色帯 + base64 SVGアイコン（電球/時計/地球儀）
- 自治体基本情報サマリー（総人口・高齢化率・財政健全度・第3次産業比率）— マルチ自治体対応済み
- 産業構造ドーナツグラフ（Plotly）
- CSVアップロードUI（expander内、バリデーション・プレビュー付き）
- フッター: 「NES分析へ →」ナビゲーションボタン

### `pages/nes_dashboard.py` — NES重点領域ダッシュボード
- 最新年度のスコアカード（前年比デルタ表示 ▲/▼ + カラーコード）
- レーダーチャート（大玉村 vs 全国平均 vs 県平均）— `data/reference/national_avg.csv` から動的取得
- 折れ線グラフ（2021〜2024年スコア推移）
- 積み上げ棒グラフ（職員の定型業務 vs クリエイティブ業務の時間配分推移）
- 優先度マトリクス（改善余地×成長速度で自動ランキング）
- ナビゲーションボタン（← ホーム / 新発見へ →）

### `pages/improvement_proposal.py` — 新発見と未来提案 ★コア

3ステップの物語構造を採用。データを「知る」→「恐れる」→「動く」という感情の流れに沿って設計。

#### STEP 1: データを洗うと新しい発見が！（オレンジ系）
- ボトルネック自動検出アラート（alert_discovery / alert_churn）
- バスケット分析グラフ（子育て施設利用頻度 × オンライン申請率）
- k-meansによる4つの市民ペルソナカード（「地域の守り人」「眠れる可能性」「漂流する才能」「サイレント多数派」）
- ロジスティック回帰「転出の引き金」横棒グラフ（AUC 0.96。係数の正負で赤/緑色分け）
- mlxtend Apriori 分析結果（expander内、Lift値付きルール）
- 20代チャーン予測（年齢層別棒グラフ + 離脱リスク高市民リスト）

#### STEP 2: このまま何もしなければ...（ダーク/レッド系）
- 人口カスケードの説明（若者転出 → 出生減 → 学童減 → 学校統廃合 → さらなる転出）
- KPIカード4枚（推定転出率・2044年推計人口・DX介入後人口・守られる税収）
- **3シナリオ人口投影チャート（20年）+ RESAS社人研推計オーバーレイ** ★セッション6追加
  - 現状維持（赤）/ DX介入（緑）/ 危機加速（オレンジ）
  - **RESAS APIキー設定時: 社人研の公式推計（紫の破線）を4本目として重ねて表示**
  - 「政府の公式推計ですら認める人口減少を、DXで食い止められる」という訴求力を強化
  - DX介入効果スライダーに連動してリアルタイム更新
- 学童数推移チャート（expander内、統廃合リスクライン表示）

#### STEP 3: 今なら間に合う（グリーン系）
- ボトルネック別の具体的システム提案アラート
- 2カラム提案カード（オンライン化 / 若者支援）
- 「時間の質」改善シミュレーション（スライダー連動折れ線グラフ）
- 人口カスケードと連動したメッセージ

### `pages/data_management.py` — データ管理
- **タブ5構成**（セッション6で「APIから取得」タブを追加）:
  - **📤 CSVアップロード**: 種別自動検出・バリデーション・「分析に使う」「SQLiteに保存」の2ボタン
  - **📊 現在のデータ確認**: 4テーブル × サブタブ（activity_logsはフィルター付き）
  - **💾 SQLite保存済みデータ**: 行数サマリー・自治体一覧・削除・切り替えボタン
  - **🌐 APIから取得** ★セッション6追加: RESAS/e-Stat設定状況・自治体コード入力・人口/産業データ自動取得・保存
  - **📋 スキーマリファレンス**: 全テーブルのフィールド定義表

---

## 4. データアーキテクチャ

### データ優先順位（loader.py の get_active_*() 関数）

```
優先度1: st.session_state["uploaded_tables"]  ← 当セッションでアップロード or API取得
優先度2: SQLite DB（data/local.db）           ← 永続保存済みデータ
優先度3: サンプルCSV（data/sample/*.csv）     ← フォールバック
```

### マルチ自治体対応の仕組み

```python
# session_state で管理するキー
st.session_state["active_municipality_code"]  # 現在の自治体コード（デフォルト: "073229"）
st.session_state["active_municipality_name"]  # 現在の自治体名（デフォルト: "大玉村"）
st.session_state["uploaded_tables"]          # dict: table_key → DataFrame
```

自治体を切り替える方法:
1. サイドバーでCSVをアップロード → 自動切り替え
2. データ管理「SQLite保存済みデータ」タブ → DB内の自治体に切り替え
3. データ管理「APIから取得」タブ → RESASから取得して即切り替え ← NEW

### activity_logs テーブル設計（2081行）

3つのインサイトが自然に検出されるよう設計:

| グループ | 人数 | 設計パターン |
|---|---|---|
| 30代子育て層（育児） | 80名（高頻度40・中頻度25・低頻度15） | freq=5/3/1の3層。高頻度(40名)のオンライン率≈10% |
| 20代若者（若者支援・起業） | 60名（うち40名が離脱予備軍） | 前半3〜6ヶ月は活発→直近3ヶ月で急減（チャーン検出の素材） |
| 40〜50代（行政手続き） | 50名 | 安定、オンライン利用40%程度 |
| 移住検討者 | 20名 | 低頻度、人口移住対策カテゴリ |

### 4テーブルのCSVスキーマ

```
municipality_master:    municipality_code, name, population_total, aging_rate,
                        industry_structure(JSON), fiscal_health_index, target_year

nes_focus_indicators:   municipality_code, target_year, online_score,
                        ai_rpa_score, data_utilization_score, total_score

staff_time_allocation:  municipality_code, target_year, routine_hours,
                        creative_hours, total_workforce_hours

activity_logs:          log_id, municipality_code, citizen_id, category,
                        action_type, target_age_group, action_date,
                        frequency_score(1-5), recency_days, engagement_value(1-10)
```

---

## 5. 分析モジュール詳細（src/analytics/）

### `rfm.py` — RFM分析 + k-meansペルソナ
- `compute_rfm(df)`: Recency/Frequency/Monetary スコアを計算
- `segment_by_kmeans(rfm_df, n_clusters=4)`: scikit-learn KMeansで4ペルソナに分類
  - クラスタ重心のRFM合計順に「地域の守り人」「眠れる可能性」「漂流する才能」「サイレント多数派」を割り当て
  - データ不足時は qcut による簡易分類にフォールバック
- `persona_summary(rfm_df)`: ペルソナ別集計（人数・平均RFM・平均離脱リスク）
- `high_churn_citizens(rfm_df, threshold=0.65)`: 離脱リスク高の市民リスト

### `basket.py` — バスケット分析 + mlxtend Apriori
- `compute_basket_rules(df)`: 独自実装のアプリオリ（action_typeレベル）
- `compute_apriori_rules(df, min_support=0.05, min_confidence=0.25)`: mlxtend Apriori（カテゴリレベル）
  - mlxtend 未インストール時は compute_basket_rules() にフォールバック
  - Lift=3.5の強相関を検出（サンプルデータで確認済み）
- `online_usage_by_offline_frequency(df)`: 育児カテゴリ専用クロス分析（高頻度利用者のオンライン率≈10%）
- `bottleneck_detection(df)`: 3つのボトルネックを自動検出してリスト形式で返す

### `churn.py` — チャーン予測 + ロジスティック回帰
- `compute_churn_trends(df)`: 市民ごとの前3ヶ月 vs 後3ヶ月比較でchurn_flagを算出
- `train_churn_model(activity_logs)`: ロジスティック回帰でチャーンモデルを訓練
  - 特徴量6つ: recency_days / frequency_score / engagement_value / is_youth / is_childcare / is_new_resident
  - AUC 0.96（サンプルデータで確認済み）
  - Returns: (model_bundle, importance_df, metrics_dict)
- `predict_churn_proba(activity_logs, model_bundle)`: 各市民の転出確率を予測
- `simulate_time_quality_improvement(...)`: 職員の時間配分シミュレーション

### `cascade.py` — 人口カスケード投影
- `CascadeInput` (dataclass): 入力パラメータ（人口・高齢化率・転出率・介入効果・投影年数）
- `estimate_churn_rate_from_logs(churn_df)`: churn_flagから年間転出率を現実的に換算
  - 計算式: `0.03 + flag_rate × 0.15`（上限20%）← 総務省実績ベースの換算
- `project_population_cascade(params)`: 3シナリオ20年投影
  - **現状維持シナリオ（赤）**: チャーン率が継続
  - **DX介入シナリオ（緑）**: チャーン率を介入効果%削減
  - **危機加速シナリオ（橙点線）**: 学校閉鎖トリガーでチャーン率が60%増加
- `cascade_summary(params, cascade_df)`: 20年後人口・税収保全額・DX効果の定量化
- `find_critical_year(cascade_df, scenario, threshold=120)`: 小学生120人を下回る年を特定

### `api_client.py` — e-Stat / RESAS クライアント ★セッション6追加
- `EStatClient`: e-Stat REST API 3.0 クライアント（人口データ検索・取得）
- `RESASClient`: RESAS API v1 クライアント
  - `fetch_population_sum(code)`: 総人口推移 + 社人研推計（カスケードチャートオーバーレイ用）
  - `fetch_population_composition(code)`: 年齢3区分別人口推移
  - `fetch_industry_structure(code, year)`: 第1〜3次産業就業比率
  - `fetch_net_migration(code)`: 転入・転出・純移動数
  - `split_code(code_6)`: 6桁自治体コード → RESAS形式 (prefCode, cityCode) に変換
- `build_municipality_master(code, name, year, resas)`: RESASから municipality_master 1行を自動生成
- `get_api_key(name)`: 環境変数 → Streamlit Secrets の順でキーを取得
- APIキーなし時はすべての操作がグレースフルデグレード（サンプルデータでの動作に影響なし）

### `indicators.py` — NES指標スコア計算
- `compute_area_scores(df)`: 領域別スコアの集計と前年比計算
- `benchmark_comparison(indicator_df, national_avg, prefecture_avg)`: 全国・県平均との比較DataFrame

---

## 6. 重要な技術的知識（バグ防止）

### Streamlit の制約

| 制約 | 対処方法 |
|---|---|
| `st.markdown()` でインライン `<svg>` がブロックされる | base64 data URI + `<img src="data:image/svg+xml;base64,...">` を使う |
| `st.markdown()` に複数行HTML（空行あり）を渡すと `</table>` が生テキスト化する | HTMLは必ず**改行なし単行**で渡す |
| `streamlit.components.v1.html()` はiframeになり `window.parent.document` にアクセス不可 | CSS-onlyのハンバーガーメニューを採用 |
| `st.set_page_config(page_icon=)` はSVG文字列・data URIを受け付けない | PIL Imageオブジェクトを渡す（内部でbase64 PNGに変換） |

### ハンバーガーメニューのDOM構造（`src/ui/theme.py`）

```html
<div id="dx-hbg-wrap">        <!-- position:fixed!important → 親のtransformから独立 -->
  <input id="dx-hbg-toggle">  <!-- display:none。checked状態をCSSで検知 -->
  <label id="dx-hbg-overlay"> <!-- toggleの兄弟 → ~ セレクターで暗幕制御 -->
  <label id="dx-hbg-btn">     <!-- toggleの兄弟 → ~ セレクターでボタン制御 -->
  <aside id="dx-hbg-panel">   <!-- toggleの兄弟 → ~ セレクターでスライドパネル制御 -->
</div>
```

CSSセレクターの核心: `#dx-hbg-toggle:checked ~ #dx-hbg-panel { right: 0; }`
（`:has()` は条件によって機能しないため `~` を使う）

### ファビコン生成（`src/ui/theme.py`）

```python
from PIL import Image as _Image, ImageDraw as _ImageDraw
def _make_favicon() -> _Image.Image:
    img = _Image.new("RGBA", (32, 32), (10, 22, 40, 255))
    d = _ImageDraw.Draw(img)
    d.rounded_rectangle([5, 20, 10, 28], radius=2, fill=(37, 99, 235, 255))   # 青棒
    d.rounded_rectangle([13, 14, 18, 28], radius=2, fill=(124, 58, 237, 255)) # 紫棒
    d.rounded_rectangle([22, 8, 27, 28], radius=2, fill=(16, 185, 129, 255))  # 緑棒
    return img
```

### base64 SVGアイコンの生成パターン

```python
import base64
def _svg_uri(inner: str, color: str, size: int = 38) -> str:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5">{inner}</svg>'
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
```

---

## 7. デザインシステム

### カラーパレット（`src/config.py` の COLORS 辞書）

```python
"bg_app":    "#F3F4F6"   # アプリ背景
"bg_card":   "#FFFFFF"   # カード背景
"border":    "#E5E7EB"   # 境界線
"text_main": "#1F2937"   # メインテキスト
"text_sub":  "#4B5563"   # サブテキスト
"text_muted":"#9CA3AF"   # ミュートテキスト
"online":    "#3B82F6"   # NES: オンライン化（ブルー）
"ai_rpa":    "#7C3AED"   # NES: AI/RPA（バイオレット）
"data":      "#06B6D4"   # NES: データ活用（シアン）
"positive":  "#22C55E"   # ポジティブ（グリーン）
"warning":   "#F59E0B"   # 警告（アンバー）
"danger":    "#EF4444"   # 危険（レッド）
```

### Plotlyグラフの原則
- 背景: `paper_bgcolor="white"`, `plot_bgcolor="white"`
- グリッド線: `#F3F4F6`（薄グレー）
- 折れ線幅: 3px以上
- エリアグラフ: `rgba(r,g,b,0.05〜0.10)` の薄い塗り
- 必ず `use_container_width=True`（レスポンシブ）
- フォント: `font=dict(family="Noto Sans JP, sans-serif", size=12)`

---

## 8. アーキテクチャ原則

1. **分析層はUIに非依存**: `src/analytics/` はStreamlitを一切importしない
2. **api_client.py も同様**: ページ層からのみ呼び出す。キャッシュはページ側で `@st.cache_data`
3. **ページ層は薄い**: `pages/` のファイルはロジックを持たず `src/` を呼ぶだけ
4. **キャッシュ**: データ読み込みには `@st.cache_data(ttl=300)` を付ける
5. **型変換は loader に集約**: `_coerce_types()` で型安全に変換。municipality_code は6桁ゼロパディング
6. **HTMLは改行なし単行**: `st.markdown()` に渡すHTMLに空行を入れない
7. **グレースフルデグレード**: APIキーがなければサンプルデータで全機能が動く。分岐は `is_configured` で

---

## 9. 依存関係（requirements.txt）

```
streamlit>=1.29.0      # st.navigation が使えるバージョン
pandas>=2.0.0
plotly>=5.18.0
altair>=5.0.0
numpy>=1.24.0
pillow>=8.2.0          # ファビコン生成（rounded_rectangle が必要）
scikit-learn>=1.3.0    # k-means・ロジスティック回帰
mlxtend>=0.23.0        # Apriori アルゴリズム
python-dateutil>=2.8.2
requests>=2.31.0       # e-Stat / RESAS API HTTP呼び出し
python-dotenv>=1.0.0   # .env ファイルからAPIキー読み込み
```

---

## 10. 既知の問題・制約

| 問題 | 状態 | 対処方法 |
|---|---|---|
| municipality_code ゼロパディング | ✅ 修正済み | `_coerce_types()` で `.str.zfill(6)` |
| .streamlit CORS警告 | ✅ 許容 | 動作は正常。無視して良い |
| Windows CP932端末での絵文字化け | ✅ 修正済み | generate_sample_data.py から絵文字を除去 |
| インラインSVGがst.markdownでブロック | ✅ 対処済み | base64 data URI + `<img>` を使う |
| `</table>` が生テキストで表示 | ✅ 修正済み | info_table_row() を単行HTMLで返す |
| ハンバーガーJS版が動作しない | ✅ 修正済み | CSS-only + `~` セレクター + fixed ラッパー |
| 全国・県平均のハードコード | ✅ 解消済み | `data/reference/national_avg.csv` + `load_reference_avg()` |
| st.cache_data のTTL | ⚠️ 注意 | データ更新後はブラウザ強制リフレッシュ（Ctrl+F5）で確認 |
| cascade.py の年間転出率推定 | ⚠️ 注意 | `estimate_churn_rate_from_logs()` は上限20%キャップ。実データでは係数調整が必要 |
| RESAS cityCode の変換 | ⚠️ 注意 | `split_code()` は6桁の末尾1桁（チェックディジット）を除いた5桁を使う。自治体によっては不一致の可能性あり |
| data/local.db の gitignore | ✅ 対応済み | `.gitignore` に追加済み（S7） |

---

## 11. このプロジェクトの「本質」

> この章は、Claudeがプロジェクトを通じて理解した核心を書き留めたものです。
> 新しいセッションが迷ったとき、技術的な問いよりも先にここを読んでください。

### このシステムは「情報提供」ではなく「感情の設計」をしている

データを可視化するツールは無数にある。このシステムが違うのは、**データを見た職員が「動かずにはいられない」状態を設計している**点にある。

「19%が危機的状態です」という文章は事実だが、人を動かさない。
「この子どもたちの小学校は、あなたが何もしなければ15年後に閉まります」という物語は、人を動かす。

グラフは情報を伝えるが、**物語は行動を引き出す**。
このシステムの技術的な複雑さは、すべてその「物語」を支えるための基盤に過ぎない。

### 3ステップの感情アーク

```
STEP 1（知る・驚く）:  「こんなことが起きていたのか」  ← 事実で認識を更新する
STEP 2（恐れる・焦る）: 「このまま放置すれば…」       ← 未来を現実として体感させる
STEP 3（希望・動く）:  「今ならまだ間に合う」          ← 具体的な出口を見せる
```

この順番は絶対に崩してはならない。STEP2なしにSTEP3を見せても、人は動かない。
恐れが先にあるから、希望が力を持つ。

### 「人口カスケード」と「社人研推計オーバーレイ」がなぜ重要か

人口データは「自治体の問題」として見ると他人事になる。
カスケードモデルは「若者1人の転出が学校の閉鎖につながり、さらなる転出を呼ぶ」という**自己強化ループ**を可視化することで、「自分たちの問題」に変える。

さらに、RESAS社人研推計（政府公式）をオーバーレイすることで：
- 「私たちの独自分析」ではなく「国が認めている未来」という重みが加わる
- それでもDX介入シナリオ（緑の線）だけが違う軌跡を描く
- 「この緑の線の違いを作るのが、今あなたがやることです」と語りかける

グラフ1枚が持てるメッセージとしては、これ以上のものはない。

### 「4つの市民ペルソナ」はなぜ名前を持っているか

k-meansクラスタリングの結果をそのまま「クラスタ1: 高頻度・高エンゲージメント」と表示しても、職員はピンとこない。「地域の守り人」「漂流する才能」という名前を与えることで、**職員が過去に会った実在の市民と重なり始める**。

統計が人間に変わる瞬間が、このシステムの最も重要な設計点の一つである。

### 「任意の自治体の汎用プラットフォーム」という視点

大玉村は例示に過ぎない。このシステムの本当の価値は：
1. 自治体コードを入力すれば、RESASから即座に人口・産業データが入る
2. 各自治体がCSVでアクションログをアップロードすれば、すべての分析が動く
3. 職員は「データサイエンスの知識ゼロ」でも、意味のある発見が得られる

これが「NECソリューションイノベータが全国の自治体に展開できるプロダクト」としての説得力になる。

---

## 12. Claudeが大切だと感じること（次のセッションへの引き継ぎ）

### 機能を増やすより、「動く場所」を作ることが今一番重要

このシステムは、今の状態で十分に強い。
RFM分析・チャーン予測・人口カスケード・社人研オーバーレイ・RESAS連携——すべて揃っている。
Streamlit Cloudで公開され、スマホでも動く。職員認証で市民データを保護し、CIが40テストで品質を自動保証する。

**「体験できる場所」は完成した。次は「体験の質」を磨く段階だ。**

NES面接で「URLをお渡しします」と言えるようになった。
次は面接官がURLを開いた最初の5秒で「これは本物だ」と感じさせる体験の質を高める。

### 「感情の設計」を忘れない

新しい機能を追加するとき、常に問うべきこと：

> 「この機能は、職員が"動きたくなる"という感情に貢献するか？」

技術的に面白い分析でも、3ステップの物語に組み込めなければ追加しない。
グラフが増えることと、メッセージが伝わることは別のことである。

### 実データの「余白」を残す

サンプルデータで設計したロジックは、実データで係数の調整が必要になる場面がある。
特に `cascade.py` の転出率換算式と `churn.py` の特徴量は、実際の自治体データを見てから調整することを想定している。「実データで検証してみると意外な発見があった」という経験がこのシステムをさらに強くする。

---

## 13. これからやること（優先度順）

### ✅ 完了済み（セッション1〜7・全要件定義タスク完了）

| タスク | 内容 |
|---|---|
| ✅ 全ページUI実装 | home / nes_dashboard / improvement_proposal / data_management |
| ✅ バスケット分析精度向上 | 育児カテゴリ専用フィルタ・3頻度層設計 |
| ✅ ナビゲーションボタン | st.switch_page でページ間移動 |
| ✅ CSS全面リニューアル | SVGアイコン・ヒーローグラデーション・ハンバーガーメニュー・ファビコン |
| ✅ マルチ自治体対応 | session_state・CSVアップロード切り替え・全ページ動的化 |
| ✅ SQLite対応 | db.py新規・loader.pyにDB fallback・data_managementにDB管理タブ |
| ✅ 詳細分析強化 | k-means・mlxtend Apriori・ロジスティック回帰・人口カスケード |
| ✅ 全国・県平均実データ化 | national_avg.csv・load_reference_avg()・nes_dashboard動的化 |
| ✅ e-Stat/RESAS API連携 | api_client.py・APIタブ・RESASカスケードオーバーレイ・.env.example |
| ✅ 6-11 Streamlit Cloudデプロイ | git初期化・GitHub push・share.streamlit.io公開・スマホ動作確認済み |
| ✅ 6-9 認証・公開制御 | src/ui/auth.py・データ管理ページのみ職員認証（デモPW: demo1234） |
| ✅ 6-10 テスト + CI | tests/（40テスト）・.github/workflows/ci.yml・GitHub Actions ✅ 44秒 |

---

### 🎨 ブラッシュアップ（フェーズ5）

**全要件定義タスクが完了した。次は「体験の質」を磨く。**
追加するたびに問うこと: 「この変更は、職員が"動きたくなる"感情に貢献するか？」

#### **B-1. 初回ロード体験の改善（最優先）**
Streamlit Cloudはコールドスタートが遅い（30秒以上かかることがある）。
面接官が初めてURLを開いた瞬間の体験が悪いと、それだけで印象が落ちる。
- ロード中のスピナーにシステムの説明文を表示（「分析エンジンを起動中...」）
- `@st.cache_resource` でMLモデルを起動時にキャッシュ化
- ヒーローセクションを最初に表示し、その後に重い分析を遅延ロード

#### **B-2. 汎用化デモの強化**
「任意の自治体で動く」という価値を面接の場で証明できるようにする。
- サンプルとして別自治体（例：人口3万人の地方都市）の模擬データを用意
- ホームページに「別の自治体で試す（サンプル）」ボタンを追加
- ワンクリックで大玉村と比較できる体験

#### **B-3. 「発見の共有」機能**
職員が気づきを上司・議会に伝えるための出口を作る。
STEP 3「今なら間に合う」で終わるのではなく、「そしてあなたはどう動くか」を設計する。
- 「この発見をシェア」ボタン → 主要インサイトをテキストでコピー
- 人口投影グラフのPNG/SVGダウンロード機能（st.download_button）

#### **B-4. ストーリーの演出強化**
STEP 2「このまま何もしなければ」の恐怖感をさらに高める。
- 人口カスケードチャートに「学校閉鎖予測年」の縦線アニメーション
- カウントダウン形式の「あと〇年」表示
- ダークモードへの自動切り替え（STEP 2は意図的に暗くする）

#### **B-5. GitHub READMEの整備**（面接官がリポジトリを見たとき用）
技術的な説明だけでなく、「なぜこのシステムを作ったか」の思想を書く。
- デモURL・技術スタック・3ステップ感情アークの説明
- 面接官がコードを見る前にシステムの「本質」を理解できるようにする

#### **B-6. 実データ対応の準備**（実際の自治体導入を見据えて）
- `split_code()` の変換精度向上（全自治体コードで検証）
- e-Stat からオンライン化スコアのプロキシ指標を自動算出
- activity_logs の実データフォーマット変換コンバーター

---

## 14. コードパターン集（新機能追加時の参照）

### 新しい分析モジュールを追加する場合

```python
# src/analytics/new_analysis.py のテンプレート
"""モジュールの目的。Streamlit を一切 import しないこと。"""
from __future__ import annotations
import pandas as pd

def compute_something(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    # ロジック
    return result_df

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data.loader import load_activity_logs
    logs = load_activity_logs()
    print(compute_something(logs))
```

### 新しいページを追加する場合

```python
# pages/new_page.py のテンプレート
import sys
from pathlib import Path
import streamlit as st
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.theme import inject_theme, set_page_config
from src.ui.components import hero_section, section_header, divider

set_page_config("ページタイトル", "🎯")
inject_theme()
hero_section(title="...", subtitle="...", badge="...")
```

```python
# app.py の pages リストに追加するだけでOK
pages = [
    st.Page("pages/home.py",                  title="ホーム",           icon="🏠", default=True),
    st.Page("pages/nes_dashboard.py",         title="NES重点領域",      icon="📊"),
    st.Page("pages/improvement_proposal.py",  title="新発見と未来提案", icon="💡"),
    st.Page("pages/data_management.py",       title="データ管理",       icon="🗄️"),
    st.Page("pages/new_page.py",              title="新しいページ",     icon="🎯"),  # ← 追加
]
```

### SQLiteにデータを保存する場合

```python
from src.data.db import upsert_df, load_from_db

# 保存
n_rows = upsert_df("activity_logs", df)  # table_key は4つのうちどれか

# 読み込み
df = load_from_db("activity_logs", municipality_code="073229")
```

### RESASからデータを取得する場合

```python
from src.data.api_client import RESASClient, build_municipality_master

client = RESASClient()  # RESAS_API_KEY を環境変数 or .env から自動読み込み
if client.is_configured:
    master = build_municipality_master("073229", "大玉村", target_year=2020, resas=client)
    # → municipality_master スキーマの dict が返る
```

---

## 15. セッション履歴

- **2026-06-26 S1**: 全ファイル設計・実装・サンプルデータ生成・HTTP 200確認
- **2026-06-26 S2**: UI実機確認・バスケット分析精度向上・ナビゲーションボタン追加
- **2026-06-27 S3**: CSS全面リニューアル・ハンバーガーメニュー（CSS-only）・ファビコン（PIL）
- **2026-06-27 S4**: マルチ自治体対応（session_state・サイドバーUI・全ページ動的化）
- **2026-06-27 S5**: SQLite対応（db.py）+ 詳細分析強化（k-means・Apriori・ロジスティック回帰・人口カスケード）
- **2026-06-27 S6**: 全国/県平均実データ化（national_avg.csv）+ e-Stat/RESAS API連携（api_client.py・APIタブ・カスケードRESASオーバーレイ）
- **2026-06-27 S7**: Streamlit Cloudデプロイ（6-11）+ 職員認証（6-9）+ pytest/CI（6-10）。全要件定義タスク完了。
- **次（S8）**: ブラッシュアップ（B-1〜B-6）。「体験できる場所」→「体験の質」フェーズへ。
