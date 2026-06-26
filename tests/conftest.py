"""共有フィクスチャ。サンプルデータを一度だけ読み込んでテスト間で使い回す。"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample"


@pytest.fixture(scope="session")
def sample_logs() -> pd.DataFrame:
    """activity_logs.csv をロードして型変換した DataFrame。"""
    df = pd.read_csv(SAMPLE_DIR / "activity_logs.csv", encoding="utf-8-sig")
    df["action_date"] = pd.to_datetime(df["action_date"], errors="coerce")
    df["frequency_score"] = pd.to_numeric(df["frequency_score"], errors="coerce").fillna(0).astype(int)
    df["recency_days"] = pd.to_numeric(df["recency_days"], errors="coerce").fillna(0).astype(int)
    df["engagement_value"] = pd.to_numeric(df["engagement_value"], errors="coerce")
    df["municipality_code"] = df["municipality_code"].astype(str).str.zfill(6)
    return df[df["municipality_code"] == "073229"].reset_index(drop=True)


@pytest.fixture(scope="session")
def minimal_logs() -> pd.DataFrame:
    """最小限のインラインデータ。エッジケーステスト用。"""
    return pd.DataFrame({
        "log_id": [f"L{i:03d}" for i in range(20)],
        "municipality_code": ["073229"] * 20,
        "citizen_id": [f"C{i:02d}" for i in range(10)] * 2,
        "category": ["育児", "若者支援"] * 10,
        "action_type": ["子育て施設チェックイン", "コワーキング利用"] * 10,
        "target_age_group": ["30代子育て層", "20代若者"] * 10,
        "action_date": pd.date_range("2023-01-01", periods=20, freq="15D"),
        "frequency_score": [3, 4, 2, 5, 1, 3, 4, 2, 5, 1] * 2,
        "recency_days": [30, 10, 90, 5, 180, 45, 15, 120, 8, 200] * 2,
        "engagement_value": [5.0, 8.0, 3.0, 9.0, 2.0, 6.0, 7.0, 4.0, 9.5, 1.5] * 2,
    })
