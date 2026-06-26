"""SQLite永続化レイヤー。アップロードCSVをセッションをまたいで保持する中間ストレージ。"""
from __future__ import annotations
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = Path("data/local.db")

_DDL: dict[str, str] = {
    "municipality_master": (
        "CREATE TABLE IF NOT EXISTS municipality_master ("
        "municipality_code TEXT, name TEXT, population_total INTEGER, "
        "aging_rate REAL, industry_structure TEXT, fiscal_health_index REAL, "
        "target_year INTEGER, PRIMARY KEY (municipality_code, target_year))"
    ),
    "nes_focus_indicators": (
        "CREATE TABLE IF NOT EXISTS nes_focus_indicators ("
        "municipality_code TEXT, target_year INTEGER, online_score REAL, "
        "ai_rpa_score REAL, data_utilization_score REAL, total_score REAL, "
        "PRIMARY KEY (municipality_code, target_year))"
    ),
    "staff_time_allocation": (
        "CREATE TABLE IF NOT EXISTS staff_time_allocation ("
        "municipality_code TEXT, target_year INTEGER, routine_hours REAL, "
        "creative_hours REAL, total_workforce_hours REAL, "
        "PRIMARY KEY (municipality_code, target_year))"
    ),
    "activity_logs": (
        "CREATE TABLE IF NOT EXISTS activity_logs ("
        "log_id TEXT PRIMARY KEY, municipality_code TEXT, citizen_id TEXT, "
        "category TEXT, action_type TEXT, target_age_group TEXT, action_date TEXT, "
        "frequency_score INTEGER, recency_days INTEGER, engagement_value REAL)"
    ),
}


@contextmanager
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    """全テーブルを作成（存在しない場合のみ）。"""
    with _conn() as con:
        for ddl in _DDL.values():
            con.execute(ddl)


def upsert_df(table_key: str, df: pd.DataFrame) -> int:
    """DataFrameをSQLiteにUPSERT。戻り値は保存した行数。"""
    if df.empty or table_key not in _DDL:
        return 0
    init_db()
    with _conn() as con:
        # activity_logsはlog_id単位でマージ、他は自治体×年度でREPLACE
        if table_key == "activity_logs" and "municipality_code" in df.columns:
            code = str(df["municipality_code"].iloc[0]).strip().zfill(6)
            con.execute("DELETE FROM activity_logs WHERE municipality_code = ?", (code,))
        elif "municipality_code" in df.columns and "target_year" in df.columns:
            code = str(df["municipality_code"].iloc[0]).strip().zfill(6)
            con.execute(f"DELETE FROM {table_key} WHERE municipality_code = ?", (code,))
        df.to_sql(table_key, con, if_exists="append", index=False)
    return len(df)


def load_from_db(table_key: str, municipality_code: str) -> pd.DataFrame:
    """DBから指定自治体のデータを読み込む。テーブル未存在や空の場合は空DataFrame。"""
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with _conn() as con:
            return pd.read_sql_query(
                f"SELECT * FROM {table_key} WHERE municipality_code = ?",
                con,
                params=(municipality_code,),
            )
    except Exception as e:
        logger.warning("DB load failed for %s/%s: %s", table_key, municipality_code, e)
        return pd.DataFrame()


def list_municipalities_in_db() -> pd.DataFrame:
    """DB内の自治体一覧を municipality_master から返す。"""
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with _conn() as con:
            return pd.read_sql_query(
                "SELECT municipality_code, name, MAX(target_year) AS latest_year "
                "FROM municipality_master GROUP BY municipality_code, name "
                "ORDER BY municipality_code",
                con,
            )
    except Exception:
        return pd.DataFrame()


def list_tables_in_db() -> dict[str, int]:
    """各テーブルの保存済み行数を返す。テーブルが存在しない場合は0。"""
    if not DB_PATH.exists():
        return {k: 0 for k in _DDL}
    counts: dict[str, int] = {}
    try:
        with _conn() as con:
            for table_key in _DDL:
                try:
                    row = con.execute(f"SELECT COUNT(*) FROM {table_key}").fetchone()
                    counts[table_key] = row[0] if row else 0
                except Exception:
                    counts[table_key] = 0
    except Exception:
        counts = {k: 0 for k in _DDL}
    return counts


def delete_municipality_from_db(municipality_code: str) -> None:
    """指定自治体のデータをDB全テーブルから削除する。"""
    if not DB_PATH.exists():
        return
    with _conn() as con:
        for table_key in _DDL:
            try:
                con.execute(
                    f"DELETE FROM {table_key} WHERE municipality_code = ?",
                    (municipality_code,),
                )
            except Exception as e:
                logger.warning("Delete failed for %s/%s: %s", table_key, municipality_code, e)
