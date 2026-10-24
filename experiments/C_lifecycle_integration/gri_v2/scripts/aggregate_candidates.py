import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "GRI_v2_candidate_dimensions.csv"
OUTPUT = ROOT / "results" / "GRI_v2_candidate_case_summary.csv"

cases = defaultdict(list)

with INPUT.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        cases[row["case_id"]].append(row)


rows = []

for case_id, records in sorted(cases.items()):

    total = len(records)

    point_scores = []
    unresolved = []
    positive_unresolved = []
    construct_unresolved = []

    for row in records:

        status = row["v2_score_status"]
        raw_score = row["candidate_score"].strip()
        dimension = row["dimension"]

        if status == "CANDIDATE" and raw_score:
            point_scores.append(float(raw_score))
            continue

        unresolved.append(dimension)

        if status == "POSITIVE_MAGNITUDE_UNRESOLVED":
            positive_unresolved.append(dimension)

        if status == "CONSTRUCT_UNRESOLVED":
            construct_unresolved.append(dimension)

    coverage = (
        len(point_scores) / total
        if total
        else 0.0
    )

    if unresolved:
        composite = ""
        composite_status = "WITHHELD"
    else:
        composite = (
            f"{sum(point_scores) / len(point_scores):.10f}"
            if point_scores
            else ""
        )
        composite_status = (
            "CANDIDATE"
            if composite
            else "WITHHELD"
        )

    rows.append({
        "case_id": case_id,
        "applicable_dimensions": total,
        "point_scored_dimensions": len(point_scores),
        "coverage": f"{coverage:.4f}",
        "candidate_composite": composite,
        "composite_status": composite_status,
        "unresolved_dimensions": (
            "|".join(sorted(set(unresolved)))
            if unresolved
            else ""
        ),
        "positive_magnitude_unresolved": (
            "|".join(sorted(set(positive_unresolved)))
            if positive_unresolved
            else ""
        ),
        "construct_unresolved": (
            "|".join(sorted(set(construct_unresolved)))
            if construct_unresolved
            else ""
        )
    })


with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(rows)


print("GRI v2 CASE SUMMARY")
print("=" * 110)

for row in rows:

    gri = row["candidate_composite"] or "WITHHELD"

    unresolved = (
        row["unresolved_dimensions"]
        or "NONE"
    )

    positive = (
        row["positive_magnitude_unresolved"]
        or "NONE"
    )

    construct = (
        row["construct_unresolved"]
        or "NONE"
    )

    print(
        f'{row["case_id"]:24} '
        f'coverage={row["coverage"]} '
        f'GRI={gri:12} '
        f'unresolved={unresolved:8} '
        f'positive-unresolved={positive:8} '
        f'construct-unresolved={construct}'
    )

print()
print(f"Output: {OUTPUT}")
