#!/usr/bin/env python3
"""
GenoPhylax — Unified B1+B3 Multi-Seed, Multi-Draw Analysis (v2, fixed)

Fixes a defect found in the v1 multi-seed run: calibrate_against_23andme()
computes n_compromised = max(1, int(registered * 0.001)). At this
population scale (~1,650 registered), that floors to exactly 1 compromised
account -- so amplification becomes "how connected is one random node",
not a population-scale breach. This produced a bimodal, not-meaningfully-
variable result (1-2x for isolated draws, 500-1400x for connected ones).

Fix: for each of the N_SEEDS graphs, draw N_DRAWS independent breaches
(same n_compromised count, different random compromised nodes) and average
within the graph BEFORE computing cross-seed statistics. This preserves
the real 23andMe breach-ratio calibration while removing single-node
selection luck as the dominant source of variance.

Second fix (this version): the B3 minimum-k-for-99%-reduction metric used
a sentinel value (999) for draws that never reached 99% within k<=50. The
first version of this script accidentally averaged that sentinel in with
real k values, producing impossible results (e.g. "mean k=107"). This
version tracks achieved and not-achieved draws separately and only
averages real k values from draws that actually achieved 99% reduction.
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
from graph_model import generate_kinship_graph, simulate_registration, simulate_breach
from containment_algorithm import (
    compute_containment_targets,
    simulate_contained_breach,
    generate_access_sessions,
    evaluate_detection,
)

N_SEEDS = 20
N_DRAWS = 10
N_FAMILIES = 800
COUSIN_PROB = 0.20
AVG_CHILDREN = 2
REGISTRATION_RATE = 0.4
K_VALUES = [5, 10, 15, 20, 30, 40, 50]
AUTH_SEED = 999
REAL_AMPLIFICATION = 6_900_000 / 14_000  # 492.857...

ORIGIN_LABELS = ["Low-Degree\n(Peripheral)", "Mid-Degree\n(Average User)", "High-Degree\n(Hub Account)"]

def summarize(label, values):
    return {
        "label": label, "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2), "max": round(max(values), 2),
        "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }

def print_summary(s):
    print(f"      {s['label']:<28} mean={s['mean']:>9} median={s['median']:>9} "
          f"min={s['min']:>9} max={s['max']:>9} stdev={s['stdev']:>9}")

def multidraw_amplification(G, registered_nodes, n_draws):
    total_registered = len(registered_nodes)
    n_compromised = max(1, int(total_registered * (14_000 / 14_000_000)))
    amps = []
    for _ in range(n_draws):
        result = simulate_breach(G, registered_nodes, n_compromised, max_hops=3)
        amps.append(result["amplification"])
    return amps, n_compromised

def origin_pools(registered_nodes, G):
    reg_list = sorted(registered_nodes, key=lambda n: G.degree(n))
    n = len(reg_list)
    return {
        ORIGIN_LABELS[0]: reg_list[:n // 4],
        ORIGIN_LABELS[1]: reg_list[n // 4:n // 2],
        ORIGIN_LABELS[2]: reg_list[3 * n // 4:],
    }

def multidraw_origin_analysis(G, registered_nodes, k_values, n_draws):
    pools = origin_pools(registered_nodes, G)
    n = len(registered_nodes)
    n_comp = max(5, int(n * 0.005))
    out = {label: {"k10_reductions": [], "min_ks_achieved": [], "n_not_achieved": 0, "n_draws": 0}
           for label in ORIGIN_LABELS}

    for label, pool in pools.items():
        for _ in range(n_draws):
            compromised = random.sample(pool, min(n_comp, len(pool)))
            for node in G.nodes():
                G.nodes[node]["exposed"] = False
                G.nodes[node]["compromised"] = False
            for node in compromised:
                G.nodes[node]["compromised"] = True
                G.nodes[node]["exposed"] = True

            baseline_set, _ = simulate_contained_breach(G, registered_nodes, compromised, [], max_hops=3)
            baseline = len(baseline_set)
            if baseline == 0:
                continue

            out[label]["n_draws"] += 1
            min_k = None
            k10_reduction = None
            for k in k_values:
                for node in G.nodes():
                    G.nodes[node]["exposed"] = False
                    G.nodes[node]["compromised"] = False
                for node in compromised:
                    G.nodes[node]["compromised"] = True
                    G.nodes[node]["exposed"] = True
                targets, _ = compute_containment_targets(G, registered_nodes, compromised, top_k=k)
                exposed, _ = simulate_contained_breach(G, registered_nodes, compromised, targets, max_hops=3)
                reduction = round((1 - len(exposed) / baseline) * 100, 2)
                if k == 10:
                    k10_reduction = reduction
                if reduction >= 99.0 and min_k is None:
                    min_k = k

            out[label]["k10_reductions"].append(k10_reduction)
            if min_k is not None:
                out[label]["min_ks_achieved"].append(min_k)
            else:
                out[label]["n_not_achieved"] += 1

    return out

def main():
    print("=" * 74)
    print(f" GenoPhylax — Unified B1+B3 Multi-Seed Multi-Draw Analysis")
    print(f" ({N_SEEDS} graph seeds x {N_DRAWS} breach draws per graph)")
    print("=" * 74)
    print(f" Parameters: n_families={N_FAMILIES}, cousin_prob={COUSIN_PROB}, "
          f"registration_rate={REGISTRATION_RATE}")
    print()

    per_graph_amp_means = []
    node_counts, edge_counts = [], []
    origin_k10_pergraph = {label: [] for label in ORIGIN_LABELS}
    origin_mink_pergraph = {label: [] for label in ORIGIN_LABELS}
    origin_not_achieved_total = {label: 0 for label in ORIGIN_LABELS}
    origin_draws_total = {label: 0 for label in ORIGIN_LABELS}

    for seed in range(1, N_SEEDS + 1):
        print(f"[seed {seed:>2}/{N_SEEDS}] building graph + {N_DRAWS} draws...", end=" ")
        random.seed(seed)
        np.random.seed(seed)

        G, _ = generate_kinship_graph(n_families=N_FAMILIES, avg_children=AVG_CHILDREN, cousin_prob=COUSIN_PROB)
        registered = simulate_registration(G, registration_rate=REGISTRATION_RATE)
        node_counts.append(G.number_of_nodes())
        edge_counts.append(G.number_of_edges())

        amps, n_comp = multidraw_amplification(G, registered, N_DRAWS)
        graph_mean_amp = round(statistics.mean(amps), 2)
        per_graph_amp_means.append(graph_mean_amp)
        print(f"n_comp={n_comp} mean_amp={graph_mean_amp}x", end=" ")

        origin_results = multidraw_origin_analysis(G, registered, K_VALUES, N_DRAWS)
        for label in ORIGIN_LABELS:
            k10_vals = [v for v in origin_results[label]["k10_reductions"] if v is not None]
            if k10_vals:
                origin_k10_pergraph[label].append(round(statistics.mean(k10_vals), 2))
            achieved = origin_results[label]["min_ks_achieved"]
            if achieved:
                origin_mink_pergraph[label].append(round(statistics.mean(achieved), 2))
            origin_not_achieved_total[label] += origin_results[label]["n_not_achieved"]
            origin_draws_total[label] += origin_results[label]["n_draws"]
        print("done")

    print("\n" + "=" * 74)
    print(" B1 — Amplification: per-graph mean (across N_DRAWS), then cross-seed stats")
    print("=" * 74)
    print_summary(summarize("amplification (x)", per_graph_amp_means))
    print_summary(summarize("node count", node_counts))
    print_summary(summarize("edge count", edge_counts))
    print(f"\n      Locked authoritative single value: 464.4x")
    print(f"      v1 (single-draw) result: mean=856.85x stdev=498.3 (dominated by n=1 breach draws)")
    print(f"      Real 23andMe anchor: {REAL_AMPLIFICATION:.2f}x")

    print("\n" + "=" * 74)
    print(" B3 — Containment by origin: per-graph mean (across N_DRAWS) k=10 reduction %")
    print("=" * 74)
    for label in ORIGIN_LABELS:
        print_summary(summarize(label.replace(chr(10), " "), origin_k10_pergraph[label]))

    print("\n" + "=" * 74)
    print(" B3 — Minimum k for >=99% reduction: per-graph mean of ACHIEVED draws only")
    print("=" * 74)
    for label in ORIGIN_LABELS:
        if origin_mink_pergraph[label]:
            print_summary(summarize(label.replace(chr(10), " "), origin_mink_pergraph[label]))
        else:
            print(f"      {label.replace(chr(10), ' '):<28} no draws ever reached 99% reduction within k<=50")
        not_ach = origin_not_achieved_total[label]
        total = origin_draws_total[label]
        pct = round(100 * not_ach / total, 1) if total else 0.0
        print(f"      {'':28} {not_ach}/{total} draws ({pct}%) never reached 99% reduction within k<=50")

    print("\n" + "=" * 74)
    print(" B3 — Authentication classifier (graph-independent, isolated seed, unchanged from v1)")
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

    print("\n" + "=" * 74)
    print(" NOTES")
    print("=" * 74)
    print(" - B1 n_compromised per draw is fixed by the real breach ratio (0.1%), which")
    print("   floors to a small integer at this population scale -- multi-draw averaging")
    print("   smooths selection luck but does not change that underlying ratio.")
    print(" - Hub-origin k=10 reduction was extremely stable even in v1 (stdev ~0.15) --")
    print("   that finding is robust. Hub min-k-for-99% achievement rate is reported above")
    print("   instead of averaged, since some hub draws may never reach 99% within k<=50.")

if __name__ == "__main__":
    main()