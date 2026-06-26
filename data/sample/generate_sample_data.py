"""
大玉村サンプルデータ生成スクリプト。
以下の分析インサイトが自然に浮かび上がるよう設計されたデータセット:
  1. 子育て高頻度層のオンライン申請率が12%未満
  2. 20代若者のエンゲージメントが3ヶ月で30%以上減少
  3. 教育と育児カテゴリ間の隠れた相関（バスケット分析）

Usage:
    python data/sample/generate_sample_data.py
"""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUTPUT_DIR = Path(__file__).parent
MUNICIPALITY_CODE = "073229"
MUNICIPALITY_NAME = "大玉村"

# ── 1. 自治体マスター ─────────────────────────────────────────

MUNICIPALITY_MASTER = [
    {
        "municipality_code": MUNICIPALITY_CODE,
        "name": MUNICIPALITY_NAME,
        "population_total": 7821,
        "aging_rate": 0.312,
        "industry_structure": json.dumps({"primary": 0.15, "secondary": 0.28, "tertiary": 0.57}),
        "fiscal_health_index": 0.48,
        "target_year": 2024,
    },
    {
        "municipality_code": MUNICIPALITY_CODE,
        "name": MUNICIPALITY_NAME,
        "population_total": 7912,
        "aging_rate": 0.301,
        "industry_structure": json.dumps({"primary": 0.16, "secondary": 0.27, "tertiary": 0.57}),
        "fiscal_health_index": 0.46,
        "target_year": 2023,
    },
    {
        "municipality_code": MUNICIPALITY_CODE,
        "name": MUNICIPALITY_NAME,
        "population_total": 8045,
        "aging_rate": 0.291,
        "industry_structure": json.dumps({"primary": 0.17, "secondary": 0.27, "tertiary": 0.56}),
        "fiscal_health_index": 0.45,
        "target_year": 2022,
    },
    {
        "municipality_code": MUNICIPALITY_CODE,
        "name": MUNICIPALITY_NAME,
        "population_total": 8193,
        "aging_rate": 0.278,
        "industry_structure": json.dumps({"primary": 0.18, "secondary": 0.28, "tertiary": 0.54}),
        "fiscal_health_index": 0.43,
        "target_year": 2021,
    },
]

# ── 2. NES重点領域指標 ─────────────────────────────────────────

NES_FOCUS_INDICATORS = [
    {"municipality_code": MUNICIPALITY_CODE, "target_year": 2021, "online_score": 35.0, "ai_rpa_score": 20.0, "data_utilization_score": 15.0, "total_score": 23.3},
    {"municipality_code": MUNICIPALITY_CODE, "target_year": 2022, "online_score": 43.0, "ai_rpa_score": 28.0, "data_utilization_score": 22.0, "total_score": 31.0},
    {"municipality_code": MUNICIPALITY_CODE, "target_year": 2023, "online_score": 51.0, "ai_rpa_score": 38.0, "data_utilization_score": 30.0, "total_score": 39.7},
    {"municipality_code": MUNICIPALITY_CODE, "target_year": 2024, "online_score": 62.0, "ai_rpa_score": 45.0, "data_utilization_score": 38.0, "total_score": 48.3},
]

# ── 3. 職員の時間配分 ──────────────────────────────────────────

STAFF_TIME_ALLOCATION = [
    {"municipality_code": MUNICIPALITY_CODE, "target_year": 2021, "routine_hours": 168.0, "creative_hours": 12.0, "total_workforce_hours": 180.0},
    {"municipality_code": MUNICIPALITY_CODE, "target_year": 2022, "routine_hours": 163.0, "creative_hours": 17.0, "total_workforce_hours": 180.0},
    {"municipality_code": MUNICIPALITY_CODE, "target_year": 2023, "routine_hours": 155.0, "creative_hours": 25.0, "total_workforce_hours": 180.0},
    {"municipality_code": MUNICIPALITY_CODE, "target_year": 2024, "routine_hours": 142.0, "creative_hours": 38.0, "total_workforce_hours": 180.0},
]

# ── 4. アクションログ生成ロジック ─────────────────────────────

CATEGORIES = {
    "育児": {
        "actions": ["子育て施設チェックイン", "子育て相談", "保育所申込(窓口)"],
        "online_actions": ["児童手当申請(オンライン)"],
        "age_groups": ["30代子育て層", "20代子育て層"],
        "weight": 0.30,
    },
    "若者支援": {
        "actions": ["コワーキング利用", "起業サロン参加", "キャリア相談"],
        "online_actions": [],
        "age_groups": ["20代若者", "30代子育て層"],
        "weight": 0.20,
    },
    "教育": {
        "actions": ["施設チェックイン", "図書館利用", "学習支援参加"],
        "online_actions": [],
        "age_groups": ["10代", "20代若者", "30代子育て層"],
        "weight": 0.20,
    },
    "行政手続き": {
        "actions": ["窓口申請", "マイナンバー手続き"],
        "online_actions": ["オンライン申請"],
        "age_groups": ["30代子育て層", "40代", "50代以上"],
        "weight": 0.15,
    },
    "起業支援": {
        "actions": ["創業セミナー参加", "補助金申請(窓口)"],
        "online_actions": ["補助金申請(オンライン)"],
        "age_groups": ["20代若者", "30代子育て層"],
        "weight": 0.08,
    },
    "人口移住対策": {
        "actions": ["移住相談", "UIターン窓口"],
        "online_actions": [],
        "age_groups": ["20代若者", "30代子育て層"],
        "weight": 0.07,
    },
}


def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_activity_logs() -> list[dict]:
    logs = []
    log_id_counter = 1
    today = date(2024, 12, 31)
    six_months_ago = today - timedelta(days=180)
    three_months_ago = today - timedelta(days=90)

    # ── グループ1: 育児層（子育て施設利用頻度に勾配をつける）────────────
    # 設計意図: 高頻度=週2回以上(freq 4-5)→ オンライン率〜8%（精神的余裕なし）
    #           中頻度=週1〜2回(freq 2-3) → オンライン率〜20%
    #           低頻度=月数回(freq 1)    → オンライン率〜35%
    N_CHILDCARE = 80
    childcare_citizens = [f"C{i:04d}" for i in range(1, N_CHILDCARE + 1)]

    # サブグループ分割: 高頻度40名, 中頻度25名, 低頻度15名
    high_freq_ids  = childcare_citizens[:40]   # freq 4-5, online ~8%
    mid_freq_ids   = childcare_citizens[40:65]  # freq 2-3, online ~20%
    low_freq_ids   = childcare_citizens[65:]    # freq 1,   online ~35%

    # freq_scoreを1/3/5に分離してbinの境界と一致させる
    childcare_tiers = [
        (high_freq_ids,  5, (15, 22), 0.08),  # 高頻度: freq=5, オンライン率8%
        (mid_freq_ids,   3, (6,  12), 0.22),  # 中頻度: freq=3, オンライン率22%
        (low_freq_ids,   1, (2,   5), 0.38),  # 低頻度: freq=1, オンライン率38%
    ]

    for tier_ids, freq_score, visit_range, online_prob in childcare_tiers:
        for cid in tier_ids:
            n_visits = random.randint(*visit_range)
            recency  = random.randint(1, 20) if freq_score >= 4 else random.randint(10, 60)

            for _ in range(n_visits):
                logs.append({
                    "log_id": f"L{log_id_counter:05d}",
                    "municipality_code": MUNICIPALITY_CODE,
                    "citizen_id": cid,
                    "category": "育児",
                    "action_type": random.choices(
                        ["子育て施設チェックイン", "子育て相談", "保育所申込(窓口)"],
                        weights=[0.70, 0.20, 0.10],
                    )[0],
                    "target_age_group": "30代子育て層",
                    "action_date": rand_date(six_months_ago, today).isoformat(),
                    "frequency_score": freq_score,
                    "recency_days": recency,
                    "engagement_value": round(random.uniform(5.5, 8.5), 1),
                })
                log_id_counter += 1

            # 教育との共起（バスケット分析の素材）
            if random.random() < 0.55:
                logs.append({
                    "log_id": f"L{log_id_counter:05d}",
                    "municipality_code": MUNICIPALITY_CODE,
                    "citizen_id": cid,
                    "category": "教育",
                    "action_type": random.choices(["図書館利用", "学習支援参加"], weights=[0.7, 0.3])[0],
                    "target_age_group": "30代子育て層",
                    "action_date": rand_date(six_months_ago, today).isoformat(),
                    "frequency_score": random.randint(1, 3),
                    "recency_days": random.randint(5, 40),
                    "engagement_value": round(random.uniform(4.0, 7.0), 1),
                })
                log_id_counter += 1

            # オンライン申請（頻度層別確率）
            if random.random() < online_prob:
                logs.append({
                    "log_id": f"L{log_id_counter:05d}",
                    "municipality_code": MUNICIPALITY_CODE,
                    "citizen_id": cid,
                    "category": "育児",
                    "action_type": "児童手当申請(オンライン)",
                    "target_age_group": "30代子育て層",
                    "action_date": rand_date(six_months_ago, today).isoformat(),
                    "frequency_score": 1,
                    "recency_days": random.randint(30, 90),
                    "engagement_value": round(random.uniform(3.0, 6.0), 1),
                })
                log_id_counter += 1

    # ── グループ2: 20代若者（チャーン設計: 前半は活発 → 後半は急減）──────
    N_YOUTH = 60
    youth_citizens = [f"C{i:04d}" for i in range(N_CHILDCARE + 1, N_CHILDCARE + N_YOUTH + 1)]

    for i, cid in enumerate(youth_citizens):
        is_churn = i < 40  # 40名が離脱予備軍

        if is_churn:
            # 3〜6ヶ月前は活発（freq 4-5）
            n_old = random.randint(5, 10)
            for _ in range(n_old):
                logs.append({
                    "log_id": f"L{log_id_counter:05d}",
                    "municipality_code": MUNICIPALITY_CODE,
                    "citizen_id": cid,
                    "category": random.choice(["若者支援", "起業支援"]),
                    "action_type": random.choice(["コワーキング利用", "起業サロン参加", "創業セミナー参加"]),
                    "target_age_group": "20代若者",
                    "action_date": rand_date(six_months_ago, three_months_ago).isoformat(),
                    "frequency_score": random.randint(4, 5),
                    "recency_days": random.randint(60, 120),
                    "engagement_value": round(random.uniform(5.0, 8.0), 1),
                })
                log_id_counter += 1

            # 直近3ヶ月は激減（freq 1-2）
            n_recent = random.randint(0, 2)
            for _ in range(n_recent):
                logs.append({
                    "log_id": f"L{log_id_counter:05d}",
                    "municipality_code": MUNICIPALITY_CODE,
                    "citizen_id": cid,
                    "category": random.choice(["若者支援", "起業支援"]),
                    "action_type": random.choice(["コワーキング利用", "キャリア相談"]),
                    "target_age_group": "20代若者",
                    "action_date": rand_date(three_months_ago, today).isoformat(),
                    "frequency_score": random.randint(1, 2),
                    "recency_days": random.randint(45, 90),
                    "engagement_value": round(random.uniform(2.0, 4.5), 1),
                })
                log_id_counter += 1
        else:
            # 安定した20代（離脱なし）
            n_visits = random.randint(6, 12)
            for _ in range(n_visits):
                logs.append({
                    "log_id": f"L{log_id_counter:05d}",
                    "municipality_code": MUNICIPALITY_CODE,
                    "citizen_id": cid,
                    "category": random.choice(["若者支援", "教育", "起業支援"]),
                    "action_type": random.choice(["コワーキング利用", "図書館利用", "キャリア相談", "補助金申請(オンライン)"]),
                    "target_age_group": "20代若者",
                    "action_date": rand_date(six_months_ago, today).isoformat(),
                    "frequency_score": random.randint(3, 5),
                    "recency_days": random.randint(5, 40),
                    "engagement_value": round(random.uniform(5.0, 9.0), 1),
                })
                log_id_counter += 1

    # ── グループ3: 40代〜50代（行政手続き中心）──────────────────────────
    N_ADULT = 50
    adult_citizens = [f"C{i:04d}" for i in range(N_CHILDCARE + N_YOUTH + 1, N_CHILDCARE + N_YOUTH + N_ADULT + 1)]

    for cid in adult_citizens:
        age = random.choices(["40代", "50代以上"], weights=[0.45, 0.55])[0]
        n_visits = random.randint(4, 10)
        use_online = random.random() < 0.40  # 40代以上はオンライン利用率40%

        for _ in range(n_visits):
            category = random.choice(["行政手続き", "教育"])
            action = (
                random.choice(["オンライン申請", "窓口申請"]) if category == "行政手続き" and use_online
                else random.choice(["窓口申請", "マイナンバー手続き", "図書館利用"])
            )
            logs.append({
                "log_id": f"L{log_id_counter:05d}",
                "municipality_code": MUNICIPALITY_CODE,
                "citizen_id": cid,
                "category": category,
                "action_type": action,
                "target_age_group": age,
                "action_date": rand_date(six_months_ago, today).isoformat(),
                "frequency_score": random.randint(2, 4),
                "recency_days": random.randint(10, 80),
                "engagement_value": round(random.uniform(4.0, 7.5), 1),
            })
            log_id_counter += 1

    # ── グループ4: 移住検討者・UIターン層 ────────────────────────────────
    N_MIGRATION = 20
    migration_citizens = [f"C{i:04d}" for i in range(N_CHILDCARE + N_YOUTH + N_ADULT + 1,
                                                        N_CHILDCARE + N_YOUTH + N_ADULT + N_MIGRATION + 1)]
    for cid in migration_citizens:
        n_visits = random.randint(2, 5)
        for _ in range(n_visits):
            logs.append({
                "log_id": f"L{log_id_counter:05d}",
                "municipality_code": MUNICIPALITY_CODE,
                "citizen_id": cid,
                "category": "人口移住対策",
                "action_type": random.choice(["移住相談", "UIターン窓口"]),
                "target_age_group": "20代若者",
                "action_date": rand_date(six_months_ago, today).isoformat(),
                "frequency_score": random.randint(1, 3),
                "recency_days": random.randint(20, 120),
                "engagement_value": round(random.uniform(3.0, 7.0), 1),
            })
            log_id_counter += 1

    return logs


# ── CSV書き出し ────────────────────────────────────────────────

def write_csv(filename: str, rows: list[dict]) -> None:
    if not rows:
        print(f"  [warn] {filename}: empty data")
        return
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [ok] {filepath} ({len(rows)} rows)")


if __name__ == "__main__":
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp932", "shift_jis", "mbcs"):
        # Windows CP932環境での絵文字回避
        ok = "[OK]"
        warn = "[!!]"
    else:
        ok = "OK"
        warn = "!!"

    print("Generating sample data for Otama Village...")
    write_csv("municipality_master.csv", MUNICIPALITY_MASTER)
    write_csv("nes_focus_indicators.csv", NES_FOCUS_INDICATORS)
    write_csv("staff_time_allocation.csv", STAFF_TIME_ALLOCATION)
    logs = generate_activity_logs()
    write_csv("activity_logs.csv", logs)
    print(f"\nDone! activity_logs: {len(logs)} rows generated.")
    print("Next step: streamlit run app.py")
