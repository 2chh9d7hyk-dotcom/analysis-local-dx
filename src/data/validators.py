"""スキーマバリデーション。アップロードされたCSVの整合性チェック。"""
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from src.config import EXPECTED_SCHEMAS


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    row_count: int
    detected_table: str | None = None

    @property
    def summary(self) -> str:
        if self.is_valid:
            return f"✅ バリデーション OK ({self.row_count}行)"
        return f"❌ バリデーションエラー ({len(self.errors)}件)"


def validate_csv(df: pd.DataFrame, table_key: str) -> ValidationResult:
    """CSVデータのバリデーションを実行する。"""
    errors: list[str] = []
    warnings: list[str] = []
    expected_cols = EXPECTED_SCHEMAS.get(table_key, [])

    # 必須カラムチェック
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        errors.append(f"必須カラムが不足: {', '.join(missing)}")

    # 空データチェック
    if df.empty:
        errors.append("データが空です。")
        return ValidationResult(False, errors, warnings, 0, table_key)

    # テーブル別バリデーション
    validators = {
        "municipality_master": _validate_municipality_master,
        "nes_focus_indicators": _validate_nes_indicators,
        "staff_time_allocation": _validate_staff_time,
        "activity_logs": _validate_activity_logs,
    }
    if table_key in validators and not missing:
        extra_errors, extra_warnings = validators[table_key](df)
        errors.extend(extra_errors)
        warnings.extend(extra_warnings)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        row_count=len(df),
        detected_table=table_key,
    )


def _validate_municipality_master(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if "aging_rate" in df.columns:
        invalid = df["aging_rate"].apply(lambda x: not (0 <= float(x) <= 1) if pd.notna(x) else False)
        if invalid.any():
            errors.append("aging_rate は 0〜1 の範囲で指定してください。")
    if "fiscal_health_index" in df.columns:
        if (pd.to_numeric(df["fiscal_health_index"], errors="coerce") < 0).any():
            warnings.append("fiscal_health_index に負の値が含まれています。")
    if "population_total" in df.columns:
        if (pd.to_numeric(df["population_total"], errors="coerce") <= 0).any():
            errors.append("population_total は正の整数である必要があります。")
    return errors, warnings


def _validate_nes_indicators(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    score_cols = ["online_score", "ai_rpa_score", "data_utilization_score", "total_score"]
    for col in score_cols:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            if (vals < 0).any() or (vals > 100).any():
                errors.append(f"{col} は 0〜100 の範囲で指定してください。")
    return errors, warnings


def _validate_staff_time(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    hour_cols = ["routine_hours", "creative_hours", "total_workforce_hours"]
    for col in hour_cols:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            if (vals < 0).any():
                errors.append(f"{col} は 0 以上の値である必要があります。")
    if all(c in df.columns for c in ["routine_hours", "creative_hours", "total_workforce_hours"]):
        df_num = df[hour_cols].apply(pd.to_numeric, errors="coerce")
        total_check = df_num["routine_hours"] + df_num["creative_hours"]
        if (total_check > df_num["total_workforce_hours"] * 1.01).any():
            warnings.append("routine_hours + creative_hours が total_workforce_hours を超える行があります。")
    return errors, warnings


def _validate_activity_logs(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if "frequency_score" in df.columns:
        vals = pd.to_numeric(df["frequency_score"], errors="coerce")
        if (vals < 1).any() or (vals > 5).any():
            errors.append("frequency_score は 1〜5 の範囲で指定してください。")
    if "engagement_value" in df.columns:
        vals = pd.to_numeric(df["engagement_value"], errors="coerce")
        if (vals < 1).any() or (vals > 10).any():
            warnings.append("engagement_value は 1〜10 の範囲が推奨です。")
    if "recency_days" in df.columns:
        vals = pd.to_numeric(df["recency_days"], errors="coerce")
        if (vals < 0).any():
            errors.append("recency_days は 0 以上の値である必要があります。")
    if "action_date" in df.columns:
        try:
            pd.to_datetime(df["action_date"])
        except Exception:
            errors.append("action_date は YYYY-MM-DD 形式で指定してください。")
    if "log_id" in df.columns and df["log_id"].duplicated().any():
        warnings.append("log_id に重複があります。")
    return errors, warnings


def show_validation_result(result: ValidationResult) -> None:
    """Streamlit上にバリデーション結果を表示する。"""
    import streamlit as st
    if result.is_valid:
        st.success(f"✅ バリデーション完了 — {result.row_count}行のデータが正常です。")
    else:
        st.error(f"❌ バリデーションエラー ({len(result.errors)}件)")
        for err in result.errors:
            st.error(f"• {err}", icon="🚫")
    for warn in result.warnings:
        st.warning(f"• {warn}", icon="⚠️")
