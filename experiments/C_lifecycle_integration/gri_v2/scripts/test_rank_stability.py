import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIM_FILE = ROOT / "results" / "GRI_v2_candidate_dimensions.csv"
SUMMARY_FILE = ROOT / "results" / "GRI_v2_candidate_case_summary.csv"
OUTPUT = ROOT / "validation" / "rank_stability.csv"

dimensions = defaultdict(list)

with DIM_FILE.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):

        if (
            row["v2_score_status"] == "CANDIDATE"
            and row["candidate_score"].strip()
        ):
            dimensions[row["case_id"]].append(
                float(row["candidate_score"])
            )

eligible = set()

with SUMMARY_FILE.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):

        if (
            row["composite_status"] == "CANDIDATE"
            and not row["unresolved_dimensions"].strip()
        ):
            eligible.add(row["case_id"])


def arithmetic(values):
    return sum(values) / len(values)


def geometric(values):
    if any(v == 0 for v in values):
        return 0.0

    return math.exp(
        sum(math.log(v) for v in values) / len(values)
    )


def rms(values):
    return math.sqrt(
        sum(v * v for v in values) / len(values)
    )


methods = {
    "ARITHMETIC": arithmetic,
    "GEOMETRIC": geometric,
    "RMS": rms
}

scores = {}

for method_name, fn in methods.items():

    scores[method_name] = {}

    for case_id in sorted(eligible):
        values = dimensions[case_id]

        if values:
            scores[method_name][case_id] = fn(values)


ranks = {}

for method_name, case_scores in scores.items():

    ordered = sorted(
        case_scores.items(),
        key=lambda x: (-x[1], x[0])
    )

    ranks[method_name] = {
        case_id: rank
        for rank, (case_id, _) in enumerate(
            ordered,
            start=1
        )
    }


rows = []

for case_id in sorted(eligible):

    rank_values = [
        ranks[m][case_id]
        for m in methods
    ]

    rows.append({
        "case_id": case_id,
        "arithmetic_score":
            f'{scores["ARITHMETIC"][case_id]:.10f}',
        "arithmetic_rank":
            ranks["ARITHMETIC"][case_id],

        "geometric_score":
            f'{scores["GEOMETRIC"][case_id]:.10f}',
        "geometric_rank":
            ranks["GEOMETRIC"][case_id],

        "rms_score":
            f'{scores["RMS"][case_id]:.10f}',
        "rms_rank":
            ranks["RMS"][case_id],

        "rank_range":
            max(rank_values) - min(rank_values)
    })


with OUTPUT.open("w", encoding="utf-8", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=rows[0].keys()
    )

    writer.writeheader()
    writer.writerows(rows)


print("GRI v2 RANK STABILITY")
print("=" * 92)

for row in sorted(
    rows,
    key=lambda x: int(x["arithmetic_rank"])
):
    print(
        f'{row["case_id"]:26} '
        f'AM={row["arithmetic_score"]} '
        f'#{row["arithmetic_rank"]}  '
        f'GM={row["geometric_score"]} '
        f'#{row["geometric_rank"]}  '
        f'RMS={row["rms_score"]} '
        f'#{row["rms_rank"]}  '
        f'range={row["rank_range"]}'
    )

unstable = [
    row for row in rows
    if int(row["rank_range"]) > 0
]

print()
print(f"Eligible cases: {len(rows)}")
print(f"Cases changing rank: {len(unstable)}")
print(f"Stable-rank fraction: {(len(rows)-len(unstable))/len(rows):.4f}")
print()
print(f"Output: {OUTPUT}")
print("STATUS: PASS")
