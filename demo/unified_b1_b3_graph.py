#!/usr/bin/env python3
"""
GenoPhylax — Unified B1+B3 Graph (single seeded instance)

Resolves a reviewer-facing gap: the locked B1 authoritative results
(4,144 nodes) and B3 authoritative results (3,303 nodes) were produced
from DIFFERENT graph instances (different n_families/cousin_prob), even
though B3 imports its graph generator directly from B1's module.

This script builds exactly ONE kinship graph, using the parameters B1's
own calibration sweep determined to be optimal (n_families=1000,
cousin_prob=0.20 — the value closest to the real 23andMe amplification
target), and runs BOTH the B1 amplification/calibration analysis and the
B3 containment/authentication analysis against that same graph object.

This does NOT overwrite the locked B_final_audit authoritative values —
those remain the historical record of what was originally reported. This
is a new, clearly-labeled, internally-consistent companion result.
"""
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE)
sys.path.insert(0, os.path.join(REPO_ROOT, "experiments", "B1_graph_amplification"))
sys.path.insert(0, os.path.join(REPO_ROOT, "experiments", "B3_authentication"))

# Import triggers each module's own top-level random.seed(42)/np.random.seed(42) —
# harmless, since we explicitly reseed ourselves right before building the graph.
from graph_model import generate_kinship_graph, simulate_registration, calibrate_against_23andme
from containment_algorithm import (
    analyze_containment_effectiveness,
    analyze_attack_origins,
    generate_access_sessions,
    evaluate_detection,
    compute_d4_score,
)

import random
import numpy as np

# ── Unified graph parameters ──
# n_families=1000: matches B1's calibration_tuning.py run (not amplification_analysis.py's
#   default call, which also used 1000 — consistent there).
# cousin_prob=0.20: the value B1's own 9-point sweep [0.01..0.30] found closest to the
#   real 23andMe target (492.86x); this is what produced the "464.4x calibrated" figure.
N_FAMILIES = 1000
COUSIN_PROB = 0.20
AVG_CHILDREN = 2
REGISTRATION_RATE = 0.4
K_VALUES = [5, 10, 15, 20, 30, 40, 50]

def main():
    print("=" * 70)
    print(" GenoPhylax — Unified B1+B3 Graph (single seeded instance)")
    print("=" * 70)
    print(f" Parameters: n_families={N_FAMILIES}, avg_children={AVG_CHILDREN}, "
          f"cousin_prob={COUSIN_PROB}, registration_rate={REGISTRATION_RATE}")
    print(" (cousin_prob is B1's own calibration-optimal value, not either")
    print("  module's original default — see script docstring)")
    print()

    # Explicit, deliberate seed point — overrides any import-time seeding above.
    random.seed(42)
    np.random.seed(42)

    print("[1/5] Building unified kinship graph...")
    G, family_data = generate_kinship_graph(
        n_families=N_FAMILIES, avg_children=AVG_CHILDREN, cousin_prob=COUSIN_PROB
    )
    print(f"      Nodes: {G.number_of_nodes():,}")
    print(f"      Edges: {G.number_of_edges():,}")

    registered = simulate_registration(G, registration_rate=REGISTRATION_RATE)
    print(f"      Registered: {len(registered):,}")

    print("\n[2/5] B1 — Running 23andMe calibration/amplification on unified graph...")
    cal = calibrate_against_23andme(G, registered)
    print(f"      Model amplification : {cal['amplification']}x")
    print(f"      Real amplification  : {cal['real_amplification']}x")
    print(f"      Model/Real ratio    : {cal['model_vs_real']}")
    print(f"      Compromised/Exposed : {cal['n_compromised']:,} / {cal['n_exposed']:,}")

    print("\n[3/5] B3 — Running containment effectiveness sweep on unified graph...")
    n_comp = max(5, int(len(registered) * 0.005))
    containment_results, baseline = analyze_containment_effectiveness(
        G, registered, n_comp, K_VALUES
    )
    print(f"      Baseline exposed (no containment): {baseline:,}")
    print(f"      {'k':>5} {'Exposed':>10} {'Reduction%':>12} {'Cost%':>8} {'Efficiency':>12}")
    print("      " + "-" * 52)
    for r in containment_results:
        print(f"      {r['k']:>5} {r['n_exposed']:>10} {r['reduction_pct']:>11.1f}% "
              f"{r['containment_cost']:>7.2f}% {r['efficiency']:>12.2f}")

    print("\n[4/5] B3 — Running attack-origin analysis on unified graph...")
    origin_results = analyze_attack_origins(G, registered, K_VALUES)
    print(f"\n      {'Origin':<25} {'Baseline':>10} {'k=10 Reduction':>16} {'Min k for 99%':>15}")
    print("      " + "-" * 70)
    for label, data in origin_results.items():
        k10 = next(r for r in data["results"] if r["k"] == 10)
        threshold = data["threshold_k"]
        thresh_str = f"k={threshold}" if threshold else "Not achieved (k<=50)"
        print(f"      {label.replace(chr(10), ' '):<25} {data['baseline']:>10} "
              f"{k10['reduction']:>15.1f}% {thresh_str:>15}")

    print("\n[5/5] B3 — Running authentication classifier (graph-independent)...")
    sessions = generate_access_sessions(n_normal=200, n_attack=50)
    best_f1, best_threshold, best_metrics = 0, 4.0, None
    for t in [x * 0.1 for x in range(20, 80)]:
        _, m = evaluate_detection(sessions, threshold=t)
        if m["f1"] > best_f1 and m["precision"] >= 0.85 and m["recall"] >= 0.75:
            best_f1, best_threshold, best_metrics = m["f1"], t, m
    if best_metrics is None:
        print("      Warning: no threshold met constraints, falling back to best F1")
        for t in [x * 0.1 for x in range(20, 80)]:
            _, m = evaluate_detection(sessions, threshold=t)
            if m["f1"] > best_f1:
                best_f1, best_threshold, best_metrics = m["f1"], t, m
    print(f"      Best threshold : {best_threshold:.1f}")
    print(f"      Precision : {best_metrics['precision']:.4f}")
    print(f"      Recall    : {best_metrics['recall']:.4f}")
    print(f"      F1 Score  : {best_metrics['f1']:.4f}")
    print(f"      Accuracy  : {best_metrics['accuracy']:.4f}")
    print(f"      TP={best_metrics['tp']} FP={best_metrics['fp']} "
          f"TN={best_metrics['tn']} FN={best_metrics['fn']}")
    print("      NOTE: compute_anomaly_score()'s noise term uses the global numpy RNG,")
    print("      not a locally seeded generator — so this result is deterministic given")
    print("      this script's fixed call order, but is NOT independently reproducible")
    print("      if someone changes what runs before this step.")

    best_reduction = max(r["reduction_pct"] for r in containment_results)
    d4 = compute_d4_score(best_reduction, best_metrics["f1"])

    print("\n" + "=" * 70)
    print(" SUMMARY — Unified Single-Graph Result (compare against locked B1/B3)")
    print("=" * 70)
    print(f" Graph              : {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")
    print(f" B1 amplification   : {cal['amplification']}x (vs real {cal['real_amplification']}x, "
          f"ratio {cal['model_vs_real']})")
    print(f" B3 best reduction  : {best_reduction}%")
    print(f" B3 auth F1         : {best_metrics['f1']:.4f}")
    print(f" GRI D4 score       : {d4} / 10")
    print()
    print(" This is a single consistent graph feeding both B1 and B3 analyses.")
    print(" Locked authoritative values (d180bd6) used two DIFFERENT graph instances")
    print(" (B1: n_families=1000/cousin_prob=0.3 default run vs calibration-sweep run;")
    print(" B3: n_families=800/cousin_prob=0.20) and are retained separately as the")
    print(" original historical record, not overwritten by this result.")

if __name__ == "__main__":
    main()