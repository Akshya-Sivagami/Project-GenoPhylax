import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIM_FILE = ROOT / "results" / "GRI_v2_candidate_dimensions.csv"
SUMMARY_FILE = ROOT / "results" / "GRI_v2_candidate_case_summary.csv"
LOO_FILE = ROOT / "validation" / "leave_one_dimension_out.csv"

OUTPUT = ROOT / "results" / "GRI_v2_reliability_envelope.csv"


# ------------------------------------------------------------
# Load dimension results
# ------------------------------------------------------------

case_dimensions = defaultdict(list)

with DIM_FILE.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        case_dimensions[row["case_id"]].append(row)


# ------------------------------------------------------------
# Load case summaries
# ------------------------------------------------------------

summaries = {}

with SUMMARY_FILE.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        summaries[row["case_id"]] = row


# ------------------------------------------------------------
# Load leave-one-out sensitivity
# ------------------------------------------------------------

loo = defaultdict(list)

if LOO_FILE.exists():
    with LOO_FILE.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            loo[row["case_id"]].append(
                float(row["absolute_change"])
            )


# ------------------------------------------------------------
# Build envelope
# ------------------------------------------------------------

rows = []

for case_id in sorted(case_dimensions):

    records = case_dimensions[case_id]
    summary = summaries[case_id]

    quantitative = [
        r for r in records
        if (
            r["v2_score_status"] == "CANDIDATE"
            and r["candidate_score"].strip()
        )
    ]

    applicable = len(records)
    scored = len(quantitative)

    resolution = (
        scored / applicable
        if applicable
        else 0.0
    )

    breadth_fraction = scored / 7.0

    evidence = Counter(
        r["evidence_class"]
        for r in quantitative
    )

    # Current result rows inherit source-backed case records.
    # Verify provenance directly from case JSON.
    case_path = ROOT / "cases" / f"{case_id}.json"

    provenance_total = 0
    provenance_present = 0

    if case_path.exists():

        with case_path.open("r", encoding="utf-8") as f:
            case_json = json.load(f)

        source_by_dimension_metric = {}

        for record in case_json["dimensions"]:
            source_by_dimension_metric[
                (
                    record["dimension"],
                    record["raw_metric"]
                )
            ] = record.get("source", "").strip()

        for record in quantitative:

            provenance_total += 1

            source = source_by_dimension_metric.get(
                (
                    record["dimension"],
                    record["raw_metric"]
                ),
                ""
            )

            if source:
                provenance_present += 1

    provenance_completeness = (
        provenance_present / provenance_total
        if provenance_total
        else 0.0
    )

    loo_values = loo.get(case_id, [])

    max_loo = (
        max(loo_values)
        if loo_values
        else None
    )

    unresolved_positive = summary.get(
        "positive_magnitude_unresolved",
        ""
    ).strip()

    unresolved_all = summary.get(
        "unresolved_dimensions",
        ""
    ).strip()

    rows.append({
        "case_id": case_id,
        "composite":
            summary["candidate_composite"].strip()
            or "WITHHELD",
        "resolution_coverage":
            f"{resolution:.4f}",
        "quantitative_breadth_count":
            scored,
        "quantitative_breadth_of_7":
            f"{breadth_fraction:.4f}",
        "experimental_n":
            evidence["EXPERIMENTAL"],
        "observational_n":
            evidence["OBSERVATIONAL"],
        "calibrated_model_n":
            evidence["CALIBRATED_MODEL"],
        "modelled_n":
            evidence["MODELLED"],
        "inferred_n":
            evidence["INFERRED"],
        "quantitative_provenance_completeness":
            f"{provenance_completeness:.4f}",
        "max_leave_one_out_delta":
            (
                f"{max_loo:.10f}"
                if max_loo is not None
                else "NA"
            ),
        "unresolved_dimensions":
            unresolved_all or "NONE",
        "positive_magnitude_unresolved":
            unresolved_positive or "NONE"
    })


with OUTPUT.open("w", encoding="utf-8", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=rows[0].keys()
    )

    writer.writeheader()
    writer.writerows(rows)


print("GRI v2 RELIABILITY ENVELOPE")
print("=" * 105)

for row in rows:

    print(
        f'{row["case_id"]:27} '
        f'GRI={row["composite"]:12} '
        f'resolution={row["resolution_coverage"]} '
        f'breadth={row["quantitative_breadth_count"]}/7 '
        f'LOO={row["max_leave_one_out_delta"]:12} '
        f'prov={row["quantitative_provenance_completeness"]}'
    )

print()
print("Evidence profile retained separately in output CSV.")
print("Reliability does NOT modify the GRI magnitude.")
print()
print(f"Output: {OUTPUT}")
print("STATUS: PASS")

