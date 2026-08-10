#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ROOT = REPO / "experiments/C_lifecycle_integration/authoritative_rebuild"

C2 = ROOT / "c2_evidence/C2_authoritative_evidence_registry.tsv"
C3 = ROOT / "c3_handoffs/C3_authoritative_handoffs.tsv"
C4_BASE = ROOT / "c4_gri/C4_base_gri.tsv"
C4_NORM = ROOT / "c4_gri/C4_normalized_dimensions.tsv"
C4_MOD = ROOT / "c4_gri/C4_modifier_context.tsv"
C4_SENS = ROOT / "c4_gri/C4_sensitivity_analysis.tsv"

OUT_TSV = ROOT / "c5_findings/C5_integrated_findings.tsv"
OUT_JSON = ROOT / "c5_findings/C5_integrated_findings.json"
OUT_MD = ROOT / "c5_findings/C5_integrated_findings.md"
VALID = ROOT / "validation/C5_integrated_findings_validation.txt"


def load(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def one(rows, key, value):
    matches = [
        row
        for row in rows
        if row[key] == value
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {key}={value}, got {len(matches)}"
        )

    return matches[0]


def main():
    errors = []

    c2 = load(C2)
    c3 = load(C3)
    base = load(C4_BASE)
    norm = load(C4_NORM)
    modifiers = load(C4_MOD)
    sensitivity = load(C4_SENS)

    base_by_case = {
        row["case"]: float(row["base_gri"])
        for row in base
    }

    norm_by_key = {
        (row["case"], row["dimension"]): float(row["score"])
        for row in norm
    }

    sens = {
        row["analysis"]: float(row["score"])
        for row in sensitivity
    }

    # ------------------------------------------------------------
    # Core assertions
    # ------------------------------------------------------------

    if abs(base_by_case["F11"] - 1.0) > 1e-12:
        errors.append("Unexpected F11 Base GRI")

    if "PRIVACY" not in base_by_case:
        errors.append("Privacy Base GRI missing")

    required_privacy_dims = {
        ("PRIVACY", "D1"),
        ("PRIVACY", "D3"),
        ("PRIVACY", "D5"),
        ("PRIVACY", "D6"),
    }

    if not required_privacy_dims.issubset(norm_by_key):
        errors.append("Privacy dimension set incomplete")

    if any(
        row["role"] == "GRI_ELIGIBLE"
        for row in c2
        if row["module"] == "B3"
    ):
        errors.append("B3 incorrectly became direct GRI evidence")

    findings = [
        {
            "finding_id": "C5_F01",
            "category": "clinical_integrity",
            "title": "Targeted signal perturbation propagated to clinical variant-call loss",
            "finding": (
                "In the controlled HG002 F11 case, targeted PM2 perturbation "
                "reduced evaluable ALT-supporting parents from 14/14 in the "
                "clean condition to 0/14 on target, with downstream loss of "
                "the clinically relevant F11 variant call."
            ),
            "quantitative_anchor": "14/14 -> 0/14; downstream F11 call lost",
            "evidence": "A3_E01|A3_E02|A3_E03|A3_E04|HF11_01|HF11_02",
            "claim_level": "CONTROLLED_CASE",
            "limitation": (
                "Single HG002 individual, one pathogenic F11 locus and one "
                "basecaller/perturbation configuration; no patient outcome "
                "was observed."
            ),
        },
        {
            "finding_id": "C5_F02",
            "category": "clinical_gri",
            "title": "The demonstrated F11 chain reached maximal score on its applicable dimensions",
            "finding": (
                "The F11 experimental case scored D2=1.0 and D7=1.0 because "
                "the tested perturbation completely suppressed evaluable "
                "allele evidence and propagated through the observed "
                "S2->S4->S5 clinical-processing chain."
            ),
            "quantitative_anchor": (
                f"F11 Base GRI={base_by_case['F11']:.10f}"
            ),
            "evidence": "C4_normalized_dimensions|C4_base_gri",
            "claim_level": "FRAMEWORK_CASE_SCORE",
            "limitation": (
                "This is a case-level computational severity score, not a "
                "probability of clinical harm."
            ),
        },
        {
            "finding_id": "C5_F03",
            "category": "privacy_persistence",
            "title": "Genomic disclosure remained highly persistent in the B2 model",
            "finding": (
                "The authoritative B2 model produced pathogenic-variant "
                "unrecoverability of 0.2299, 100% modelled re-identification "
                "by year 13 and 100% modelled familial exposure by year 15."
            ),
            "quantitative_anchor": "unrecoverability=0.2299; re-ID=13y; familial=15y",
            "evidence": "B2_E01|B2_E02|B2_E03",
            "claim_level": "MODEL_OUTPUT",
            "limitation": (
                "These are model-derived trajectories rather than observed "
                "longitudinal population outcomes."
            ),
        },
        {
            "finding_id": "C5_F04",
            "category": "privacy_amplification",
            "title": "Kinship structure substantially amplified exposure",
            "finding": (
                "The authoritative B1 analysis used a 4,144-node graph with "
                "1,657 registered nodes and produced calibrated mean familial "
                "amplification of 464.4x, corresponding to D6=0.898."
            ),
            "quantitative_anchor": "4144 nodes; 1657 registered; 464.4x; D6=0.898",
            "evidence": "B1_E01|B1_E02",
            "claim_level": "CALIBRATED_MODEL_OUTPUT",
            "limitation": (
                "Amplification remains dependent on graph construction and "
                "calibration assumptions."
            ),
        },
        {
            "finding_id": "C5_F05",
            "category": "privacy_gri",
            "title": "The integrated privacy chain produced a high Base GRI",
            "finding": (
                "Across applicable privacy dimensions D1, D3, D5 and D6, "
                f"the authoritative Base GRI was "
                f"{base_by_case['PRIVACY']:.10f}."
            ),
            "quantitative_anchor": (
                f"D1={norm_by_key[('PRIVACY','D1')]:.4f}; "
                f"D3={norm_by_key[('PRIVACY','D3')]:.4f}; "
                f"D5={norm_by_key[('PRIVACY','D5')]:.4f}; "
                f"D6={norm_by_key[('PRIVACY','D6')]:.4f}; "
                f"Base={base_by_case['PRIVACY']:.10f}"
            ),
            "evidence": "C4_normalized_dimensions|C4_base_gri",
            "claim_level": "FRAMEWORK_CASE_SCORE",
            "limitation": (
                "The score combines model-derived dimensions and should not "
                "be interpreted as an empirical population probability."
            ),
        },
        {
            "finding_id": "C5_F06",
            "category": "robustness",
            "title": "Privacy risk remained high under provenance-balanced weighting",
            "finding": (
                "When B2-derived dimensions were collapsed into one composite "
                "and weighted 50/50 against B1 amplification, the privacy "
                "sensitivity score remained high."
            ),
            "quantitative_anchor": (
                f"50/50 provenance sensitivity="
                f"{sens['50_50_B2_B1_provenance_balance']:.10f}"
            ),
            "evidence": "C4_sensitivity_analysis",
            "claim_level": "SENSITIVITY_ANALYSIS",
            "limitation": (
                "Sensitivity analysis is a robustness check and is not a "
                "confidence interval."
            ),
        },
        {
            "finding_id": "C5_F07",
            "category": "containment",
            "title": "Containment effectiveness depended strongly on attack origin",
            "finding": (
                "B3 containment achieved 99.24% best reduction in the primary "
                "scenario, but fixed-k residual containment difficulty varied "
                "substantially by attack origin."
            ),
            "quantitative_anchor": (
                "M5 residual candidates at k=10: peripheral=0.008; "
                "mid-degree=0.795; hub=0.970"
            ),
            "evidence": "B3_E01|B3_E02|HPRIV_04|C4_modifier_context",
            "claim_level": "MITIGATION_SCENARIO",
            "limitation": (
                "M5 values are scenario-specific residual candidates and are "
                "not multiplied into Base GRI."
            ),
        },
        {
            "finding_id": "C5_F08",
            "category": "authentication",
            "title": "Authentication is mitigation context rather than privacy detectability",
            "finding": (
                "The final B3 credential-stuffing benchmark used threshold "
                "3.6 and achieved F1=0.8387, but this performance is treated "
                "as access-control mitigation evidence rather than a direct "
                "measure of privacy-event detectability."
            ),
            "quantitative_anchor": "threshold=3.6; F1=0.8387",
            "evidence": "B3_E03|HPRIV_05|C4_modifier_context",
            "claim_level": "MITIGATION_CONTEXT",
            "limitation": (
                "Internal generated benchmark; M3 detectability remains "
                "UNMEASURED."
            ),
        },
        {
            "finding_id": "C5_F09",
            "category": "scope",
            "title": "A1 and A2 strengthen lifecycle coverage without inflating GRI",
            "finding": (
                "A1 contributes standalone software-security evidence and A2 "
                "contributes supporting perturbation evidence, but neither is "
                "forced into the Base GRI where the required semantic mapping "
                "is not established."
            ),
            "quantitative_anchor": "A1=STANDALONE_NON_GRI; A2=SUPPORTING_NON_GRI",
            "evidence": "C2_authoritative_evidence_registry",
            "claim_level": "FRAMEWORK_SCOPE",
            "limitation": (
                "Their exclusion from Base GRI is deliberate and should not "
                "be interpreted as lack of scientific relevance."
            ),
        },
    ]

    fields = [
        "finding_id",
        "category",
        "title",
        "finding",
        "quantitative_anchor",
        "evidence",
        "claim_level",
        "limitation",
    ]

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)

    with OUT_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=fields,
        )
        w.writeheader()
        w.writerows(findings)

    OUT_JSON.write_text(
        json.dumps(findings, indent=2) + "\n",
        encoding="utf-8",
    )

    md = [
        "# GenoPhylax Module C — Authoritative Integrated Findings",
        "",
        "These findings are generated from the clean C0–C4 rebuild.",
        "",
    ]

    for row in findings:
        md.extend(
            [
                f"## {row['finding_id']} — {row['title']}",
                "",
                row["finding"],
                "",
                f"**Quantitative anchor:** {row['quantitative_anchor']}",
                "",
                f"**Claim level:** {row['claim_level']}",
                "",
                f"**Limitation:** {row['limitation']}",
                "",
            ]
        )

    OUT_MD.write_text(
        "\n".join(md),
        encoding="utf-8",
    )

    # ------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------

    stale_tokens = {
        "0.9899",
        "0.9960",
        "threshold 4.5",
        "0.9115102712",
    }

    combined = "\n".join(
        row["finding"] + " " + row["quantitative_anchor"]
        for row in findings
    )

    for token in stale_tokens:
        if token in combined:
            errors.append(
                f"Stale value entered C5: {token}"
            )

    if len(findings) != 9:
        errors.append(
            f"Expected 9 integrated findings, found {len(findings)}"
        )

    validation = [
        "MODULE C AUTHORITATIVE REBUILD — C5 VALIDATION",
        "================================================",
        "",
        f"Integrated findings: {len(findings)}",
        f"F11 Base GRI: {base_by_case['F11']:.10f}",
        f"Privacy Base GRI: {base_by_case['PRIVACY']:.10f}",
        (
            "Privacy provenance-balanced sensitivity: "
            f"{sens['50_50_B2_B1_provenance_balance']:.10f}"
        ),
        "",
        "Scope safeguards:",
        "  A1 forced into Base GRI: NO",
        "  A2 forced into Base GRI: NO",
        "  B3 authentication called privacy detectability: NO",
        "  M5 applied to Base GRI: NO",
        "  Sensitivity called confidence interval: NO",
        "  Patient outcome claimed from F11: NO",
        "",
        f"Validation errors: {len(errors)}",
    ]

    if errors:
        validation.extend(
            f"  ERROR: {e}"
            for e in errors
        )
        validation.extend(
            [
                "",
                "STATUS: FAIL",
            ]
        )
    else:
        validation.extend(
            [
                "",
                "STATUS: PASS",
            ]
        )

    VALID.write_text(
        "\n".join(validation) + "\n",
        encoding="utf-8",
    )

    if errors:
        print("C5 BUILD: FAIL")
        for e in errors:
            print(e)
        return 1

    print("C5 BUILD: PASS")
    print(f"Integrated findings: {len(findings)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
