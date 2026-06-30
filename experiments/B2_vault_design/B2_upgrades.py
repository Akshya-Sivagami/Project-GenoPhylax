import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),
                             '..', 'B1_graph_amplification'))
from graph_model import (generate_kinship_graph,
                          simulate_registration,
                          simulate_breach)

# ═══════════════════════════════════════════════════════════════
# B2 UPGRADE 1 — Lifetime Risk with Driver Annotations
# Shows WHICH factor dominates risk growth at each time period
# ═══════════════════════════════════════════════════════════════

CURRENT_YEAR = 2025
YEARS        = np.arange(0, 81)

BASELINE_REID_RISK     = 0.05
BASELINE_DISEASE_RISK  = 0.10
BASELINE_FAMILIAL_RISK = 0.15

def database_growth_factor(years, doubling_time=3.5, saturation=50.0):
    return np.minimum(2 ** (years / doubling_time), saturation)

def technology_decay_factor(years, half_life=2.0, floor=0.001):
    cost = np.maximum(0.5 ** (years / half_life), floor)
    return 1.0 / cost

def inference_expansion_factor(years, midpoint=20,
                                steepness=0.2, max_factor=8.0):
    sigmoid = 1.0 / (1.0 + np.exp(-steepness * (years - midpoint)))
    return 1.0 + (max_factor - 1.0) * sigmoid

def compute_lifetime_risk(years):
    db_factor   = database_growth_factor(years)
    tech_factor = technology_decay_factor(years)
    inf_factor  = inference_expansion_factor(years)

    reid_risk     = np.minimum(
        BASELINE_REID_RISK * db_factor * np.sqrt(inf_factor), 1.0)
    disease_risk  = np.minimum(
        BASELINE_DISEASE_RISK * inf_factor, 1.0)
    familial_risk = np.minimum(
        BASELINE_FAMILIAL_RISK * db_factor * 0.4, 1.0)
    composite     = (reid_risk + disease_risk + familial_risk) / 3.0
    d5_score      = np.minimum(composite * 10.0, 10.0)

    return {
        "reid": reid_risk, "disease": disease_risk,
        "familial": familial_risk, "composite": composite,
        "d5_score": d5_score, "db_factor": db_factor,
        "tech_factor": tech_factor, "inf_factor": inf_factor,
    }


def plot_lifetime_risk_with_drivers(years, risks):
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(
        "Module B2 — Lifetime Risk with Dominant Driver Annotations\n"
        "Project GenoPhylax",
        fontsize=13, fontweight="bold", color="#0D1B2A"
    )
    fig.patch.set_facecolor("#F1F5F9")

    C = {"reid": "#C0392B", "disease": "#D97706",
         "familial": "#6D28D9", "d5": "#0D9488"}

    # ── Plot 1: Risk curves with driver phase annotations ──
    ax = axes[0]
    ax.set_facecolor("white")
    ax.plot(years, risks["reid"],     color=C["reid"],
            lw=2.5, label="Re-identification Risk")
    ax.plot(years, risks["disease"],  color=C["disease"],
            lw=2.5, label="Disease Inference Risk")
    ax.plot(years, risks["familial"], color=C["familial"],
            lw=2.5, label="Familial Cascade Risk")

    # Driver phase annotations
    phases = [
        (0,  12,  "#EFF6FF", "Phase 1\nDatabase Growth\nDominates",     5),
        (12, 35,  "#FEF3C7", "Phase 2\nInference Expansion\nDominates", 22),
        (35, 80,  "#FEF2F2", "Phase 3\nSaturation +\nFamilial Cascade", 55),
    ]
    for x0, x1, col, label, tx in phases:
        ax.axvspan(x0, x1, alpha=0.18, color=col)
        ax.text(tx, 0.92, label, fontsize=8, color="#374151",
                ha="center", va="top", style="italic",
                bbox=dict(boxstyle="round,pad=0.2",
                          facecolor="white", alpha=0.7))

    ax.axhline(0.5, color="gray", linestyle=":", lw=1, alpha=0.6)
    ax.set_xlabel("Years After Data Collection", fontsize=10)
    ax.set_ylabel("Risk Probability", fontsize=10)
    ax.set_title("Lifetime Risk Trajectories — Mechanistic Drivers",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)

    # Driver annotations at specific milestones
    milestones = [
        (8,  risks["reid"][8],     "DB doubles\n3rd time",  "#1B3A6B"),
        (20, risks["disease"][20], "Inference\nmidpoint",   "#D97706"),
        (13, risks["familial"][13],"Familial\n50% risk",    "#6D28D9"),
    ]
    for mx, my, mlabel, mc in milestones:
        ax.annotate(mlabel,
                    xy=(mx, my),
                    xytext=(mx + 6, my - 0.12),
                    arrowprops=dict(arrowstyle="->",
                                   color=mc, lw=1.2),
                    fontsize=8, color=mc)

    # ── Plot 2: D5 score with driver contribution breakdown ──
    ax = axes[1]
    ax.set_facecolor("white")

    # Stacked area showing contribution of each risk dimension
    reid_contrib     = risks["reid"]     / 3.0 * 10.0
    disease_contrib  = risks["disease"]  / 3.0 * 10.0
    familial_contrib = risks["familial"] / 3.0 * 10.0

    ax.stackplot(years,
                 np.minimum(reid_contrib,     10/3),
                 np.minimum(disease_contrib,  10/3),
                 np.minimum(familial_contrib, 10/3),
                 labels=["Re-ID contribution",
                         "Disease Inference contribution",
                         "Familial Cascade contribution"],
                 colors=["#FECACA", "#FDE68A", "#DDD6FE"],
                 alpha=0.85)
    ax.plot(years, np.minimum(risks["d5_score"], 10),
            color="#0D1B2A", lw=2, linestyle="--",
            label="D5 Total Score")

    # Severity bands
    for lo, hi, lbl in [(0,2,"Minimal"),(2,4,"Low"),
                         (4,6,"Moderate"),(6,8,"High"),
                         (8,10,"Critical")]:
        ax.text(78, (lo+hi)/2, lbl, fontsize=7.5,
                color="#64748B", va="center", style="italic")

    ax.set_xlabel("Years After Data Collection", fontsize=10)
    ax.set_ylabel("GRI D5 Score Contribution", fontsize=10)
    ax.set_title("D5 Score — Dimensional Contribution Breakdown",
                 fontweight="bold")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_ylim(0, 10.5)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("B2_lifetime_risk_drivers.png", dpi=150,
                bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Saved: B2_lifetime_risk_drivers.png")


# ═══════════════════════════════════════════════════════════════
# B2 UPGRADE 2 — Risk vs Number of Enrolled Relatives
# Directly demonstrates collective genomic privacy thesis:
# your risk increases as more relatives enroll in the platform
# ═══════════════════════════════════════════════════════════════

def compute_relative_enrollment_risk(G, target_node,
                                     registered_nodes,
                                     n_relatives_enrolled,
                                     d6_amplification=464.4):
    """
    For a target individual, compute their D5+D6 composite risk
    as more of their biological relatives enroll on the platform.
    """
    # Get all graph neighbors within 3 hops of target
    relatives = set()
    frontier  = {target_node}
    for hop in range(3):
        next_f = set()
        for node in frontier:
            for nb in G.neighbors(node):
                if nb != target_node and nb not in relatives:
                    relatives.add(nb)
                    next_f.add(nb)
        frontier = next_f

    relatives = list(relatives)
    n_enroll  = min(n_relatives_enrolled, len(relatives))

    if n_enroll == 0:
        enrolled_relatives = []
    else:
        enrolled_relatives = relatives[:n_enroll]

    # D3 familial cascade risk scales with enrolled relatives
    d3_risk = min(0.15 + 0.016 * n_enroll, 1.0)

    # D6 amplification risk — more enrolled = larger graph component
    # Use log scaling since amplification saturates
    if n_enroll == 0:
        d6_component = 0.0
    else:
        amp_factor   = min(1.0 + n_enroll * 12.5, d6_amplification)
        d6_component = min(
            np.log10(amp_factor) / np.log10(d6_amplification), 1.0
        )

    # D1 re-identification risk — more relatives = easier kinship match
    d1_risk = min(0.05 + 0.008 * n_enroll, 1.0)

    # Composite D5 score (persistence × collective exposure)
    composite = (d1_risk + d3_risk + d6_component) / 3.0
    d5_score  = round(min(composite * 10.0, 10.0), 2)

    return {
        "n_relatives"  : n_enroll,
        "d1_risk"      : round(d1_risk, 4),
        "d3_risk"      : round(d3_risk, 4),
        "d6_component" : round(d6_component, 4),
        "composite"    : round(composite, 4),
        "d5_score"     : d5_score,
    }


def analyze_relative_enrollment(n_relatives_range):
    print("\nBuilding graph for enrollment analysis...")
    G, _        = generate_kinship_graph(
        n_families=600, avg_children=2, cousin_prob=0.20
    )
    registered  = simulate_registration(G, registration_rate=0.4)

    # Pick a representative target node (mid-degree)
    reg_sorted  = sorted(registered, key=lambda n: G.degree(n))
    target      = reg_sorted[len(reg_sorted) // 2]

    results = []
    for n in n_relatives_range:
        r = compute_relative_enrollment_risk(
            G, target, registered, n
        )
        results.append(r)

    return results


def plot_relative_enrollment(results):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "Module B2 — Collective Privacy: Risk vs Enrolled Relatives\n",
        fontsize=13, fontweight="bold", color="#0D1B2A"
    )
    fig.patch.set_facecolor("#F1F5F9")

    n_rels  = [r["n_relatives"]  for r in results]
    d5s     = [r["d5_score"]     for r in results]
    d1s     = [r["d1_risk"]      for r in results]
    d3s     = [r["d3_risk"]      for r in results]
    d6s     = [r["d6_component"] for r in results]

    # ── Plot 1: D5 score vs enrolled relatives ──
    ax = axes[0]
    ax.set_facecolor("white")
    ax.plot(n_rels, d5s, color="#0D9488", lw=2.5,
            marker="o", markersize=5)
    ax.fill_between(n_rels, d5s, alpha=0.2, color="#0D9488")

    # Severity bands
    bands = [(0,2,"#F0FDF4","Minimal"), (2,4,"#F0FDFA","Low"),
             (4,6,"#FEF3C7","Moderate"), (6,8,"#FEF2F2","High"),
             (8,10,"#FFF0EE","Critical")]
    for lo, hi, col, lbl in bands:
        ax.axhspan(lo, hi, alpha=0.2, color=col)
        ax.text(95, (lo+hi)/2, lbl, fontsize=8,
                color="#64748B", va="center", style="italic")

    # Annotate key thresholds
    for threshold, label in [(4.0, "Moderate"), (6.0, "High"),
                              (8.0, "Critical")]:
        crossings = [i for i, d in enumerate(d5s) if d >= threshold]
        if crossings:
            nx_val = n_rels[crossings[0]]
            ax.axvline(nx_val, color="gray", linestyle=":",
                       lw=1, alpha=0.7)
            ax.text(nx_val + 1, threshold + 0.15,
                    f"{label}\n@ {nx_val} relatives",
                    fontsize=7.5, color="#374151")

    ax.set_xlabel("Number of Biological Relatives Enrolled",
                  fontsize=10)
    ax.set_ylabel("GRI D5 Score (0-10)", fontsize=10)
    ax.set_title("Individual Risk Grows with Relative Enrollment\n"
                 "(Collective Privacy Effect)",
                 fontweight="bold")
    ax.set_ylim(0, 10.5)
    ax.set_xlim(0, max(n_rels) + 5)
    ax.grid(True, alpha=0.3)

    # ── Plot 2: Component breakdown ──
    ax = axes[1]
    ax.set_facecolor("white")
    ax.plot(n_rels, d1s, color="#C0392B", lw=2,
            label="D1 Re-identification Risk", marker="s",
            markersize=4)
    ax.plot(n_rels, d3s, color="#6D28D9", lw=2,
            label="D3 Familial Cascade Risk", marker="^",
            markersize=4)
    ax.plot(n_rels, d6s, color="#D97706", lw=2,
            label="D6 Amplification Component", marker="o",
            markersize=4)
    ax.axhline(0.5, color="gray", linestyle=":",
               lw=1, alpha=0.6, label="50% risk threshold")
    ax.set_xlabel("Number of Biological Relatives Enrolled",
                  fontsize=10)
    ax.set_ylabel("Risk Score (0-1)", fontsize=10)
    ax.set_title("Risk Dimension Breakdown vs Enrolled Relatives",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("B2_collective_privacy.png", dpi=150,
                bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Saved: B2_collective_privacy.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Module B2 Upgrades")
    print("  1. Lifetime Risk with Driver Annotations")
    print("  2. Collective Privacy — Risk vs Enrolled Relatives")
    print("=" * 60)

    print("\n[1/2] Generating lifetime risk with driver annotations...")
    risks = compute_lifetime_risk(YEARS)
    plot_lifetime_risk_with_drivers(YEARS, risks)

    print("\n[2/2] Analyzing relative enrollment impact...")
    n_relatives_range = list(range(0, 101, 5))
    enrollment_results = analyze_relative_enrollment(
        n_relatives_range
    )

    print(f"\n  {'Relatives':>10} {'D1':>8} {'D3':>8} "
          f"{'D6':>8} {'D5 Score':>10}")
    print("  " + "-" * 48)
    for r in enrollment_results:
        print(f"  {r['n_relatives']:>10} {r['d1_risk']:>8.4f} "
              f"{r['d3_risk']:>8.4f} {r['d6_component']:>8.4f} "
              f"{r['d5_score']:>10.2f}")

    plot_relative_enrollment(enrollment_results)
    print("\nAll B2 upgrades complete.")