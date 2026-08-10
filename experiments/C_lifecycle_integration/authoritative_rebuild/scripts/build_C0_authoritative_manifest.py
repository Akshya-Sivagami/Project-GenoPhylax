#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
OUT_ROOT = REPO / "experiments/C_lifecycle_integration/authoritative_rebuild"

MANIFEST = OUT_ROOT / "inputs/C0_authoritative_sources.tsv"
VALIDATION = OUT_ROOT / "validation/C0_authoritative_sources_validation.txt"

# ------------------------------------------------------------------
# ONLY upstream A/B evidence is allowed here.
# Old Module C numerical outputs are deliberately prohibited.
# ------------------------------------------------------------------

SOURCES = [
    # -------------------------
    # A1 — BWA memory audit
    # -------------------------
    (
        "A1",
        "campaign",
        "experiments/A1_memory_audit/provenance/A1_campaign_reconstruction.tsv",
        "Canonical sanitized BWA fuzzing campaign provenance",
    ),
    (
        "A1",
        "findings",
        "experiments/A1_memory_audit/provenance/A1_finding_summary.tsv",
        "Locked source-level BWA memory-safety findings",
    ),
    (
        "A1",
        "limitations",
        "experiments/A1_memory_audit/provenance/A1_claims_and_limitations.md",
        "A1 publication claim boundaries",
    ),
    (
        "A1",
        "identity",
        "experiments/A1_memory_audit/provenance/A1_bwa_identity.tsv",
        "BWA version and target identity",
    ),
    (
        "A1",
        "validation",
        "experiments/A1_memory_audit/provenance/A1_campaign_attribution_validation.txt",
        "Canonical A1 campaign validation",
    ),

    # -------------------------
    # A2 — nanopore perturbation
    # -------------------------
    (
        "A2",
        "master_findings",
        "experiments/A2_adversarial_dna/basecalling/findings/master_A2_GPU/A2_GPU_master_findings.md",
        "Final consolidated A2 GPU findings",
    ),
    (
        "A2",
        "numerical_summary",
        "experiments/A2_adversarial_dna/basecalling/findings/master_A2_GPU/A2_GPU_numerical_summary.md",
        "Final A2 numerical summary",
    ),
    (
        "A2",
        "claims",
        "experiments/A2_adversarial_dna/basecalling/findings/master_A2_GPU/A2_GPU_claims_limitations_matrix.md",
        "A2 claims and limitations",
    ),
    (
        "A2",
        "gaussian_dose_response",
        "experiments/A2_adversarial_dna/basecalling/perturbations/metrics/hg002_100reads_gaussian_dose_response_summary.tsv",
        "Controlled Gaussian perturbation dose-response",
    ),
    (
        "A2",
        "cross_locus_W0",
        "experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/findings/experiment_E_final_cross_locus_findings.md",
        "Final cross-locus W0 specificity and replication evidence",
    ),

    # -------------------------
    # A3 — F11 clinical case
    # -------------------------
    (
        "A3",
        "final_summary",
        "experiments/A3_clinical_consequence_mapping/findings/A3_F11_final_numerical_summary.tsv",
        "Final F11 controlled targeted-signal numerical summary",
    ),
    (
        "A3",
        "claims",
        "experiments/A3_clinical_consequence_mapping/findings/A3_F11_claims_and_limitations.md",
        "F11 claims and limitations",
    ),
    (
        "A3",
        "findings",
        "experiments/A3_clinical_consequence_mapping/findings/A3_F11_targeted_signal_attack_findings.md",
        "Final F11 targeted-signal attack findings",
    ),
    (
        "A3",
        "variant_calling",
        "experiments/A3_clinical_consequence_mapping/results/F11_candidate/controlled_hybrid_variant_calling/F11_controlled_clinical_consequence_summary.tsv",
        "Controlled downstream F11 variant-call consequence",
    ),
    (
        "A3",
        "off_target_control",
        "experiments/A3_clinical_consequence_mapping/results/F11_candidate/PM2_off_target_sham/F11_PM2_off_target_sham_summary.tsv",
        "Matched off-target PM2 sham control",
    ),

    # -------------------------
    # B1/B2/B3 — FINAL AUDIT
    # -------------------------
    (
        "B1",
        "authoritative_final",
        "experiments/B_final_audit/B1_authoritative_final.tsv",
        "Locked final B1 values",
    ),
    (
        "B2",
        "authoritative_final",
        "experiments/B_final_audit/B2_authoritative_final.tsv",
        "Locked final B2 values",
    ),
    (
        "B3",
        "authoritative_final",
        "experiments/B_final_audit/B3_authoritative_final.tsv",
        "Locked final B3 values",
    ),
    (
        "B",
        "validation",
        "experiments/B_final_audit/B_authoritative_validation.txt",
        "Final B1/B2/B3 audit validation",
    ),

    # -------------------------
    # C1 architecture only
    # -------------------------
    (
        "C1",
        "lifecycle_schema",
        "experiments/C_lifecycle_integration/schema/C1_lifecycle_stages.json",
        "Previously validated S1-S10 lifecycle architecture; architecture only",
    ),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        text=True,
    ).strip()


def main() -> int:
    errors: list[str] = []
    rows: list[dict[str, str]] = []

    for module, role, relative, purpose in SOURCES:
        path = REPO / relative

        # Only the C1 schema itself may originate from Module C.
        if (
            relative.startswith("experiments/C_lifecycle_integration/")
            and role != "lifecycle_schema"
        ):
            errors.append(
                f"PROHIBITED OLD-C INPUT: {relative}"
            )

        if not path.exists():
            errors.append(f"MISSING: {relative}")
            continue

        if not path.is_file():
            errors.append(f"NOT_FILE: {relative}")
            continue

        rows.append(
            {
                "module": module,
                "role": role,
                "source_file": relative,
                "purpose": purpose,
                "size_bytes": str(path.stat().st_size),
                "sha256": sha256(path),
                "git_head_at_lock": git_head(),
            }
        )

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION.parent.mkdir(parents=True, exist_ok=True)

    with MANIFEST.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=[
                "module",
                "role",
                "source_file",
                "purpose",
                "size_bytes",
                "sha256",
                "git_head_at_lock",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    modules = sorted({row["module"] for row in rows})

    validation_lines = [
        "MODULE C AUTHORITATIVE REBUILD — C0 INPUT VALIDATION",
        "====================================================",
        "",
        f"Git HEAD: {git_head()}",
        f"Expected sources: {len(SOURCES)}",
        f"Resolved sources: {len(rows)}",
        f"Modules represented: {','.join(modules)}",
        "",
        "Architecture policy:",
        "  Old Module C numerical outputs: PROHIBITED",
        "  Existing C1 S1-S10 schema: ALLOWED",
        "  A/B authoritative upstream evidence: REQUIRED",
        "",
    ]

    if errors:
        validation_lines.append("Errors:")
        validation_lines.extend(f"  {e}" for e in errors)
        validation_lines.append("")
        validation_lines.append("STATUS: FAIL")
    else:
        validation_lines.extend(
            [
                "Missing sources: 0",
                "Prohibited old-C numerical inputs: 0",
                "",
                "STATUS: PASS",
            ]
        )

    VALIDATION.write_text(
        "\n".join(validation_lines) + "\n",
        encoding="utf-8",
    )

    if errors:
        print("C0 SOURCE LOCK: FAIL")
        for error in errors:
            print(error)
        return 1

    print("C0 SOURCE LOCK: PASS")
    print(f"Sources locked: {len(rows)}")
    print(f"Manifest: {MANIFEST.relative_to(REPO)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
