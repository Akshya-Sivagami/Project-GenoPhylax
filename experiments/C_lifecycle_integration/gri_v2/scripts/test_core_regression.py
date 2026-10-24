import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))

from gri_core import load_metric_registry, score_metric, aggregate_case


CASES = ROOT / "cases"
VALIDATION = ROOT / "validation"
RESULTS = ROOT / "results"

FROZEN_DIMENSIONS = RESULTS / "GRI_v2_candidate_dimensions.csv"
FROZEN_SUMMARY = RESULTS / "GRI_v2_candidate_case_summary.csv"

TOLERANCE = 5e-11

errors = []


def load_csv_by_case(path):
    data = {}

    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        for row in csv.DictReader(f):
            data[row["case_id"]] = row

    return data


def load_auxiliary_inputs():
    auxiliary = {}

    d4 = load_csv_by_case(
        VALIDATION / "D4_rubric_application.csv"
    )

    for case_id, row in d4.items():
        auxiliary.setdefault(case_id, {})["D4"] = {
            "boundary_breach": row["boundary_breach"],
            "access_scope_level": row["access_scope_level"],
        }

    d5 = load_csv_by_case(
        VALIDATION / "D5_rubric_application.csv"
    )

    for case_id, row in d5.items():
        auxiliary.setdefault(case_id, {})["D5"] = {
            "recoverability_fraction":
                row["recoverability_fraction"],
            "temporal_persistence":
                row["temporal_persistence"],
        }

    d6 = load_csv_by_case(
        VALIDATION / "D6_amplification_inputs.csv"
    )

    for case_id, row in d6.items():
        auxiliary.setdefault(case_id, {})["D6"] = {
            "amplification_ratio":
                row["amplification_ratio"],
        }

    d7 = load_csv_by_case(
        VALIDATION / "D7_rubric_application.csv"
    )

    for case_id, row in d7.items():
        auxiliary.setdefault(case_id, {})["D7"] = {
            "rubric_level": row["rubric_level"],
        }

    return auxiliary


def load_frozen_dimensions():
    frozen = {}

    with FROZEN_DIMENSIONS.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        for row in csv.DictReader(f):
            key = (
                row["case_id"],
                row["dimension"],
                row["raw_metric"],
            )
            frozen[key] = row

    return frozen


def load_frozen_summary():
    frozen = {}

    with FROZEN_SUMMARY.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        for row in csv.DictReader(f):
            frozen[row["case_id"]] = row

    return frozen


registry = load_metric_registry()
auxiliary = load_auxiliary_inputs()
frozen_dimensions = load_frozen_dimensions()
frozen_summary = load_frozen_summary()

new_dimensions = {}
new_cases = {}

for path in sorted(CASES.glob("*.json")):

    with path.open("r", encoding="utf-8") as f:
        case = json.load(f)

    case_id = case["case_id"]
    scored = []

    for record in case["dimensions"]:

        if record.get("status") != "APPLICABLE":
            continue

        dimension = record["dimension"]

        result = score_metric(
            record,
            registry,
            auxiliary.get(
                case_id,
                {}
            ).get(
                dimension,
                {}
            ),
        )

        row = {
            "case_id": case_id,
            "dimension": dimension,
            "raw_metric": record["raw_metric"],
            "raw_value": str(record["raw_value"]),
            "evidence_class": record["evidence_class"],
            "candidate_score":
                result["candidate_score"],
            "normalization_method":
                result["normalization_method"],
            "v2_score_status":
                result["v2_score_status"],
        }

        key = (
            case_id,
            dimension,
            record["raw_metric"],
        )

        new_dimensions[key] = row
        scored.append(row)

    new_cases[case_id] = aggregate_case(scored)


# ------------------------------------------------------------
# Dimension-level regression
# ------------------------------------------------------------

all_dimension_keys = (
    set(frozen_dimensions)
    | set(new_dimensions)
)

for key in sorted(all_dimension_keys):

    frozen = frozen_dimensions.get(key)
    new = new_dimensions.get(key)

    if frozen is None:
        errors.append(
            f"{key}: new dimension row absent from frozen output"
        )
        continue

    if new is None:
        errors.append(
            f"{key}: frozen dimension row missing from new core"
        )
        continue

    if (
        frozen["normalization_method"]
        != new["normalization_method"]
    ):
        errors.append(
            f"{key}: normalization method mismatch: "
            f'{frozen["normalization_method"]} != '
            f'{new["normalization_method"]}'
        )

    if (
        frozen["v2_score_status"]
        != new["v2_score_status"]
    ):
        errors.append(
            f"{key}: status mismatch: "
            f'{frozen["v2_score_status"]} != '
            f'{new["v2_score_status"]}'
        )

    frozen_score = frozen["candidate_score"].strip()
    new_score = new["candidate_score"]

    if frozen_score:

        if new_score is None:
            errors.append(
                f"{key}: frozen numeric score became unresolved"
            )
        else:
            difference = abs(
                float(frozen_score) - float(new_score)
            )

            if difference > TOLERANCE:
                errors.append(
                    f"{key}: score mismatch "
                    f"{frozen_score} != {new_score:.10f}"
                )

    else:

        if new_score is not None:
            errors.append(
                f"{key}: frozen unresolved score became numeric "
                f"{new_score:.10f}"
            )


# ------------------------------------------------------------
# Case-level regression
# ------------------------------------------------------------

all_case_ids = (
    set(frozen_summary)
    | set(new_cases)
)

for case_id in sorted(all_case_ids):

    frozen = frozen_summary.get(case_id)
    new = new_cases.get(case_id)

    if frozen is None:
        errors.append(
            f"{case_id}: new case absent from frozen summary"
        )
        continue

    if new is None:
        errors.append(
            f"{case_id}: frozen case missing from new core"
        )
        continue

    if (
        int(frozen["applicable_dimensions"])
        != new["applicable_dimensions"]
    ):
        errors.append(
            f"{case_id}: applicable dimension count mismatch"
        )

    if (
        int(frozen["point_scored_dimensions"])
        != new["point_scored_dimensions"]
    ):
        errors.append(
            f"{case_id}: point-scored dimension count mismatch"
        )

    if abs(
        float(frozen["coverage"])
        - float(new["coverage"])
    ) > 0.00005:
        errors.append(
            f"{case_id}: coverage mismatch"
        )

    if (
        frozen["composite_status"]
        != new["composite_status"]
    ):
        errors.append(
            f"{case_id}: composite status mismatch"
        )

    frozen_composite = (
        frozen["candidate_composite"].strip()
    )
    new_composite = new["candidate_composite"]

    if frozen_composite:

        if new_composite is None:
            errors.append(
                f"{case_id}: frozen composite became withheld"
            )
        else:
            difference = abs(
                float(frozen_composite)
                - float(new_composite)
            )

            if difference > TOLERANCE:
                errors.append(
                    f"{case_id}: composite mismatch "
                    f"{frozen_composite} != "
                    f"{new_composite:.10f}"
                )

    else:

        if new_composite is not None:
            errors.append(
                f"{case_id}: frozen withheld composite "
                "became numeric"
            )

    expected_unresolved = sorted(
        x for x in
        frozen["unresolved_dimensions"].split("|")
        if x
    )

    if expected_unresolved != new["unresolved_dimensions"]:
        errors.append(
            f"{case_id}: unresolved dimension mismatch"
        )

    expected_positive = sorted(
        x for x in
        frozen["positive_magnitude_unresolved"].split("|")
        if x
    )

    if (
        expected_positive
        != new["positive_magnitude_unresolved"]
    ):
        errors.append(
            f"{case_id}: positive-unresolved mismatch"
        )

    expected_construct = sorted(
        x for x in
        frozen["construct_unresolved"].split("|")
        if x
    )

    if (
        expected_construct
        != new["construct_unresolved"]
    ):
        errors.append(
            f"{case_id}: construct-unresolved mismatch"
        )


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("GRI v2 CORE REGRESSION")
print("=" * 60)
print(
    f"Frozen dimension rows: {len(frozen_dimensions)}"
)
print(
    f"New-core dimension rows: {len(new_dimensions)}"
)
print(
    f"Frozen cases: {len(frozen_summary)}"
)
print(
    f"New-core cases: {len(new_cases)}"
)
print(
    f"Regression errors: {len(errors)}"
)

if errors:
    print("\nERRORS")
    for error in errors:
        print(" -", error)

    print("\nSTATUS: FAIL")
    sys.exit(1)

print("\nDimension scores/statuses/methods: EXACT MATCH")
print("Case composites/withholding: EXACT MATCH")
print("Unresolved-state classification: EXACT MATCH")
print("\nSTATUS: PASS")
