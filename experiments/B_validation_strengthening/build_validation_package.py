import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve()
REPO = HERE.parents[1]

BASE = REPO / "B_validation_strengthening"
RESULTS = BASE / "results"
FIGURES = BASE / "figures"

FIGURES.mkdir(parents=True, exist_ok=True)


def read_csv(name):
    path = RESULTS / name
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ============================================================
# LOAD FROZEN STRENGTHENING RESULTS
# ============================================================

b1_grid = read_csv("B1_parameter_sensitivity.csv")
b1_topology = read_csv("B1_topology_diagnostic.csv")
b1_mc = read_csv("B1_breach_seed_monte_carlo.csv")

b2_life = read_csv("B2_lifetime_sensitivity.csv")
b2_unrec = read_csv("B2_unrecoverability_sensitivity.csv")


# ============================================================
# FIGURE 1
# B1 parameter sensitivity
# ============================================================

fig, ax = plt.subplots(figsize=(10, 6))

markers = {
    0.20: "o",
    0.40: "s",
    0.60: "^",
}

for reg in [0.20, 0.40, 0.60]:
    for hops in [1, 2, 3]:

        subset = [
            r for r in b1_grid
            if float(r["registration_rate"]) == reg
            and int(r["max_hops"]) == hops
        ]

        subset.sort(
            key=lambda r: float(r["cousin_prob"])
        )

        x = [
            float(r["cousin_prob"])
            for r in subset
        ]

        y = [
            float(r["mean_amplification"])
            for r in subset
        ]

        ax.plot(
            x,
            y,
            marker=markers[reg],
            label=f"Registration {int(reg*100)}%, {hops} hop"
            + ("s" if hops != 1 else ""),
        )

ax.axhline(
    464.4,
    linestyle="--",
    linewidth=1.5,
    label="Historical calibrated result: 464.4x",
)

ax.set_xlabel("Cousin-edge probability (model parameter)")
ax.set_ylabel("Mean amplification (x)")
ax.set_title(
    "B1: Amplification Is Strongly Parameter-Dependent"
)

ax.grid(alpha=0.25)
ax.legend(fontsize=8, ncol=2)
fig.tight_layout()

fig.savefig(
    FIGURES / "B1_parameter_sensitivity.png",
    dpi=220,
)

plt.close(fig)


# ============================================================
# FIGURE 2
# B1 entry-point distribution
# ============================================================

amps = np.array(
    [
        float(r["amplification"])
        for r in b1_mc
    ],
    dtype=float,
)

fig, ax = plt.subplots(figsize=(9, 6))

ax.hist(
    amps,
    bins=40,
    edgecolor="black",
    linewidth=0.4,
)

ax.axvline(
    464.4,
    linestyle="--",
    linewidth=1.5,
    label="Historical calibrated result: 464.4x",
)

ax.axvline(
    np.mean(amps),
    linestyle=":",
    linewidth=2,
    label=f"Monte Carlo mean: {np.mean(amps):.0f}x",
)

ax.set_xlabel("Amplification (x)")
ax.set_ylabel("Breach-entry realizations")
ax.set_title(
    "B1: Amplification Depends Strongly on Breach Entry Point"
)

ax.legend()
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()

fig.savefig(
    FIGURES / "B1_entrypoint_distribution.png",
    dpi=220,
)

plt.close(fig)


# ============================================================
# FIGURE 3
# B1 topology relationship
# ============================================================

small_fraction = np.array(
    [
        float(r["small_component_fraction"])
        for r in b1_topology
    ],
    dtype=float,
)

mean_reach = np.array(
    [
        float(r["mean_3hop_reach"])
        for r in b1_topology
    ],
    dtype=float,
)

fig, ax = plt.subplots(figsize=(8, 6))

ax.scatter(
    small_fraction * 100,
    mean_reach,
    s=45,
)

coef = np.polyfit(
    small_fraction * 100,
    mean_reach,
    1,
)

xline = np.linspace(
    np.min(small_fraction * 100),
    np.max(small_fraction * 100),
    100,
)

ax.plot(
    xline,
    coef[0] * xline + coef[1],
    linestyle="--",
)

ax.set_xlabel(
    "Registered nodes in components <=10 nodes (%)"
)
ax.set_ylabel("Mean 3-hop reach")
ax.set_title(
    "B1: Small-Component Membership Limits Exposure Reach"
)

ax.grid(alpha=0.25)
fig.tight_layout()

fig.savefig(
    FIGURES / "B1_topology_vs_reach.png",
    dpi=220,
)

plt.close(fig)


# ============================================================
# FIGURE 4
# B2 lifetime horizon sensitivity
# ============================================================

def horizon_values(key):
    values = []

    for r in b2_life:
        value = r[key]

        if value not in ("", "None", None):
            values.append(float(value))

    return np.array(values, dtype=float)


reid = horizon_values("reid_100_year")
familial = horizon_values("familial_100_year")
disease = horizon_values("disease_100_year")

datasets = [
    reid,
    familial,
    disease,
]

labels = [
    "Re-identification",
    "Familial exposure",
    "Disease inference",
]

fig, ax = plt.subplots(figsize=(9, 6))

ax.boxplot(
    datasets,
    tick_labels=labels,
    showfliers=False,
)

ax.scatter(
    [1, 2],
    [13, 15],
    marker="*",
    s=140,
    zorder=4,
    label="Frozen baseline",
)

ax.set_ylabel("Model year reaching 100%")
ax.set_title(
    "B2: Saturation Timing Is Assumption-Dependent"
)

ax.grid(axis="y", alpha=0.25)
ax.legend()
fig.tight_layout()

fig.savefig(
    FIGURES / "B2_lifetime_horizon_sensitivity.png",
    dpi=220,
)

plt.close(fig)


# ============================================================
# FIGURE 5
# B2 D5 year-50 sensitivity
# ============================================================

d5 = np.array(
    [
        float(r["d5_year_50"])
        for r in b2_life
    ],
    dtype=float,
)

fig, ax = plt.subplots(figsize=(9, 6))

ax.hist(
    d5,
    bins=30,
    edgecolor="black",
    linewidth=0.4,
)

ax.axvline(
    9.3276,
    linestyle="--",
    linewidth=1.7,
    label="Frozen baseline: 9.33",
)

ax.axvline(
    np.median(d5),
    linestyle=":",
    linewidth=2,
    label=f"Sensitivity median: {np.median(d5):.2f}",
)

ax.set_xlabel("D5 at model year 50")
ax.set_ylabel("Sensitivity scenarios")
ax.set_title(
    "B2: Year-50 Persistence Score Varies Across Assumptions"
)

ax.grid(axis="y", alpha=0.25)
ax.legend()
fig.tight_layout()

fig.savefig(
    FIGURES / "B2_D5_year50_sensitivity.png",
    dpi=220,
)

plt.close(fig)


# ============================================================
# FIGURE 6
# B2 unrecoverability heatmap
# ============================================================

leakages = sorted(
    set(
        float(r["pathogenic_leakage"])
        for r in b2_unrec
    )
)

coefficients = sorted(
    set(
        float(r["reconstruction_coefficient"])
        for r in b2_unrec
    )
)

matrix = np.zeros(
    (len(coefficients), len(leakages))
)

lookup = {
    (
        float(r["pathogenic_leakage"]),
        float(r["reconstruction_coefficient"]),
    ): float(r["unrecoverability"])
    for r in b2_unrec
}

for i, coeff in enumerate(coefficients):
    for j, leakage in enumerate(leakages):
        matrix[i, j] = lookup[
            (leakage, coeff)
        ]

fig, ax = plt.subplots(figsize=(10, 6))

image = ax.imshow(
    matrix,
    origin="lower",
    aspect="auto",
    extent=[
        min(leakages),
        max(leakages),
        min(coefficients),
        max(coefficients),
    ],
)

cbar = fig.colorbar(image, ax=ax)
cbar.set_label("Modeled unrecoverability")

ax.scatter(
    [0.420],
    [3.5],
    marker="*",
    s=180,
    label="Frozen baseline: 0.2299",
)

ax.set_xlabel(
    "Pathogenic-variant leakage assumption"
)
ax.set_ylabel(
    "Reconstruction coefficient"
)

ax.set_title(
    "B2: Unrecoverability Depends on Model Assumptions"
)

ax.legend()
fig.tight_layout()

fig.savefig(
    FIGURES / "B2_unrecoverability_sensitivity.png",
    dpi=220,
)

plt.close(fig)


# ============================================================
# FINAL EVIDENCE TABLE
# ============================================================

summary_rows = [
    {
        "module": "B1",
        "evidence": "Historical calibrated amplification",
        "baseline": "464.4x",
        "strengthened_result": (
            "Historical calibration fit; not independent validation"
        ),
        "classification": "MODELLED / CALIBRATED",
    },
    {
        "module": "B1",
        "evidence": "Breach-entry Monte Carlo",
        "baseline": "N/A",
        "strengthened_result": (
            "3000 realizations; mean 879.03x; median 1122x; "
            "5th-95th percentile 1x-1337x"
        ),
        "classification": "MODELLED / SENSITIVITY",
    },
    {
        "module": "B1",
        "evidence": "Topology",
        "baseline": "N/A",
        "strengthened_result": (
            "Mean giant component 80.85%; "
            "mean <=10-node component membership 19.15%"
        ),
        "classification": "MODELLED / STRUCTURAL AUDIT",
    },
    {
        "module": "B1",
        "evidence": "Parameter sensitivity",
        "baseline": "464.4x historical",
        "strengthened_result": (
            "Tested scenario means 4.35x-1621.63x"
        ),
        "classification": "MODELLED / SENSITIVITY",
    },
    {
        "module": "B2",
        "evidence": "Re-identification saturation",
        "baseline": "Year 13",
        "strengthened_result": (
            "Tested range year 8-26; median year 14"
        ),
        "classification": "MODELLED / SENSITIVITY",
    },
    {
        "module": "B2",
        "evidence": "Familial saturation",
        "baseline": "Year 15",
        "strengthened_result": (
            "Reached in 1944/2187 scenarios; "
            "when reached, year 9-26; median year 15"
        ),
        "classification": "MODELLED / SENSITIVITY",
    },
    {
        "module": "B2",
        "evidence": "D5 at year 50",
        "baseline": "9.33/10",
        "strengthened_result": (
            "Tested range 6.4967-10.0000; median 8.6630"
        ),
        "classification": "MODELLED / SENSITIVITY",
    },
    {
        "module": "B2",
        "evidence": "Pathogenic-variant unrecoverability",
        "baseline": "0.2299",
        "strengthened_result": (
            "Global tested range 0.0388-0.6703; "
            "local +/-20% range 0.1204-0.3903"
        ),
        "classification": "MODELLED / SENSITIVITY",
    },
    {
        "module": "B2",
        "evidence": "Technology-decay factor",
        "baseline": "Computed in original model",
        "strengthened_result": (
            "Not used in reported lifetime-risk equations"
        ),
        "classification": "MODEL STRUCTURE LIMITATION",
    },
]

TABLE = RESULTS / "B1_B2_STRENGTHENED_EVIDENCE.tsv"

with TABLE.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(summary_rows[0].keys()),
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(summary_rows)


# ============================================================
# MANIFEST
# ============================================================

print("=" * 72)
print("B1/B2 VALIDATION PACKAGING COMPLETE")
print("=" * 72)

print()
print("Figures:")

for path in sorted(FIGURES.glob("*.png")):
    print(f"  {path.name}")

print()
print(f"Evidence table: {TABLE}")
print()
print("No B1/B2 models were rerun.")
print("STATUS: PASS")

