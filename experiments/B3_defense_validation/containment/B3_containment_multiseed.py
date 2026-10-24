import csv
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
B3_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "B3_authentication"))
B1_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "B1_graph_amplification"))
RESULTS_DIR = os.path.abspath(os.path.join(HERE, "..", "results"))

sys.path.insert(0, B3_DIR)
sys.path.insert(0, B1_DIR)

from graph_model import generate_kinship_graph, simulate_registration
from containment_algorithm import (
    compute_containment_targets,
    simulate_contained_breach,
)

os.makedirs(RESULTS_DIR, exist_ok=True)

# Keep historical B3 graph configuration fixed.
N_FAMILIES = 800
AVG_CHILDREN = 2
COUSIN_PROB = 0.20
REGISTRATION_RATE = 0.40
MAX_HOPS = 3
BREACH_FRACTION = 0.005

# Dense k grid lets us measure the actual minimum tested budget.
K_VALUES = list(range(1, 51))

# Explicit independent validation seeds.
SEEDS = list(range(1, 21))


def reset_state(G, compromised):
    for node in G.nodes():
        G.nodes[node]["exposed"] = False
        G.nodes[node]["compromised"] = False

    for node in compromised:
        G.nodes[node]["compromised"] = True
        G.nodes[node]["exposed"] = True


def origin_pools(G, registered):
    reg = sorted(registered, key=lambda n: G.degree(n))
    n = len(reg)

    return {
        "peripheral": reg[: n // 4],
        "mid_degree": reg[n // 4 : n // 2],
        "hub": reg[3 * n // 4 :],
    }


def summarize(values):
    a = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(a)),
        "median": float(np.median(a)),
        "std": float(np.std(a, ddof=1)) if len(a) > 1 else 0.0,
        "min": float(np.min(a)),
        "q05": float(np.quantile(a, 0.05)),
        "q25": float(np.quantile(a, 0.25)),
        "q75": float(np.quantile(a, 0.75)),
        "q95": float(np.quantile(a, 0.95)),
        "max": float(np.max(a)),
    }


rows = []

print("=" * 72)
print("GenoPhylax B3 - Multi-Seed Containment Validation")
print("=" * 72)

for seed in SEEDS:
    print(f"[seed {seed:02d}/{SEEDS[-1]:02d}] building graph...")

    random.seed(seed)
    np.random.seed(seed)

    G, _ = generate_kinship_graph(
        n_families=N_FAMILIES,
        avg_children=AVG_CHILDREN,
        cousin_prob=COUSIN_PROB,
    )

    registered = simulate_registration(
        G,
        registration_rate=REGISTRATION_RATE,
    )

    pools = origin_pools(G, registered)
    n_comp = max(5, int(len(registered) * BREACH_FRACTION))

    for origin, pool in pools.items():
        # Explicit deterministic sampling for this seed/origin.
        origin_offset = {
            "peripheral": 101,
            "mid_degree": 202,
            "hub": 303,
        }[origin]

        rng = random.Random(seed * 1000 + origin_offset)
        compromised = rng.sample(pool, min(n_comp, len(pool)))

        reset_state(G, compromised)

        baseline_set, _ = simulate_contained_breach(
            G,
            registered,
            compromised,
            containment_targets=[],
            max_hops=MAX_HOPS,
        )
        baseline = len(baseline_set)

        reductions = {}

        for k in K_VALUES:
            reset_state(G, compromised)

            targets, _ = compute_containment_targets(
                G,
                registered,
                compromised,
                top_k=k,
            )

            exposed, locked = simulate_contained_breach(
                G,
                registered,
                compromised,
                targets,
                max_hops=MAX_HOPS,
            )

            reduction = (
                (1.0 - len(exposed) / baseline) * 100.0
                if baseline > 0
                else 0.0
            )

            reductions[k] = reduction

            rows.append({
                "seed": seed,
                "origin": origin,
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "registered": len(registered),
                "n_compromised": len(compromised),
                "baseline_exposed": baseline,
                "k": k,
                "actual_locked": len(locked),
                "exposed_after": len(exposed),
                "reduction_pct": reduction,
            })

        k99 = next(
            (k for k in K_VALUES if reductions[k] >= 99.0),
            None,
        )

        print(
            f"    {origin:<11} "
            f"baseline={baseline:4d} "
            f"k=5={reductions[5]:6.2f}% "
            f"k=10={reductions[10]:6.2f}% "
            f"k=20={reductions[20]:6.2f}% "
            f"k99={k99}"
        )


raw_path = os.path.join(
    RESULTS_DIR,
    "B3_containment_multiseed_raw.csv",
)

with open(raw_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)


summary_rows = []

for origin in ["peripheral", "mid_degree", "hub"]:
    origin_rows = [r for r in rows if r["origin"] == origin]

    for k in [5, 10, 20, 30, 40, 50]:
        vals = [
            r["reduction_pct"]
            for r in origin_rows
            if r["k"] == k
        ]

        s = summarize(vals)

        summary_rows.append({
            "origin": origin,
            "metric": f"reduction_at_k{k}",
            **s,
        })

    baselines = []
    k99_values = []

    for seed in SEEDS:
        sr = [
            r for r in origin_rows
            if r["seed"] == seed
        ]

        baselines.append(sr[0]["baseline_exposed"])

        hit = next(
            (
                r["k"]
                for r in sr
                if r["reduction_pct"] >= 99.0
            ),
            None,
        )

        if hit is not None:
            k99_values.append(hit)

    summary_rows.append({
        "origin": origin,
        "metric": "baseline_exposed",
        **summarize(baselines),
    })

    if k99_values:
        summary_rows.append({
            "origin": origin,
            "metric": "minimum_k_for_99pct_when_achieved",
            **summarize(k99_values),
        })


summary_path = os.path.join(
    RESULTS_DIR,
    "B3_containment_multiseed_summary.csv",
)

with open(summary_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "origin", "metric",
        "mean", "median", "std", "min",
        "q05", "q25", "q75", "q95", "max",
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(summary_rows)


print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)

for origin in ["peripheral", "mid_degree", "hub"]:
    print(f"\n{origin.upper()}")

    for k in [5, 10, 20]:
        vals = [
            r["reduction_pct"]
            for r in rows
            if r["origin"] == origin and r["k"] == k
        ]

        s = summarize(vals)

        print(
            f"  k={k:<2} "
            f"mean={s['mean']:6.2f}% "
            f"median={s['median']:6.2f}% "
            f"range={s['min']:6.2f}-{s['max']:6.2f}%"
        )

    hits = []

    for seed in SEEDS:
        sr = [
            r for r in rows
            if r["origin"] == origin and r["seed"] == seed
        ]

        k99 = next(
            (
                r["k"]
                for r in sr
                if r["reduction_pct"] >= 99.0
            ),
            None,
        )

        hits.append(k99)

    achieved = [x for x in hits if x is not None]

    print(
        f"  99% threshold achieved in "
        f"{len(achieved)}/{len(SEEDS)} seeds"
    )

    if achieved:
        print(
            f"  k99 median={np.median(achieved):.1f}, "
            f"range={min(achieved)}-{max(achieved)}"
        )


print("\nSaved:")
print(f"  {raw_path}")
print(f"  {summary_path}")
print("\nHistorical B3 files were not modified.")
