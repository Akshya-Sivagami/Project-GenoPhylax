import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "GRI_v2_candidate_dimensions.csv"
OUTPUT = ROOT / "validation" / "ceiling_source_analysis.csv"

rows = []

with INPUT.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):

        raw = row["candidate_score"].strip()

        if not raw:
            continue

        score = float(raw)

        if score != 1.0:
            continue

        method = row["normalization_method"]
        metric = row["raw_metric"]

        if method == "RISK_FRACTION":
            reason = "RAW_FRACTION_AT_BOUNDARY"

        elif method == "PROTECTION_RETAINED_FRACTION":
            reason = "INVERSE_RAW_FRACTION_AT_BOUNDARY"

        elif "RUBRIC" in method:
            reason = "RUBRIC_MAXIMUM_LEVEL"

        else:
            reason = "OTHER_BOUNDARY"

        rows.append({
            "case_id": row["case_id"],
            "dimension": row["dimension"],
            "raw_metric": metric,
            "raw_value": row["raw_value"],
            "normalization_method": method,
            "ceiling_reason": reason
        })


with OUTPUT.open("w", encoding="utf-8", newline="") as f:

    fieldnames = [
        "case_id",
        "dimension",
        "raw_metric",
        "raw_value",
        "normalization_method",
        "ceiling_reason"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


print("GRI v2 CEILING SOURCE ANALYSIS")
print("=" * 78)

for row in rows:
    print(
        f'{row["case_id"]:22} '
        f'{row["dimension"]:3} '
        f'{row["ceiling_reason"]:32} '
        f'{row["raw_metric"]}'
    )

print()
print(f"Ceiling observations: {len(rows)}")

counts = defaultdict(int)

for row in rows:
    counts[row["ceiling_reason"]] += 1

print("\nBy cause:")

for reason, count in sorted(counts.items()):
    print(f" - {reason}: {count}")

print()
print(f"Output: {OUTPUT}")
print("STATUS: PASS")
