import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# ═══════════════════════════════════════════════════════════════
# MODULE B2 — Lifetime Genomic Risk Model
#
# Models how genomic privacy risk evolves over a person's lifetime.
# Three compounding factors drive risk growth:
#
#   1. Database Growth     — more reference genomes = easier re-ID
#   2. Technology Decay    — sequencing costs drop = more adversaries
#   3. Inference Expansion — ML models extract more from same data
#
# GRI Dimension: D5 (Persistence Risk)
# Key insight: genomic data has a risk horizon of 50-80 years
# because the underlying biology never changes.
# ═══════════════════════════════════════════════════════════════

# ── Constants ─────────────────────────────────────────────────
CURRENT_YEAR      = 2025
BIRTH_YEAR        = 2025   # person whose risk we're modeling
LIFE_EXPECTANCY   = 80     # years
YEARS             = np.arange(0, LIFE_EXPECTANCY + 1)
CALENDAR_YEARS    = CURRENT_YEAR + YEARS

# ── Baseline risk parameters ──────────────────────────────────
BASELINE_REID_RISK       = 0.05   # 5% re-identification risk at time 0
BASELINE_DISEASE_RISK    = 0.10   # 10% disease inference risk at time 0
BASELINE_FAMILIAL_RISK   = 0.15   # 15% familial exposure risk at time 0


# ═══════════════════════════════════════════════════════════════
# 1. DATABASE GROWTH MODEL
# Public genomic databases double roughly every 3-4 years.
# More reference genomes = higher re-identification probability.
# Modeled as exponential growth with saturation.
# ═══════════════════════════════════════════════════════════════

def database_growth_factor(years, doubling_time=3.5, saturation=50.0):
    """
    Returns a multiplier representing database growth over time.
    Saturates at `saturation` x baseline (databases can't grow forever).
    """
    raw = 2 ** (years / doubling_time)
    return np.minimum(raw, saturation)


# ═══════════════════════════════════════════════════════════════
# 2. TECHNOLOGY DECAY MODEL
# Sequencing cost follows Moore's Law-like decline.
# Cheaper sequencing = more adversaries able to sequence = higher risk.
# ═══════════════════════════════════════════════════════════════

def technology_decay_factor(years, half_life=2.0, floor=0.001):
    """
    Models sequencing cost decay. Returns a risk amplification factor
    — as cost drops, adversary capability increases inversely.
    Cost halves every `half_life` years.
    Risk amplification = 1 / normalized_cost
    """
    cost = np.maximum(0.5 ** (years / half_life), floor)
    # Normalize: at year 0, cost=1, amplification=1
    amplification = 1.0 / cost
    return amplification


# ═══════════════════════════════════════════════════════════════
# 3. INFERENCE EXPANSION MODEL
# ML models extract increasingly more from the same genomic data.
# Phenotype prediction, disease inference, ancestry all improve.
# Modeled as sigmoid growth — slow start, rapid expansion, plateau.
# ═══════════════════════════════════════════════════════════════

def inference_expansion_factor(years, midpoint=20, steepness=0.2, max_factor=8.0):
    """
    Sigmoid growth model for ML inference capability expansion.
    At midpoint years, capability is at 50% of maximum.
    """
    sigmoid = 1.0 / (1.0 + np.exp(-steepness * (years - midpoint)))
    # Scale: starts at ~0.5 at year 0 (some inference already possible)
    factor = 1.0 + (max_factor - 1.0) * sigmoid
    return factor


# ═══════════════════════════════════════════════════════════════
# 4. COMPOSITE LIFETIME RISK
# Combines all three factors into per-dimension risk trajectories.
# Each dimension is capped at 1.0 (100% risk).
# ═══════════════════════════════════════════════════════════════

def compute_lifetime_risk(years):
    db_factor   = database_growth_factor(years)
    tech_factor = technology_decay_factor(years)
    inf_factor  = inference_expansion_factor(years)

    # Re-identification risk: driven by database growth + inference
    reid_risk = np.minimum(
        BASELINE_REID_RISK * db_factor * np.sqrt(inf_factor),
        1.0
    )

    # Disease inference risk: driven by inference expansion
    disease_risk = np.minimum(
        BASELINE_DISEASE_RISK * inf_factor,
        1.0
    )

    # Familial cascade risk: driven by database growth (more relatives enrolled)
    familial_risk = np.minimum(
        BASELINE_FAMILIAL_RISK * db_factor * 0.4,
        1.0
    )

    # Composite GRI D5 score (0-10)
    composite = (reid_risk + disease_risk + familial_risk) / 3.0
    d5_score  = np.minimum(composite * 10.0, 10.0)

    return {
        "reid"     : reid_risk,
        "disease"  : disease_risk,
        "familial" : familial_risk,
        "composite": composite,
        "d5_score" : d5_score,
        "db_factor": db_factor,
        "tech_factor": tech_factor,
        "inf_factor" : inf_factor,
    }


# ═══════════════════════════════════════════════════════════════
# 5. RISK HORIZON ANALYSIS
# At what age does each risk dimension cross critical thresholds?
# ═══════════════════════════════════════════════════════════════

def find_risk_horizons(risks, years, thresholds=[0.25, 0.5, 0.75, 1.0]):
    horizons = {}
    for dim in ["reid", "disease", "familial"]:
        horizons[dim] = {}
        for t in thresholds:
            crossings = np.where(risks[dim] >= t)[0]
            if len(crossings) > 0:
                horizons[dim][t] = int(years[crossings[0]])
            else:
                horizons[dim][t] = None
    return horizons


# ═══════════════════════════════════════════════════════════════
# 6. PLOT
# ═══════════════════════════════════════════════════════════════

def plot_lifetime_risk(years, calendar_years, risks, horizons):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Module B2 — Lifetime Genomic Risk Model",
                 fontsize=14, fontweight="bold", color="#0D1B2A")
    fig.patch.set_facecolor("#F1F5F9")

    C = {"reid": "#C0392B", "disease": "#D97706",
         "familial": "#6D28D9", "composite": "#0D1B2A",
         "d5": "#0D9488"}

    # ── Plot 1: Risk trajectories ──
    ax = axes[0, 0]
    ax.set_facecolor("white")
    ax.plot(years, risks["reid"],     color=C["reid"],     lw=2.5, label="Re-identification Risk")
    ax.plot(years, risks["disease"],  color=C["disease"],  lw=2.5, label="Disease Inference Risk")
    ax.plot(years, risks["familial"], color=C["familial"], lw=2.5, label="Familial Cascade Risk")
    ax.plot(years, risks["composite"],color=C["composite"],lw=2,
            linestyle="--", label="Composite Risk")
    ax.axhline(0.5, color="gray", linestyle=":", lw=1, alpha=0.7)
    ax.axhline(1.0, color="red",  linestyle=":", lw=1, alpha=0.5)
    ax.set_xlabel("Years After Data Collection", fontsize=10)
    ax.set_ylabel("Risk Probability", fontsize=10)
    ax.set_title("Lifetime Risk Trajectories", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)

    # ── Plot 2: GRI D5 Score over time ──
    ax = axes[0, 1]
    ax.set_facecolor("white")
    ax.fill_between(years, risks["d5_score"], alpha=0.3, color=C["d5"])
    ax.plot(years, risks["d5_score"], color=C["d5"], lw=2.5)
    # Severity bands
    bands = [(0,2,"#F0FDF4","Minimal"), (2,4,"#F0FDFA","Low"),
             (4,6,"#FEF3C7","Moderate"), (6,8,"#FEF2F2","High"),
             (8,10,"#FFF0EE","Critical")]
    for lo, hi, col, lbl in bands:
        ax.axhspan(lo, hi, alpha=0.2, color=col)
        ax.text(78, (lo+hi)/2, lbl, fontsize=7.5, color="#64748B",
                va="center", style="italic")
    ax.set_xlabel("Years After Data Collection", fontsize=10)
    ax.set_ylabel("GRI D5 Score (0-10)", fontsize=10)
    ax.set_title("GRI D5 — Persistence Risk Score Over Lifetime", fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 10.5)

    # ── Plot 3: Driving factors ──
    ax = axes[1, 0]
    ax.set_facecolor("white")
    ax2 = ax.twinx()
    ax.plot(years, np.minimum(risks["db_factor"], 50),
            color="#1B3A6B", lw=2, label="DB Growth (x)")
    ax.plot(years, risks["inf_factor"],
            color="#BE185D", lw=2, label="Inference Expansion (x)")
    ax2.plot(years, 1.0/np.maximum(risks["tech_factor"]/risks["tech_factor"].max(), 0.001),
             color="#D97706", lw=2, linestyle="--", label="Sequencing Cost (norm.)")
    ax.set_xlabel("Years After Data Collection", fontsize=10)
    ax.set_ylabel("Growth Multiplier (x)", fontsize=10)
    ax2.set_ylabel("Normalized Cost", fontsize=10, color="#D97706")
    ax.set_title("Risk Driving Factors Over Time", fontweight="bold")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8)
    ax.grid(True, alpha=0.3)

    # ── Plot 4: Risk horizon heatmap ──
    ax = axes[1, 1]
    ax.set_facecolor("white")
    dims       = ["Re-identification", "Disease Inference", "Familial Cascade"]
    dim_keys   = ["reid", "disease", "familial"]
    thresholds = [0.25, 0.5, 0.75, 1.0]
    matrix     = []
    for dk in dim_keys:
        row = []
        for t in thresholds:
            val = horizons[dk].get(t)
            row.append(val if val is not None else 80)
        matrix.append(row)
    matrix = np.array(matrix, dtype=float)
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto",
                   vmin=0, vmax=80)
    ax.set_xticks(range(len(thresholds)))
    ax.set_xticklabels([f"{int(t*100)}% risk" for t in thresholds], fontsize=9)
    ax.set_yticks(range(len(dims)))
    ax.set_yticklabels(dims, fontsize=9)
    ax.set_title("Risk Horizon — Years Until Threshold Crossed", fontweight="bold")
    for i in range(len(dims)):
        for j in range(len(thresholds)):
            val = int(matrix[i, j])
            label = f"Yr {val}" if val < 80 else "Never"
            ax.text(j, i, label, ha="center", va="center",
                    fontsize=9, fontweight="bold",
                    color="white" if matrix[i,j] < 30 else "black")
    plt.colorbar(im, ax=ax, label="Years until threshold")

    plt.tight_layout()
    plt.savefig("B2_lifetime_risk.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Plot saved as B2_lifetime_risk.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  Module B2 — Lifetime Genomic Risk Model")
    print("=" * 55)

    print("\nComputing lifetime risk trajectories...")
    risks = compute_lifetime_risk(YEARS)

    print("\nRisk at key milestones:")
    milestones = [0, 10, 20, 30, 50, 80]
    print(f"  {'Year':<6} {'Re-ID':>8} {'Disease':>10} {'Familial':>10} {'D5 Score':>10}")
    print("  " + "-" * 48)
    for m in milestones:
        idx = m
        print(f"  {m:<6} {risks['reid'][idx]:>8.3f} "
              f"{risks['disease'][idx]:>10.3f} "
              f"{risks['familial'][idx]:>10.3f} "
              f"{risks['d5_score'][idx]:>10.2f}")

    print("\nFinding risk horizons...")
    horizons = find_risk_horizons(risks, YEARS)
    print(f"\n  {'Dimension':<20} {'25% risk':>10} {'50% risk':>10} "
          f"{'75% risk':>10} {'100% risk':>10}")
    print("  " + "-" * 64)
    dim_names = {"reid": "Re-identification",
                 "disease": "Disease Inference",
                 "familial": "Familial Cascade"}
    for dk, dn in dim_names.items():
        row = horizons[dk]
        def fmt(v): return f"Yr {v}" if v is not None else "Never"
        print(f"  {dn:<20} {fmt(row[0.25]):>10} {fmt(row[0.5]):>10} "
              f"{fmt(row[0.75]):>10} {fmt(row[1.0]):>10}")

    print("\nGenerating plots...")
    plot_lifetime_risk(YEARS, CALENDAR_YEARS, risks, horizons)