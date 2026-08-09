#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "experiments/C_lifecycle_integration"

VALUES = BASE / "gri/C4_5a_modifier_values.tsv"
APPLICABILITY = BASE / "gri/C4_5_case_modifier_applicability.tsv"
ARCH = BASE / "gri/C4_5_modifier_architecture.json"
ARCH_A = BASE / "gri/C4_5a_modifier_architecture.json"
REPORT = BASE / "gri/C4_8_modifier_reporting_profile.tsv"
CASE_OUT = BASE / "gri/C4_8_case_output_profile.tsv"
BASELINE_JSON = BASE / "gri/C4_8_baseline_GRI.json"

METH = BASE / "methodology/C4_5_modifier_methodology.md"
CONF_METH = BASE / "methodology/C4_6_evidence_confidence_methodology.md"

VALID = BASE / "validation/C4_9_privacy_M3_semantic_correction_validation.txt"
SUMMARY = BASE / "gri/C4_9_privacy_M3_semantic_correction.md"
MARKER = BASE / "markers/C4_9_PRIVACY_M3_SEMANTIC_CORRECTION.COMPLETE"

CASE = "C3_PRIVACY"
MOD = "M3"

EXPECTED_BASE = "0.9115102712"


def read_tsv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_tsv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def find_row(rows):
    for row in rows:
        if (
            row.get("case_id") == CASE
            and row.get("modifier_id") == MOD
        ):
            return row
    raise RuntimeError(f"{CASE}/{MOD} row not found")


def patch_privacy_m3_tsv(path: Path):
    fields, rows = read_tsv(path)
    row = find_row(rows)

    for key in (
        "normalized_value",
        "value",
        "modifier_value",
    ):
        if key in fields:
            row[key] = "UNMEASURED"

    for key in (
        "resolution_status",
        "modifier_status",
        "status",
    ):
        if key in fields:
            row[key] = "UNMEASURED"

    # Schema-independent safeguard: some generated modifier tables
    # use a differently named status field. For the Privacy/M3 row,
    # any legacy numerical-resolution state must become UNMEASURED.
    for key in fields:
        if row.get(key) in {
            "RESOLVED_MODEL_SUPPORTED",
            "NUMERICALLY_RESOLVED",
        }:
            row[key] = "UNMEASURED"

    if "source" in fields:
        row["source"] = "NO_DIRECT_PRIVACY_DETECTION_MEASUREMENT"

    if "source_basis" in fields:
        row["source_basis"] = "NO_DIRECT_PRIVACY_DETECTION_MEASUREMENT"

    if "evidence_basis" in fields:
        row["evidence_basis"] = "NO_DIRECT_PRIVACY_DETECTION_MEASUREMENT"

    if "provenance_class" in fields:
        row["provenance_class"] = "UNMEASURED"

    if "applicability_status" in fields:
        row["applicability_status"] = "UNMEASURED"

    for key in (
        "rationale",
        "notes",
        "interpretation",
        "reason",
    ):
        if key in fields:
            row[key] = (
                "No direct empirical or calibrated measurement of "
                "privacy-event detectability was produced. B3 authentication "
                "F1=0.9899 and its complement 0.0101 are retained only as "
                "contextual authentication/mitigation-performance descriptors "
                "and are not interpreted as Privacy M3."
            )

    write_tsv(path, fields, rows)


def patch_json(path: Path):
    obj = json.loads(path.read_text(encoding="utf-8"))

    def walk(value):
        if isinstance(value, dict):
            is_target = (
                value.get("case_id") == CASE
                and value.get("modifier_id") == MOD
            )

            if is_target:
                if "normalized_value" in value:
                    value["normalized_value"] = "UNMEASURED"
                if "value" in value:
                    value["value"] = "UNMEASURED"

                for key in (
                    "resolution_status",
                    "modifier_status",
                    "status",
                ):
                    if key in value:
                        value[key] = "UNMEASURED"

                for key in (
                    "source",
                    "source_basis",
                    "evidence_basis",
                ):
                    if key in value:
                        value[key] = (
                            "NO_DIRECT_PRIVACY_DETECTION_MEASUREMENT"
                        )

                if "rationale" in value:
                    value["rationale"] = (
                        "No direct privacy-event detectability measurement "
                        "was produced. Authentication F1=0.9899 and "
                        "1-F1=0.0101 remain contextual mitigation-performance "
                        "descriptors only."
                    )

                if "notes" in value:
                    value["notes"] = (
                        "B3 authentication F1 is CONTEXT_ONLY and must not "
                        "be interpreted as Privacy M3 detectability."
                    )

            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(obj)

    path.write_text(
        json.dumps(obj, indent=2) + "\n",
        encoding="utf-8",
    )


def patch_case_output(path: Path):
    fields, rows = read_tsv(path)

    for row in rows:
        if row.get("case_id") != CASE:
            continue

        for key, value in list(row.items()):
            if not isinstance(value, str):
                continue

            value = value.replace(
                "M3=0.0101",
                "M3=UNMEASURED",
            )
            value = value.replace(
                "M3=0.0101000000",
                "M3=UNMEASURED",
            )
            row[key] = value

    write_tsv(path, fields, rows)


def patch_methodology():
    text = METH.read_text(encoding="utf-8")

    text = text.replace(
        "M3_privacy = 1 - F1",
        (
            "M3_privacy = UNMEASURED\n\n"
            "The B3 authentication complement `1 - F1 = 0.0101` is retained "
            "only as a contextual mitigation-performance descriptor. It does "
            "not measure privacy-event detectability and is not assigned to "
            "Privacy M3."
        ),
    )

    text = text.replace(
        "M3 Privacy: model-supported numerical descriptor.",
        (
            "M3 Privacy: UNMEASURED. No direct empirical or calibrated "
            "privacy-event detectability measurement is available. "
            "Authentication F1 and 1-F1 are CONTEXT_ONLY mitigation "
            "performance descriptors."
        ),
    )

    METH.write_text(text, encoding="utf-8")

    text = CONF_METH.read_text(encoding="utf-8")

    text = text.replace(
        "Privacy M3 is based on an internally generated B3 benchmark.",
        (
            "Privacy M3 is UNMEASURED. The internally generated B3 "
            "authentication benchmark is retained as contextual mitigation "
            "performance evidence only and does not constitute a measurement "
            "of privacy-event detectability."
        ),
    )

    CONF_METH.write_text(text, encoding="utf-8")


def main():
    required = [
        VALUES,
        APPLICABILITY,
        ARCH,
        ARCH_A,
        REPORT,
        CASE_OUT,
        BASELINE_JSON,
        METH,
        CONF_METH,
    ]

    for p in required:
        if not p.exists():
            raise SystemExit(f"ERROR: missing required file: {p}")

    # TSV artifacts with explicit modifier rows.
    for p in (VALUES, APPLICABILITY, REPORT):
        patch_privacy_m3_tsv(p)

    # JSON modifier/reporting structures.
    for p in (ARCH, ARCH_A, BASELINE_JSON):
        patch_json(p)

    patch_case_output(CASE_OUT)
    patch_methodology()

    # ---------------------------------------------------------
    # Validate semantic state.
    # ---------------------------------------------------------

    errors = []

    fields, values = read_tsv(VALUES)
    m3 = find_row(values)

    value = (
        m3.get("normalized_value")
        or m3.get("value")
        or m3.get("modifier_value")
    )

    if value != "UNMEASURED":
        errors.append(
            f"C4_5a Privacy M3 expected UNMEASURED, found {value!r}"
        )

    fields, app = read_tsv(APPLICABILITY)
    a = find_row(app)

    joined = " ".join(str(x) for x in a.values())

    if "NUMERICALLY_RESOLVED" in joined:
        errors.append(
            "Privacy M3 still NUMERICALLY_RESOLVED in applicability table"
        )

    case_text = CASE_OUT.read_text(encoding="utf-8")

    if "M3=0.0101" in case_text:
        errors.append(
            "C4_8 case output still reports M3=0.0101"
        )

    if "M3=UNMEASURED" not in case_text:
        errors.append(
            "C4_8 case output does not report M3=UNMEASURED"
        )

    # Base GRI numerical lock.
    base_text = CASE_OUT.read_text(encoding="utf-8")
    json_text = BASELINE_JSON.read_text(encoding="utf-8")

    if EXPECTED_BASE not in base_text:
        errors.append(
            "Privacy Base GRI missing from C4_8 case output"
        )

    if EXPECTED_BASE not in json_text:
        errors.append(
            "Privacy Base GRI missing from C4_8 baseline JSON"
        )

    # The original authentication residual must remain available upstream.
    norm_file = BASE / "gri/C4_3_normalized_anchor_inputs.tsv"
    norm_text = norm_file.read_text(encoding="utf-8")

    if "NORM_PRIV_D4_AUTH_RESIDUAL" not in norm_text:
        errors.append(
            "Authentication residual normalization unexpectedly missing"
        )

    if "0.0101000000" not in norm_text:
        errors.append(
            "Authentication residual value 0.0101 unexpectedly removed"
        )

    now = datetime.now(timezone.utc).isoformat()

    summary = f"""# C4.9 Privacy M3 Construct-Validity Correction

## Decision

Privacy M3 (Detectability) is now:

`UNMEASURED`

The project did not directly measure or calibrate privacy-event detectability.

## Authentication benchmark retained

The B3 authentication benchmark remains valid:

- threshold: 4.5
- precision: 1.0000
- recall: 0.9800
- F1: 0.9899
- residual performance complement: 1 - F1 = 0.0101

The 0.0101 value remains a `DIRECT_MITIGATION_ONLY` /
`CONTEXT_ONLY` authentication-performance descriptor.

It is not a measurement of Privacy M3.

## GRI impact

Privacy Base GRI remains:

`{EXPECTED_BASE}`

No Base GRI dimension or aggregation mathematics were changed.

Generated UTC: {now}
"""

    SUMMARY.write_text(summary, encoding="utf-8")

    validation = [
        "C4.9 PRIVACY M3 SEMANTIC CORRECTION VALIDATION",
        "===============================================",
        "",
        f"Generated UTC: {now}",
        f"Validation errors: {len(errors)}",
        f"Privacy M3: {'FAIL' if errors else 'UNMEASURED'}",
        "Authentication F1: 0.9899 RETAINED",
        "Authentication residual 1-F1: 0.0101 RETAINED_CONTEXT_ONLY",
        f"Privacy Base GRI: {EXPECTED_BASE}",
        "Base GRI changed: NO",
        "",
        f"STATUS: {'FAIL' if errors else 'PASS'}",
    ]

    if errors:
        validation.extend(["", "Errors:"])
        validation.extend(f"- {x}" for x in errors)

    VALID.write_text(
        "\n".join(validation) + "\n",
        encoding="utf-8",
    )

    if errors:
        for err in errors:
            print("ERROR:", err)
        raise SystemExit(1)

    MARKER.write_text(
        "\n".join(
            [
                "Status: COMPLETE",
                f"UTC: {now}",
                "Privacy M3: UNMEASURED",
                "Authentication F1: 0.9899 RETAINED",
                "Authentication residual: 0.0101 CONTEXT_ONLY",
                f"Privacy Base GRI: {EXPECTED_BASE}",
                "Base GRI changed: NO",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print("C4.9 Privacy M3 semantic correction complete")
    print("Privacy M3: UNMEASURED")
    print("Authentication F1: 0.9899 RETAINED")
    print("Authentication residual 1-F1: 0.0101 CONTEXT_ONLY")
    print(f"Privacy Base GRI: {EXPECTED_BASE}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
