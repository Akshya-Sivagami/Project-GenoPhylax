import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from graph_model import generate_kinship_graph, simulate_registration, simulate_breach

# ═══════════════════════════════════════════════════════════════
# GRI D6 — Amplification Risk Scoring
#
# D6 measures how much a platform's architecture multiplies
# exposure beyond the initially compromised accounts.
#
# Scoring formula:
#   Raw score = log10(amplification_factor) / log10(max_possible)
#   Normalized to 0-10 scale
#
# Thresholds (calibrated against 23andMe ground truth):
#   0-2   : Minimal   — isolated platform, no kinship features
#   2-4   : Low       — limited relative matching
#   4-6   : Moderate  — partial kinship graph exposure
#   6-8   : High      — active relative matching features
#   8-10  : Critical  — dense kinship graph, DTC-scale exposure
# ═══════════════════════════════════════════════════════════════

MAX_AMP    = 1000.0   # theoretical max amplification for normalization
REAL_23AME = 492.86   # ground truth reference

def compute_d6_score(amplification_factor, max_amp=MAX_AMP):
    """
    Convert raw amplification factor to a 0-10 GRI D6 score.
    Uses log10 scaling since amplification spans orders of magnitude.
    """
    if amplification_factor <= 1.0:
        return 0.0
    raw   = np.log10(amplification_factor) / np.log10(max_amp)
    score = round(min(raw * 10, 10.0), 2)
    return score


def get_severity_label(score):
    if score < 2:   return "Minimal",  "#15803D"
    if score < 4:   return "Low",      "#0D9488"
    if score < 6:   return "Moderate", "#D97706"
    if score < 8:   return "High",     "#C0392B"
    return               "Critical",  "#7C2D12"


# ═══════════════════════════════════════════════════════════════
# SCENARIO DEFINITIONS
# Six representative genomic platform scenarios evaluated
# against the D6 scoring rubric
# ═══════════════════════════════════════════════════════════════

SCENARIOS = [
    {
        "name"        : "Isolated Research DB",
        "description" : "No kinship features; records not linked to relatives",
        "cousin_prob" : 0.0,
        "reg_rate"    : 0.1,
        "breach_frac" : 0.01,
        "max_hops"    : 1,
    },
    {
        "name"        : "Hospital EHR System",
        "description" : "Clinical genomic records; limited family linkage",
        "cousin_prob" : 0.02,
        "reg_rate"    : 0.2,
        "breach_frac" : 0.005,
        "max_hops"    : 1,
    },
    {
        "name"        : "Research Biobank",
        "description" : "Population study; some family enrollment",
        "cousin_prob" : 0.05,
        "reg_rate"    : 0.3,
        "breach_frac" : 0.001,
        "max_hops"    : 2,
    },
    {
        "name"        : "Regional DTC Platform",
        "description" : "Consumer genetics; basic relative matching",
        "cousin_prob" : 0.10,
        "reg_rate"    : 0.4,
        "breach_frac" : 0.001,
        "max_hops"    : 2,
    },
    {
        "name"        : "National DTC Platform",
        "description" : "Large-scale consumer genetics; active DNA relatives",
        "cousin_prob" : 0.20,
        "reg_rate"    : 0.5,
        "breach_frac" : 0.001,
        "max_hops"    : 3,
    },
    {
        "name"        : "23andMe-Scale Platform",
        "description" : "Global DTC; dense kinship graph; DNA Relatives feature",
        "cousin_prob" : 0.20,
        "reg_rate"    : 0.6,
        "breach_frac" : 0.001,
        "max_hops"    : 3,
    },
]


def evaluate_scenarios():
    results = []

    print(f"\n{'Scenario':<28} {'Amp Factor':>12} {'D6 Score':>10} {'Severity':>10}")
    print("-" * 65)

    for sc in SCENARIOS:
        G, _ = generate_kinship_graph(
            n_families=800,
            avg_children=2,
            cousin_prob=sc["cousin_prob"]
        )
        registered = simulate_registration(G, registration_rate=sc["reg_rate"])

        # Patch: simulate_registration takes registration_rate
        for n in G.nodes():
            G.nodes[n]["registered"] = False
        n_reg = int(G.number_of_nodes() * sc["reg_rate"])
        import random
        reg_nodes = random.sample(list(G.nodes()), n_reg)
        for n in reg_nodes:
            G.nodes[n]["registered"] = True

        n_comp = max(1, int(n_reg * sc["breach_frac"]))
        r = simulate_breach(G, reg_nodes, n_comp, max_hops=sc["max_hops"])

        d6    = compute_d6_score(r["amplification"])
        label, color = get_severity_label(d6)

        results.append({
            "name"         : sc["name"],
            "description"  : sc["description"],
            "amplification": r["amplification"],
            "d6_score"     : d6,
            "severity"     : label,
            "color"        : color,
            "n_compromised": r["n_compromised"],
            "n_exposed"    : r["n_exposed"],
        })

        print(f"{sc['name']:<28} {r['amplification']:>12.2f} {d6:>10.2f} {label:>10}")

    # 23andMe reference
    ref_d6 = compute_d6_score(REAL_23AME)
    ref_label, _ = get_severity_label(ref_d6)
    print(f"\n{'23andMe (real breach)':<28} {REAL_23AME:>12.2f} "
          f"{ref_d6:>10.2f} {ref_label:>10}  ← ground truth")

    return results, ref_d6


def plot_d6_scores(results, ref_d6):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("GRI Dimension D6 — Amplification Risk Scores",
                 fontsize=13, fontweight="bold", color="#0D1B2A")
    fig.patch.set_facecolor("#F1F5F9")

    names  = [r["name"] for r in results]
    scores = [r["d6_score"] for r in results]
    colors = [r["color"] for r in results]

    # Plot 1: D6 Score per scenario
    ax = axes[0]
    ax.set_facecolor("white")
    bars = ax.barh(names, scores, color=colors, edgecolor="white", height=0.6)
    ax.axvline(x=ref_d6, color="#1B3A6B", linestyle="--", linewidth=1.8,
               label=f"23andMe ref ({ref_d6})")
    for bar, val in zip(bars, scores):
        ax.text(val + 0.05, bar.get_y() + bar.get_height()/2,
                f"{val}", va="center", fontsize=9, fontweight="bold")
    ax.set_xlabel("GRI D6 Score (0-10)", fontsize=10)
    ax.set_title("D6 Score by Platform Scenario", fontweight="bold")
    ax.set_xlim(0, 11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="x")

    # Severity band backgrounds
    band_colors = ["#F0FDF4", "#F0FDFA", "#FEF3C7", "#FEF2F2", "#FFF0EE"]
    bands = [(0,2), (2,4), (4,6), (6,8), (8,10)]
    labels_b = ["Minimal", "Low", "Moderate", "High", "Critical"]
    for (lo, hi), bc, lb in zip(bands, band_colors, labels_b):
        ax.axvspan(lo, hi, alpha=0.25, color=bc)
        ax.text((lo+hi)/2, -0.7, lb, ha="center", fontsize=7.5,
                color="#64748B", style="italic")

    # Plot 2: Amplification factor per scenario
    ax = axes[1]
    ax.set_facecolor("white")
    amps = [r["amplification"] for r in results]
    bars = ax.barh(names, amps, color=colors, edgecolor="white", height=0.6)
    ax.axvline(x=REAL_23AME, color="#1B3A6B", linestyle="--", linewidth=1.8,
               label=f"23andMe real ({REAL_23AME}x)")
    for bar, val in zip(bars, amps):
        ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                f"{val}x", va="center", fontsize=9)
    ax.set_xlabel("Amplification Factor (x)", fontsize=10)
    ax.set_title("Raw Amplification by Platform Scenario", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="x")

    # Legend for severity
    patches = [
        mpatches.Patch(color="#15803D", label="Minimal (0-2)"),
        mpatches.Patch(color="#0D9488", label="Low (2-4)"),
        mpatches.Patch(color="#D97706", label="Moderate (4-6)"),
        mpatches.Patch(color="#C0392B", label="High (6-8)"),
        mpatches.Patch(color="#7C2D12", label="Critical (8-10)"),
    ]
    fig.legend(handles=patches, loc="lower center", ncol=5,
               fontsize=9, title="D6 Severity Levels", title_fontsize=9,
               bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout()
    plt.savefig("B1_gri_d6_scores.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Plot saved as B1_gri_d6_scores.png")


if __name__ == "__main__":
    print("=" * 65)
    print("  GRI Dimension D6 — Amplification Risk Scoring")
    print("  Calibrated against 23andMe breach ground truth")
    print("=" * 65)

    results, ref_d6 = evaluate_scenarios()

    print(f"\n23andMe reference D6 score: {ref_d6}")
    print("\nGenerating D6 score plots...")
    plot_d6_scores(results, ref_d6)

    print("\n" + "=" * 65)
    print("  D6 Scoring Summary")
    print("=" * 65)
    for r in results:
        print(f"  {r['name']:<28} D6={r['d6_score']:>5}  [{r['severity']}]")
    print(f"\n  23andMe ground truth         D6={ref_d6:>5}  [reference]")