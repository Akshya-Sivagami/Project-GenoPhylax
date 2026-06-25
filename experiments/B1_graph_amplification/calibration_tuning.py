import numpy as np
import matplotlib.pyplot as plt
from graph_model import generate_kinship_graph, simulate_registration, calibrate_against_23andme

# ═══════════════════════════════════════════════════════════════
# CALIBRATION TUNING
# Sweeps cousin_prob values to find which one produces an
# amplification factor closest to the real 23andMe value (492.86x)
# ═══════════════════════════════════════════════════════════════

TARGET_AMPLIFICATION = 492.86
N_RUNS_PER_PARAM = 5  # average over multiple runs to reduce randomness

def tune_cousin_probability():
    cousin_probs = [0.01, 0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30]
    results = []

    print(f"{'Cousin Prob':>12} | {'Avg Amplification':>18} | {'Ratio to Real':>14} | {'Delta':>10}")
    print("-" * 62)

    for cp in cousin_probs:
        run_amps = []
        for run in range(N_RUNS_PER_PARAM):
            G, family_data = generate_kinship_graph(
                n_families=1000, avg_children=2, cousin_prob=cp
            )
            registered = simulate_registration(G, registration_rate=0.4)
            cal = calibrate_against_23andme(G, registered)
            run_amps.append(cal["amplification"])

        avg_amp = round(np.mean(run_amps), 2)
        ratio   = round(avg_amp / TARGET_AMPLIFICATION, 4)
        delta   = round(abs(avg_amp - TARGET_AMPLIFICATION), 2)

        results.append({
            "cousin_prob"  : cp,
            "avg_amp"      : avg_amp,
            "ratio"        : ratio,
            "delta"        : delta,
        })

        marker = " ◄ best so far" if delta == min(r["delta"] for r in results) else ""
        print(f"{cp:>12.2f} | {avg_amp:>18.2f} | {ratio:>14.4f} | {delta:>10.2f}{marker}")

    # Find best match
    best = min(results, key=lambda r: r["delta"])
    print(f"\n{'='*62}")
    print(f"  Best cousin_prob : {best['cousin_prob']}")
    print(f"  Avg amplification: {best['avg_amp']}x")
    print(f"  Target           : {TARGET_AMPLIFICATION}x")
    print(f"  Delta            : {best['delta']}")
    print(f"{'='*62}")

    return results, best


def plot_tuning(results):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Module B1 — Calibration Tuning",
                 fontsize=13, fontweight="bold", color="#0D1B2A")
    fig.patch.set_facecolor("#F1F5F9")

    probs = [r["cousin_prob"] for r in results]
    amps  = [r["avg_amp"] for r in results]
    best  = min(results, key=lambda r: r["delta"])

    # Plot 1: Amplification vs cousin_prob
    ax = axes[0]
    ax.set_facecolor("white")
    ax.plot(probs, amps, color="#0D9488", linewidth=2.5, marker="o", markersize=7)
    ax.axhline(y=TARGET_AMPLIFICATION, color="#C0392B", linestyle="--",
               linewidth=1.8, label=f"23andMe target ({TARGET_AMPLIFICATION}x)")
    ax.axvline(x=best["cousin_prob"], color="#D97706", linestyle=":",
               linewidth=1.8, label=f"Best fit (cp={best['cousin_prob']})")
    ax.set_xlabel("Cousin Edge Probability", fontsize=10)
    ax.set_ylabel("Amplification Factor (x)", fontsize=10)
    ax.set_title("Amplification vs Cousin Probability", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Plot 2: Delta from target
    ax = axes[1]
    ax.set_facecolor("white")
    deltas = [r["delta"] for r in results]
    bar_colors = ["#C0392B" if r["cousin_prob"] == best["cousin_prob"]
                  else "#1B3A6B" for r in results]
    bars = ax.bar([str(p) for p in probs], deltas, color=bar_colors, edgecolor="white")
    for bar, val in zip(bars, deltas):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f"{val:.0f}", ha="center", va="bottom", fontsize=8)
    ax.set_xlabel("Cousin Edge Probability", fontsize=10)
    ax.set_ylabel("Delta from 23andMe Target", fontsize=10)
    ax.set_title("Calibration Error by Cousin Probability", fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("B1_calibration_tuning.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Plot saved as B1_calibration_tuning.png")


if __name__ == "__main__":
    print("="*62)
    print("  Module B1 — Calibration Tuning Against 23andMe")
    print(f"  Target amplification: {TARGET_AMPLIFICATION}x")
    print(f"  Runs per parameter : {N_RUNS_PER_PARAM}")
    print("="*62 + "\n")

    results, best = tune_cousin_probability()

    print("\nGenerating plots...")
    plot_tuning(results)