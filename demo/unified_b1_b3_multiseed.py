#!/usr/bin/env python3
"""
GenoPhylax — Unified B1+B3 Multi-Seed Analysis

Builds N independent kinship graphs (same generator/parameters, different
seeds) and runs B1 amplification + B3 containment-by-origin on each one,
reporting mean/median/min/max instead of a single point estimate.

Resolves two issues found in prior single-instance work:
  1. B1 and B3 locked authoritative results used DIFFERENT graph instances
     (see demo/unified_b1_b3_graph.py for the single-shared-graph version).
  2. Even a single shared graph instance is a fragile point estimate —
     B1 amplification varied from 464.4x (5-run average) to 1175.0x
     (single run) at the same parameters. This script characterizes that
     variance properly instead of reporting one number.

The authentication classifier does not depend on the kinship graph at all
(it's a separate synthetic session dataset), so it is run once, outside
the seed loop, with its own explicit seed -- this also removes the
global-RNG-order dependency present in the original containment_algorithm.py
script, where the classifier's randomness was downstream of whatever graph
code ran before it.
"""
import sys
import os
import random
import statistics

BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE)
sys.path.insert(0, os.path.join(REPO_ROOT, "experiments", "B1_graph_amplification"))
sys.path.insert(0, os.path.join(REPO_ROOT, "experiments", "B3_authentication"))

import numpy as np
from graph_model import generate_kinship_graph, simulate_registration, calibrate_against_23andme
from containment_algorithm import (
    analyze_attack_origins,
    generate_access_sessions,
    evaluate_detection,
)

N_SEEDS = 20
N_FAMILIES = 1000
COUSIN_PROB = 0.20
AVG_CHILDREN = 2
REGISTRATION_RATE = 0.4
K_VALUES = [5, 10, 15, 20, 30, 40, 50]
AUTH_SEED = 999  # isolated from graph seeds, by design (see docstring)

def summarize(label, values):
    return {
        "label": label,
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }

def print_summary(s):
    print(f"      {s['label']:<28} mean={s['mean']:>9} median={s['median']:>9} "
          f"min={s['min']:>9} max={s['max']:>9} stdev={s['stdev']:>9}")

def main():
    print("=" * 74)
    print(f" GenoPhylax — Unified B1+B3 Multi-Seed Analysis ({N_SEEDS} seeds)")
    print("=" * 74)
    print(f" Parameters: n_families={N_FAMILIES}, cousin_prob={COUSIN_PROB}, "
          f"registration_rate={REGISTRATION_RATE}")
    print()

    amp_values = []
    node_counts = []
    edge_counts = []
    origin_k10 = {"Low-Degree\n(Peripheral)": [], "Mid-Degree\n(Average User)": [], "High-Degree\n(Hub Account)": []}
    origin_mink = {"Low-Degree\n(Peripheral)": [], "Mid-Degree\n(Average User)": [], "High-Degree\n(Hub Account)": []}

    for seed in range(1, N_SEEDS + 1):
        print(f"[seed {seed:>2}/{N_SEEDS}] building graph...", end=" ")
        random.seed(seed)
        np.random.seed(seed)

        G, _ = generate_kinship_graph(
            n_families=N_FAMILIES, avg_children=AVG_CHILDREN, cousin_prob=COUSIN_PROB
        )
        registered = simulate_registration(G, registration_rate=REGISTRATION_RATE)
        node_counts.append(G.number_of_nodes())
        edge_counts.append(G.number_of_edges())

        cal = calibrate_against_23andme(G, registered)
        amp_values.append(cal["amplification"])
        print(f"nodes={G.number_of_nodes():,} amp={cal['amplification']}x", end=" ")

        origin_results = analyze_attack_origins(G, registered, K_VALUES)
        for label, data in origin_results.items():
            k10 = next(r for r in data["results"] if r["k"] == 10)
            origin_k10[label].append(k10["reduction"])
            origin_mink[label].append(data["threshold_k"] if data["threshold_k"] else 999)
        print("done")

    print("\n" + "=" * 74)
    print(" B1 — Amplification across seeds")
    print("=" * 74)
    print_summary(summarize("amplification (x)", amp_values))
    print_summary(summarize("node count", node_counts))
    print_summary(summarize("edge count", edge_counts))
    print(f"\n      Locked authoritative single value: 464.4x")
    print(f"      Real 23andMe anchor: 492.86x")

    print("\n" + "=" * 74)
    print(" B3 — Containment by attack origin across seeds (k=10 reduction %)")
    print("=" * 74)
    for label in origin_k10:
        print_summary(summarize(label.replace(chr(10), " "), origin_k10[label]))

    print("\n" + "=" * 74)
    print(" B3 — Minimum k for >=99% reduction across seeds (999 = not achieved by k=50)")
    print("=" * 74)
    for label in origin_mink:
        not_achieved = sum(1 for v in origin_mink[label] if v == 999)
        achieved = [v for v in origin_mink[label] if v != 999]
        if achieved:
            print_summary(summarize(label.replace(chr(10), " "), achieved))
            if not_achieved:
                print(f"      {'':28} ({not_achieved}/{N_SEEDS} seeds did not reach 99% by k=50)")
        else:
            print(f"      {label.replace(chr(10), ' '):<28} never achieved 99% reduction within k<=50 in any seed")

    print("\n" + "=" * 74)
    print(" B3 — Authentication classifier (graph-independent, run once, isolated seed)")
    print("=" * 74)
    random.seed(AUTH_SEED)
    np.random.seed(AUTH_SEED)
    sessions = generate_access_sessions(n_normal=200, n_attack=50, seed=AUTH_SEED)
    best_f1, best_threshold, best_metrics = 0, 4.0, None
    for t in [x * 0.1 for x in range(20, 80)]:
        _, m = evaluate_detection(sessions, threshold=t)
        if m["f1"] > best_f1 and m["precision"] >= 0.85 and m["recall"] >= 0.75:
            best_f1, best_threshold, best_metrics = m["f1"], t, m
    if best_metrics is None:
        for t in [x * 0.1 for x in range(20, 80)]:
            _, m = evaluate_detection(sessions, threshold=t)
            if m["f1"] > best_f1:
                best_f1, best_threshold, best_metrics = m["f1"], t, m
    print(f"      threshold={best_threshold:.1f}  precision={best_metrics['precision']:.4f}  "
          f"recall={best_metrics['recall']:.4f}  F1={best_metrics['f1']:.4f}  "
          f"accuracy={best_metrics['accuracy']:.4f}")
    print(f"      Locked authoritative single value: threshold=3.6, F1=0.8387")
    print(f"      (isolated from graph-seed loop — deterministic regardless of graph work order)")

    print("\n" + "=" * 74)
    print(" RECOMMENDATION FOR REPORTING")
    print("=" * 74)
    print(" Report B1 amplification and B3 hub-origin containment as ranges, not single")
    print(" points — single-seed variance is large enough (see stdev above) that one")
    print(" number invites a fair 'cherry-picked?' challenge from a reviewer.")

if __name__ == "__main__":
    main()