import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases"
SPEC = ROOT / "spec"
RESULTS = ROOT / "results"
VALIDATION = ROOT / "validation"

RESULTS.mkdir(parents=True, exist_ok=True)


def clamp(x):
    return max(0.0, min(1.0, float(x)))


def load_registry():
    path = SPEC / "GRI_v2_metric_registry.csv"
    registry = {}

    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            registry[row["raw_metric"]] = row

    return registry


def lookup_candidate(case_id, filename):
    path = VALIDATION / filename

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("case_id") == case_id:
                raw = row.get("candidate_score", "").strip()

                if raw:
                    return clamp(raw)

    return None


def lookup_d6(case_id):
    path = VALIDATION / "D6_amplification_inputs.csv"

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):

            if row["case_id"] != case_id:
                continue

            raw = row["amplification_ratio"].strip()

            if not raw:
                return None

            ratio = float(raw)

            if ratio < 1:
                return None

            anchor = 1000.0
            value = math.log10(ratio) / math.log10(anchor)

            return clamp(value)

    return None


def score(case_id, record, registry):
    metric = record["raw_metric"]
    dimension = record["dimension"]
    value = record["raw_value"]

    mapping = registry.get(metric)

    if mapping is None:
        return None, "UNREGISTERED_METRIC", "UNSCORED"

    if mapping["dimension"] != dimension:
        return None, "METRIC_DIMENSION_MISMATCH", "UNSCORED"

    semantic = mapping["semantic_type"]
    rule = mapping["scoring_rule"]

    # --------------------------------------------------------
    # Construct-validity gate.
    # Quantitative evidence may exist, but no dimension score
    # is issued until the metric-to-dimension mapping is accepted.
    # --------------------------------------------------------

    if rule == "CONSTRUCT_REVIEW":
        return (
            None,
            "CONSTRUCT_REVIEW",
            "CONSTRUCT_UNRESOLVED"
        )

    # --------------------------------------------------------
    # Binary demonstration proves existence, not magnitude.
    # --------------------------------------------------------

    if semantic == "BINARY_DEMONSTRATION":
        try:
            demonstrated = float(value)
        except (TypeError, ValueError):
            return None, "INVALID_BINARY_VALUE", "UNSCORED"

        if demonstrated not in (0.0, 1.0):
            return None, "INVALID_BINARY_VALUE", "UNSCORED"

        if demonstrated == 1.0:
            return (
                None,
                "BINARY_DEMONSTRATION",
                "POSITIVE_MAGNITUDE_UNRESOLVED"
            )

        return (
            None,
            "BINARY_DEMONSTRATION",
            "NO_POSITIVE_DEMONSTRATION"
        )

    # --------------------------------------------------------
    # Quantitative direct / inverse metrics
    # --------------------------------------------------------

    if rule == "DIRECT":
        try:
            return (
                clamp(value),
                semantic,
                "CANDIDATE"
            )
        except (TypeError, ValueError):
            return None, "INVALID_DIRECT_VALUE", "UNSCORED"

    if rule == "INVERSE":
        try:
            return (
                clamp(1.0 - float(value)),
                semantic,
                "CANDIDATE"
            )
        except (TypeError, ValueError):
            return None, "INVALID_INVERSE_VALUE", "UNSCORED"

    # --------------------------------------------------------
    # Dimension-specific rubrics / composites
    # --------------------------------------------------------

    if rule == "D4":
        result = lookup_candidate(
            case_id,
            "D4_rubric_application.csv"
        )

        if result is not None:
            return (
                result,
                "D4_ACCESSIBILITY_RUBRIC",
                "CANDIDATE"
            )

        return None, "D4_RUBRIC_REQUIRED", "UNSCORED"

    if rule == "D5":
        result = lookup_candidate(
            case_id,
            "D5_rubric_application.csv"
        )

        if result is not None:
            return (
                result,
                "D5_PERSISTENCE_COMPOSITE",
                "CANDIDATE"
            )

        return None, "D5_COMPONENTS_REQUIRED", "UNSCORED"

    if rule == "D6":
        result = lookup_d6(case_id)

        if result is not None:
            return (
                result,
                "D6_LOG10_ANCHORED_1000_SENSITIVITY_CANDIDATE",
                "CANDIDATE"
            )

        return None, "D6_RATIO_REQUIRED", "UNSCORED"

    if rule == "D6_DENOMINATOR_REQUIRED":
        return None, "D6_DENOMINATOR_REQUIRED", "UNSCORED"

    if rule == "D7":
        result = lookup_candidate(
            case_id,
            "D7_rubric_application.csv"
        )

        if result is not None:
            return (
                result,
                "D7_PIPELINE_RUBRIC",
                "CANDIDATE"
            )

        return None, "D7_RUBRIC_REQUIRED", "UNSCORED"

    return None, "UNKNOWN_SCORING_RULE", "UNSCORED"


def main():
    registry = load_registry()
    rows = []

    for path in sorted(CASES.glob("*.json")):

        with path.open("r", encoding="utf-8") as f:
            case = json.load(f)

        for record in case["dimensions"]:

            if record.get("status") != "APPLICABLE":
                continue

            candidate, method, status = score(
                case["case_id"],
                record,
                registry
            )

            rows.append({
                "case_id": case["case_id"],
                "dimension": record["dimension"],
                "raw_metric": record["raw_metric"],
                "raw_value": str(record["raw_value"]),
                "evidence_class": record["evidence_class"],
                "candidate_score": (
                    ""
                    if candidate is None
                    else f"{candidate:.10f}"
                ),
                "normalization_method": method,
                "v2_score_status": status
            })

    outfile = RESULTS / "GRI_v2_candidate_dimensions.csv"

    with outfile.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print("GRI v2 GENERIC METRIC SCORING")
    print("=" * 68)

    for row in rows:
        value = row["candidate_score"] or "NO_POINT_SCORE"

        print(
            f'{row["case_id"]:24} '
            f'{row["dimension"]:3} '
            f'{value:14} '
            f'{row["v2_score_status"]:30} '
            f'{row["normalization_method"]}'
        )

    print()
    print(f"Cases processed: {len(set(r['case_id'] for r in rows))}")
    print(f"Dimension rows: {len(rows)}")
    print(f"Output: {outfile}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
