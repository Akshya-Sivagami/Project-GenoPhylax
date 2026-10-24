import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "GRI_v2_candidate_dimensions.csv"
OUTPUT = ROOT / "validation" / "leave_one_dimension_out.csv"

cases = defaultdict(list)

with INPUT.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):

        if (
            row["v2_score_status"] == "CANDIDATE"
            and row["candidate_score"].strip()
        ):
            cases[row["case_id"]].append(
                (
                    row["dimension"],
                    float(row["candidate_score"])
                )
            )


rows = []

for case_id, values in sorted(cases.items()):

    if len(values) < 2:
        continue

    full = sum(v for _, v in values) / len(values)

    for omitted_dimension, _ in values:

        retained = [
            v
            for dimension, v in values
            if dimension != omitted_dimension
        ]

        if not retained:
            continue

        reduced = sum(retained) / len(retained)

        rows.append({
            "case_id": case_id,
            "omitted_dimension": omitted_dimension,
            "full_composite": f"{full:.10f}",
            "reduced_composite": f"{reduced:.10f}",
            "absolute_change":
                f"{abs(reduced-full):.10f}"
        })


with OUTPUT.open("w", encoding="utf-8", newline="") as f:

    fields = [
        "case_id",
        "omitted_dimension",
        "full_composite",
        "reduced_composite",
        "absolute_change"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields
    )

    writer.writeheader()
    writer.writerows(rows)


print("GRI v2 LEAVE-ONE-DIMENSION-OUT SENSITIVITY")
print("=" * 76)

for row in rows:
    print(
        f'{row["case_id"]:26} '
        f'omit={row["omitted_dimension"]} '
        f'full={row["full_composite"]} '
        f'reduced={row["reduced_composite"]} '
        f'delta={row["absolute_change"]}'
    )

print()
print(f"Comparisons: {len(rows)}")
print(f"Output: {OUTPUT}")
print("STATUS: PASS")
