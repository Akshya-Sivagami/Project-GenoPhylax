import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from gri_core import (
    aggregate_case,
    load_metric_registry,
    score_metric,
)


VERSION = "GRI-v2-development-freeze"


def fail(message, code=2):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def load_case(path):
    try:
        with path.open("r", encoding="utf-8") as f:
            case = json.load(f)
    except FileNotFoundError:
        fail(f"Case file not found: {path}")
    except json.JSONDecodeError as exc:
        fail(
            f"Invalid JSON in {path}: "
            f"line {exc.lineno}, column {exc.colno}"
        )

    return case


def validate_case(case):
    errors = []

    required_top = [
        "case_id",
        "case_type",
        "source_type",
        "dimensions",
    ]

    for key in required_top:
        if key not in case:
            errors.append(
                f"Missing required top-level field: {key}"
            )

    if "dimensions" in case:
        if not isinstance(case["dimensions"], list):
            errors.append(
                "dimensions must be an array"
            )
        elif not case["dimensions"]:
            errors.append(
                "dimensions must contain at least one record"
            )

    seen_dimensions = set()

    for index, record in enumerate(
        case.get("dimensions", [])
    ):
        prefix = f"dimensions[{index}]"

        required = [
            "dimension",
            "status",
        ]

        for key in required:
            if key not in record:
                errors.append(
                    f"{prefix}: missing {key}"
                )

        dimension = record.get("dimension")

        if dimension not in {
            "D1", "D2", "D3", "D4",
            "D5", "D6", "D7"
        }:
            errors.append(
                f"{prefix}: invalid dimension "
                f"{dimension}"
            )

        if dimension in seen_dimensions:
            errors.append(
                f"{prefix}: duplicate dimension "
                f"{dimension}"
            )

        seen_dimensions.add(dimension)

        status = record.get("status")

        if status not in {
            "APPLICABLE",
            "NOT_APPLICABLE",
            "UNMEASURED",
        }:
            errors.append(
                f"{prefix}: invalid status {status}"
            )

        if status != "APPLICABLE":
            continue

        for key in [
            "raw_metric",
            "raw_value",
            "evidence_class",
            "source",
            "limitations",
        ]:
            if key not in record:
                errors.append(
                    f"{prefix}: applicable dimension "
                    f"missing {key}"
                )

    return errors


def auxiliary_from_record(record):
    auxiliary = record.get("scoring_inputs", {})

    if auxiliary is None:
        return {}

    if not isinstance(auxiliary, dict):
        return {}

    return auxiliary


def score_case(case):
    registry = load_metric_registry()

    scored = []

    for record in case["dimensions"]:
        if record["status"] != "APPLICABLE":
            continue

        result = score_metric(
            record,
            registry,
            auxiliary_from_record(record),
        )

        scored.append({
            "dimension": record["dimension"],
            "raw_metric": record["raw_metric"],
            "raw_value": record["raw_value"],
            "evidence_class":
                record["evidence_class"],
            "source": record["source"],
            "limitations": record["limitations"],
            "candidate_score":
                result["candidate_score"],
            "normalization_method":
                result["normalization_method"],
            "v2_score_status":
                result["v2_score_status"],
        })

    summary = aggregate_case(scored)

    evidence_profile = {}

    for row in scored:
        if (
            row["v2_score_status"] == "CANDIDATE"
            and row["candidate_score"] is not None
        ):
            evidence = row["evidence_class"]
            evidence_profile[evidence] = (
                evidence_profile.get(evidence, 0) + 1
            )

    return {
        "gri_version": VERSION,
        "case_id": case["case_id"],
        "case_type": case["case_type"],
        "source_type": case["source_type"],
        "dimensions": scored,
        "summary": {
            **summary,
            "breadth_count":
                summary["point_scored_dimensions"],
            "breadth_fraction_of_seven":
                summary["point_scored_dimensions"] / 7.0,
            "evidence_profile":
                evidence_profile,
        },
        "interpretation": {
            "score_type":
                "normalized comparative indicator",
            "probability_of_harm": False,
            "probability_of_attack_success": False,
            "clinical_probability": False,
            "population_prevalence": False,
            "d6_anchor_universal": False,
        },
    }


def format_score(value):
    if value is None:
        return "NO_POINT_SCORE"

    return f"{float(value):.10f}"


def print_human(result):
    summary = result["summary"]

    print("GenoPhylax Risk Index v2")
    print("=" * 72)
    print(f'Version: {result["gri_version"]}')
    print(f'Case: {result["case_id"]}')
    print(f'Type: {result["case_type"]}')
    print(f'Source: {result["source_type"]}')
    print()

    print("DIMENSION RESULTS")
    print("-" * 72)

    for row in result["dimensions"]:
        print(
            f'{row["dimension"]:3} '
            f'{format_score(row["candidate_score"]):14} '
            f'{row["v2_score_status"]:30} '
            f'{row["normalization_method"]}'
        )

    print()
    print("CASE SUMMARY")
    print("-" * 72)

    composite = summary["candidate_composite"]

    print(
        "GRI: "
        + (
            f"{composite:.10f}"
            if composite is not None
            else "WITHHELD"
        )
    )

    print(
        "Composite status: "
        f'{summary["composite_status"]}'
    )

    print(
        "Resolution coverage: "
        f'{summary["coverage"]:.4f}'
    )

    print(
        "Breadth: "
        f'{summary["breadth_count"]}/7'
    )

    unresolved = (
        ", ".join(summary["unresolved_dimensions"])
        or "NONE"
    )

    positive = (
        ", ".join(
            summary[
                "positive_magnitude_unresolved"
            ]
        )
        or "NONE"
    )

    construct = (
        ", ".join(
            summary["construct_unresolved"]
        )
        or "NONE"
    )

    print(f"Unresolved dimensions: {unresolved}")
    print(
        "Positive magnitude unresolved: "
        f"{positive}"
    )
    print(
        "Construct unresolved: "
        f"{construct}"
    )

    print()
    print(
        "Interpretation: normalized comparative "
        "indicator; NOT a probability of harm."
    )

    if any(
        row["dimension"] == "D6"
        and row["v2_score_status"] == "CANDIDATE"
        for row in result["dimensions"]
    ):
        print(
            "D6 warning: 1000x is a development "
            "normalization anchor, not a universal threshold."
        )


def command_score(args):
    path = Path(args.case_file)
    case = load_case(path)

    errors = validate_case(case)

    if errors:
        print("CASE VALIDATION FAILED", file=sys.stderr)

        for error in errors:
            print(f" - {error}", file=sys.stderr)

        sys.exit(2)

    result = score_case(case)

    if args.json_output:
        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=False,
            )
        )
    else:
        print_human(result)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="gri",
        description=(
            "GenoPhylax Risk Index v2 "
            "development-freeze CLI"
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=VERSION,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    score_parser = subparsers.add_parser(
        "score",
        help="Score one self-contained GRI v2 JSON case.",
    )

    score_parser.add_argument(
        "case_file",
        help="Path to the GRI v2 case JSON file.",
    )

    score_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )

    score_parser.set_defaults(
        func=command_score
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
