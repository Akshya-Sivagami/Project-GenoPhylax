import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "cases"
SPEC_DIR = ROOT / "spec"

DIMENSIONS = {"D1", "D2", "D3", "D4", "D5", "D6", "D7"}
CASE_TYPES = {
    "INTEGRITY", "PRIVACY", "SOFTWARE_SECURITY",
    "ACCESS_CONTROL", "MIXED"
}
SOURCE_TYPES = {
    "GENOPHYLAX_EXPERIMENT", "GENOPHYLAX_MODEL",
    "EXTERNAL_EMPIRICAL", "EXTERNAL_INCIDENT",
    "EXTERNAL_RESEARCH"
}
STATUSES = {"APPLICABLE", "NOT_APPLICABLE", "UNMEASURED"}
EVIDENCE_CLASSES = {
    "EXPERIMENTAL", "OBSERVATIONAL",
    "CALIBRATED_MODEL", "MODELLED", "INFERRED"
}

FORBIDDEN_SCORE_FIELDS = {
    "score",
    "normalized_score",
    "gri",
    "base_gri",
    "risk_score"
}


def error(errors, filename, message):
    errors.append(f"{filename}: {message}")


def validate_case(path):
    errors = []

    try:
        with path.open("r", encoding="utf-8") as f:
            case = json.load(f)
    except Exception as exc:
        return [f"{path.name}: invalid JSON: {exc}"]

    required_case_fields = {
        "case_id", "title", "case_type",
        "source_type", "dimensions"
    }

    missing = required_case_fields - set(case)
    if missing:
        error(errors, path.name,
              f"missing case fields: {sorted(missing)}")

    if case.get("case_type") not in CASE_TYPES:
        error(errors, path.name,
              f"invalid case_type: {case.get('case_type')}")

    if case.get("source_type") not in SOURCE_TYPES:
        error(errors, path.name,
              f"invalid source_type: {case.get('source_type')}")

    dimensions = case.get("dimensions")

    if not isinstance(dimensions, list) or not dimensions:
        error(errors, path.name,
              "dimensions must be a non-empty list")
        return errors

    seen = set()

    for i, record in enumerate(dimensions, start=1):

        if not isinstance(record, dict):
            error(errors, path.name,
                  f"dimension record {i} is not an object")
            continue

        dimension = record.get("dimension")

        if dimension not in DIMENSIONS:
            error(errors, path.name,
                  f"record {i}: invalid dimension {dimension}")
        elif dimension in seen:
            error(errors, path.name,
                  f"record {i}: duplicate dimension {dimension}")
        else:
            seen.add(dimension)

        status = record.get("status")

        if status not in STATUSES:
            error(errors, path.name,
                  f"{dimension}: invalid status {status}")

        forbidden = FORBIDDEN_SCORE_FIELDS.intersection(record)

        if forbidden:
            error(
                errors,
                path.name,
                f"{dimension}: manual score fields forbidden: "
                f"{sorted(forbidden)}"
            )

        if status == "APPLICABLE":

            required_dimension_fields = {
                "raw_metric",
                "raw_value",
                "unit",
                "evidence_class",
                "source",
                "limitations"
            }

            missing_dimension = (
                required_dimension_fields - set(record)
            )

            if missing_dimension:
                error(
                    errors,
                    path.name,
                    f"{dimension}: missing fields "
                    f"{sorted(missing_dimension)}"
                )

            evidence = record.get("evidence_class")

            if evidence not in EVIDENCE_CLASSES:
                error(
                    errors,
                    path.name,
                    f"{dimension}: invalid evidence_class "
                    f"{evidence}"
                )

            source = record.get("source")

            if not isinstance(source, str) or not source.strip():
                error(errors, path.name,
                      f"{dimension}: provenance/source missing")

            metric = record.get("raw_metric")

            if not isinstance(metric, str) or not metric.strip():
                error(errors, path.name,
                      f"{dimension}: raw_metric missing")

            if record.get("raw_value") is None:
                error(errors, path.name,
                      f"{dimension}: raw_value missing")

            limitations = record.get("limitations")

            if (
                not isinstance(limitations, str)
                or not limitations.strip()
            ):
                error(errors, path.name,
                      f"{dimension}: limitations missing")

    return errors


def main():
    case_files = sorted(CASES_DIR.glob("*.json"))

    if not case_files:
        print("FAIL: no case files found")
        sys.exit(1)

    all_errors = []
    ids = {}

    for path in case_files:
        errors = validate_case(path)
        all_errors.extend(errors)

        try:
            with path.open("r", encoding="utf-8") as f:
                case = json.load(f)

            case_id = case.get("case_id")

            if case_id:
                if case_id in ids:
                    all_errors.append(
                        f"{path.name}: duplicate case_id "
                        f"{case_id}; first seen in {ids[case_id]}"
                    )
                else:
                    ids[case_id] = path.name
        except Exception:
            pass

    print("GRI v2 CASE CORPUS VALIDATION")
    print("=" * 40)
    print(f"Cases checked: {len(case_files)}")
    print(f"Unique case IDs: {len(ids)}")
    print(f"Validation errors: {len(all_errors)}")

    if all_errors:
        print("\nERRORS")
        for item in all_errors:
            print(f" - {item}")

        print("\nSTATUS: FAIL")
        sys.exit(1)

    print("\nValidated cases:")
    for case_id, filename in sorted(ids.items()):
        print(f" - {case_id}: {filename}")

    print("\nScientific safeguards:")
    print(" - Manual normalized scores allowed: NO")
    print(" - Missing dimensions converted to zero: NO")
    print(" - Provenance required: YES")
    print(" - Evidence class required: YES")
    print(" - Limitations required: YES")

    print("\nSTATUS: PASS")


if __name__ == "__main__":
    main()
