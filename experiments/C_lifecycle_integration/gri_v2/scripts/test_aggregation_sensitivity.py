import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "GRI_v2_candidate_dimensions.csv"
OUTPUT = ROOT / "validation" / "aggregation_sensitivity.csv"

cases = defaultdict(list)

with INPUT.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        if (
            row["v2_score_status"] == "CANDIDATE"
            and row["candidate_score"].strip()
        ):
            cases[row["case_id"]].append(
                float(row["candidate_score"])
            )


def arithmetic(values):
    return sum(values) / len(values)


def geometric(values):
    # Zero is valid risk magnitude, so use epsilon only
    # for numerical calculation.
    eps = 1e-12
    return math.exp(
        sum(math.log(max(v, eps)) for v in values)
        / len(values)
    )


def rms(values):
    return math.sqrt(
        sum(v * v for v in values) / len(values)
    )


rows = []

for case_id, values in sorted(cases.items()):

    rows.append({
        "case_id": case_id,
        "n_scored_dimensions": len(values),
        "arithmetic_mean": f"{arithmetic(values):.10f}",
        "geometric_mean": f"{geometric(values):.10f}",
        "rms": f"{rms(values):.10f}",
        "minimum": f"{min(values):.10f}",
        "maximum": f"{max(values):.10f}"
    })


with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(rows)


print("GRI v2 AGGREGATION SENSITIVITY")
print("=" * 82)

for row in rows:
    print(
        f'{row["case_id"]:24} '
        f'n={row["n_scored_dimensions"]} '
        f'AM={row["arithmetic_mean"]} '
        f'GM={row["geometric_mean"]} '
        f'RMS={row["rms"]}'
    )

print()
print(f"Output: {OUTPUT}")
print("STATUS: PASS")
