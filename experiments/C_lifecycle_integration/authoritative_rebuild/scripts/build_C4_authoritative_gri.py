#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[4]
ROOT = REPO / "experiments/C_lifecycle_integration/authoritative_rebuild"

C2 = ROOT / "c2_evidence/C2_authoritative_evidence_registry.tsv"
C3 = ROOT / "c3_handoffs/C3_authoritative_handoffs.tsv"

B1 = REPO / "experiments/B_final_audit/B1_authoritative_final.tsv"
B2 = REPO / "experiments/B_final_audit/B2_authoritative_final.tsv"
B3 = REPO / "experiments/B_final_audit/B3_authoritative_final.tsv"

DIMENSIONS = ROOT / "c4_gri/C4_dimension_registry.tsv"
RAW = ROOT / "c4_gri/C4_raw_metrics.tsv"
NORMALIZED = ROOT / "c4_gri/C4_normalized_dimensions.tsv"
BASE = ROOT / "c4_gri/C4_base_gri.tsv"
MODIFIERS = ROOT / "c4_gri/C4_modifier_context.tsv"
SENSITIVITY = ROOT / "c4_gri/C4_sensitivity_analysis.tsv"
JSON_OUT = ROOT / "c4_gri/C4_authoritative_gri.json"
METHODOLOGY = ROOT / "c4_gri/C4_methodology.md"
VALIDATION = ROOT / "validation/C4_authoritative_gri_validation.txt"


DIMENSION_DEFS = [
    {
        "dimension": "D1",
        "name": "Identity Risk",
        "meaning": (
            "Risk that genomic disclosure enables persistent "
            "re-identification of the individual."
        ),
    },
    {
        "dimension": "D2",
        "name": "Disease Inference / Clinical Interpretation Risk",
        "meaning": (
            "Risk that genomic manipulation or disclosure changes or "
            "reveals clinically relevant interpretation."
        ),
    },
    {
        "dimension": "D3",
        "name": "Familial Cascade Risk",
        "meaning": (
            "Risk propagated from one genomic subject to biologically "
            "related individuals."
        ),
    },
    {
        "dimension": "D4",
        "name": "Accessibility Risk",
        "meaning": (
            "Risk associated with unauthorized or inappropriate access "
            "to genomic information."
        ),
    },
    {
        "dimension": "D5",
        "name": "Persistence Risk",
        "meaning": (
            "Risk that disclosure or exposure remains difficult to "
            "reverse across time."
        ),
    },
    {
        "dimension": "D6",
        "name": "Amplification Risk",
        "meaning": (
            "Risk that an initial genomic disclosure expands through "
            "sharing, kinship or downstream reuse."
        ),
    },
    {
        "dimension": "D7",
        "name": "Pipeline Exposure Risk",
        "meaning": (
            "Risk that an upstream integrity failure propagates across "
            "multiple downstream genomic-processing stages."
        ),
    },
]


def load_tsv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def metric_table(path: Path):
    rows = load_tsv(path)

    result = {}

    for row in rows:
        metric = row["metric"].strip()
        value = row["value"].strip()
        result[metric] = value

    return result


def require_float(metrics, key):
    if key not in metrics:
        raise KeyError(f"Missing authoritative metric: {key}")

    return float(metrics[key])


def require_int(metrics, key):
    if key not in metrics:
        raise KeyError(f"Missing authoritative metric: {key}")

    return int(float(metrics[key]))


def write_tsv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    errors = []

    c2_rows = load_tsv(C2)
    c3_rows = load_tsv(C3)

    c2 = {
        row["evidence_id"]: row
        for row in c2_rows
    }

    c3 = {
        row["handoff_id"]: row
        for row in c3_rows
    }

    b1 = metric_table(B1)
    b2 = metric_table(B2)
    b3 = metric_table(B3)

    # ============================================================
    # C4.1 — DIMENSION ARCHITECTURE
    # ============================================================

    dimension_rows = []

    applicability = {
        "F11": {
            "D1": "N/A",
            "D2": "APPLICABLE",
            "D3": "N/A",
            "D4": "N/A",
            "D5": "N/A",
            "D6": "N/A",
            "D7": "APPLICABLE",
        },
        "PRIVACY": {
            "D1": "APPLICABLE",
            "D2": "N/A",
            "D3": "APPLICABLE",
            "D4": "N/A",
            "D5": "APPLICABLE",
            "D6": "APPLICABLE",
            "D7": "N/A",
        },
    }

    for definition in DIMENSION_DEFS:
        d = definition["dimension"]

        dimension_rows.append(
            {
                "dimension": d,
                "name": definition["name"],
                "meaning": definition["meaning"],
                "F11_applicability": applicability["F11"][d],
                "PRIVACY_applicability": applicability["PRIVACY"][d],
                "scoring_policy": (
                    "Equal weighting across applicable dimensions only; "
                    "N/A and UNMEASURED are never converted to zero."
                ),
            }
        )

    write_tsv(
        DIMENSIONS,
        dimension_rows,
        [
            "dimension",
            "name",
            "meaning",
            "F11_applicability",
            "PRIVACY_applicability",
            "scoring_policy",
        ],
    )

    # ============================================================
    # C4.2 — AUTHORITATIVE RAW METRICS
    # ============================================================

    b1_d6 = require_float(b1, "ground_truth_D6_score")

    b2_unrecoverability = require_float(
        b2,
        "clinician_pathogenic_variants_unrecoverability",
    )

    b2_reid_100 = require_int(
        b2,
        "reidentification_100pct_year",
    )

    b2_familial_100 = require_int(
        b2,
        "familial_100pct_year",
    )

    b2_d5_y50 = require_float(
        b2,
        "D5_year_50",
    )

    b3_auth_threshold = require_float(
        b3,
        "auth_threshold",
    )

    b3_auth_f1 = require_float(
        b3,
        "auth_f1",
    )

    b3_peripheral_residual = require_float(
        b3,
        "M5_peripheral_residual_candidate",
    )

    b3_mid_residual = require_float(
        b3,
        "M5_mid_residual_candidate",
    )

    b3_hub_residual = require_float(
        b3,
        "M5_hub_residual_candidate",
    )

    raw_rows = [
        {
            "metric_id": "RAW_F11_ALT_AFTER_PM2",
            "case": "F11",
            "source": "A3_E02",
            "raw_value": c2["A3_E02"]["numeric_value"],
            "unit": c2["A3_E02"]["unit"],
            "purpose": "D2 clinical-interpretation integrity anchor",
        },
        {
            "metric_id": "RAW_F11_CALL_LOSS",
            "case": "F11",
            "source": "A3_E03",
            "raw_value": "OBSERVED",
            "unit": "controlled downstream call loss",
            "purpose": "D2 and D7 propagation anchor",
        },
        {
            "metric_id": "RAW_B2_UNRECOVERABILITY",
            "case": "PRIVACY",
            "source": "B2_authoritative_final.tsv",
            "raw_value": f"{b2_unrecoverability:.4f}",
            "unit": "proportion",
            "purpose": "D5 irreversibility component",
        },
        {
            "metric_id": "RAW_B2_REID_100_YEAR",
            "case": "PRIVACY",
            "source": "B2_authoritative_final.tsv",
            "raw_value": str(b2_reid_100),
            "unit": "years",
            "purpose": "D1 identity saturation evidence",
        },
        {
            "metric_id": "RAW_B2_FAMILIAL_100_YEAR",
            "case": "PRIVACY",
            "source": "B2_authoritative_final.tsv",
            "raw_value": str(b2_familial_100),
            "unit": "years",
            "purpose": "D3 familial saturation evidence",
        },
        {
            "metric_id": "RAW_B2_D5_YEAR50",
            "case": "PRIVACY",
            "source": "B2_authoritative_final.tsv",
            "raw_value": f"{b2_d5_y50:.2f}",
            "unit": "0_to_10",
            "purpose": "D5 long-horizon persistence component",
        },
        {
            "metric_id": "RAW_B1_D6",
            "case": "PRIVACY",
            "source": "B1_authoritative_final.tsv",
            "raw_value": f"{b1_d6:.2f}",
            "unit": "0_to_10",
            "purpose": "D6 calibrated amplification score",
        },
        {
            "metric_id": "RAW_B3_AUTH_F1",
            "case": "PRIVACY",
            "source": "B3_authoritative_final.tsv",
            "raw_value": f"{b3_auth_f1:.4f}",
            "unit": "proportion",
            "purpose": "Context only; NOT M3 detectability",
        },
        {
            "metric_id": "RAW_B3_AUTH_THRESHOLD",
            "case": "PRIVACY",
            "source": "B3_authoritative_final.tsv",
            "raw_value": f"{b3_auth_threshold:.1f}",
            "unit": "score_threshold",
            "purpose": "Authentication benchmark context only",
        },
    ]

    write_tsv(
        RAW,
        raw_rows,
        [
            "metric_id",
            "case",
            "source",
            "raw_value",
            "unit",
            "purpose",
        ],
    )

    # ============================================================
    # C4.3 — NORMALIZATION
    #
    # IMPORTANT:
    # Scores are 0..1.
    # Missing/non-applicable dimensions are not scored.
    # ============================================================

    # F11 D2:
    # Complete on-target loss of evaluable ALT-support plus observed
    # downstream loss of the clinically relevant call.
    if c2["A3_E02"]["numeric_value"] != "0/14":
        errors.append(
            "F11 D2 prerequisite changed: expected A3_E02 = 0/14"
        )

    if "A3_E03" not in c2:
        errors.append(
            "F11 D2 prerequisite missing: A3_E03"
        )

    f11_d2 = 1.0

    # F11 D7:
    # The demonstrated effect traverses the complete observed clinical
    # chain represented here: S2 -> S4 -> S5.
    required_f11_handoffs = {"HF11_01", "HF11_02"}

    if not required_f11_handoffs.issubset(c3):
        errors.append(
            "F11 D7 prerequisite handoffs missing"
        )

    f11_d7 = 1.0

    # Privacy D1:
    # B2 explicitly reaches 100% modelled re-identification saturation.
    # Year-to-saturation remains reported as context rather than using an
    # arbitrary external time-horizon transformation.
    privacy_d1 = 1.0

    # Privacy D3:
    # B2 explicitly reaches 100% modelled familial saturation.
    privacy_d3 = 1.0

    # Privacy D5:
    # Combine two conceptually related persistence signals INSIDE ONE
    # dimension:
    #
    #   irreversibility component = 1 - unrecoverability
    #   long-horizon persistence  = D5(year 50) / 10
    #
    # Averaging inside D5 prevents these correlated B2 outputs from
    # becoming separate GRI dimensions.
    irreversibility_component = 1.0 - b2_unrecoverability
    persistence_y50_component = b2_d5_y50 / 10.0

    privacy_d5 = mean(
        [
            irreversibility_component,
            persistence_y50_component,
        ]
    )

    # Privacy D6:
    # B1 already reports a calibrated 0..10 D6 score.
    privacy_d6 = b1_d6 / 10.0

    normalized_rows = [
        {
            "case": "F11",
            "dimension": "D2",
            "status": "MEASURED",
            "score": f"{f11_d2:.10f}",
            "formula": (
                "1.0 because targeted PM2 produced complete evaluable "
                "ALT-support loss and downstream F11 call loss"
            ),
            "provenance": "A3_E02|A3_E03",
        },
        {
            "case": "F11",
            "dimension": "D7",
            "status": "MEASURED",
            "score": f"{f11_d7:.10f}",
            "formula": (
                "1.0 because the demonstrated effect traversed the full "
                "observed clinical chain S2->S4->S5"
            ),
            "provenance": "HF11_01|HF11_02",
        },
        {
            "case": "PRIVACY",
            "dimension": "D1",
            "status": "MODELLED",
            "score": f"{privacy_d1:.10f}",
            "formula": (
                "1.0 because B2 reaches 100% modelled re-identification "
                f"saturation; saturation year={b2_reid_100}"
            ),
            "provenance": "B2_E02",
        },
        {
            "case": "PRIVACY",
            "dimension": "D3",
            "status": "MODELLED",
            "score": f"{privacy_d3:.10f}",
            "formula": (
                "1.0 because B2 reaches 100% modelled familial "
                f"saturation; saturation year={b2_familial_100}"
            ),
            "provenance": "B2_E03",
        },
        {
            "case": "PRIVACY",
            "dimension": "D5",
            "status": "MODELLED",
            "score": f"{privacy_d5:.10f}",
            "formula": (
                "mean(1 - clinician pathogenic-variant unrecoverability, "
                "D5_year_50 / 10)"
            ),
            "provenance": "B2_E01|B2_authoritative_final.tsv",
        },
        {
            "case": "PRIVACY",
            "dimension": "D6",
            "status": "CALIBRATED_MODEL",
            "score": f"{privacy_d6:.10f}",
            "formula": "ground_truth_D6_score / 10",
            "provenance": "B1_E02|B1_authoritative_final.tsv",
        },
    ]

    for row in normalized_rows:
        value = float(row["score"])

        if not 0 <= value <= 1:
            errors.append(
                f"{row['case']} {row['dimension']} outside 0..1"
            )

    write_tsv(
        NORMALIZED,
        normalized_rows,
        [
            "case",
            "dimension",
            "status",
            "score",
            "formula",
            "provenance",
        ],
    )

    # ============================================================
    # C4.4 — BASE GRI
    # Equal weighting over APPLICABLE MEASURED dimensions.
    # No evidence-tier multiplier.
    # No B3 mitigation multiplier.
    # ============================================================

    case_scores = {}

    for row in normalized_rows:
        case_scores.setdefault(
            row["case"],
            [],
        ).append(
            (
                row["dimension"],
                float(row["score"]),
            )
        )

    base_rows = []

    for case, items in case_scores.items():
        score = mean(value for _, value in items)

        base_rows.append(
            {
                "case": case,
                "applicable_dimensions": "|".join(
                    d for d, _ in items
                ),
                "dimension_count": str(len(items)),
                "base_gri": f"{score:.10f}",
                "weighting": (
                    "equal weight across applicable measured dimensions"
                ),
                "evidence_tier_multiplier": "NONE",
                "mitigation_modifier_applied": "NO",
            }
        )

    write_tsv(
        BASE,
        base_rows,
        [
            "case",
            "applicable_dimensions",
            "dimension_count",
            "base_gri",
            "weighting",
            "evidence_tier_multiplier",
            "mitigation_modifier_applied",
        ],
    )

    base_lookup = {
        row["case"]: float(row["base_gri"])
        for row in base_rows
    }

    # ============================================================
    # C4.5 — MODIFIER CONTEXT
    # ============================================================

    modifier_rows = [
        {
            "case": "F11",
            "modifier": "M3",
            "meaning": "Detectability",
            "status": "UNMEASURED",
            "value": "",
            "scenario": "",
            "application": "NOT_APPLIED",
            "rationale": (
                "No validated measure of attack/event detectability is "
                "available for the F11 experiment."
            ),
        },
        {
            "case": "PRIVACY",
            "modifier": "M3",
            "meaning": "Detectability",
            "status": "UNMEASURED",
            "value": "",
            "scenario": "",
            "application": "NOT_APPLIED",
            "rationale": (
                "Authentication F1 is access-control performance, not "
                "privacy-event detectability."
            ),
        },
        {
            "case": "PRIVACY",
            "modifier": "M5",
            "meaning": "Containment difficulty residual",
            "status": "SCENARIO_CANDIDATE",
            "value": f"{b3_peripheral_residual:.3f}",
            "scenario": "peripheral_origin_at_k10",
            "application": "NOT_APPLIED_TO_BASE_GRI",
            "rationale": (
                "Residual candidate = 1 - k10 containment reduction."
            ),
        },
        {
            "case": "PRIVACY",
            "modifier": "M5",
            "meaning": "Containment difficulty residual",
            "status": "SCENARIO_CANDIDATE",
            "value": f"{b3_mid_residual:.3f}",
            "scenario": "mid_degree_origin_at_k10",
            "application": "NOT_APPLIED_TO_BASE_GRI",
            "rationale": (
                "Residual candidate = 1 - k10 containment reduction."
            ),
        },
        {
            "case": "PRIVACY",
            "modifier": "M5",
            "meaning": "Containment difficulty residual",
            "status": "SCENARIO_CANDIDATE",
            "value": f"{b3_hub_residual:.3f}",
            "scenario": "hub_origin_at_k10",
            "application": "NOT_APPLIED_TO_BASE_GRI",
            "rationale": (
                "Residual candidate = 1 - k10 containment reduction."
            ),
        },
    ]

    write_tsv(
        MODIFIERS,
        modifier_rows,
        [
            "case",
            "modifier",
            "meaning",
            "status",
            "value",
            "scenario",
            "application",
            "rationale",
        ],
    )

    # ============================================================
    # C4.6 — SENSITIVITY
    # ============================================================

    sensitivity_rows = []

    privacy_values = {
        "D1": privacy_d1,
        "D3": privacy_d3,
        "D5": privacy_d5,
        "D6": privacy_d6,
    }

    baseline_privacy = mean(privacy_values.values())

    sensitivity_rows.append(
        {
            "case": "PRIVACY",
            "analysis": "equal_dimension_baseline",
            "score": f"{baseline_privacy:.10f}",
            "interpretation": (
                "Primary Base GRI; equal weight across D1,D3,D5,D6."
            ),
        }
    )

    for omitted in privacy_values:
        retained = [
            value
            for dimension, value in privacy_values.items()
            if dimension != omitted
        ]

        sensitivity_rows.append(
            {
                "case": "PRIVACY",
                "analysis": f"leave_one_out_{omitted}",
                "score": f"{mean(retained):.10f}",
                "interpretation": (
                    f"Sensitivity only; {omitted} omitted."
                ),
            }
        )

    # B2 provides D1, D3 and D5 while B1 provides D6.
    # This alternative gives the B1 and B2 provenance families equal
    # total weight, rather than equal dimension weight.
    b2_composite = mean(
        [
            privacy_d1,
            privacy_d3,
            privacy_d5,
        ]
    )

    provenance_balanced = mean(
        [
            b2_composite,
            privacy_d6,
        ]
    )

    sensitivity_rows.append(
        {
            "case": "PRIVACY",
            "analysis": "50_50_B2_B1_provenance_balance",
            "score": f"{provenance_balanced:.10f}",
            "interpretation": (
                "Sensitivity only: B2-derived dimensions combined into "
                "one composite and weighted 50/50 against B1 D6."
            ),
        }
    )

    write_tsv(
        SENSITIVITY,
        sensitivity_rows,
        [
            "case",
            "analysis",
            "score",
            "interpretation",
        ],
    )

    # ============================================================
    # C4.7 — VALIDATION
    # ============================================================

    if abs(base_lookup["F11"] - 1.0) > 1e-12:
        errors.append(
            "Unexpected F11 Base GRI"
        )

    if b3_auth_threshold != 3.6:
        errors.append(
            "B3 authoritative authentication threshold is not 3.6"
        )

    if abs(b3_auth_f1 - 0.8387) > 1e-12:
        errors.append(
            "B3 authoritative authentication F1 is not 0.8387"
        )

    for row in base_rows:
        if row["mitigation_modifier_applied"] != "NO":
            errors.append(
                f"{row['case']} incorrectly applies modifier to Base GRI"
            )

    result = {
        "dimension_architecture": DIMENSION_DEFS,
        "normalized_dimensions": normalized_rows,
        "base_gri": base_rows,
        "modifiers": modifier_rows,
        "sensitivity": sensitivity_rows,
        "policy": {
            "missing_equals_zero": False,
            "evidence_tiers_are_numeric_weights": False,
            "modifiers_multiply_base_gri": False,
            "authentication_f1_is_detectability": False,
            "sensitivity_is_confidence_interval": False,
        },
    }

    JSON_OUT.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    methodology = f"""# C4 Authoritative GRI Methodology

## Core rule

The Base GenoPhylax Risk Index is the arithmetic mean of only the
applicable, evidence-backed dimensions for a case.

Missing, non-applicable, contextual and unmeasured dimensions are not
converted to zero.

Evidence tiers describe evidentiary strength and are not numerical
multipliers.

Mitigation modifiers are reported separately and do not alter Base GRI.

## F11 case

Applicable dimensions:

- D2 Disease Inference / Clinical Interpretation Risk = {f11_d2:.4f}
- D7 Pipeline Exposure Risk = {f11_d7:.4f}

Base GRI = {base_lookup['F11']:.10f}

The F11 score is an experimental-case severity score for the demonstrated
computational chain. It is not a patient-outcome probability.

## Privacy case

Applicable dimensions:

- D1 Identity Risk = {privacy_d1:.4f}
- D3 Familial Cascade Risk = {privacy_d3:.4f}
- D5 Persistence Risk = {privacy_d5:.4f}
- D6 Amplification Risk = {privacy_d6:.4f}

D5 is the mean of:

- irreversibility component = 1 - {b2_unrecoverability:.4f}
  = {irreversibility_component:.4f}
- year-50 persistence component = {b2_d5_y50:.2f} / 10
  = {persistence_y50_component:.4f}

Base Privacy GRI = {base_lookup['PRIVACY']:.10f}

## B3 mitigation

Authentication threshold = {b3_auth_threshold:.1f}
Authentication F1 = {b3_auth_f1:.4f}

These values are mitigation-performance context and are not used as M3
detectability.

M5 containment-difficulty residual candidates at fixed k=10 are:

- peripheral origin: {b3_peripheral_residual:.3f}
- mid-degree origin: {b3_mid_residual:.3f}
- hub origin: {b3_hub_residual:.3f}

They are scenario-specific and are not multiplied into Base GRI.

## Sensitivity

The 50/50 B2-vs-B1 provenance-balanced Privacy sensitivity score is
{provenance_balanced:.10f}.

Sensitivity analyses are robustness checks, not confidence intervals.
"""

    METHODOLOGY.write_text(
        methodology,
        encoding="utf-8",
    )

    validation_lines = [
        "MODULE C AUTHORITATIVE REBUILD — C4 VALIDATION",
        "================================================",
        "",
        f"F11 Base GRI: {base_lookup['F11']:.10f}",
        f"Privacy Base GRI: {base_lookup['PRIVACY']:.10f}",
        (
            "Privacy 50/50 B2-B1 provenance sensitivity: "
            f"{provenance_balanced:.10f}"
        ),
        "",
        "Privacy normalized dimensions:",
        f"  D1: {privacy_d1:.10f}",
        f"  D3: {privacy_d3:.10f}",
        f"  D5: {privacy_d5:.10f}",
        f"  D6: {privacy_d6:.10f}",
        "",
        "B3 mitigation context:",
        f"  auth threshold: {b3_auth_threshold:.1f}",
        f"  auth F1: {b3_auth_f1:.4f}",
        f"  M5 peripheral: {b3_peripheral_residual:.3f}",
        f"  M5 mid-degree: {b3_mid_residual:.3f}",
        f"  M5 hub: {b3_hub_residual:.3f}",
        "",
        "Scientific safeguards:",
        "  Missing/N/A converted to zero: NO",
        "  Evidence tiers used as numeric weights: NO",
        "  B3 authentication used as M3 detectability: NO",
        "  M5 multiplied into Base GRI: NO",
        "  Sensitivity called confidence interval: NO",
        "  Old Module C numeric output consumed: NO",
        "",
        f"Validation errors: {len(errors)}",
    ]

    if errors:
        validation_lines.extend(
            f"  ERROR: {error}"
            for error in errors
        )
        validation_lines.extend(
            [
                "",
                "STATUS: FAIL",
            ]
        )
    else:
        validation_lines.extend(
            [
                "",
                "STATUS: PASS",
            ]
        )

    VALIDATION.write_text(
        "\n".join(validation_lines) + "\n",
        encoding="utf-8",
    )

    if errors:
        print("C4 BUILD: FAIL")

        for error in errors:
            print(error)

        return 1

    print("C4 BUILD: PASS")
    print(f"F11 Base GRI: {base_lookup['F11']:.10f}")
    print(
        f"Privacy Base GRI: "
        f"{base_lookup['PRIVACY']:.10f}"
    )
    print(
        "Privacy provenance-balanced sensitivity: "
        f"{provenance_balanced:.10f}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
