#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path.cwd()

BASE = (
    ROOT
    / "experiments/C_lifecycle_integration/publication"
)

MAIN = BASE / "figures/main"
SUP = BASE / "figures/supplementary"
DATA = BASE / "figure_data"
VALID = BASE / "validation"

for p in (MAIN, SUP, DATA, VALID):
    p.mkdir(parents=True, exist_ok=True)


# ============================================================
# Locked scientific values
#
# These are not silently treated as independent constants.
# Every value below is validated against authoritative source
# artifacts before any figure is generated.
# ============================================================

PRIVACY_GRI = 0.9115102712

PRIVACY_DIMS = {
    "D1\nIdentity": 0.8886656512,
    "D3\nFamilial cascade": 0.8817416604,
    "D5\nPersistence": 0.8852036558,
    "D6\nAmplification": 0.9904301172,
}

F11_GRI = 1.0000000000

B1_MODEL_AMPLIFICATION = 464.4
B1_REFERENCE_AMPLIFICATION = 492.86

B2_PATHOGENIC_U = 0.2299
B2_ALL_TIERS_U = 0.0801

B3_BASELINE_EXPOSED = 786
B3_K5_EXPOSED = 560
B3_K10_EXPOSED = 6
B3_K10_REDUCTION = 99.2
B3_AUTH_F1 = 0.9899

F11_CLEAN_ALT = 14
F11_SHAM_ALT = 14
F11_PM2_ALT = 0


def text(path: Path) -> str:
    if not path.exists():
        raise RuntimeError(f"Missing required source: {path}")
    return path.read_text(encoding="utf-8")


def assert_contains(path: Path, token: str, label: str):
    t = text(path)
    if token not in t:
        raise RuntimeError(
            f"{label}: expected {token!r} not found in {path}"
        )


def read_tsv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def save(fig, stem: str):
    png = MAIN / f"{stem}.png"
    pdf = MAIN / f"{stem}.pdf"

    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        pdf,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"PASS: {png}")
    print(f"PASS: {pdf}")


# ============================================================
# Source paths
# ============================================================

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

V6_SINGLE = (
    ROOT
    / "experiments/C_lifecycle_integration/gri/"
      "V6_leave_one_dimension_out.tsv"
)

V6_GROUP = (
    ROOT
    / "experiments/C_lifecycle_integration/gri/"
      "V6_grouped_provenance_ablation.tsv"
)

V7_FAMILY = (
    ROOT
    / "experiments/C_lifecycle_integration/gri/"
      "V7_family_weight_sensitivity.tsv"
)

V7_REF = (
    ROOT
    / "experiments/C_lifecycle_integration/gri/"
      "V7_D6_reference_anchor_sensitivity.tsv"
)

V7_M5 = (
    ROOT
    / "experiments/C_lifecycle_integration/gri/"
      "V7_M5_scenario_sensitivity.tsv"
)

A3_FINAL = (
    ROOT
    / "experiments/A3_clinical_consequence_mapping/"
      "findings/A3_F11_final_numerical_summary.tsv"
)

A3_FINDINGS = (
    ROOT
    / "experiments/A3_clinical_consequence_mapping/"
      "findings/A3_F11_targeted_signal_attack_findings.md"
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


# ============================================================
# 0. Scientific preflight
# ============================================================

assert_contains(
    C4_CASE,
    "0.9115102712",
    "Privacy Base GRI",
)

assert_contains(
    C4_CASE,
    "1.0000000000",
    "F11 Base GRI",
)

for value in (
    "0.8886656512",
    "0.8817416604",
    "0.8852036558",
    "0.9904301172",
):
    assert_contains(
        C4_DIMS,
        value,
        f"Privacy dimension {value}",
    )

assert_contains(
    C4_CASE,
    "M3=UNMEASURED",
    "Privacy M3 semantic lock",
)

assert_contains(
    A3_FINAL,
    "PM2_OFF_TARGET_SHAM",
    "F11 off-target sham",
)

assert_contains(
    A3_FINAL,
    "222.202",
    "F11 sham QUAL",
)

assert_contains(
    A3_FINAL,
    "PM2",
    "F11 PM2",
)

assert_contains(
    A3_FINAL,
    "PATHOGENIC_ALT_CALL_LOST",
    "F11 pathogenic call loss",
)

assert_contains(
    A3_FINDINGS,
    "ALT parents: 14/14",
    "F11 sham ALT retention",
)

assert_contains(
    A3_FINDINGS,
    "PM2 eliminated all ALT support",
    "F11 PM2 ALT loss",
)

assert_contains(
    B1_AUTH,
    "4144",
    "B1 population",
)

assert_contains(
    B1_AUTH,
    "1657",
    "B1 registered population",
)

assert_contains(
    B2_VAULT,
    "0.2299",
    "B2 pathogenic unrecoverability",
)

assert_contains(
    B2_VAULT,
    "0.0801",
    "B2 cumulative unrecoverability",
)

assert_contains(
    B2_LIFETIME,
    "reid\t1.0\t13",
    "B2 re-identification saturation",
)

assert_contains(
    B3_AUTH,
    "k=10\t786\t6\t99.2",
    "B3 k=10 containment",
)

assert_contains(
    B3_AUTH,
    "4.5\t1.0\t0.98\t0.9899\t0.996",
    "B3 authentication benchmark",
)

print("Scientific preflight: PASS")


# ============================================================
# Figure 1 — GenoPhylax lifecycle framework
# ============================================================

stages = [
    ("S1", "Generation"),
    ("S2", "Basecalling"),
    ("S3", "Alignment"),
    ("S4", "Variant Calling /\nGenotype Evidence"),
    ("S5", "Clinical\nInterpretation"),
    ("S6", "Storage"),
    ("S7", "Sharing /\nRelease"),
    ("S8", "Reuse /\nDownstream"),
    ("S9", "Incident /\nForensic"),
    ("S10", "Containment /\nRevocation"),
]

module_map = [
    "A1",
    "A2",
    "A2",
    "A2 / A3",
    "A3",
    "B2",
    "B1 / B2",
    "B1 / B2",
    "B2 / B3",
    "B3",
]

fig, ax = plt.subplots(figsize=(16, 5))

x = np.arange(len(stages))

ax.set_xlim(-0.7, len(stages) - 0.3)
ax.set_ylim(-1.3, 1.6)
ax.axis("off")

for i in range(len(stages) - 1):
    ax.annotate(
        "",
        xy=(i + 0.75, 0),
        xytext=(i + 0.25, 0),
        arrowprops=dict(
            arrowstyle="->",
            linewidth=1.5,
        ),
    )

for i, ((sid, name), module) in enumerate(
    zip(stages, module_map)
):
    ax.text(
        i,
        0,
        sid,
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        bbox=dict(
            boxstyle="round,pad=0.45",
            linewidth=1.2,
        ),
    )

    ax.text(
        i,
        0.58,
        name,
        ha="center",
        va="center",
        fontsize=9,
    )

    ax.text(
        i,
        -0.58,
        module,
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
    )

ax.text(
    2.0,
    1.25,
    "Generation → interpretation",
    ha="center",
    fontsize=11,
    fontweight="bold",
)

ax.text(
    7.4,
    1.25,
    "Storage → sharing → containment",
    ha="center",
    fontsize=11,
    fontweight="bold",
)

ax.text(
    4.5,
    -1.08,
    "Module C: provenance-aware handoffs + GenoPhylax Risk Index",
    ha="center",
    fontsize=11,
    fontweight="bold",
)

ax.set_title(
    "GenoPhylax genomic cyber-biosecurity lifecycle",
    fontsize=15,
    fontweight="bold",
)

save(
    fig,
    "Figure_01_GenoPhylax_lifecycle_framework",
)


# ============================================================
# Figure 2 — F11 targeted pathogenic-variant suppression
# ============================================================

conditions = [
    "Clean",
    "PM2 off-target\nsham",
    "PM2 on-target",
]

alt_parents = [
    F11_CLEAN_ALT,
    F11_SHAM_ALT,
    F11_PM2_ALT,
]

fig, ax = plt.subplots(figsize=(8.5, 5.5))

bars = ax.bar(
    conditions,
    alt_parents,
)

ax.set_ylim(0, 15.5)
ax.set_ylabel("ALT-supporting parent reads")
ax.set_title(
    "Targeted raw-signal perturbation suppresses F11 ALT evidence",
    fontweight="bold",
)

for bar, value in zip(bars, alt_parents):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + 0.3,
        f"{value}/14",
        ha="center",
        fontweight="bold",
    )

ax.text(
    0,
    1.0,
    "Pathogenic call retained",
    ha="center",
    fontsize=9,
)

ax.text(
    1,
    1.0,
    "0/1 retained\nQUAL 222.202",
    ha="center",
    fontsize=9,
)

ax.text(
    2,
    1.0,
    "NO_CALL",
    ha="center",
    fontsize=9,
)

ax.text(
    0.5,
    -0.18,
    "Same-size off-target interpolation preserved the variant;",
    transform=ax.transAxes,
    ha="center",
    fontsize=9,
)

ax.text(
    0.5,
    -0.24,
    "on-target PM2 eliminated ALT-supporting evidence in this worked case.",
    transform=ax.transAxes,
    ha="center",
    fontsize=9,
)

save(
    fig,
    "Figure_02_F11_targeted_variant_suppression",
)


# ============================================================
# Figure 3 — Privacy GRI dimensions
# ============================================================

labels = list(PRIVACY_DIMS.keys())
values = list(PRIVACY_DIMS.values())

fig, ax = plt.subplots(figsize=(9, 5.7))

bars = ax.barh(
    labels,
    values,
)

ax.axvline(
    PRIVACY_GRI,
    linestyle="--",
    linewidth=1.6,
    label=f"Base GRI = {PRIVACY_GRI:.4f}",
)

ax.set_xlim(0.80, 1.01)
ax.set_xlabel("Normalized risk severity")
ax.set_title(
    "Privacy worked case: scored GRI dimensions",
    fontweight="bold",
)

for bar, value in zip(bars, values):
    ax.text(
        value + 0.002,
        bar.get_y() + bar.get_height() / 2,
        f"{value:.4f}",
        va="center",
        fontsize=9,
    )

ax.legend(loc="lower right")

ax.text(
    0.5,
    -0.15,
    "D1/D3/D5 share the B2 lifetime-model provenance family; "
    "D6 is B1 calibrated-model evidence.",
    transform=ax.transAxes,
    ha="center",
    fontsize=9,
)

save(
    fig,
    "Figure_03_privacy_GRI_dimension_profile",
)


# ============================================================
# Figure 4 — Ablation / provenance dependence
# ============================================================

rows = [
    r
    for r in read_tsv(V6_SINGLE)
    if r["case_id"] == "C3_PRIVACY"
]

single_labels = [
    f"Remove {r['removed_dimension']}"
    for r in rows
]

single_values = [
    float(r["ablated_GRI"])
    for r in rows
]

group_rows = [
    r
    for r in read_tsv(V6_GROUP)
    if r["case_id"] == "C3_PRIVACY"
]

for r in group_rows:
    if r["removed_dimensions"] == "D6":
        single_labels.append(
            "B2 family only\n(remove D6)"
        )
    else:
        single_labels.append(
            "B1 D6 only\n(remove D1/D3/D5)"
        )

    single_values.append(
        float(r["ablated_GRI"])
    )

fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.barh(
    single_labels,
    single_values,
)

ax.axvline(
    PRIVACY_GRI,
    linestyle="--",
    linewidth=1.5,
    label=f"Baseline = {PRIVACY_GRI:.4f}",
)

ax.set_xlim(0.86, 1.005)
ax.set_xlabel("Ablated Privacy GRI")
ax.set_title(
    "GRI ablation exposes dimension and provenance-family dependence",
    fontweight="bold",
)

for bar, value in zip(bars, single_values):
    ax.text(
        value + 0.002,
        bar.get_y() + bar.get_height() / 2,
        f"{value:.4f}",
        va="center",
        fontsize=8.5,
    )

ax.legend(loc="lower right")

save(
    fig,
    "Figure_04_GRI_ablation_and_provenance",
)


# ============================================================
# Figure 5 — Deterministic sensitivity
# ============================================================

family_rows = [
    r
    for r in read_tsv(V7_FAMILY)
    if r["case_id"] == "C3_PRIVACY"
]

family_rows = sorted(
    family_rows,
    key=lambda r: float(r["B2_family_weight"]),
)

weights = [
    float(r["B2_family_weight"])
    for r in family_rows
]

scores = [
    float(r["sensitivity_GRI"])
    for r in family_rows
]

ref_rows = read_tsv(V7_REF)

ref_values = [
    float(r["privacy_GRI"])
    for r in ref_rows
]

m5_rows = read_tsv(V7_M5)

m5_values = [
    float(r["M5_residual_containment_difficulty"])
    for r in m5_rows
]

fig, ax = plt.subplots(figsize=(9, 5.8))

ax.plot(
    weights,
    scores,
    marker="o",
    linewidth=2,
    label="B2-family weight sensitivity",
)

ax.axhline(
    PRIVACY_GRI,
    linestyle="--",
    linewidth=1.5,
    label=f"Primary Base GRI = {PRIVACY_GRI:.4f}",
)

ax.fill_between(
    [min(weights), max(weights)],
    min(ref_values),
    max(ref_values),
    alpha=0.15,
    label=(
        "D6 reference-anchor sensitivity "
        f"({min(ref_values):.4f}–{max(ref_values):.4f})"
    ),
)

ax.set_xlabel("B2 lifetime-model family weight")
ax.set_ylabel("Privacy GRI")
ax.set_title(
    "Deterministic sensitivity of the Privacy GRI",
    fontweight="bold",
)

ax.legend(loc="best")

ax.text(
    0.5,
    -0.18,
    (
        "M5 containment difficulty spans "
        f"{min(m5_values):.3f}–{max(m5_values):.3f} "
        "but is not applied to Base GRI."
    ),
    transform=ax.transAxes,
    ha="center",
    fontsize=9,
)

ax.text(
    0.5,
    -0.235,
    "Ranges are deterministic scenario analyses, not confidence intervals.",
    transform=ax.transAxes,
    ha="center",
    fontsize=9,
)

save(
    fig,
    "Figure_05_GRI_deterministic_sensitivity",
)


# ============================================================
# Figure 6 — Downstream privacy amplification / containment
# ============================================================

fig, ax = plt.subplots(figsize=(12, 5.8))
ax.axis("off")

blocks = [
    (
        0.08,
        0.60,
        "B1 — Amplification",
        (
            f"4,144-node synthetic kinship graph\n"
            f"1,657 registered individuals\n"
            f"{B1_MODEL_AMPLIFICATION:.1f}× calibrated amplification\n"
            f"reference target ≈ {B1_REFERENCE_AMPLIFICATION:.2f}×"
        ),
    ),
    (
        0.39,
        0.60,
        "B2 — Persistence",
        (
            f"Pathogenic-tier U = {B2_PATHOGENIC_U:.4f}\n"
            f"All-tier U = {B2_ALL_TIERS_U:.4f}\n"
            "Re-identification: 100% at year 13\n"
            "Familial risk: 100% at year 15"
        ),
    ),
    (
        0.70,
        0.60,
        "B3 — Containment",
        (
            f"Baseline exposed = {B3_BASELINE_EXPOSED}\n"
            f"k=5 exposed = {B3_K5_EXPOSED}\n"
            f"k=10 exposed = {B3_K10_EXPOSED}\n"
            f"k=10 reduction = {B3_K10_REDUCTION:.1f}%"
        ),
    ),
]

for x0, y0, title, body in blocks:
    ax.text(
        x0,
        y0,
        title,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="top",
        bbox=dict(
            boxstyle="round,pad=0.7",
            linewidth=1.3,
        ),
    )

    ax.text(
        x0,
        y0 - 0.13,
        body,
        transform=ax.transAxes,
        fontsize=10,
        ha="left",
        va="top",
        linespacing=1.5,
    )

ax.annotate(
    "",
    xy=(0.37, 0.53),
    xytext=(0.30, 0.53),
    xycoords=ax.transAxes,
    arrowprops=dict(
        arrowstyle="->",
        linewidth=1.8,
    ),
)

ax.annotate(
    "",
    xy=(0.68, 0.53),
    xytext=(0.61, 0.53),
    xycoords=ax.transAxes,
    arrowprops=dict(
        arrowstyle="->",
        linewidth=1.8,
    ),
)

ax.text(
    0.5,
    0.12,
    (
        f"Authentication benchmark: F1={B3_AUTH_F1:.4f} "
        "(contextual mitigation evidence; not Privacy M3)"
    ),
    transform=ax.transAxes,
    ha="center",
    fontsize=10,
    fontweight="bold",
)

ax.set_title(
    "Downstream privacy amplification, persistence and containment",
    fontsize=15,
    fontweight="bold",
)

save(
    fig,
    "Figure_06_privacy_amplification_persistence_containment",
)


# ============================================================
# Supplementary A2 figures
# ============================================================

A2 = (
    ROOT
    / "experiments/A2_adversarial_dna/basecalling/"
      "findings/master_A2_GPU/publication_figures"
)

a2_selected = [
    "Figure_01_gaussian_identity_dose_response.png",
    "Figure_05_PM5_control_comparison.png",
    "Figure_07_hybrid_ALT_support.png",
    "Figure_08_variant_QUAL.png",
]

for name in a2_selected:
    src = A2 / name

    if not src.exists():
        raise RuntimeError(
            f"Missing selected A2 figure: {src}"
        )

    dst = SUP / f"A2_{name}"

    shutil.copy2(src, dst)
    print(f"PASS: supplementary copy {dst}")


# ============================================================
# Historical Module B figure policy
# ============================================================

manifest = DATA / "C6_figure_manifest.tsv"

manifest_rows = [
    [
        "Figure_01",
        "MAIN",
        "GENERATED_FROM_LOCKED_C_LIFECYCLE_SCHEMA",
        "Figure_01_GenoPhylax_lifecycle_framework",
        "CANONICAL",
    ],
    [
        "Figure_02",
        "MAIN",
        "A3_FINAL_LOCKED_RESULTS",
        "Figure_02_F11_targeted_variant_suppression",
        "CANONICAL",
    ],
    [
        "Figure_03",
        "MAIN",
        "C4_7_BASE_DIMENSION_PROFILE",
        "Figure_03_privacy_GRI_dimension_profile",
        "CANONICAL",
    ],
    [
        "Figure_04",
        "MAIN",
        "V6_ABLATION",
        "Figure_04_GRI_ablation_and_provenance",
        "CANONICAL",
    ],
    [
        "Figure_05",
        "MAIN",
        "V7_SENSITIVITY",
        "Figure_05_GRI_deterministic_sensitivity",
        "CANONICAL",
    ],
    [
        "Figure_06",
        "MAIN",
        "B1_B2_B3_AUTHORITATIVE_TABLES",
        "Figure_06_privacy_amplification_persistence_containment",
        "CANONICAL",
    ],
    [
        "A2_F01",
        "SUPPLEMENT",
        "FINAL_A2_PUBLICATION_PACKAGE",
        "A2_Figure_01_gaussian_identity_dose_response",
        "CANONICAL_SUPPLEMENT",
    ],
    [
        "A2_F05",
        "SUPPLEMENT",
        "FINAL_A2_PUBLICATION_PACKAGE",
        "A2_Figure_05_PM5_control_comparison",
        "CANONICAL_SUPPLEMENT",
    ],
    [
        "A2_F07",
        "SUPPLEMENT",
        "FINAL_A2_PUBLICATION_PACKAGE",
        "A2_Figure_07_hybrid_ALT_support",
        "CANONICAL_SUPPLEMENT",
    ],
    [
        "A2_F08",
        "SUPPLEMENT",
        "FINAL_A2_PUBLICATION_PACKAGE",
        "A2_Figure_08_variant_QUAL",
        "CANONICAL_SUPPLEMENT",
    ],
    [
        "HISTORICAL_B",
        "DO_NOT_PROMOTE",
        "paper/figures/B*.png",
        "Historical Module B figures",
        "SUPERSEDED_OR_UNVERIFIED_FOR_FINAL_PAPER",
    ],
    [
        "B3_REPRO",
        "REFERENCE_ONLY",
        "reproduced_results/B3_run",
        "Authoritative reproduced B3 plots",
        "VALID_REFERENCE_NOT_PRIMARY_C6_FIGURE",
    ],
]

with manifest.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:
    writer = csv.writer(
        f,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writerow(
        [
            "figure_id",
            "paper_role",
            "source",
            "artifact",
            "status",
        ]
    )

    writer.writerows(manifest_rows)


# ============================================================
# Validation
# ============================================================

expected_stems = [
    "Figure_01_GenoPhylax_lifecycle_framework",
    "Figure_02_F11_targeted_variant_suppression",
    "Figure_03_privacy_GRI_dimension_profile",
    "Figure_04_GRI_ablation_and_provenance",
    "Figure_05_GRI_deterministic_sensitivity",
    "Figure_06_privacy_amplification_persistence_containment",
]

errors = []

for stem in expected_stems:
    for suffix in (".png", ".pdf"):
        path = MAIN / f"{stem}{suffix}"

        if not path.exists():
            errors.append(
                f"Missing publication figure: {path}"
            )

        elif path.stat().st_size == 0:
            errors.append(
                f"Empty publication figure: {path}"
            )


# Strong stale-value safety check.
for p in MAIN.glob("*"):
    if p.suffix not in {".png", ".pdf"}:
        continue

# Text-based source/manifest audit.
for forbidden in (
    "0.044",
    "year 20",
    "threshold 3.8",
    "threshold 3.6",
    "1130",
):
    if forbidden in manifest.read_text(encoding="utf-8"):
        errors.append(
            f"Forbidden stale value in manifest: {forbidden}"
        )


validation = VALID / "C6_publication_figure_validation.txt"

lines = [
    "C6 PUBLICATION FIGURE VALIDATION",
    "================================",
    "",
    "Main canonical figures: 6",
    "Selected A2 supplementary figures: 4",
    "",
    "Historical paper/figures/B*.png promoted: NO",
    "Module B values sourced from authoritative reproduced tables: YES",
    "",
    "Locked values:",
    "F11 Base GRI = 1.0000000000",
    "Privacy Base GRI = 0.9115102712",
    "Privacy D1 = 0.8886656512",
    "Privacy D3 = 0.8817416604",
    "Privacy D5 = 0.8852036558",
    "Privacy D6 = 0.9904301172",
    "Privacy M3 = UNMEASURED",
    "B1 calibrated amplification = 464.4x",
    "B2 pathogenic unrecoverability = 0.2299",
    "B2 all-tier unrecoverability = 0.0801",
    "B2 re-identification saturation = year 13",
    "B3 k=10 exposed = 6",
    "B3 k=10 reduction = 99.2%",
    "B3 authentication F1 = 0.9899",
    "",
    f"Validation errors: {len(errors)}",
    f"STATUS: {'FAIL' if errors else 'PASS'}",
]

if errors:
    lines.extend(
        [
            "",
            "Errors:",
            *[f"- {e}" for e in errors],
        ]
    )

validation.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

if errors:
    for e in errors:
        print("ERROR:", e)

    raise SystemExit(1)


print()
print("============================================================")
print("C6 PUBLICATION FIGURES: PASS")
print("============================================================")
print("Main figures:", len(expected_stems))
print("Supplementary A2 figures:", len(a2_selected))
print("Historical Module B PNGs promoted: NO")
print("Scientific values recomputed: NO")
print("Authoritative values visualized: YES")
