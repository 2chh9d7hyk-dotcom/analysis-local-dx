"""データ読み込みモジュール。CSV/アップロードデータを型安全なDataFrameとして提供する。"""
from __future__ import annotations
import logging
from pathlib import Path
import pandas as pd
import streamlit as st
from src.config import SAMPLE_DIR, DEFAULT_MUNICIPALITY_CODE, DEFAULT_MUNICIPALITY_NAME, EXPECTED_SCHEMAS

REFERENCE_DIR = Path(__file__).parent.parent.parent / "data" / "reference"

logger = logging.getLogger(__name__)


# ── キャッシュ付きローダー ────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def load_municipality_master(
    path: str | None = None,
    municipality_code: str = DEFAULT_MUNICIPALITY_CODE,
) -> pd.DataFrame:
    """自治体マスターを読み込む。pathが指定されない場合はサンプルデータを使用。"""
    _path = path or str(SAMPLE_DIR / "municipality_master.csv")
    df = _read_csv(_path)
    df = _coerce_types(df, {
        "municipality_code": str,
        "population_total": int,
        "aging_rate": float,
        "fiscal_health_index": float,
        "target_year": int,
    })
    return df[df["municipality_code"] == municipality_code].reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False)
def load_nes_indicators(
    path: str | None = None,
    municipality_code: str = DEFAULT_MUNICIPALITY_CODE,
) -> pd.DataFrame:
    """NES重点領域指標を読み込む。"""
    _path = path or str(SAMPLE_DIR / "nes_focus_indicators.csv")
    df = _read_csv(_path)
    df = _coerce_types(df, {
        "municipality_code": str,
        "target_year": int,
        "online_score": float,
        "ai_rpa_score": float,
        "data_utilization_score": float,
        "total_score": float,
    })
    return df[df["municipality_code"] == municipality_code].sort_values("target_year").reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False)
def load_staff_time(
    path: str | None = None,
    municipality_code: str = DEFAULT_MUNICIPALITY_CODE,
) -> pd.DataFrame:
    """職員の時間配分データを読み込む。"""
    _path = path or str(SAMPLE_DIR / "staff_time_allocation.csv")
    df = _read_csv(_path)
    df = _coerce_types(df, {
        "municipality_code": str,
        "target_year": int,
        "routine_hours": float,
        "creative_hours": float,
        "total_workforce_hours": float,
    })
    return df[df["municipality_code"] == municipality_code].sort_values("target_year").reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False)
def load_activity_logs(
    path: str | None = None,
    municipality_code: str = DEFAULT_MUNICIPALITY_CODE,
) -> pd.DataFrame:
    """住民・行政アクションログを読み込む。"""
    _path = path or str(SAMPLE_DIR / "activity_logs.csv")
    df = _read_csv(_path)
    df = _coerce_types(df, {
        "municipality_code": str,
        "frequency_score": int,
        "recency_days": int,
        "engagement_value": float,
    })
    if "action_date" in df.columns:
        df["action_date"] = pd.to_datetime(df["action_date"], errors="coerce")
    return df[df["municipality_code"] == municipality_code].reset_index(drop=True)


# ── アップロードデータのローダー ────────────────────────────────

def load_from_uploaded(uploaded_file, table_key: str) -> tuple[pd.DataFrame | None, str]:
    """
    Streamlit UploadedFile からデータを読み込む。
    Returns: (DataFrame or None, error_message)
    """
    try:
        df = pd.read_csv(uploaded_file)
        expected = EXPECTED_SCHEMAS.get(table_key, [])
        missing = [c for c in expected if c not in df.columns]
        if missing:
            return None, f"必須カラムが不足しています: {', '.join(missing)}"
        return df, ""
    except Exception as e:
        logger.exception("Failed to load uploaded file")
        return None, f"ファイル読み込みエラー: {e}"


def detect_table_type(df: pd.DataFrame) -> str | None:
    """DataFrameのカラムからテーブル種別を自動推定する。"""
    cols = set(df.columns)
    for table_key, expected in EXPECTED_SCHEMAS.items():
        if len(set(expected) & cols) >= len(expected) * 0.8:
            return table_key
    return None


# ── 内部ユーティリティ ────────────────────────────────────────

def _read_csv(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        logger.warning("CSV not found: %s — returning empty DataFrame", path)
        return pd.DataFrame()
    try:
        return pd.read_csv(p, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(p, encoding="cp932")


def _coerce_types(df: pd.DataFrame, type_map: dict[str, type]) -> pd.DataFrame:
    """カラムの型を強制変換する。変換失敗時はNaNを維持。"""
    for col, dtype in type_map.items():
        if col not in df.columns:
            continue
        try:
            if dtype == int:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            elif dtype == float:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif dtype == str:
                df[col] = df[col].astype(str)
                # 自治体コードは6桁にゼロパディング（例: "73229" → "073229"）
                if col == "municipality_code":
                    df[col] = df[col].str.strip().str.zfill(6)
        except Exception as e:
            logger.warning("Type coercion failed for %s: %s", col, e)
    return df


# ── マルチ自治体対応: session_state 経由のアクティブデータ取得 ────

def active_municipality_code() -> str:
    """現在選択中の自治体コードを返す。"""
    return st.session_state.get("active_municipality_code", DEFAULT_MUNICIPALITY_CODE)


def active_municipality_name() -> str:
    """現在選択中の自治体名を返す。"""
    return st.session_state.get("active_municipality_name", DEFAULT_MUNICIPALITY_NAME)


def get_active_master() -> pd.DataFrame:
    """アップロードデータ優先で現在の自治体マスターを返す。session_state → DB → サンプルCSV の順。"""
    from src.data.db import load_from_db
    tables: dict = st.session_state.get("uploaded_tables", {})
    code = active_municipality_code()
    if "municipality_master" in tables:
        df = _coerce_types(tables["municipality_master"].copy(), {
            "municipality_code": str,
            "population_total": int,
            "aging_rate": float,
            "fiscal_health_index": float,
            "target_year": int,
        })
        subset = df[df["municipality_code"] == code].reset_index(drop=True)
        if not subset.empty:
            return subset
    db_df = load_from_db("municipality_master", code)
    if not db_df.empty:
        return _coerce_types(db_df, {
            "municipality_code": str,
            "population_total": int,
            "aging_rate": float,
            "fiscal_health_index": float,
            "target_year": int,
        })
    return load_municipality_master(municipality_code=code)


def get_active_indicators() -> pd.DataFrame:
    """アップロードデータ優先で現在の自治体NES指標を返す。session_state → DB → サンプルCSV の順。"""
    from src.data.db import load_from_db
    tables: dict = st.session_state.get("uploaded_tables", {})
    code = active_municipality_code()
    _type_map = {
        "municipality_code": str,
        "target_year": int,
        "online_score": float,
        "ai_rpa_score": float,
        "data_utilization_score": float,
        "total_score": float,
    }
    if "nes_focus_indicators" in tables:
        df = _coerce_types(tables["nes_focus_indicators"].copy(), _type_map)
        subset = df[df["municipality_code"] == code].sort_values("target_year").reset_index(drop=True)
        if not subset.empty:
            return subset
    db_df = load_from_db("nes_focus_indicators", code)
    if not db_df.empty:
        return _coerce_types(db_df, _type_map).sort_values("target_year").reset_index(drop=True)
    return load_nes_indicators(municipality_code=code)


def get_active_staff_time() -> pd.DataFrame:
    """アップロードデータ優先で現在の自治体職員時間配分を返す。session_state → DB → サンプルCSV の順。"""
    from src.data.db import load_from_db
    tables: dict = st.session_state.get("uploaded_tables", {})
    code = active_municipality_code()
    _type_map = {
        "municipality_code": str,
        "target_year": int,
        "routine_hours": float,
        "creative_hours": float,
        "total_workforce_hours": float,
    }
    if "staff_time_allocation" in tables:
        df = _coerce_types(tables["staff_time_allocation"].copy(), _type_map)
        subset = df[df["municipality_code"] == code].sort_values("target_year").reset_index(drop=True)
        if not subset.empty:
            return subset
    db_df = load_from_db("staff_time_allocation", code)
    if not db_df.empty:
        return _coerce_types(db_df, _type_map).sort_values("target_year").reset_index(drop=True)
    return load_staff_time(municipality_code=code)


def get_active_activity_logs() -> pd.DataFrame:
    """アップロードデータ優先で現在の自治体アクションログを返す。session_state → DB → サンプルCSV の順。"""
    from src.data.db import load_from_db
    tables: dict = st.session_state.get("uploaded_tables", {})
    code = active_municipality_code()
    _type_map = {
        "municipality_code": str,
        "frequency_score": int,
        "recency_days": int,
        "engagement_value": float,
    }

    def _process(df: pd.DataFrame) -> pd.DataFrame:
        df = _coerce_types(df, _type_map)
        if "action_date" in df.columns:
            df["action_date"] = pd.to_datetime(df["action_date"], errors="coerce")
        return df

    if "activity_logs" in tables:
        df = _process(tables["activity_logs"].copy())
        subset = df[df["municipality_code"] == code].reset_index(drop=True)
        if not subset.empty:
            return subset
    db_df = load_from_db("activity_logs", code)
    if not db_df.empty:
        return _process(db_df)
    return load_activity_logs(municipality_code=code)


@st.cache_data(ttl=3600, show_spinner=False)
def load_reference_avg(year: int | None = None) -> dict[str, dict[str, float]]:
    """全国平均・県平均の参照データを返す。

    Returns:
        {"national": {area: score, ...}, "pref": {area: score, ...}}
        area は "online" / "ai_rpa" / "data" / "total"
    """
    _defaults = {
        "national": {"online": 55.0, "ai_rpa": 42.0, "data": 38.0, "total": 45.0},
        "pref":     {"online": 48.0, "ai_rpa": 35.0, "data": 30.0, "total": 38.0},
    }
    csv_path = REFERENCE_DIR / "national_avg.csv"
    if not csv_path.exists():
        logger.warning("national_avg.csv not found at %s — using built-in defaults", csv_path)
        return _defaults

    df = _read_csv(str(csv_path))
    if df.empty or "target_year" not in df.columns:
        return _defaults

    df["target_year"] = pd.to_numeric(df["target_year"], errors="coerce").fillna(0).astype(int)

    if year is not None:
        subset = df[df["target_year"] == year]
        if subset.empty:
            available = sorted(df["target_year"].unique())
            closest = min(available, key=lambda y: abs(y - year))
            subset = df[df["target_year"] == closest]
    else:
        latest_year = int(df["target_year"].max())
        subset = df[df["target_year"] == latest_year]

    result: dict[str, dict[str, float]] = {"national": {}, "pref": {}}
    for _, row in subset.iterrows():
        area = str(row.get("area", "")).strip()
        if area not in ("online", "ai_rpa", "data", "total"):
            continue
        result["national"][area] = float(row.get("national_avg", 0))
        result["pref"][area]     = float(row.get("pref_avg", 0))

    for key in ("national", "pref"):
        for area in ("online", "ai_rpa", "data", "total"):
            result[key].setdefault(area, _defaults[key][area])

    return result


def get_latest_year(df: pd.DataFrame) -> int | None:
    """DataFrameの最新年度を返す。"""
    if "target_year" not in df.columns or df.empty:
        return None
    return int(df["target_year"].max())


def get_year_delta(df: pd.DataFrame, col: str, year: int) -> float | None:
    """指定年と前年の差分を返す。"""
    if df.empty or "target_year" not in df.columns:
        return None
    row_now = df[df["target_year"] == year]
    row_prev = df[df["target_year"] == year - 1]
    if row_now.empty or row_prev.empty:
        return None
    return float(row_now[col].iloc[0]) - float(row_prev[col].iloc[0])
