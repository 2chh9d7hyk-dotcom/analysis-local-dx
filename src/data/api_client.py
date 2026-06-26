"""e-Stat / RESAS API クライアント。APIキーがない場合はグレースフルデグレードする。

Streamlit を import しないこと（analytics 層と同じルール）。
ページ層から呼ばれ、キャッシュは呼び出し元で @st.cache_data を使う。
"""
from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent.parent / ".env")
    except ImportError:
        pass


_load_dotenv()


def get_api_key(name: str) -> str | None:
    """環境変数 → Streamlit Secrets の順でAPIキーを取得する。"""
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st  # type: ignore
        return st.secrets.get(name)
    except Exception:
        return None


# ── e-Stat クライアント ────────────────────────────────────────

class EStatClient:
    """政府統計の総合窓口 (e-Stat) REST API 3.0 クライアント。"""

    BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json"
    TIMEOUT = 15

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_api_key("ESTAT_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get(self, endpoint: str, params: dict[str, Any]) -> dict | None:
        if not self.is_configured:
            return None
        try:
            import requests
            resp = requests.get(
                f"{self.BASE_URL}/{endpoint}",
                params={"appId": self.api_key, **params},
                timeout=self.TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("e-Stat API error [%s]: %s", endpoint, exc)
            return None

    def ping(self) -> bool:
        """APIキーの疎通確認。"""
        data = self._get("getStatsList", {"searchWord": "人口", "limit": "1"})
        return data is not None

    def search_population_datasets(self) -> list[dict]:
        """人口関連統計データセット一覧を返す（最大10件）。"""
        data = self._get("getStatsList", {
            "searchWord": "人口 市区町村",
            "statsField": "02",
            "limit": "10",
        })
        if not data:
            return []
        try:
            tables = data["GET_STATS_LIST"]["DATALIST_INF"]["TABLE_INF"]
            if isinstance(tables, dict):
                tables = [tables]
            return [
                {
                    "id": t["@id"],
                    "title": t.get("TITLE", {}).get("$", ""),
                    "survey_date": t.get("SURVEY_DATE", ""),
                    "gov_org": t.get("GOV_ORG", {}).get("$", ""),
                }
                for t in tables
            ]
        except (KeyError, TypeError):
            return []

    def fetch_population_by_municipality(
        self,
        municipality_code: str,
        stats_data_id: str = "0003443229",
    ) -> dict | None:
        """
        市区町村別人口データを取得する。
        デフォルト statsDataId: 国勢調査2020 年齢(各歳), 男女別人口
        """
        data = self._get("getStatsData", {
            "statsDataId": stats_data_id,
            "cdArea": municipality_code,
            "metaGetFlg": "N",
            "cntGetFlg": "N",
            "explanationGetFlg": "N",
        })
        if not data:
            return None
        try:
            values = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
            if isinstance(values, dict):
                values = [values]
            return {"values": values, "municipality_code": municipality_code}
        except (KeyError, TypeError) as exc:
            logger.error("e-Stat parse error: %s", exc)
            return None


# ── RESAS クライアント ────────────────────────────────────────

class RESASClient:
    """地域経済分析システム (RESAS) API v1 クライアント。"""

    BASE_URL = "https://opendata.resas-portal.go.jp/api/v1"
    TIMEOUT = 15

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_api_key("RESAS_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict | None:
        if not self.is_configured:
            return None
        try:
            import requests
            resp = requests.get(
                f"{self.BASE_URL}{path}",
                params=params or {},
                headers={"X-API-KEY": self.api_key},
                timeout=self.TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("RESAS API error [%s]: %s", path, exc)
            return None

    def ping(self) -> bool:
        """APIキーの疎通確認。"""
        data = self._get("/prefectures")
        return bool(data and "result" in data)

    @staticmethod
    def split_code(code_6: str) -> tuple[int, str]:
        """
        6桁自治体コード → RESAS の (prefCode, cityCode) に変換する。
        例: "073229" → (7, "07322")
        ※ 6桁目はチェックディジットのため除外し5桁 cityCode とする。
        """
        pref = int(code_6[:2])
        city = code_6[:5]
        return pref, city

    def fetch_population_sum(self, municipality_code: str) -> dict | None:
        """
        人口推移（実績 + 社人研推計）を取得する。
        Returns: {
            "boundary_year": int,  # 実績と推計の境界年
            "series": [{"label": str, "data": [{"year": int, "value": int}]}]
        }
        """
        pref, city = self.split_code(municipality_code)
        data = self._get(
            "/population/sum/perYear",
            {"prefCode": pref, "cityCode": city},
        )
        if not data or "result" not in data or not data["result"]:
            return None
        result = data["result"]
        return {
            "boundary_year": result.get("boundaryYear", 2020),
            "series": result.get("data", []),
        }

    def fetch_population_composition(self, municipality_code: str) -> list[dict] | None:
        """
        年齢3区分別人口推移を取得する。
        Returns: [{"year": int, "total": int, "young": int, "working": int,
                   "elderly": int, "aging_rate": float}, ...]
        """
        pref, city = self.split_code(municipality_code)
        data = self._get(
            "/population/composition/perYear",
            {"prefCode": pref, "cityCode": city},
        )
        if not data or "result" not in data or not data["result"]:
            return None

        label_map = {
            "総人口": "total",
            "年少人口": "young",
            "生産年齢人口": "working",
            "老年人口": "elderly",
        }
        by_year: dict[int, dict] = {}
        for series in data["result"].get("data", []):
            key = label_map.get(series.get("label", ""))
            if not key:
                continue
            for pt in series.get("data", []):
                yr = int(pt["year"])
                by_year.setdefault(yr, {})[key] = int(pt["value"])

        rows = []
        for yr in sorted(by_year):
            d = by_year[yr]
            total = d.get("total", 0)
            elderly = d.get("elderly", 0)
            rows.append({
                "year": yr,
                "total": total,
                "young": d.get("young", 0),
                "working": d.get("working", 0),
                "elderly": elderly,
                "aging_rate": round(elderly / total, 4) if total > 0 else 0.0,
            })
        return rows if rows else None

    def fetch_industry_structure(
        self, municipality_code: str, year: int = 2015
    ) -> dict | None:
        """
        産業別就業人口から第1〜3次産業比率を返す。
        Returns: {"primary": float, "secondary": float, "tertiary": float}
        """
        pref, city = self.split_code(municipality_code)
        data = self._get(
            "/municipality/industry/power/forArea",
            {"prefCode": pref, "cityCode": city, "sicCode": "-", "year": str(year)},
        )
        if not data or "result" not in data or not data["result"]:
            return None

        totals = {"primary": 0.0, "secondary": 0.0, "tertiary": 0.0}
        for ind in data["result"].get("industries", []):
            code = str(ind.get("sicCode", ""))
            emp = float(ind.get("employees") or 0)
            if code in ("A", "B"):
                totals["primary"] += emp
            elif code in ("C", "D", "E"):
                totals["secondary"] += emp
            else:
                totals["tertiary"] += emp

        grand = sum(totals.values())
        if grand <= 0:
            return None
        return {k: round(v / grand, 3) for k, v in totals.items()}

    def fetch_net_migration(self, municipality_code: str) -> list[dict] | None:
        """
        社会増減（転入数・転出数・純移動数）を取得する。
        Returns: [{"year": int, "inflow": int, "outflow": int, "net": int}, ...]
        """
        pref, city = self.split_code(municipality_code)
        data = self._get(
            "/population/society/forCity",
            {"prefCode": pref, "cityCode": city},
        )
        if not data or "result" not in data or not data["result"]:
            return None

        rows = []
        for pt in data["result"].get("data", []):
            rows.append({
                "year": int(pt.get("year", 0)),
                "inflow": int(pt.get("moveFrom", 0) or 0),
                "outflow": int(pt.get("moveTo", 0) or 0),
                "net": int(pt.get("net", 0) or 0),
            })
        return rows if rows else None


# ── 統合ファクトリー ──────────────────────────────────────────

def build_municipality_master(
    municipality_code: str,
    municipality_name: str,
    target_year: int = 2020,
    resas: RESASClient | None = None,
) -> dict | None:
    """
    RESAS から municipality_master スキーマ1行分のデータを構築する。
    Returns: dict（失敗時は None）
    """
    client = resas or RESASClient()
    if not client.is_configured:
        return None

    comp = client.fetch_population_composition(municipality_code)
    if not comp:
        return None

    available = [r["year"] for r in comp]
    actual_year = min(available, key=lambda y: abs(y - target_year)) if available else None
    if not actual_year:
        return None

    row = next((r for r in comp if r["year"] == actual_year), None)
    if not row:
        return None

    industry = client.fetch_industry_structure(municipality_code) or {
        "primary": 0.0, "secondary": 0.0, "tertiary": 1.0,
    }

    return {
        "municipality_code": municipality_code,
        "name": municipality_name,
        "population_total": row["total"],
        "aging_rate": row["aging_rate"],
        "industry_structure": json.dumps(industry, ensure_ascii=False),
        "fiscal_health_index": 0.50,  # APIからは取得不可 → デフォルト値
        "target_year": actual_year,
    }
