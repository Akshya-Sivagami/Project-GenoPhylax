import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "validation" / "D6_amplification_inputs.csv"
OUTPUT = ROOT / "validation" / "D6_anchor_sensitivity.csv"

ANCHORS = [100.0, 1000.0, 10000.0]


def score(ratio, anchor):
    if ratio < 1:
        raise ValueError("Amplification ratio cannot be below 1")

    value = math.log10(ratio) / math.log10(anchor)
    return max(0.0, min(1.0, value))


rows = []

with INPUT.open("r", encoding="utf-8", newline="") as f:
    for record in csv.DictReader(f):

        raw = record["amplification_ratio"].strip()

        if not raw:
            for anchor in ANCHORS:
                rows.append({
                    "case_id": record["case_id"],
                    "ratio": "",
                    "upper_anchor": int(anchor),
                    "candidate_score": "",
                    "status": "UNSCORED_DENOMINATOR_REQUIRED"
                })
            continue

        ratio = float(raw)

        for anchor in ANCHORS:
            rows.append({
                "case_id": record["case_id"],
                "ratio": f"{ratio:.10f}",
                "upper_anchor": int(anchor),
                "candidate_score": f"{score(ratio, anchor):.10f}",
                "status": "SENSITIVITY_CANDIDATE"
            })

with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "case_id",
            "ratio",
            "upper_anchor",
            "candidate_score",
            "status"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print("D6 AMPLIFICATION ANCHOR SENSITIVITY")
print("=" * 55)

for row in rows:
    value = row["candidate_score"] or "UNSCORED"

    print(
        f'{row["case_id"]:20} '
        f'anchor={row["upper_anchor"]:5} '
        f'score={value}'
    )

print()
print(f"Output: {OUTPUT}")
print("STATUS: PASS")
