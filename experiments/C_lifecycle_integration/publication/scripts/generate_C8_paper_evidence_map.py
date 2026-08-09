#!/usr/bin/env python3

from pathlib import Path
import csv


ROOT = Path.cwd()

BASE = (
    ROOT
    / "experiments/C_lifecycle_integration/publication"
)

CLAIM_DIR = BASE / "claims"
DATA_DIR = BASE / "claim_data"
VALID_DIR = BASE / "validation"

for p in (CLAIM_DIR, DATA_DIR, VALID_DIR):
    p.mkdir(parents=True, exist_ok=True)


C2 = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "evidence_registry/C2_cross_module_evidence_registry.tsv"
)

C4_CASE = (
    ROOT
    / "experiments/C_lifecycle_integration/gri/"
      "C4_8_case_output_profile.tsv"
)

C6_MANIFEST = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "publication/figure_data/C6_figure_manifest.tsv"
)

C7_MANIFEST = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "publication/table_data/C7_table_manifest.tsv"
)

C5_FINDINGS = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "findings/C_master_findings.md"
)


def read_tsv(path):
    if not path.exists():
        raise RuntimeError(f"Missing required source: {path}")

    with path.open(
        newline="",
        encoding="utf-8",
    ) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path, rows, fields):
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_md_table(path, title, rows, fields, note=None):
    lines = [
        f"# {title}",
        "",
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]

    for row in rows:
        vals = []
        for field in fields:
            val = str(row.get(field, ""))
            val = val.replace("|", "\\|")
            vals.append(val)

        lines.append(
            "| " + " | ".join(vals) + " |"
        )

    if note:
        lines += [
            "",
            f"**Note:** {note}",
        ]

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


# ============================================================
# Source preflight
# ============================================================

c2_rows = read_tsv(C2)

if len(c2_rows) != 20:
    raise RuntimeError(
        f"Expected 20 C2 evidence rows; found {len(c2_rows)}"
    )

if "evidence_id" not in c2_rows[0]:
    raise RuntimeError(
        "C2 registry does not contain evidence_id"
    )

evidence = {
    r["evidence_id"]: r
    for r in c2_rows
}

expected_ids = {
    "A1_E01",
    "A1_E02",
    "A1_E03",
    "A1_E04",
    "A2_E01",
    "A2_E02",
    "A2_E03",
    "A2_E04",
    "A3_E01",
    "A3_E02",
    "A3_E03",
    "A3_E04",
    "B1_E01",
    "B1_E02",
    "B2_E01",
    "B2_E02",
    "B2_E03",
    "B3_E01",
    "B3_E02",
    "B3_E03",
}

missing_ids = expected_ids - set(evidence)

if missing_ids:
    raise RuntimeError(
        "Missing expected evidence IDs: "
        + ", ".join(sorted(missing_ids))
    )

tiers = {}

for eid, row in evidence.items():
    tier = row.get("evidence_tier", "").strip()

    if not tier:
        raise RuntimeError(
            f"{eid}: missing evidence tier"
        )

    tiers[eid] = tier


expected_tiers = {
    "A1_E01": "E2",
    "A1_E02": "E2",
    "A1_E03": "E2",
    "A1_E04": "E2",
    "A2_E01": "E2",
    "A2_E02": "E1",
    "A2_E03": "E2",
    "A2_E04": "E1",
    "A3_E01": "E2",
    "A3_E02": "E2",
    "A3_E03": "E2",
    "A3_E04": "E2",
    "B1_E01": "E4",
    "B1_E02": "E3",
    "B2_E01": "E4",
    "B2_E02": "E4",
    "B2_E03": "E4",
    "B3_E01": "E4",
    "B3_E02": "E4",
    "B3_E03": "E4",
}

for eid, expected in expected_tiers.items():
    observed = tiers[eid]

    if observed != expected:
        raise RuntimeError(
            f"{eid}: expected {expected}, observed {observed}"
        )


# GRI locks
c4_text = C4_CASE.read_text(encoding="utf-8")

for token in (
    "1.0000000000",
    "0.9115102712",
    "M3=UNMEASURED",
):
    if token not in c4_text:
        raise RuntimeError(
            f"Missing locked GRI token: {token}"
        )


# Figure/table manifests must already exist.
figure_manifest = read_tsv(C6_MANIFEST)
table_manifest = read_tsv(C7_MANIFEST)

if len(
    [
        r for r in figure_manifest
        if r.get("status") == "CANONICAL"
    ]
) != 6:
    raise RuntimeError(
        "Expected exactly 6 canonical main C6 figures"
    )

if len(table_manifest) != 6:
    raise RuntimeError(
        "Expected exactly 6 C7 publication tables"
    )

print("C8 source preflight: PASS")


# ============================================================
# Primary paper claims
# ============================================================

claims = [
    {
        "claim_id": "P01",
        "claim_short": "BWA memory-safety findings",
        "primary_module": "A1",
        "evidence_ids": "A1_E02|A1_E03|A1_E04",
        "evidence_profile": "E2_CONTROLLED_EMPIRICAL_SOFTWARE_AUDIT",
        "permitted_wording": (
            "The BWA audit recovered two distinct ASAN-confirmed "
            "out-of-bounds-read root causes: a heap-backed read in "
            "ksw_extend2 (ksw.c:428) and a global/static-storage read "
            "in mem_aln2sam (bwamem.c:906), both classified as CWE-125."
        ),
        "must_not_claim": (
            "Do not claim memory-write corruption, remote code execution, "
            "arbitrary code execution, assigned CVEs, patient harm, or "
            "that these were the first BWA vulnerabilities."
        ),
        "paper_figure": "None required",
        "paper_table": "Table_06",
        "scope_limit": (
            "Recovered controlled software-audit findings; A1 remains "
            "STANDALONE_NON_GRI."
        ),
    },
    {
        "claim_id": "P02",
        "claim_short": "Raw-signal perturbation affects sequence evidence",
        "primary_module": "A2",
        "evidence_ids": "A2_E01|A2_E02|A2_E03|A2_E04",
        "evidence_profile": "MIXED_E1_E2_EMPIRICAL",
        "permitted_wording": (
            "Controlled nanopore raw-signal perturbations altered "
            "basecalling and downstream sequence evidence under the tested "
            "Dorado/HG002 configurations, while the W0 cross-locus "
            "replication produced no target-state change in 0 of 20 "
            "evaluated parent-locus observations."
        ),
        "must_not_claim": (
            "Do not claim universal transferability across sequencing "
            "platforms, basecallers, genomes, loci, or clinical pipelines."
        ),
        "paper_figure": (
            "Supplementary A2_Figure_01; A2_Figure_05; "
            "A2_Figure_07; A2_Figure_08"
        ),
        "paper_table": "Table_02",
        "scope_limit": (
            "Controlled HG002 nanopore experiments using the tested "
            "Dorado configuration."
        ),
    },
    {
        "claim_id": "P03",
        "claim_short": "F11 targeted pathogenic-call suppression",
        "primary_module": "A3",
        "evidence_ids": "A3_E01|A3_E02|A3_E03|A3_E04",
        "evidence_profile": "E2_CONTROLLED_EMPIRICAL_CASE",
        "permitted_wording": (
            "In the F11 worked case, on-target PM2 and larger perturbation "
            "windows eliminated ALT-supporting parent evidence and removed "
            "the pathogenic target VCF call, whereas an identically sized "
            "off-target PM2 sham retained 14/14 ALT-supporting parents, "
            "the 0/1 genotype, and QUAL 222.202. The ceiling F11 Base GRI "
            "arose because the attack produced complete ALT-support loss "
            "under the continuous D2 loss-fraction metric and reached S5 "
            "under the ordinal D7 terminal-reach metric; the score is not "
            "the result of binary success/failure scoring."
        ),
        "must_not_claim": (
            "Do not interpret the result as a probability of patient harm. "
            "This is not population-level evidence, not a population-wide "
            "clinical failure rate, and not external clinical validation."
        ),
        "paper_figure": "Figure_02",
        "paper_table": "Table_03",
        "scope_limit": (
            "Single HG002/F11 locus worked case under the tested "
            "Dorado/configuration."
        ),
    },
    {
        "claim_id": "P04",
        "claim_short": "Kinship amplification",
        "primary_module": "B1",
        "evidence_ids": "B1_E01|B1_E02",
        "evidence_profile": "E3_CALIBRATED_PLUS_E4_INTERNAL_MODEL",
        "permitted_wording": (
            "The primary B1 graph reproduction generated 4,144 nodes with "
            "1,657 registered individuals. Separately, a five-run-per-"
            "parameter calibration sweep over cousin-edge probability "
            "selected cousin_prob=0.20, yielding mean amplification of "
            "464.4-fold against the 492.86-fold reference target, "
            "corresponding to approximately 5.8 percent deviation."
        ),
        "must_not_claim": (
            "Do not present 464.4-fold as an observed real-world breach "
            "rate or independently validated population estimate."
        ),
        "paper_figure": "Figure_06",
        "paper_table": "Table_05",
        "scope_limit": (
            "The 4,144-node/1,657-registered result describes the primary "
            "B1 graph reproduction, whereas 464.4-fold is the mean result "
            "of a separate stochastic calibration sweep. Node counts from "
            "the individual calibration runs were not recorded in the "
            "tuning output and must not be attributed to the primary "
            "reproduction graph."
        ),
    },
    {
        "claim_id": "P05",
        "claim_short": "Persistent genomic disclosure",
        "primary_module": "B2",
        "evidence_ids": "B2_E01|B2_E02|B2_E03",
        "evidence_profile": "E4_INTERNAL_MODEL",
        "permitted_wording": (
            "Within the configured B2 models, Pathogenic Variants alone "
            "produced unrecoverability 0.2299, cumulative disclosure across "
            "all six modeled tiers reduced unrecoverability to 0.0801, "
            "re-identification reached 100 percent at year 13, and familial "
            "risk reached 100 percent at year 15."
        ),
        "must_not_claim": (
            "Do not describe unrecoverability as a formal cryptographic "
            "guarantee or lifetime-model trajectories as observed "
            "population incidence."
        ),
        "paper_figure": "Figure_06",
        "paper_table": "Table_05",
        "scope_limit": (
            "Configured internal vault and lifetime-risk models."
        ),
    },
    {
        "claim_id": "P06",
        "claim_short": "Containment and authentication",
        "primary_module": "B3",
        "evidence_ids": "B3_E01|B3_E02|B3_E03",
        "evidence_profile": "E4_INTERNAL_MODEL",
        "permitted_wording": (
            "In the principal B3 containment simulation, exposure decreased "
            "from 786 baseline nodes to 560 at k=5 and 6 at k=10, a 99.2 "
            "percent reduction at k=10. The internal authentication benchmark "
            "used threshold 4.5 and achieved F1 0.9899."
        ),
        "must_not_claim": (
            "This is not external real-world validation. Do not revive the "
            "unsupported hub-origin k=20 claim, and do not interpret 1-F1 "
            "as a privacy-event detectability probability."
        ),
        "paper_figure": "Figure_06",
        "paper_table": "Table_05",
        "scope_limit": (
            "Internal graph-containment and authentication benchmark."
        ),
    },
    {
        "claim_id": "P07",
        "claim_short": "GRI worked-case synthesis",
        "primary_module": "C",
        "evidence_ids": (
            "A3_E01|A3_E02|A3_E03|A3_E04|"
            "B1_E01|B1_E02|"
            "B2_E01|B2_E02|B2_E03|"
            "B3_E01|B3_E02|B3_E03"
        ),
        "evidence_profile": "MIXED_E2_E3_E4_PROVENANCE_AWARE",
        "permitted_wording": (
            "The locked GenoPhylax Risk Index produced Base GRI "
            "1.0000000000 for the controlled F11 worked case and "
            "0.9115102712 for the model-dependent Privacy worked case. "
            "Privacy M3 remains UNMEASURED. Evidence tiers and contextual "
            "modifiers remain separate from the Base GRI computation. "
            "Because three of the four scored Privacy dimensions "
            "(D1, D3, D5) share B2 provenance, equal per-dimension "
            "weighting implicitly assigns 75 percent of the Base GRI "
            "weight to that model family and 25 percent to B1-derived D6; "
            "a correlation-aware 50/50 provenance-family sensitivity "
            "was therefore also evaluated, yielding GRI=0.9378168865 "
            "(approximately 0.9378)."
        ),
        "must_not_claim": (
            "Do not interpret GRI as probability of breach, probability of "
            "patient harm, clinical risk calibration, or an externally "
            "validated universal risk score. Evidence tiers are not numeric "
            "GRI multipliers, and unmeasured/N/A dimensions are not zero."
        ),
        "paper_figure": "Figure_03|Figure_04|Figure_05",
        "paper_table": "Table_04",
        "scope_limit": (
            "Two worked-case profiles with deterministic sensitivity analysis. "
            "Equal per-dimension weighting is a transparent baseline, not "
            "an empirically optimized weighting scheme; D1, D3 and D5 "
            "share B2 model provenance and are not independent empirical "
            "confirmations. The Privacy GRI is not externally calibrated."
        ),
    },
    {
        "claim_id": "P08",
        "claim_short": "Lifecycle integration contribution",
        "primary_module": "C",
        "evidence_ids": (
            "A1_E01|A1_E02|A1_E03|A1_E04|"
            "A2_E01|A2_E02|A2_E03|A2_E04|"
            "A3_E01|A3_E02|A3_E03|A3_E04|"
            "B1_E01|B1_E02|"
            "B2_E01|B2_E02|B2_E03|"
            "B3_E01|B3_E02|B3_E03"
        ),
        "evidence_profile": "SYNTHESIS_ACROSS_E1_E2_E3_E4",
        "permitted_wording": (
            "GenoPhylax organizes heterogeneous cyber-biosecurity evidence "
            "across a ten-stage genomic lifecycle and preserves evidence "
            "provenance when linking generation-time integrity findings to "
            "storage-, sharing-, persistence-, and containment-time risk."
        ),
        "must_not_claim": (
            "Not every lifecycle handoff was directly observed end-to-end, and "
            "no single empirical experiment traversed all ten stages."
        ),
        "paper_figure": "Figure_01",
        "paper_table": "Table_01|Table_02",
        "scope_limit": (
            "Evidence-integration framework spanning heterogeneous direct "
            "experiments and internal models."
        ),
    },
]


# ============================================================
# Validate evidence references used by claims
# ============================================================

for claim in claims:
    ids = claim["evidence_ids"].split("|")

    for eid in ids:
        if eid not in evidence:
            raise RuntimeError(
                f"{claim['claim_id']}: unknown evidence ID {eid}"
            )


claim_fields = [
    "claim_id",
    "claim_short",
    "primary_module",
    "evidence_ids",
    "evidence_profile",
    "permitted_wording",
    "must_not_claim",
    "paper_figure",
    "paper_table",
    "scope_limit",
]

write_tsv(
    DATA_DIR / "C8_paper_claim_evidence_map.tsv",
    claims,
    claim_fields,
)

write_md_table(
    CLAIM_DIR / "C8_paper_claim_evidence_map.md",
    "C8 — Paper Claim-to-Evidence Map",
    claims,
    claim_fields,
    note=(
        "This map governs publication wording. Evidence tiers represent "
        "evidence/provenance strength and are not numerical GRI weights."
    ),
)


# ============================================================
# Claim wording lock — compact manuscript-facing version
# ============================================================

wording_rows = []

for c in claims:
    wording_rows.append(
        {
            "claim_id": c["claim_id"],
            "use_in_paper": "YES",
            "approved_claim": c["permitted_wording"],
            "prohibited_interpretation": c["must_not_claim"],
            "scope": c["scope_limit"],
        }
    )

wording_fields = [
    "claim_id",
    "use_in_paper",
    "approved_claim",
    "prohibited_interpretation",
    "scope",
]

write_tsv(
    DATA_DIR / "C8_claim_wording_lock.tsv",
    wording_rows,
    wording_fields,
)

write_md_table(
    CLAIM_DIR / "C8_claim_wording_lock.md",
    "C8 — Publication Claim Wording Lock",
    wording_rows,
    wording_fields,
    note=(
        "Future manuscript drafting should stay within these wording "
        "boundaries unless new evidence is added and re-audited."
    ),
)


# ============================================================
# Manuscript section evidence map
# ============================================================

section_rows = [
    {
        "manuscript_section": "Introduction",
        "claim_ids": "P08",
        "figures": "Figure_01",
        "tables": "Table_01",
        "writing_role": (
            "Motivate lifecycle fragmentation and introduce GenoPhylax "
            "as an integration framework."
        ),
    },
    {
        "manuscript_section": "Methods — A1",
        "claim_ids": "P01",
        "figures": "",
        "tables": "Table_02",
        "writing_role": "Describe sanitized BWA memory-safety audit.",
    },
    {
        "manuscript_section": "Methods — A2/A3",
        "claim_ids": "P02|P03",
        "figures": "Figure_02",
        "tables": "Table_03",
        "writing_role": (
            "Describe controlled nanopore perturbations and F11 worked case."
        ),
    },
    {
        "manuscript_section": "Methods — B1/B2/B3",
        "claim_ids": "P04|P05|P06",
        "figures": "Figure_06",
        "tables": "Table_05",
        "writing_role": (
            "Describe calibrated/internal privacy, persistence and "
            "containment models."
        ),
    },
    {
        "manuscript_section": "Methods — Integration / GRI",
        "claim_ids": "P07|P08",
        "figures": "Figure_01",
        "tables": "Table_01|Table_02|Table_04",
        "writing_role": (
            "Define lifecycle handoffs, evidence tiers, dimensions, "
            "modifiers and Base GRI policy."
        ),
    },
    {
        "manuscript_section": "Results — Integrity",
        "claim_ids": "P01|P02|P03",
        "figures": "Figure_02",
        "tables": "Table_03|Table_06",
        "writing_role": (
            "Report software and raw-signal integrity findings without "
            "generalizing beyond observed scope."
        ),
    },
    {
        "manuscript_section": "Results — Privacy / Containment",
        "claim_ids": "P04|P05|P06",
        "figures": "Figure_06",
        "tables": "Table_05",
        "writing_role": (
            "Report calibrated/model-derived downstream results."
        ),
    },
    {
        "manuscript_section": "Results — GRI",
        "claim_ids": "P07",
        "figures": "Figure_03|Figure_04|Figure_05",
        "tables": "Table_04",
        "writing_role": (
            "Report Base GRI, ablation and deterministic sensitivity."
        ),
    },
    {
        "manuscript_section": "Discussion",
        "claim_ids": "P01|P02|P03|P04|P05|P06|P07|P08",
        "figures": "",
        "tables": "Table_06",
        "writing_role": (
            "Interpret cross-lifecycle significance while preserving "
            "evidence-tier and scope distinctions."
        ),
    },
    {
        "manuscript_section": "Limitations",
        "claim_ids": "P01|P02|P03|P04|P05|P06|P07|P08",
        "figures": "",
        "tables": "Table_06",
        "writing_role": (
            "Explicitly state empirical, modeling, calibration and "
            "external-validation limits."
        ),
    },
]

section_fields = [
    "manuscript_section",
    "claim_ids",
    "figures",
    "tables",
    "writing_role",
]

write_tsv(
    DATA_DIR / "C8_manuscript_evidence_map.tsv",
    section_rows,
    section_fields,
)

write_md_table(
    CLAIM_DIR / "C8_manuscript_evidence_map.md",
    "C8 — Manuscript Section Evidence Map",
    section_rows,
    section_fields,
)


# ============================================================
# Paper-level limitations lock
# ============================================================

limitations = [
    {
        "limitation_id": "L01",
        "category": "Empirical scope",
        "locked_limitation": (
            "The direct sequencing attack evidence is limited to tested "
            "HG002 nanopore data, selected loci, Dorado configurations, "
            "and one F11 clinical worked case."
        ),
    },
    {
        "limitation_id": "L02",
        "category": "Clinical validation",
        "locked_limitation": (
            "No patient outcomes were observed and no external clinical "
            "validation was performed."
        ),
    },
    {
        "limitation_id": "L03",
        "category": "Model dependence",
        "locked_limitation": (
            "B1/B2/B3 downstream privacy and containment outputs depend on "
            "configured synthetic or internal models; only B1 amplification "
            "contains an explicit external reference calibration anchor."
        ),
    },
    {
        "limitation_id": "L04",
        "category": "GRI interpretation",
        "locked_limitation": (
            "GRI is a provenance-aware severity representation for worked "
            "cases, not an empirical probability of compromise, clinical "
            "harm, or population incidence."
        ),
    },
    {
        "limitation_id": "L05",
        "category": "Evidence dependence",
        "locked_limitation": (
            "Privacy dimensions D1, D3 and D5 share the B2 lifetime-model "
            "family and are not independent replications."
        ),
    },
    {
        "limitation_id": "L06",
        "category": "Sensitivity",
        "locked_limitation": (
            "Reported V7 ranges are deterministic sensitivity analyses "
            "rather than confidence intervals."
        ),
    },
    {
        "limitation_id": "L07",
        "category": "Lifecycle coverage",
        "locked_limitation": (
            "The ten-stage lifecycle is an integration framework; not every "
            "adjacent handoff has been observed experimentally end-to-end."
        ),
    },
    {
        "limitation_id": "L08",
        "category": "A1 disclosure",
        "locked_limitation": (
            "Public repository artifacts for A1 are sanitized; raw crash "
            "inputs/reproducers remain private pending responsible "
            "disclosure decisions."
        ),
    },
    {
        "limitation_id": "L09",
        "category": "GRI weighting",
        "locked_limitation": (
            "Privacy Base GRI uses equal per-dimension weighting. Because "
            "D1, D3 and D5 share B2 provenance, this baseline implicitly "
            "assigns 75 percent of the scored weight to the B2 model family "
            "and 25 percent to B1-derived D6. This is a transparent baseline "
            "rather than an empirically optimized weighting scheme. A "
            "correlation-aware 50/50 provenance-family sensitivity yielded "
            "GRI=0.9378168865."
        ),
    },
    {
        "limitation_id": "L10",
        "category": "B1 calibration provenance",
        "locked_limitation": (
            "The 4,144-node and 1,657-registered values correspond to the "
            "primary B1 graph reproduction. The 464.4-fold value is the mean "
            "of a separate five-run-per-parameter calibration sweep at "
            "cousin_prob=0.20. The tuning output did not record node counts "
            "for each calibration run, so those population counts must not "
            "be attributed to the 464.4-fold calibration mean."
        ),
    },
]

limitation_fields = [
    "limitation_id",
    "category",
    "locked_limitation",
]

write_tsv(
    DATA_DIR / "C8_paper_limitations_lock.tsv",
    limitations,
    limitation_fields,
)

write_md_table(
    CLAIM_DIR / "C8_paper_limitations_lock.md",
    "C8 — Paper Limitations Lock",
    limitations,
    limitation_fields,
)


# ============================================================
# Validation
# ============================================================

errors = []

claim_text = (
    CLAIM_DIR / "C8_paper_claim_evidence_map.md"
).read_text(encoding="utf-8")

wording_text = (
    CLAIM_DIR / "C8_claim_wording_lock.md"
).read_text(encoding="utf-8")

limits_text = (
    CLAIM_DIR / "C8_paper_limitations_lock.md"
).read_text(encoding="utf-8")

combined = "\n".join(
    [
        claim_text,
        wording_text,
        limits_text,
    ]
)


required_tokens = [
    "A1_E02",
    "A2_E02",
    "A3_E04",
    "B1_E02",
    "B2_E02",
    "B3_E02",
    "464.4",
    "0.2299",
    "0.0801",
    "year 13",
    "99.2",
    "0.9899",
    "1.0000000000",
    "0.9115102712",
    "M3",
    "confidence intervals",
    "STANDALONE_NON_GRI",
    "75 percent",
    "25 percent",
    "0.9378168865",
    "continuous D2 loss-fraction",
    "ordinal D7 terminal-reach",
    "five-run-per-parameter calibration sweep",
    "cousin_prob=0.20",
]

for token in required_tokens:
    if token not in combined:
        errors.append(
            f"Missing required publication lock token: {token}"
        )


# Explicit stale/superseded claim audit.
for forbidden in (
    "unrecoverability 0.044",
    "100 percent at year 20",
    "threshold 3.8",
    "threshold 3.6",
    "17.69%",
    "33 unique crashes",
    "1130-fold",
    "1130×",
):
    if forbidden in combined:
        errors.append(
            f"Forbidden superseded claim found: {forbidden}"
        )


# Critical semantic locks.
required_semantics = [
    "not an empirical probability",
    "not population-level",
    "not external real-world validation",
    "not numerical GRI weights",
    "not every lifecycle handoff",
]

low = combined.lower()

for phrase in required_semantics:
    if phrase.lower() not in low:
        errors.append(
            f"Missing semantic guardrail: {phrase}"
        )


validation = (
    VALID_DIR
    / "C8_paper_claim_evidence_validation.txt"
)

lines = [
    "C8 PAPER CLAIM / EVIDENCE VALIDATION",
    "====================================",
    "",
    f"C2 evidence rows checked: {len(c2_rows)}",
    f"Primary publication claims: {len(claims)}",
    f"Paper limitations locked: {len(limitations)}",
    f"Manuscript section mappings: {len(section_rows)}",
    "",
    "Evidence tier locks:",
    "- E1 = 2",
    "- E2 = 10",
    "- E3 = 1",
    "- E4 = 7",
    "- E5 = 0",
    "",
    "Critical semantic locks:",
    "- A1 remains STANDALONE_NON_GRI",
    "- F11 is controlled E2 worked-case evidence",
    "- Privacy is mixed E3/E4 model-dependent evidence",
    "- Evidence tiers are not GRI multipliers",
    "- Missing/N/A dimensions are not zero",
    "- Privacy M3 remains UNMEASURED",
    "- B3 F1=0.9899 is contextual mitigation evidence only",
    "- V7 sensitivity ranges are not confidence intervals",
    "- GRI is not probability of breach or patient harm",
    "- Not every S1-S10 handoff was directly observed end-to-end",
    "",
    f"Validation errors: {len(errors)}",
    f"STATUS: {'FAIL' if errors else 'PASS'}",
]

if errors:
    lines += [
        "",
        "Errors:",
        *[f"- {e}" for e in errors],
    ]

validation.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

if errors:
    for error in errors:
        print("ERROR:", error)

    raise SystemExit(1)

print("C8 paper evidence map generated")
print(f"Claims: {len(claims)}")
print(f"Limitations: {len(limitations)}")
print(f"Section mappings: {len(section_rows)}")
print("STATUS: PASS")
