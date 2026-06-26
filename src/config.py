"""アプリケーション全体の設定定数。"""
from pathlib import Path

# ── パス設定 ───────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
UPLOAD_DIR = DATA_DIR / "uploads"

# ── デフォルト自治体 ────────────────────────────────────────
DEFAULT_MUNICIPALITY_CODE = "073229"
DEFAULT_MUNICIPALITY_NAME = "大玉村"

# ── カラーパレット（デザインシステム準拠） ────────────────────
COLORS = {
    # ベース
    "bg_app": "#F3F4F6",
    "bg_card": "#FFFFFF",
    "border": "#E5E7EB",
    # テキスト
    "text_main": "#1F2937",
    "text_sub": "#4B5563",
    "text_muted": "#9CA3AF",
    # NES重点領域アクセント
    "online": "#3B82F6",       # オンライン化（ブルー）
    "ai_rpa": "#7C3AED",       # AI/RPA（バイオレット）
    "data": "#06B6D4",         # データ活用（シアン）
    "positive": "#22C55E",     # ポジティブ効果（グリーン）
    # セマンティック
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#3B82F6",
    "success": "#22C55E",
}

# NES領域ラベルとカラーのマッピング
NES_AREAS = {
    "online": {"label": "オンライン化", "color": COLORS["online"], "icon": ""},
    "ai_rpa": {"label": "AI/RPA", "color": COLORS["ai_rpa"], "icon": ""},
    "data": {"label": "データ活用", "color": COLORS["data"], "icon": ""},
    "positive": {"label": "ポジティブ効果", "color": COLORS["positive"], "icon": ""},
}

# ── 分析設定 ────────────────────────────────────────────────
RFM_BINS = 5           # RFMスコア分割数
CHURN_THRESHOLD_DAYS = 90     # 離脱判定の経過日数
CHURN_DECLINE_RATE = 0.30     # 要警戒フラグの前月比減少率
BASKET_MIN_SUPPORT = 0.05     # バスケット分析の最小支持度
BASKET_MIN_CONFIDENCE = 0.30  # バスケット分析の最小確信度

# ── カテゴリ定義 ────────────────────────────────────────────
CATEGORIES = ["教育", "育児", "若者支援", "人口移住対策", "起業支援", "行政手続き"]

ACTION_TYPES = {
    "教育": ["施設チェックイン", "図書館利用", "学習支援参加"],
    "育児": ["子育て施設チェックイン", "子育て相談", "児童手当申請(オンライン)", "保育所申込(窓口)"],
    "若者支援": ["コワーキング利用", "起業サロン参加", "キャリア相談"],
    "人口移住対策": ["移住相談", "UIターン窓口"],
    "行政手続き": ["窓口申請", "オンライン申請", "マイナンバー手続き"],
    "起業支援": ["創業セミナー参加", "補助金申請(窓口)", "補助金申請(オンライン)"],
}

AGE_GROUPS = ["10代", "20代若者", "30代子育て層", "20代子育て層", "40代", "50代以上"]

# ── CSVスキーマ期待フィールド ───────────────────────────────
EXPECTED_SCHEMAS = {
    "municipality_master": [
        "municipality_code", "name", "population_total", "aging_rate",
        "industry_structure", "fiscal_health_index", "target_year",
    ],
    "nes_focus_indicators": [
        "municipality_code", "target_year", "online_score",
        "ai_rpa_score", "data_utilization_score", "total_score",
    ],
    "staff_time_allocation": [
        "municipality_code", "target_year", "routine_hours",
        "creative_hours", "total_workforce_hours",
    ],
    "activity_logs": [
        "log_id", "municipality_code", "citizen_id", "category",
        "action_type", "target_age_group", "action_date",
        "frequency_score", "recency_days", "engagement_value",
    ],
}
