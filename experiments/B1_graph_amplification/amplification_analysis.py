import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from graph_model import generate_kinship_graph, simulate_registration, simulate_breach, calibrate_against_23andme

# ═══════════════════════════════════════════════════════════════
# 1. AMPLIFICATION vs BREACH SIZE
# How does amplification factor change as more accounts are
# compromised? Smaller breaches = higher amplification ratio.
# ═══════════════════════════════════════════════════════════════

def analyze_breach_size_impact(G, registered, breach_fractions):
    results = []
    for frac in breach_fractions:
        n_comp = max(1, int(len(registered) * frac))
        r = simulate_breach(G, registered, n_comp)
        results.append({
            "fraction"     : frac,
            "n_compromised": r["n_compromised"],
            "n_exposed"    : r["n_exposed"],
            "amplification": r["amplification"],
        })
    return results


# ═══════════════════════════════════════════════════════════════
# 2. AMPLIFICATION vs REGISTRATION RATE
# How does platform adoption rate affect blast radius?
# Higher registration = more relatives in the graph = more exposure
# ═══════════════════════════════════════════════════════════════

def analyze_registration_impact(G, family_data, registration_rates, n_compromised_frac=0.001):
    results = []
    for rate in registration_rates:
        # Reset registration
        for n in G.nodes():
            G.nodes[n]["registered"] = False
        registered = simulate_registration(G, registration_rate=rate)
        n_comp = max(1, int(len(registered) * n_compromised_frac))
        r = simulate_breach(G, registered, n_comp)
        results.append({
            "registration_rate": rate,
            "n_registered"     : len(registered),
            "amplification"    : r["amplification"],
            "exposure_rate"    : r["exposure_rate"],
        })
    return results


# ═══════════════════════════════════════════════════════════════
# 3. HOP DEPTH ANALYSIS
# How many relationship hops does exposure travel?
# 1 hop = direct relatives; 2 hops = relatives of relatives; etc.
# ═══════════════════════════════════════════════════════════════

def analyze_hop_depth(G, registered, n_compromised, max_hops_range):
    results = []
    for hops in max_hops_range:
        r = simulate_breach(G, registered, n_compromised, max_hops=hops)
        results.append({
            "max_hops"     : hops,
            "n_exposed"    : r["n_exposed"],
            "amplification": r["amplification"],
        })
    return results


# ═══════════════════════════════════════════════════════════════
# 4. PLOT ALL RESULTS
# ═══════════════════════════════════════════════════════════════

def plot_results(breach_results, reg_results, hop_results, cal_result):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Module B1 — Graph Amplification Model",
                 fontsize=14, fontweight="bold", color="#0D1B2A")
    fig.patch.set_facecolor("#F1F5F9")

    colors = {"teal": "#0D9488", "navy": "#1B3A6B", "red": "#C0392B", "amber": "#D97706"}

    # ── Plot 1: Amplification vs Breach Size ──
    ax = axes[0, 0]
    ax.set_facecolor("white")
    fracs  = [r["fraction"] * 100 for r in breach_results]
    amps   = [r["amplification"] for r in breach_results]
    ax.plot(fracs, amps, color=colors["teal"], linewidth=2.5, marker="o", markersize=5)
    ax.set_xlabel("% of Registered Users Compromised", fontsize=10)
    ax.set_ylabel("Amplification Factor (x)", fontsize=10)
    ax.set_title("Amplification vs Breach Size", fontweight="bold", fontsize=11)
    ax.axhline(y=492.86, color=colors["red"], linestyle="--", linewidth=1.5,
               label="23andMe real (492x)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ── Plot 2: Amplification vs Registration Rate ──
    ax = axes[0, 1]
    ax.set_facecolor("white")
    rates = [r["registration_rate"] * 100 for r in reg_results]
    amps2 = [r["amplification"] for r in reg_results]
    ax.plot(rates, amps2, color=colors["navy"], linewidth=2.5, marker="s", markersize=5)
    ax.set_xlabel("DTC Platform Registration Rate (%)", fontsize=10)
    ax.set_ylabel("Amplification Factor (x)", fontsize=10)
    ax.set_title("Amplification vs Registration Rate", fontweight="bold", fontsize=11)
    ax.grid(True, alpha=0.3)

    # ── Plot 3: Exposure vs Hop Depth ──
    ax = axes[1, 0]
    ax.set_facecolor("white")
    hops    = [r["max_hops"] for r in hop_results]
    exposed = [r["n_exposed"] for r in hop_results]
    bars = ax.bar(hops, exposed, color=colors["amber"], edgecolor="white", linewidth=0.8)
    ax.set_xlabel("Max Relationship Hops", fontsize=10)
    ax.set_ylabel("Total Users Exposed", fontsize=10)
    ax.set_title("Exposure Spread by Hop Depth", fontweight="bold", fontsize=11)
    ax.set_xticks(hops)
    ax.set_xticklabels([f"{h} hop{'s' if h>1 else ''}" for h in hops])
    for bar, val in zip(bars, exposed):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(val), ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    # ── Plot 4: Calibration vs 23andMe ──
    ax = axes[1, 1]
    ax.set_facecolor("white")
    categories = ["Model\nAmplification", "23andMe Real\nAmplification"]
    values     = [cal_result["amplification"], cal_result["real_amplification"]]
    bar_colors = [colors["teal"], colors["red"]]
    bars = ax.bar(categories, values, color=bar_colors, edgecolor="white",
                  linewidth=0.8, width=0.5)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f"{val}x", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_ylabel("Amplification Factor (x)", fontsize=10)
    ax.set_title("Model Calibration vs 23andMe Breach", fontweight="bold", fontsize=11)
    ratio_patch = mpatches.Patch(color="none",
                                 label=f"Model/Real ratio: {cal_result['model_vs_real']}")
    ax.legend(handles=[ratio_patch], fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("B1_amplification_results.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Plot saved as B1_amplification_results.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*55)
    print("  Module B1 — Graph Amplification Analysis")
    print("  Project GenoPhylax")
    print("="*55)

    print("\n[1/4] Building kinship graph (1000 families)...")
    G, family_data = generate_kinship_graph(n_families=1000, avg_children=2, cousin_prob=0.3)
    print(f"      Nodes: {G.number_of_nodes():,}  |  Edges: {G.number_of_edges():,}")

    print("[2/4] Simulating 40% DTC registration...")
    registered = simulate_registration(G, registration_rate=0.4)
    print(f"      Registered: {len(registered):,}")

    print("[3/4] Running analyses...")

    breach_fractions = [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.2]
    breach_results = analyze_breach_size_impact(G, registered, breach_fractions)
    print("      ✓ Breach size impact")

    registration_rates = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    reg_results = analyze_registration_impact(G, family_data, registration_rates)
    print("      ✓ Registration rate impact")

    n_comp = max(1, int(len(registered) * 0.001))
    hop_results = analyze_hop_depth(G, registered, n_comp, max_hops_range=[1, 2, 3, 4, 5])
    print("      ✓ Hop depth analysis")

    cal_result = calibrate_against_23andme(G, registered)
    print("      ✓ 23andMe calibration")

    print("\n[4/4] Results summary:")
    print(f"      Calibration amplification : {cal_result['amplification']}x")
    print(f"      23andMe real amplification: {cal_result['real_amplification']}x")
    print(f"      Model/Real ratio           : {cal_result['model_vs_real']}")

    print("\n      Breach size breakdown:")
    for r in breach_results:
        print(f"        {r['fraction']*100:.2f}% compromised → {r['amplification']}x amplification")

    print("\n      Hop depth breakdown:")
    for r in hop_results:
        print(f"        {r['max_hops']} hops → {r['n_exposed']} exposed")

    print("\nGenerating plots...")
    plot_results(breach_results, reg_results, hop_results, cal_result)