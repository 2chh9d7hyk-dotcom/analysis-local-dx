"""データモデル定義（dataclasses）。型安全な入出力の基盤。"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import json


@dataclass
class MunicipalityMaster:
    municipality_code: str
    name: str
    population_total: int
    aging_rate: float
    industry_structure: dict  # {"primary": 0.15, "secondary": 0.28, "tertiary": 0.57}
    fiscal_health_index: float
    target_year: int

    @classmethod
    def from_row(cls, row: dict) -> "MunicipalityMaster":
        industry = row.get("industry_structure", "{}")
        if isinstance(industry, str):
            try:
                industry = json.loads(industry)
            except (json.JSONDecodeError, TypeError):
                industry = {}
        return cls(
            municipality_code=str(row["municipality_code"]),
            name=str(row["name"]),
            population_total=int(row["population_total"]),
            aging_rate=float(row["aging_rate"]),
            industry_structure=industry,
            fiscal_health_index=float(row["fiscal_health_index"]),
            target_year=int(row["target_year"]),
        )

    @property
    def youth_rate(self) -> float:
        """15歳未満人口比率（間接推計用）。"""
        return max(0.0, 1.0 - self.aging_rate - 0.6)

    @property
    def industry_label(self) -> str:
        s = self.industry_structure
        parts = []
        if s.get("primary", 0) > 0:
            parts.append(f"1次 {s['primary']*100:.0f}%")
        if s.get("secondary", 0) > 0:
            parts.append(f"2次 {s['secondary']*100:.0f}%")
        if s.get("tertiary", 0) > 0:
            parts.append(f"3次 {s['tertiary']*100:.0f}%")
        return " / ".join(parts)


@dataclass
class NESFocusIndicator:
    municipality_code: str
    target_year: int
    online_score: float
    ai_rpa_score: float
    data_utilization_score: float
    total_score: float

    @classmethod
    def from_row(cls, row: dict) -> "NESFocusIndicator":
        return cls(
            municipality_code=str(row["municipality_code"]),
            target_year=int(row["target_year"]),
            online_score=float(row["online_score"]),
            ai_rpa_score=float(row["ai_rpa_score"]),
            data_utilization_score=float(row["data_utilization_score"]),
            total_score=float(row["total_score"]),
        )

    @property
    def weakest_area(self) -> str:
        areas = {
            "オンライン化": self.online_score,
            "AI/RPA": self.ai_rpa_score,
            "データ活用": self.data_utilization_score,
        }
        return min(areas, key=areas.get)

    @property
    def strongest_area(self) -> str:
        areas = {
            "オンライン化": self.online_score,
            "AI/RPA": self.ai_rpa_score,
            "データ活用": self.data_utilization_score,
        }
        return max(areas, key=areas.get)


@dataclass
class StaffTimeAllocation:
    municipality_code: str
    target_year: int
    routine_hours: float
    creative_hours: float
    total_workforce_hours: float

    @classmethod
    def from_row(cls, row: dict) -> "StaffTimeAllocation":
        return cls(
            municipality_code=str(row["municipality_code"]),
            target_year=int(row["target_year"]),
            routine_hours=float(row["routine_hours"]),
            creative_hours=float(row["creative_hours"]),
            total_workforce_hours=float(row["total_workforce_hours"]),
        )

    @property
    def routine_ratio(self) -> float:
        if self.total_workforce_hours == 0:
            return 0.0
        return self.routine_hours / self.total_workforce_hours

    @property
    def creative_ratio(self) -> float:
        if self.total_workforce_hours == 0:
            return 0.0
        return self.creative_hours / self.total_workforce_hours


@dataclass
class ActivityLog:
    log_id: str
    municipality_code: str
    citizen_id: str
    category: str
    action_type: str
    target_age_group: str
    action_date: date
    frequency_score: int      # 1-5
    recency_days: int         # 直近行動からの経過日数（RFM: R）
    engagement_value: float   # 1-10 （RFM: M）

    @classmethod
    def from_row(cls, row: dict) -> "ActivityLog":
        action_date = row["action_date"]
        if isinstance(action_date, str):
            from datetime import datetime
            action_date = datetime.strptime(action_date, "%Y-%m-%d").date()
        return cls(
            log_id=str(row["log_id"]),
            municipality_code=str(row["municipality_code"]),
            citizen_id=str(row["citizen_id"]),
            category=str(row["category"]),
            action_type=str(row["action_type"]),
            target_age_group=str(row["target_age_group"]),
            action_date=action_date,
            frequency_score=int(row["frequency_score"]),
            recency_days=int(row["recency_days"]),
            engagement_value=float(row["engagement_value"]),
        )


@dataclass
class RFMSegment:
    """RFM分析の結果セグメント。"""
    citizen_id: str
    municipality_code: str
    r_score: int           # 1-5（高いほど最近）
    f_score: int           # 1-5（高いほど頻繁）
    m_score: int           # 1-5（高いほど価値高）
    rfm_total: int         # r+f+m
    segment_label: str     # 例: "アクティブ市民", "潜在離脱者"
    primary_category: str
    age_group: str
    churn_risk: float      # 0.0-1.0


@dataclass
class BasketRule:
    """アソシエーションルール（バスケット分析）の1ルール。"""
    antecedent: str        # 前件（例: "子育て施設チェックイン"）
    consequent: str        # 後件（例: "オンライン申請"）
    support: float
    confidence: float
    lift: float
    category_ant: str
    category_con: str
