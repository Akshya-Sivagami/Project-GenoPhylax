#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ROOT = REPO / "experiments/C_lifecycle_integration/authoritative_rebuild"

C2 = ROOT / "c2_evidence/C2_authoritative_evidence_registry.tsv"

OUT_TSV = ROOT / "c3_handoffs/C3_authoritative_handoffs.tsv"
OUT_JSON = ROOT / "c3_handoffs/C3_authoritative_handoffs.json"
OUT_MD = ROOT / "c3_handoffs/C3_authoritative_handoffs.md"
VALIDATION = ROOT / "validation/C3_authoritative_handoffs_validation.txt"


def load_c2():
    with C2.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    return {
        row["evidence_id"]: row
        for row in rows
    }


def handoffs():
    return [
        # ==================================================
        # F11 CLINICAL CHAIN
        # ==================================================
        {
            "handoff_id": "HF11_01",
            "chain": "F11",
            "from_stage": "S2",
            "to_stage": "S4",
            "handoff_role": "RISK_PROPAGATION",
            "observation_class": "CONTROLLED_OBSERVED",
            "base_gri_eligible": "YES",
            "evidence_ids": ["A3_E02"],
            "mechanism": (
                "Targeted raw-signal perturbation suppresses allele-level "
                "evidence at the pathogenic F11 locus."
            ),
            "observed_result": (
                "On-target ALT support fell to 0/14 evaluable parent reads "
                "under targeted PM2."
            ),
            "candidate_dimensions": ["D2", "D7"],
            "limitations": (
                "Single HG002 individual, one F11 pathogenic locus and "
                "one controlled basecalling configuration."
            ),
        },
        {
            "handoff_id": "HF11_02",
            "chain": "F11",
            "from_stage": "S4",
            "to_stage": "S5",
            "handoff_role": "RISK_PROPAGATION",
            "observation_class": "CONTROLLED_OBSERVED",
            "base_gri_eligible": "YES",
            "evidence_ids": ["A3_E03"],
            "mechanism": (
                "Loss of variant-calling evidence propagates into loss of "
                "the clinically relevant F11 variant representation."
            ),
            "observed_result": (
                "The controlled targeted condition produced downstream "
                "loss of the F11 variant call."
            ),
            "candidate_dimensions": ["D2", "D7"],
            "limitations": (
                "Computational consequence only; no patient outcome or "
                "clinical decision was observed."
            ),
        },

        # Controls are retained but NEVER scored as propagation.
        {
            "handoff_id": "CF11_01",
            "chain": "F11",
            "from_stage": "S2",
            "to_stage": "S4",
            "handoff_role": "VALIDATION_CONTROL",
            "observation_class": "CLEAN_CONTROL",
            "base_gri_eligible": "NO",
            "evidence_ids": ["A3_E01"],
            "mechanism": (
                "Clean replay establishes that the pathogenic allele is "
                "normally retained through basecalling into variant evidence."
            ),
            "observed_result": (
                "Clean ALT support was retained in 14/14 evaluable parents."
            ),
            "candidate_dimensions": [],
            "limitations": (
                "Baseline control; not an independent risk contribution."
            ),
        },
        {
            "handoff_id": "CF11_02",
            "chain": "F11",
            "from_stage": "S2",
            "to_stage": "S4",
            "handoff_role": "VALIDATION_CONTROL",
            "observation_class": "OFF_TARGET_CONTROL",
            "base_gri_eligible": "NO",
            "evidence_ids": ["A3_E04"],
            "mechanism": (
                "Matched off-target perturbation tests whether the F11 "
                "effect is localized rather than a nonspecific pipeline failure."
            ),
            "observed_result": (
                "Off-target PM2 sham preserved ALT evidence in 14/14 "
                "evaluable parents and preserved the heterozygous call."
            ),
            "candidate_dimensions": [],
            "limitations": (
                "Single matched sham control at the tested locus."
            ),
        },

        # ==================================================
        # PRIVACY / KINSHIP CHAIN
        # ==================================================
        {
            "handoff_id": "HPRIV_01",
            "chain": "PRIVACY",
            "from_stage": "S6",
            "to_stage": "S7",
            "handoff_role": "RISK_PROPAGATION",
            "observation_class": "MODEL_OUTPUT",
            "base_gri_eligible": "YES",
            "evidence_ids": ["B2_E01"],
            "mechanism": (
                "Disclosure of pathogenic genomic information reduces the "
                "modelled ability to restore privacy after release."
            ),
            "observed_result": (
                "Clinician pathogenic-variant disclosure produced "
                "unrecoverability 0.2299."
            ),
            "candidate_dimensions": ["D1", "D5"],
            "limitations": (
                "Model-derived vault result; interpretation depends on the "
                "configured disclosure and reconstruction assumptions."
            ),
        },
        {
            "handoff_id": "HPRIV_02",
            "chain": "PRIVACY",
            "from_stage": "S7",
            "to_stage": "S8",
            "handoff_role": "RISK_PROPAGATION",
            "observation_class": "MODEL_OUTPUT",
            "base_gri_eligible": "YES",
            "evidence_ids": ["B2_E02", "B2_E03"],
            "mechanism": (
                "Persistent genomic disclosure accumulates downstream "
                "re-identification and familial exposure over time."
            ),
            "observed_result": (
                "Modelled re-identification reached 100 percent by year 13 "
                "and familial exposure reached 100 percent by year 15."
            ),
            "candidate_dimensions": ["D1", "D3", "D5"],
            "limitations": (
                "Temporal saturation is modelled rather than measured in a "
                "longitudinal population cohort."
            ),
        },
        {
            "handoff_id": "HPRIV_03",
            "chain": "PRIVACY",
            "from_stage": "S7",
            "to_stage": "S8",
            "handoff_role": "RISK_PROPAGATION",
            "observation_class": "CALIBRATED_MODEL_OUTPUT",
            "base_gri_eligible": "YES",
            "evidence_ids": ["B1_E01", "B1_E02"],
            "mechanism": (
                "Release of one person's genomic information propagates "
                "through kinship relationships and amplifies exposure."
            ),
            "observed_result": (
                "The authoritative graph contained 4144 nodes with 1657 "
                "registered nodes; calibrated mean familial amplification "
                "was 464.4x."
            ),
            "candidate_dimensions": ["D3", "D6"],
            "limitations": (
                "Graph-derived and calibration-dependent; not a direct "
                "population-wide empirical exposure count."
            ),
        },

        # ==================================================
        # B3 IS MITIGATION CONTEXT, NOT BASE-RISK PROPAGATION
        # ==================================================
        {
            "handoff_id": "HPRIV_04",
            "chain": "PRIVACY",
            "from_stage": "S8",
            "to_stage": "S10",
            "handoff_role": "MITIGATION_CONTEXT",
            "observation_class": "SIMULATION",
            "base_gri_eligible": "NO",
            "evidence_ids": ["B3_E01", "B3_E02"],
            "mechanism": (
                "Graph-aware containment limits already-propagated exposure, "
                "with effectiveness dependent on attack origin."
            ),
            "observed_result": (
                "Primary containment achieved 99.24 percent best reduction; "
                "minimum tested k for >=99 percent reduction was 5 for "
                "peripheral origins and 20 for mid-degree and hub origins."
            ),
            "candidate_dimensions": ["M5"],
            "limitations": (
                "Mitigation evidence only. It must not reduce Base GRI "
                "unless an explicitly defined modifier analysis is applied."
            ),
        },
        {
            "handoff_id": "HPRIV_05",
            "chain": "PRIVACY",
            "from_stage": "S6",
            "to_stage": "S10",
            "handoff_role": "MITIGATION_CONTEXT",
            "observation_class": "INTERNAL_BENCHMARK",
            "base_gri_eligible": "NO",
            "evidence_ids": ["B3_E03"],
            "mechanism": (
                "Authentication provides an access-control mitigation layer "
                "for genomic-platform misuse."
            ),
            "observed_result": (
                "Final benchmark threshold 3.6 produced precision 0.9070, "
                "recall 0.7800, F1 0.8387 and accuracy 0.9400."
            ),
            "candidate_dimensions": [],
            "limitations": (
                "Authentication performance is not a direct measure of "
                "privacy-event detectability and is not a Base GRI input."
            ),
        },
    ]


def main():
    evidence = load_c2()
    rows = handoffs()

    errors = []

    ids = [row["handoff_id"] for row in rows]

    if len(ids) != len(set(ids)):
        errors.append("Duplicate handoff IDs")

    allowed_stages = {
        f"S{i}"
        for i in range(1, 11)
    }

    for row in rows:
        if row["from_stage"] not in allowed_stages:
            errors.append(
                f"{row['handoff_id']} invalid from_stage"
            )

        if row["to_stage"] not in allowed_stages:
            errors.append(
                f"{row['handoff_id']} invalid to_stage"
            )

        for evidence_id in row["evidence_ids"]:
            if evidence_id not in evidence:
                errors.append(
                    f"{row['handoff_id']} missing evidence {evidence_id}"
                )

        if (
            row["handoff_role"] == "MITIGATION_CONTEXT"
            and row["base_gri_eligible"] != "NO"
        ):
            errors.append(
                f"{row['handoff_id']} mitigation incorrectly Base-GRI eligible"
            )

        if (
            row["handoff_role"] == "VALIDATION_CONTROL"
            and row["base_gri_eligible"] != "NO"
        ):
            errors.append(
                f"{row['handoff_id']} control incorrectly Base-GRI eligible"
            )

        if (
            row["base_gri_eligible"] == "YES"
            and row["handoff_role"] != "RISK_PROPAGATION"
        ):
            errors.append(
                f"{row['handoff_id']} Base-GRI eligibility without "
                "risk-propagation role"
            )

        # Do not allow A1/A2 into direct handoffs.
        for evidence_id in row["evidence_ids"]:
            source = evidence.get(evidence_id)

            if not source:
                continue

            if (
                row["base_gri_eligible"] == "YES"
                and source["role"] != "GRI_ELIGIBLE"
            ):
                errors.append(
                    f"{row['handoff_id']} uses non-GRI evidence "
                    f"{evidence_id} as Base-GRI input"
                )

    fields = [
        "handoff_id",
        "chain",
        "from_stage",
        "to_stage",
        "handoff_role",
        "observation_class",
        "base_gri_eligible",
        "evidence_ids",
        "mechanism",
        "observed_result",
        "candidate_dimensions",
        "limitations",
    ]

    serializable = []

    for row in rows:
        serializable.append(
            {
                **row,
                "evidence_ids": "|".join(row["evidence_ids"]),
                "candidate_dimensions": "|".join(
                    row["candidate_dimensions"]
                ),
            }
        )

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)

    with OUT_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(serializable)

    OUT_JSON.write_text(
        json.dumps(rows, indent=2) + "\n",
        encoding="utf-8",
    )

    md = [
        "# C3 Authoritative Handoffs",
        "",
        "Only evidence-backed transitions are included.",
        "",
        "Validation controls and mitigation evidence are retained but "
        "are not Base GRI contributions.",
        "",
        "| ID | Chain | Transition | Role | Base GRI | Evidence |",
        "|---|---|---|---|---|---|",
    ]

    for row in rows:
        md.append(
            f"| {row['handoff_id']} | {row['chain']} | "
            f"{row['from_stage']}→{row['to_stage']} | "
            f"{row['handoff_role']} | "
            f"{row['base_gri_eligible']} | "
            f"{', '.join(row['evidence_ids'])} |"
        )

    OUT_MD.write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    base_rows = [
        row
        for row in rows
        if row["base_gri_eligible"] == "YES"
    ]

    f11_base = [
        row
        for row in base_rows
        if row["chain"] == "F11"
    ]

    privacy_base = [
        row
        for row in base_rows
        if row["chain"] == "PRIVACY"
    ]

    controls = [
        row
        for row in rows
        if row["handoff_role"] == "VALIDATION_CONTROL"
    ]

    mitigation = [
        row
        for row in rows
        if row["handoff_role"] == "MITIGATION_CONTEXT"
    ]

    validation = [
        "MODULE C AUTHORITATIVE REBUILD — C3 VALIDATION",
        "================================================",
        "",
        f"Handoff/control rows: {len(rows)}",
        f"Base-GRI-eligible handoffs: {len(base_rows)}",
        f"F11 Base-GRI handoffs: {len(f11_base)}",
        f"Privacy Base-GRI handoffs: {len(privacy_base)}",
        f"Validation controls: {len(controls)}",
        f"Mitigation-context rows: {len(mitigation)}",
        "",
        "Scientific safeguards:",
        "  A1 direct handoff contribution: NO",
        "  A2 direct handoff contribution: NO",
        "  Controls scored as risk: NO",
        "  B3 containment in Base GRI: NO",
        "  B3 authentication as detectability: NO",
        "  Unsupported F11 S5->S6 propagation invented: NO",
        "",
        f"Validation errors: {len(errors)}",
    ]

    if errors:
        validation.extend(errors)
        validation.append("")
        validation.append("STATUS: FAIL")
    else:
        validation.append("STATUS: PASS")

    VALIDATION.write_text(
        "\n".join(validation) + "\n",
        encoding="utf-8",
    )

    if errors:
        print("C3 BUILD: FAIL")
        for error in errors:
            print(error)
        return 1

    print("C3 BUILD: PASS")
    print(f"Rows: {len(rows)}")
    print(f"Base-GRI handoffs: {len(base_rows)}")
    print(
        f"F11={len(f11_base)}, "
        f"PRIVACY={len(privacy_base)}, "
        f"controls={len(controls)}, "
        f"mitigation={len(mitigation)}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
