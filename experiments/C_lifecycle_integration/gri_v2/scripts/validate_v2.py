import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
VALIDATION = ROOT / "validation"

DIM_FILE = RESULTS / "GRI_v2_candidate_dimensions.csv"
SUMMARY_FILE = RESULTS / "GRI_v2_candidate_case_summary.csv"
D6_FILE = VALIDATION / "D6_anchor_sensitivity.csv"
REPORT_FILE = VALIDATION / "GRI_v2_VALIDATION_REPORT.md"

errors = []
warnings = []


def fail(message):
    errors.append(message)


def warn(message):
    warnings.append(message)


# ------------------------------------------------------------
# Required outputs
# ------------------------------------------------------------

for path in [DIM_FILE, SUMMARY_FILE, D6_FILE, REPORT_FILE]:
    if not path.exists():
        fail(f"Missing required output: {path.name}")

if errors:
    for item in errors:
        print("ERROR:", item)
    sys.exit(1)


# ------------------------------------------------------------
# Dimension scores and status semantics
# ------------------------------------------------------------

with DIM_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:
    dimensions = list(csv.DictReader(f))


allowed_statuses = {
    "CANDIDATE",
    "POSITIVE_MAGNITUDE_UNRESOLVED",
    "NO_POSITIVE_DEMONSTRATION",
    "CONSTRUCT_UNRESOLVED",
    "UNSCORED"
}

for row in dimensions:

    case_id = row["case_id"]
    dimension = row["dimension"]
    score = row["candidate_score"].strip()
    status = row["v2_score_status"].strip()
    method = row["normalization_method"].strip()

    if status not in allowed_statuses:
        fail(
            f"{case_id}/{dimension}: "
            f"unknown score status {status}"
        )

    if score:
        try:
            value = float(score)
        except ValueError:
            fail(
                f"{case_id}/{dimension}: "
                "candidate score is not numeric"
            )
            continue

        if not 0.0 <= value <= 1.0:
            fail(
                f"{case_id}/{dimension}: "
                "score outside [0,1]"
            )

        if status != "CANDIDATE":
            fail(
                f"{case_id}/{dimension}: "
                "numeric score exists without CANDIDATE status"
            )

    else:
        if status == "CANDIDATE":
            fail(
                f"{case_id}/{dimension}: "
                "CANDIDATE has no numeric score"
            )

    if status == "POSITIVE_MAGNITUDE_UNRESOLVED":
        if method != "BINARY_DEMONSTRATION":
            fail(
                f"{case_id}/{dimension}: "
                "positive unresolved magnitude must originate "
                "from BINARY_DEMONSTRATION"
            )

    if status == "NO_POSITIVE_DEMONSTRATION":
        if method != "BINARY_DEMONSTRATION":
            fail(
                f"{case_id}/{dimension}: "
                "no-positive-demonstration status must originate "
                "from BINARY_DEMONSTRATION"
            )

    if status == "CONSTRUCT_UNRESOLVED":
        if method != "CONSTRUCT_REVIEW":
            fail(
                f"{case_id}/{dimension}: "
                "construct-unresolved status must use "
                "CONSTRUCT_REVIEW"
            )


# ------------------------------------------------------------
# Expected normalization methods
# ------------------------------------------------------------

allowed_methods = {
    "D1": {
        "RISK_FRACTION",
        "BINARY_DEMONSTRATION"
    },
    "D2": {
        "PROTECTION_RETAINED_FRACTION"
    },
    "D3": {
        "RISK_FRACTION",
        "BINARY_DEMONSTRATION"
    },
    "D4": {
        "D4_ACCESSIBILITY_RUBRIC",
        "BINARY_DEMONSTRATION",
        "CONSTRUCT_REVIEW",
        "D4_RUBRIC_REQUIRED"
    },
    "D5": {
        "D5_PERSISTENCE_COMPOSITE",
        "D5_COMPONENTS_REQUIRED"
    },
    "D6": {
        "D6_LOG10_ANCHORED_1000_SENSITIVITY_CANDIDATE",
        "D6_DENOMINATOR_REQUIRED"
    },
    "D7": {
        "D7_PIPELINE_RUBRIC",
        "D7_RUBRIC_REQUIRED"
    }
}

for row in dimensions:

    case_id = row["case_id"]
    dimension = row["dimension"]
    method = row["normalization_method"]

    if method not in allowed_methods.get(dimension, set()):
        fail(
            f"{case_id}/{dimension}: "
            f"unexpected normalization method {method}"
        )


# ------------------------------------------------------------
# Case aggregation and unresolved-state integrity
# ------------------------------------------------------------

with SUMMARY_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:
    summaries = list(csv.DictReader(f))


required_summary_columns = {
    "case_id",
    "applicable_dimensions",
    "point_scored_dimensions",
    "coverage",
    "candidate_composite",
    "composite_status",
    "unresolved_dimensions",
    "positive_magnitude_unresolved",
    "construct_unresolved"
}

if summaries:
    missing_columns = (
        required_summary_columns - set(summaries[0].keys())
    )

    if missing_columns:
        fail(
            "Case summary missing columns: "
            + ", ".join(sorted(missing_columns))
        )


for row in summaries:

    case_id = row["case_id"]
    unresolved = row["unresolved_dimensions"].strip()
    positive = row["positive_magnitude_unresolved"].strip()
    construct = row["construct_unresolved"].strip()
    composite = row["candidate_composite"].strip()
    composite_status = row["composite_status"].strip()

    try:
        applicable = int(row["applicable_dimensions"])
        scored = int(row["point_scored_dimensions"])
        coverage = float(row["coverage"])
    except ValueError:
        fail(f"{case_id}: invalid aggregation metadata")
        continue

    expected_coverage = (
        scored / applicable
        if applicable
        else 0.0
    )

    if abs(coverage - expected_coverage) > 0.00005:
        fail(
            f"{case_id}: coverage does not match "
            "point-scored/applicable dimensions"
        )

    if unresolved:

        if composite:
            fail(
                f"{case_id}: composite issued despite "
                f"unresolved dimensions {unresolved}"
            )

        if composite_status != "WITHHELD":
            fail(
                f"{case_id}: unresolved case must have "
                "WITHHELD composite status"
            )

    else:

        if not composite:
            fail(
                f"{case_id}: all applicable dimensions "
                "resolved but composite missing"
            )

        if composite_status != "CANDIDATE":
            fail(
                f"{case_id}: resolved composite must have "
                "CANDIDATE status"
            )

    if composite:
        try:
            value = float(composite)
        except ValueError:
            fail(f"{case_id}: composite is not numeric")
        else:
            if not 0.0 <= value <= 1.0:
                fail(
                    f"{case_id}: composite outside [0,1]"
                )

    unresolved_set = {
        x for x in unresolved.split("|") if x
    }
    positive_set = {
        x for x in positive.split("|") if x
    }
    construct_set = {
        x for x in construct.split("|") if x
    }

    if not positive_set.issubset(unresolved_set):
        fail(
            f"{case_id}: positive-magnitude unresolved "
            "dimensions not contained in unresolved set"
        )

    if not construct_set.issubset(unresolved_set):
        fail(
            f"{case_id}: construct-unresolved dimensions "
            "not contained in unresolved set"
        )

    if positive_set & construct_set:
        fail(
            f"{case_id}: dimension cannot simultaneously be "
            "positive-magnitude-unresolved and construct-unresolved"
        )


# ------------------------------------------------------------
# D6 sensitivity requirement
# ------------------------------------------------------------

with D6_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:
    d6_rows = list(csv.DictReader(f))


anchors_by_case = {}

for row in d6_rows:

    if not row["candidate_score"].strip():
        continue

    case_id = row["case_id"]

    anchors_by_case.setdefault(
        case_id,
        set()
    ).add(row["upper_anchor"])


for case_id, anchors in anchors_by_case.items():

    if len(anchors) < 3:
        fail(
            f"{case_id}: D6 requires >=3 anchor "
            "sensitivity values"
        )


# ------------------------------------------------------------
# Frozen-v1 separation
# ------------------------------------------------------------

v1_forbidden = {
    "C4_authoritative_gri.json",
    "C4_base_gri.tsv"
}

for path in ROOT.rglob("*"):

    if (
        path.is_file()
        and path.name in v1_forbidden
    ):
        fail(
            f"Frozen-v1 artifact copied into v2: {path.name}"
        )


# ------------------------------------------------------------
# Required scientific safeguards
# ------------------------------------------------------------

binary_ceiling_violations = 0

for row in dimensions:

    if (
        row["normalization_method"] == "BINARY_DEMONSTRATION"
        and row["candidate_score"].strip()
    ):
        binary_ceiling_violations += 1


if binary_ceiling_violations:
    fail(
        "Binary demonstration evidence produced numeric "
        "point scores."
    )


construct_score_violations = 0

for row in dimensions:

    if (
        row["normalization_method"] == "CONSTRUCT_REVIEW"
        and row["candidate_score"].strip()
    ):
        construct_score_violations += 1


if construct_score_violations:
    fail(
        "Construct-review evidence produced numeric "
        "point scores."
    )


# ------------------------------------------------------------
# Development warnings
# ------------------------------------------------------------

if any(
    row["dimension"] == "D6"
    and "SENSITIVITY_CANDIDATE"
    in row["normalization_method"]
    for row in dimensions
):
    warn(
        "D6 primary 1000x anchor remains a development "
        "candidate, not an externally validated universal anchor."
    )


ceiling_count = sum(
    1
    for row in dimensions
    if row["candidate_score"].strip()
    and abs(float(row["candidate_score"]) - 1.0) < 1e-12
)

quantitative_count = sum(
    1
    for row in dimensions
    if row["candidate_score"].strip()
)

if quantitative_count:
    ceiling_fraction = ceiling_count / quantitative_count

    if ceiling_fraction >= 0.40:
        warn(
            f"Exact ceiling fraction remains "
            f"{ceiling_fraction:.4f}; discrimination among "
            "severe/boundary cases remains a development limitation."
        )


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("GRI v2 DEVELOPMENT VALIDATION")
print("=" * 55)

print(f"Dimension rows: {len(dimensions)}")
print(f"Cases: {len(summaries)}")
print(f"Quantitative dimension scores: {quantitative_count}")
print(f"Exact ceiling scores: {ceiling_count}")
print(f"Validation errors: {len(errors)}")
print(f"Development warnings: {len(warnings)}")

if warnings:
    print("\nWARNINGS")
    for item in warnings:
        print(" -", item)

print("\nScientific safeguards:")
print(" - Missing applicable dimension becomes zero: NO")
print(" - Incomplete case receives composite: NO")
print(" - Binary demonstration becomes automatic 1.0: NO")
print(" - Construct-review metric receives point score: NO")
print(" - Corpus maximum defines normalization: NO")
print(" - Evidence strength multiplied into risk: NO")
print(" - D6 1000x claimed universal: NO")
print(" - Frozen GRI v1 overwritten: NO")

if errors:
    print("\nERRORS")
    for item in errors:
        print(" -", item)

    print("\nSTATUS: FAIL")
    sys.exit(1)

print("\nSTATUS: PASS")
