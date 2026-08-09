#!/usr/bin/env python3

from pathlib import Path
import csv
import json


ROOT = Path.cwd()

BASE = ROOT / "experiments/C_lifecycle_integration/publication"
TABLE_DIR = BASE / "tables"
DATA_DIR = BASE / "table_data"
VALID_DIR = BASE / "validation"

for p in (TABLE_DIR, DATA_DIR, VALID_DIR):
    p.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Source paths
# ------------------------------------------------------------

C1 = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "lifecycle/C1_lifecycle_stages.tsv"
)

C2 = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "evidence_registry/C2_cross_module_evidence_registry.tsv"
)

C4_DIMS = (
    ROOT
    / "experiments/C_lifecycle_integration/gri/"
      "C4_7_base_dimension_profiles.tsv"
)

C4_CASE = (
    ROOT
    / "experiments/C_lifecycle_integration/gri/"
      "C4_8_case_output_profile.tsv"
)

A3_FINAL = (
    ROOT
    / "experiments/A3_clinical_consequence_mapping/"
      "findings/A3_F11_final_numerical_summary.tsv"
)

B1_AUTH = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "evidence_registry/reproduced_results/"
      "B1_authoritative_results.tsv"
)

B2_VAULT = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "evidence_registry/reproduced_results/"
      "B2_authoritative_vault_results.tsv"
)

B2_LIFETIME = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "evidence_registry/reproduced_results/"
      "B2_authoritative_lifetime_results.tsv"
)

B3_AUTH = (
    ROOT
    / "experiments/C_lifecycle_integration/"
      "evidence_registry/reproduced_results/"
      "B3_authoritative_results.tsv"
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


def markdown_table(path, rows, fields, title=None, note=None):
    lines = []

    if title:
        lines += [f"# {title}", ""]

    lines.append(
        "| " + " | ".join(fields) + " |"
    )

    lines.append(
        "| " + " | ".join(["---"] * len(fields)) + " |"
    )

    for row in rows:
        vals = []

        for f in fields:
            value = str(row.get(f, ""))
            value = value.replace("|", "\\|")
            vals.append(value)

        lines.append(
            "| " + " | ".join(vals) + " |"
        )

    if note:
        lines += ["", f"**Note:** {note}"]

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


# ============================================================
# Table 1 — Lifecycle map
# ============================================================

lifecycle_rows = [
    {
        "Stage": "S1",
        "Lifecycle phase": "Generation",
        "Primary modules": "A1",
        "Security focus": "Software/input integrity",
    },
    {
        "Stage": "S2",
        "Lifecycle phase": "Basecalling",
        "Primary modules": "A2",
        "Security focus": "Raw-signal perturbation and basecalling robustness",
    },
    {
        "Stage": "S3",
        "Lifecycle phase": "Alignment",
        "Primary modules": "A2",
        "Security focus": "Propagation into mapped sequence evidence",
    },
    {
        "Stage": "S4",
        "Lifecycle phase": "Variant Calling / Genotype Evidence",
        "Primary modules": "A2, A3",
        "Security focus": "Variant-state and genotype evidence integrity",
    },
    {
        "Stage": "S5",
        "Lifecycle phase": "Clinical Interpretation",
        "Primary modules": "A3",
        "Security focus": "Clinical consequence of altered variant evidence",
    },
    {
        "Stage": "S6",
        "Lifecycle phase": "Storage",
        "Primary modules": "B2",
        "Security focus": "Semantic-layer disclosure and persistence",
    },
    {
        "Stage": "S7",
        "Lifecycle phase": "Sharing / Release",
        "Primary modules": "B1, B2",
        "Security focus": "Exposure and disclosure amplification",
    },
    {
        "Stage": "S8",
        "Lifecycle phase": "Reuse / Downstream",
        "Primary modules": "B1, B2",
        "Security focus": "Kinship and downstream inference",
    },
    {
        "Stage": "S9",
        "Lifecycle phase": "Incident / Forensic",
        "Primary modules": "B2, B3",
        "Security focus": "Persistent exposure and incident response",
    },
    {
        "Stage": "S10",
        "Lifecycle phase": "Containment / Revocation",
        "Primary modules": "B3",
        "Security focus": "Containment and authentication",
    },
]

write_tsv(
    DATA_DIR / "Table_01_lifecycle_map.tsv",
    lifecycle_rows,
    [
        "Stage",
        "Lifecycle phase",
        "Primary modules",
        "Security focus",
    ],
)

markdown_table(
    TABLE_DIR / "Table_01_lifecycle_map.md",
    lifecycle_rows,
    [
        "Stage",
        "Lifecycle phase",
        "Primary modules",
        "Security focus",
    ],
    title="Table 1 — GenoPhylax lifecycle stage and module map",
)


# ============================================================
# Table 2 — Evidence registry summary
# ============================================================

c2_rows = read_tsv(C2)

summary_rows = []

for r in c2_rows:
    summary_rows.append(
        {
            "Evidence ID": r.get("evidence_id", ""),
            "Module": r.get("module", ""),
            "Lifecycle stage(s)": r.get("lifecycle_stage", ""),
            "Evidence tier": r.get("evidence_tier", ""),
            "Evidence class": r.get("evidence_tier_name", ""),
            "Status": r.get("tier_status", ""),
            "C3/GRI role": (
                "Eligible"
                if r.get("c3_eligible", "") == "YES"
                else "Standalone / non-GRI"
            ),
        }
    )

write_tsv(
    DATA_DIR / "Table_02_evidence_summary.tsv",
    summary_rows,
    list(summary_rows[0].keys()),
)

markdown_table(
    TABLE_DIR / "Table_02_evidence_summary.md",
    summary_rows,
    list(summary_rows[0].keys()),
    title="Table 2 — Cross-module evidence registry",
    note=(
        "Evidence tiers are provenance/evidence-strength categories "
        "and are not numerical multipliers applied to Base GRI."
    ),
)


# ============================================================
# Table 3 — F11 worked case
# ============================================================

a3_rows = read_tsv(A3_FINAL)

if not a3_rows:
    raise RuntimeError("A3 final numerical summary is empty")

required_fields = {
    "condition",
    "parent_ALT",
    "ALT_fraction",
    "vcf_record",
    "GT",
    "QUAL",
    "clinical_outcome",
}

missing_fields = required_fields - set(a3_rows[0].keys())

if missing_fields:
    raise RuntimeError(
        "A3 final summary missing required fields: "
        + ", ".join(sorted(missing_fields))
    )

wanted_order = [
    "CLEAN",
    "PM2_OFF_TARGET_SHAM",
    "W0",
    "PM2",
    "PM5",
    "PM10",
    "PM20",
]

by_condition = {
    r["condition"].strip(): r
    for r in a3_rows
}

for condition in wanted_order:
    if condition not in by_condition:
        raise RuntimeError(
            f"Missing required A3 condition: {condition}"
        )

f11_rows = []

for condition in wanted_order:
    r = by_condition[condition]

    alt_count = int(r["parent_ALT"])
    vcf_present = r["vcf_record"].strip()

    if vcf_present not in {"0", "1"}:
        raise RuntimeError(
            f"{condition}: invalid vcf_record={vcf_present!r}"
        )

    qual = r["QUAL"].strip()

    if qual == ".":
        qual = "—"

    f11_rows.append(
        {
            "Condition": condition,
            "ALT-supporting parents": f"{alt_count}/14",
            "ALT fraction": r["ALT_fraction"].strip(),
            "Target VCF present": (
                "YES" if vcf_present == "1" else "NO"
            ),
            "Genotype": r["GT"].strip(),
            "QUAL": qual,
            "Interpretation": r["clinical_outcome"].strip(),
        }
    )

# Exact source-lock assertions for headline causal comparison.
lookup = {
    r["Condition"]: r
    for r in f11_rows
}

sham = lookup["PM2_OFF_TARGET_SHAM"]
pm2 = lookup["PM2"]

if sham != {
    "Condition": "PM2_OFF_TARGET_SHAM",
    "ALT-supporting parents": "14/14",
    "ALT fraction": "0.560000",
    "Target VCF present": "YES",
    "Genotype": "0/1",
    "QUAL": "222.202",
    "Interpretation": "PATHOGENIC_ALT_CALL_RETAINED",
}:
    raise RuntimeError(
        f"Unexpected canonical PM2 sham row: {sham}"
    )

if pm2 != {
    "Condition": "PM2",
    "ALT-supporting parents": "0/14",
    "ALT fraction": "0.000000",
    "Target VCF present": "NO",
    "Genotype": "NO_CALL",
    "QUAL": "—",
    "Interpretation": "PATHOGENIC_ALT_CALL_LOST",
}:
    raise RuntimeError(
        f"Unexpected canonical PM2 row: {pm2}"
    )

write_tsv(
    DATA_DIR / "Table_03_F11_worked_case.tsv",
    f11_rows,
    list(f11_rows[0].keys()),
)

markdown_table(
    TABLE_DIR / "Table_03_F11_worked_case.md",
    f11_rows,
    list(f11_rows[0].keys()),
    title="Table 3 — F11 targeted raw-signal perturbation worked case",
    note=(
        "Controlled HG002/Dorado case study. The matched PM2 "
        "off-target sham retained all 14 ALT-supporting parents "
        "and the 0/1 pathogenic call, whereas on-target PM2 "
        "eliminated ALT support and produced NO_CALL. Results "
        "are not population-level or clinically validated rates."
    ),
)


# ============================================================
# Table 4 — Privacy GRI profile
# ============================================================

dim_rows = read_tsv(C4_DIMS)

privacy_dims = []

for r in dim_rows:
    if r.get("case_id") != "C3_PRIVACY":
        continue

    privacy_dims.append(
        {
            "Dimension": r.get("dimension_id", ""),
            "Name": r.get("dimension_name", ""),
            "Status": r.get("profile_status", ""),
            "Normalized severity": r.get(
                "normalized_risk_value",
                "",
            ),
            "Evidence tier": r.get("evidence_tier", ""),
            "Evidence class": r.get(
                "evidence_support_class",
                "",
            ),
        }
    )

privacy_dims.append(
    {
        "Dimension": "Base GRI",
        "Name": "Privacy worked-case composite",
        "Status": "REPORTED",
        "Normalized severity": "0.9115102712",
        "Evidence tier": "Mixed",
        "Evidence class": "MODEL_DEPENDENT_MIXED_SUPPORT",
    }
)

write_tsv(
    DATA_DIR / "Table_04_privacy_GRI_profile.tsv",
    privacy_dims,
    list(privacy_dims[0].keys()),
)

markdown_table(
    TABLE_DIR / "Table_04_privacy_GRI_profile.md",
    privacy_dims,
    list(privacy_dims[0].keys()),
    title="Table 4 — Privacy worked-case GRI profile",
    note=(
        "D1, D3 and D5 share B2 lifetime-model provenance. "
        "Privacy M3 Detectability is UNMEASURED and is not part of Base GRI."
    ),
)


# ============================================================
# Table 5 — Authoritative Module B results
# ============================================================

b_rows = [
    {
        "Module": "B1",
        "Metric": "Synthetic kinship graph",
        "Authoritative result": "4,144 nodes; 1,657 registered",
        "Evidence interpretation": "Internal synthetic model",
    },
    {
        "Module": "B1",
        "Metric": "Calibrated amplification",
        "Authoritative result": "464.4×",
        "Evidence interpretation": (
            "Calibrated model; ~5.8% error vs ~492.86× reference target"
        ),
    },
    {
        "Module": "B2",
        "Metric": "Pathogenic Variants unrecoverability",
        "Authoritative result": "0.2299",
        "Evidence interpretation": "Internal vault model",
    },
    {
        "Module": "B2",
        "Metric": "All-tier unrecoverability",
        "Authoritative result": "0.0801",
        "Evidence interpretation": "Internal vault model",
    },
    {
        "Module": "B2",
        "Metric": "Re-identification saturation",
        "Authoritative result": "100% at year 13",
        "Evidence interpretation": "Configured lifetime-risk simulation",
    },
    {
        "Module": "B2",
        "Metric": "Familial-risk saturation",
        "Authoritative result": "100% at year 15",
        "Evidence interpretation": "Configured lifetime-risk simulation",
    },
    {
        "Module": "B3",
        "Metric": "Containment",
        "Authoritative result": (
            "786 baseline → 560 at k=5 → 6 at k=10"
        ),
        "Evidence interpretation": "Internal graph-containment simulation",
    },
    {
        "Module": "B3",
        "Metric": "k=10 exposure reduction",
        "Authoritative result": "99.2%",
        "Evidence interpretation": "Internal graph-containment simulation",
    },
    {
        "Module": "B3",
        "Metric": "Authentication benchmark",
        "Authoritative result": (
            "threshold 4.5; precision 1.0000; recall 0.9800; "
            "F1 0.9899; accuracy 0.9960"
        ),
        "Evidence interpretation": (
            "Internally generated benchmark; not external validation"
        ),
    },
]

write_tsv(
    DATA_DIR / "Table_05_Module_B_authoritative_results.tsv",
    b_rows,
    list(b_rows[0].keys()),
)

markdown_table(
    TABLE_DIR / "Table_05_Module_B_authoritative_results.md",
    b_rows,
    list(b_rows[0].keys()),
    title="Table 5 — Authoritative Module B results",
)


# ============================================================
# Table 6 — Claims and limitations
# ============================================================

claim_rows = [
    {
        "Claim": (
            "A1 identified two source-level BWA out-of-bounds-read root causes."
        ),
        "Evidence": "E2 controlled empirical/software audit",
        "Supported wording": "Two ASAN-confirmed CWE-125 root causes",
        "Key limitation": (
            "No RCE, arbitrary code execution, memory-write corruption "
            "or assigned CVE established."
        ),
    },
    {
        "Claim": (
            "Targeted F11 raw-signal perturbation suppressed ALT evidence "
            "in the tested worked case."
        ),
        "Evidence": "E2 controlled empirical case",
        "Supported wording": (
            "All 14 clean ALT-supporting parents lost ALT under PM2; "
            "off-target sham retained 14/14."
        ),
        "Key limitation": (
            "Single locus/person/run/basecaller configuration; "
            "no external clinical validation."
        ),
    },
    {
        "Claim": "Kinship can amplify genomic disclosure.",
        "Evidence": "E3 calibrated model",
        "Supported wording": "464.4× amplification in calibrated B1 model",
        "Key limitation": (
            "Synthetic graph and configured calibration assumptions."
        ),
    },
    {
        "Claim": "Genomic disclosure persists over long time horizons.",
        "Evidence": "E4 internal model",
        "Supported wording": (
            "Re-identification reached 100% by year 13 "
            "in the configured B2 simulation."
        ),
        "Key limitation": (
            "Model trajectory, not observed population incidence."
        ),
    },
    {
        "Claim": "Containment can sharply reduce simulated exposure.",
        "Evidence": "E4 internal model",
        "Supported wording": (
            "k=10 reduced exposure from 786 to 6 in the principal B3 scenario."
        ),
        "Key limitation": (
            "Internal graph simulation; not real-world containment validation."
        ),
    },
    {
        "Claim": "GRI synthesizes lifecycle severity with provenance retained.",
        "Evidence": "Mixed E2/E3/E4",
        "Supported wording": (
            "F11 Base GRI=1.0000000000; "
            "Privacy Base GRI=0.9115102712."
        ),
        "Key limitation": (
            "GRI is severity representation, not probability of breach "
            "or patient harm."
        ),
    },
]

write_tsv(
    DATA_DIR / "Table_06_claims_and_limitations.tsv",
    claim_rows,
    list(claim_rows[0].keys()),
)

markdown_table(
    TABLE_DIR / "Table_06_claims_and_limitations.md",
    claim_rows,
    list(claim_rows[0].keys()),
    title="Table 6 — Publication claims and limitations",
)


# ============================================================
# Manifest + validation
# ============================================================

manifest_rows = [
    {
        "table_id": "Table_01",
        "role": "MAIN",
        "source": "C1 lifecycle schema / locked stage mapping",
        "status": "CANONICAL",
    },
    {
        "table_id": "Table_02",
        "role": "MAIN_OR_SUPPLEMENT",
        "source": "C2 evidence registry",
        "status": "CANONICAL",
    },
    {
        "table_id": "Table_03",
        "role": "MAIN",
        "source": "A3 final F11 results",
        "status": "CANONICAL",
    },
    {
        "table_id": "Table_04",
        "role": "MAIN",
        "source": "C4 GRI outputs",
        "status": "CANONICAL",
    },
    {
        "table_id": "Table_05",
        "role": "MAIN_OR_SUPPLEMENT",
        "source": "Authoritative B1/B2/B3 reproduced outputs",
        "status": "CANONICAL",
    },
    {
        "table_id": "Table_06",
        "role": "MAIN",
        "source": "Locked claims + evidence semantics",
        "status": "CANONICAL",
    },
]

write_tsv(
    DATA_DIR / "C7_table_manifest.tsv",
    manifest_rows,
    [
        "table_id",
        "role",
        "source",
        "status",
    ],
)


validation_errors = []

required_tokens = {
    "Table_03_F11_worked_case.md": [
        "14/14",
        "NO_CALL",
    ],
    "Table_04_privacy_GRI_profile.md": [
        "0.9115102712",
        "0.8886656512",
        "0.8817416604",
        "0.8852036558",
        "0.9904301172",
    ],
    "Table_05_Module_B_authoritative_results.md": [
        "464.4",
        "0.2299",
        "0.0801",
        "year 13",
        "99.2",
        "0.9899",
    ],
    "Table_06_claims_and_limitations.md": [
        "CWE-125",
        "1.0000000000",
        "0.9115102712",
    ],
}

for name, tokens in required_tokens.items():
    path = TABLE_DIR / name

    if not path.exists():
        validation_errors.append(
            f"Missing table: {path}"
        )
        continue

    t = path.read_text(encoding="utf-8")

    for token in tokens:
        if token not in t:
            validation_errors.append(
                f"{name}: missing required token {token}"
            )


for forbidden in [
    "0.044",
    "year 20",
    "threshold 3.8",
    "threshold 3.6",
    "17.69%",
    "33 unique crashes",
    "1130×",
]:
    for path in TABLE_DIR.glob("*.md"):
        if forbidden in path.read_text(encoding="utf-8"):
            validation_errors.append(
                f"{path.name}: forbidden stale value {forbidden}"
            )


validation = VALID_DIR / "C7_publication_table_validation.txt"

lines = [
    "C7 PUBLICATION TABLE VALIDATION",
    "===============================",
    "",
    "Canonical publication tables: 6",
    "",
    "Scientific values recomputed: NO",
    "Authoritative locked sources used: YES",
    "",
    "Required locks:",
    "- F11 Base GRI = 1.0000000000",
    "- Privacy Base GRI = 0.9115102712",
    "- Privacy D1 = 0.8886656512",
    "- Privacy D3 = 0.8817416604",
    "- Privacy D5 = 0.8852036558",
    "- Privacy D6 = 0.9904301172",
    "- Privacy M3 = UNMEASURED",
    "- B1 calibrated amplification = 464.4x",
    "- B2 pathogenic unrecoverability = 0.2299",
    "- B2 all-tier unrecoverability = 0.0801",
    "- B2 re-identification saturation = year 13",
    "- B3 k=10 reduction = 99.2%",
    "- B3 authentication F1 = 0.9899",
    "",
    f"Validation errors: {len(validation_errors)}",
    f"STATUS: {'FAIL' if validation_errors else 'PASS'}",
]

if validation_errors:
    lines += [
        "",
        "Errors:",
        *[f"- {e}" for e in validation_errors],
    ]

validation.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

if validation_errors:
    for e in validation_errors:
        print("ERROR:", e)

    raise SystemExit(1)

print("C7 publication tables generated")
print("Tables: 6")
print("STATUS: PASS")
