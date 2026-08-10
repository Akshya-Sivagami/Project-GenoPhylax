#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ROOT = REPO / "experiments/C_lifecycle_integration/authoritative_rebuild"

MANIFEST = ROOT / "inputs/C0_authoritative_sources.tsv"
OUT_TSV = ROOT / "c2_evidence/C2_authoritative_evidence_registry.tsv"
OUT_JSON = ROOT / "c2_evidence/C2_authoritative_evidence_registry.json"
OUT_MD = ROOT / "c2_evidence/C2_authoritative_evidence_registry.md"
VALIDATION = ROOT / "validation/C2_authoritative_evidence_validation.txt"


def load_manifest():
    with MANIFEST.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    by_key = {
        (row["module"], row["role"]): row
        for row in rows
    }

    return rows, by_key


def require_source(by_key, module, role):
    key = (module, role)

    if key not in by_key:
        raise KeyError(
            f"Missing locked C0 source for {module}/{role}"
        )

    return by_key[key]["source_file"]


def evidence_rows(by_key):
    return [
        # --------------------------------------------------
        # A1 — standalone memory-safety evidence
        # --------------------------------------------------
        {
            "evidence_id": "A1_E01",
            "module": "A1",
            "chain": "STANDALONE",
            "stage_ids": "S3|S10",
            "evidence_tier": "E2",
            "role": "STANDALONE_NON_GRI",
            "asset": "BWA alignment software",
            "finding": (
                "Canonical sanitized BWA fuzzing campaign executed "
                "963339 test cases over approximately 23120 seconds "
                "with 15.44 percent bitmap coverage and 521 saved "
                "crash artifacts."
            ),
            "numeric_value": "963339",
            "unit": "executions",
            "source_file": require_source(
                by_key, "A1", "campaign"
            ),
            "claim_scope": "memory-safety fuzzing campaign",
            "limitations": (
                "Standalone software-security evidence; excluded from "
                "GRI computation."
            ),
        },
        {
            "evidence_id": "A1_E02",
            "module": "A1",
            "chain": "STANDALONE",
            "stage_ids": "S3|S10",
            "evidence_tier": "E2",
            "role": "STANDALONE_NON_GRI",
            "asset": "BWA alignment software",
            "finding": (
                "Two source-level out-of-bounds read findings were "
                "identified in ksw_extend2 and mem_aln2sam."
            ),
            "numeric_value": "2",
            "unit": "source-level findings",
            "source_file": require_source(
                by_key, "A1", "findings"
            ),
            "claim_scope": "memory-safety findings",
            "limitations": (
                "No claim of universal exploitability or clinical "
                "outcome."
            ),
        },

        # --------------------------------------------------
        # A2 — supporting perturbation evidence
        # --------------------------------------------------
        {
            "evidence_id": "A2_E01",
            "module": "A2",
            "chain": "SUPPORTING",
            "stage_ids": "S1|S2|S3",
            "evidence_tier": "E1",
            "role": "SUPPORTING_NON_GRI",
            "asset": "Nanopore raw-signal/basecalling pipeline",
            "finding": (
                "Controlled Gaussian perturbation produced measurable "
                "basecalling degradation while preserving substantial "
                "mapping in the tested HG002/Dorado setting."
            ),
            "numeric_value": "",
            "unit": "",
            "source_file": require_source(
                by_key, "A2", "gaussian_dose_response"
            ),
            "claim_scope": "controlled perturbation response",
            "limitations": (
                "Supporting evidence only; not used directly in Base GRI."
            ),
        },
        {
            "evidence_id": "A2_E02",
            "module": "A2",
            "chain": "SUPPORTING",
            "stage_ids": "S1|S2|S4",
            "evidence_tier": "E2",
            "role": "SUPPORTING_NON_GRI",
            "asset": "Targeted genomic perturbation specificity",
            "finding": (
                "Cross-locus W0 replication retained the ALT state in "
                "10 of 10 parents at each of two loci, with 0 of 20 "
                "combined target-state changes."
            ),
            "numeric_value": "0",
            "unit": "state changes out of 20",
            "source_file": require_source(
                by_key, "A2", "cross_locus_W0"
            ),
            "claim_scope": "cross-locus specificity control",
            "limitations": (
                "Two-locus supporting replication; not direct GRI input."
            ),
        },

        # --------------------------------------------------
        # A3 — F11 clinical chain
        # --------------------------------------------------
        {
            "evidence_id": "A3_E01",
            "module": "A3",
            "chain": "F11",
            "stage_ids": "S2|S4",
            "evidence_tier": "E3",
            "role": "GRI_ELIGIBLE",
            "asset": "F11 pathogenic locus evidence",
            "finding": (
                "Clean re-basecalling retained ALT support in 14 of 14 "
                "evaluable parent reads at the F11 pathogenic locus."
            ),
            "numeric_value": "14/14",
            "unit": "ALT-supporting evaluable parents",
            "source_file": require_source(
                by_key, "A3", "final_summary"
            ),
            "claim_scope": "clean F11 replay",
            "limitations": (
                "Single HG002 individual, one pathogenic F11 locus, "
                "one basecaller configuration."
            ),
        },
        {
            "evidence_id": "A3_E02",
            "module": "A3",
            "chain": "F11",
            "stage_ids": "S2|S4",
            "evidence_tier": "E4",
            "role": "GRI_ELIGIBLE",
            "asset": "F11 pathogenic locus evidence",
            "finding": (
                "Targeted PM2 perturbation eliminated on-target ALT "
                "support in the controlled F11 experiment."
            ),
            "numeric_value": "0/14",
            "unit": "ALT-supporting evaluable parents",
            "source_file": require_source(
                by_key, "A3", "final_summary"
            ),
            "claim_scope": "targeted F11 perturbation replay",
            "limitations": (
                "Controlled experimental case; no patient outcome claim."
            ),
        },
        {
            "evidence_id": "A3_E03",
            "module": "A3",
            "chain": "F11",
            "stage_ids": "S4|S5",
            "evidence_tier": "E4",
            "role": "GRI_ELIGIBLE",
            "asset": "F11 downstream variant call",
            "finding": (
                "The targeted PM2 condition produced downstream loss "
                "of the F11 variant call in the controlled clinical "
                "consequence workflow."
            ),
            "numeric_value": "",
            "unit": "",
            "source_file": require_source(
                by_key, "A3", "variant_calling"
            ),
            "claim_scope": "controlled variant-call consequence",
            "limitations": (
                "Computational clinical consequence, not observed "
                "patient harm."
            ),
        },
        {
            "evidence_id": "A3_E04",
            "module": "A3",
            "chain": "F11",
            "stage_ids": "S2|S4|S5",
            "evidence_tier": "E4",
            "role": "GRI_ELIGIBLE",
            "asset": "F11 off-target control",
            "finding": (
                "Matched off-target PM2 sham preserved the F11 variant "
                "evidence and heterozygous call, supporting localization "
                "of the on-target effect."
            ),
            "numeric_value": "14/14",
            "unit": "ALT-supporting evaluable parents",
            "source_file": require_source(
                by_key, "A3", "off_target_control"
            ),
            "claim_scope": "matched off-target control",
            "limitations": (
                "Single controlled locus-specific sham experiment."
            ),
        },

        # --------------------------------------------------
        # B1 — privacy amplification
        # --------------------------------------------------
        {
            "evidence_id": "B1_E01",
            "module": "B1",
            "chain": "PRIVACY",
            "stage_ids": "S7|S8",
            "evidence_tier": "E4",
            "role": "GRI_ELIGIBLE",
            "asset": "Kinship graph",
            "finding": (
                "At 40 percent registration, the authoritative B1 graph "
                "contained 4144 nodes and 1657 registered nodes."
            ),
            "numeric_value": "4144",
            "unit": "graph nodes",
            "source_file": require_source(
                by_key, "B1", "authoritative_final"
            ),
            "claim_scope": "kinship graph simulation",
            "limitations": (
                "Synthetic/modelled graph setting; not a population-wide "
                "empirical estimate."
            ),
        },
        {
            "evidence_id": "B1_E02",
            "module": "B1",
            "chain": "PRIVACY",
            "stage_ids": "S7|S8",
            "evidence_tier": "E4",
            "role": "GRI_ELIGIBLE",
            "asset": "Kinship exposure amplification",
            "finding": (
                "Calibrated mean familial amplification was 464.4x "
                "against the 492.86x external target used by the model."
            ),
            "numeric_value": "464.4",
            "unit": "amplification multiplier",
            "source_file": require_source(
                by_key, "B1", "authoritative_final"
            ),
            "claim_scope": "calibrated amplification model",
            "limitations": (
                "Calibration remains model-dependent."
            ),
        },

        # --------------------------------------------------
        # B2 — persistence / disclosure
        # --------------------------------------------------
        {
            "evidence_id": "B2_E01",
            "module": "B2",
            "chain": "PRIVACY",
            "stage_ids": "S6|S7|S8",
            "evidence_tier": "E4",
            "role": "GRI_ELIGIBLE",
            "asset": "Genomic data vault",
            "finding": (
                "Clinician pathogenic-variant disclosure produced "
                "authoritative unrecoverability of 0.2299."
            ),
            "numeric_value": "0.2299",
            "unit": "unrecoverability",
            "source_file": require_source(
                by_key, "B2", "authoritative_final"
            ),
            "claim_scope": "vault disclosure model",
            "limitations": (
                "Model-derived unrecoverability; depends on configured "
                "vault assumptions."
            ),
        },
        {
            "evidence_id": "B2_E02",
            "module": "B2",
            "chain": "PRIVACY",
            "stage_ids": "S6|S7|S8",
            "evidence_tier": "E4",
            "role": "GRI_ELIGIBLE",
            "asset": "Long-term genomic privacy",
            "finding": (
                "Modelled re-identification saturation reached 100 "
                "percent by year 13."
            ),
            "numeric_value": "13",
            "unit": "years",
            "source_file": require_source(
                by_key, "B2", "authoritative_final"
            ),
            "claim_scope": "lifetime re-identification model",
            "limitations": (
                "Modelled temporal trajectory, not longitudinal cohort "
                "observation."
            ),
        },
        {
            "evidence_id": "B2_E03",
            "module": "B2",
            "chain": "PRIVACY",
            "stage_ids": "S7|S8",
            "evidence_tier": "E4",
            "role": "GRI_ELIGIBLE",
            "asset": "Familial genomic privacy",
            "finding": (
                "Modelled familial saturation reached 100 percent by "
                "year 15."
            ),
            "numeric_value": "15",
            "unit": "years",
            "source_file": require_source(
                by_key, "B2", "authoritative_final"
            ),
            "claim_scope": "familial lifetime-risk model",
            "limitations": (
                "Model-derived trajectory."
            ),
        },

        # --------------------------------------------------
        # B3 — containment / authentication
        # --------------------------------------------------
        {
            "evidence_id": "B3_E01",
            "module": "B3",
            "chain": "PRIVACY",
            "stage_ids": "S8|S10",
            "evidence_tier": "E4",
            "role": "MITIGATION_CONTEXT",
            "asset": "Kinship graph containment",
            "finding": (
                "Primary containment reduced exposure from 786 baseline "
                "to 560 at k=5 and 6 at k=10; exact best containment "
                "reduction was 99.24 percent."
            ),
            "numeric_value": "0.9924",
            "unit": "containment reduction proportion",
            "source_file": require_source(
                by_key, "B3", "authoritative_final"
            ),
            "claim_scope": "containment simulation",
            "limitations": (
                "Effectiveness depends strongly on graph topology and "
                "attack origin."
            ),
        },
        {
            "evidence_id": "B3_E02",
            "module": "B3",
            "chain": "PRIVACY",
            "stage_ids": "S8|S10",
            "evidence_tier": "E4",
            "role": "MITIGATION_CONTEXT",
            "asset": "Attack-origin containment",
            "finding": (
                "Minimum tested containment budget reaching at least "
                "99 percent reduction was k=5 for peripheral origins "
                "and k=20 for both mid-degree and hub origins."
            ),
            "numeric_value": "5|20|20",
            "unit": "minimum tested k for >=99 percent reduction",
            "source_file": require_source(
                by_key, "B3", "authoritative_final"
            ),
            "claim_scope": "attack-origin containment simulation",
            "limitations": (
                "Applies to the tested B3 attack-origin experiment; "
                "not a universal graph-theoretic requirement."
            ),
        },
        {
            "evidence_id": "B3_E03",
            "module": "B3",
            "chain": "PRIVACY",
            "stage_ids": "S6|S10",
            "evidence_tier": "E4",
            "role": "MITIGATION_CONTEXT",
            "asset": "Authentication layer",
            "finding": (
                "Final credential-stuffing classifier used threshold "
                "3.6 with precision 0.9070, recall 0.7800, F1 0.8387 "
                "and accuracy 0.9400."
            ),
            "numeric_value": "0.8387",
            "unit": "F1 score",
            "source_file": require_source(
                by_key, "B3", "authoritative_final"
            ),
            "claim_scope": "authentication benchmark",
            "limitations": (
                "Generated internal benchmark; authentication performance "
                "is mitigation context, not direct privacy-event "
                "detectability."
            ),
        },
    ]


def main():
    manifest_rows, by_key = load_manifest()

    allowed_sources = {
        row["source_file"]
        for row in manifest_rows
    }

    rows = evidence_rows(by_key)

    errors = []

    ids = [row["evidence_id"] for row in rows]

    if len(ids) != len(set(ids)):
        errors.append("Duplicate evidence IDs")

    for row in rows:
        if row["source_file"] not in allowed_sources:
            errors.append(
                f"{row['evidence_id']} source not locked by C0: "
                f"{row['source_file']}"
            )

        if row["module"] == "A1" and row["role"] != "STANDALONE_NON_GRI":
            errors.append(
                f"{row['evidence_id']} violates A1 non-GRI policy"
            )

        if row["module"] == "A2" and row["role"] == "GRI_ELIGIBLE":
            errors.append(
                f"{row['evidence_id']} incorrectly makes A2 direct GRI input"
            )

        if row["module"] == "B3" and row["role"] != "MITIGATION_CONTEXT":
            errors.append(
                f"{row['evidence_id']} incorrectly treats B3 as direct Base GRI input"
            )

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "evidence_id",
        "module",
        "chain",
        "stage_ids",
        "evidence_tier",
        "role",
        "asset",
        "finding",
        "numeric_value",
        "unit",
        "source_file",
        "claim_scope",
        "limitations",
    ]

    with OUT_TSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(rows)

    OUT_JSON.write_text(
        json.dumps(rows, indent=2) + "\n",
        encoding="utf-8",
    )

    md = [
        "# C2 Authoritative Evidence Registry",
        "",
        "This registry is generated only from sources locked in C0.",
        "",
        "| ID | Module | Chain | Tier | Role | Finding |",
        "|---|---|---|---|---|---|",
    ]

    for row in rows:
        md.append(
            f"| {row['evidence_id']} | {row['module']} | "
            f"{row['chain']} | {row['evidence_tier']} | "
            f"{row['role']} | {row['finding']} |"
        )

    OUT_MD.write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    chain_counts = {}

    for row in rows:
        chain_counts[row["chain"]] = (
            chain_counts.get(row["chain"], 0) + 1
        )

    gri_eligible = sum(
        1
        for row in rows
        if row["role"] == "GRI_ELIGIBLE"
    )

    validation = [
        "MODULE C AUTHORITATIVE REBUILD — C2 VALIDATION",
        "================================================",
        "",
        f"Evidence rows: {len(rows)}",
        f"Unique evidence IDs: {len(set(ids))}",
        f"GRI-eligible rows: {gri_eligible}",
        f"A1 standalone rows: {chain_counts.get('STANDALONE', 0)}",
        f"A2 supporting rows: {chain_counts.get('SUPPORTING', 0)}",
        f"F11 chain rows: {chain_counts.get('F11', 0)}",
        f"Privacy chain rows: {chain_counts.get('PRIVACY', 0)}",
        "",
        "Policies:",
        "  A1 direct GRI use: NO",
        "  A2 direct Base GRI use: NO",
        "  B3 authentication as privacy detectability: NO",
        "  B3 role: MITIGATION_CONTEXT",
        "  Evidence tiers as numerical GRI weights: NO",
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
        print("C2 BUILD: FAIL")
        for error in errors:
            print(error)
        return 1

    print("C2 BUILD: PASS")
    print(f"Evidence rows: {len(rows)}")
    print(f"GRI-eligible rows: {gri_eligible}")
    print(
        "Chains: "
        + ", ".join(
            f"{k}={v}"
            for k, v in sorted(chain_counts.items())
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
