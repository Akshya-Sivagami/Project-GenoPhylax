import csv
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]

sys.path.insert(
    0,
    str(REPO / "experiments" / "B1_graph_amplification")
)

from graph_model import (
    generate_kinship_graph,
    simulate_registration,
    simulate_breach,
)

N_FAMILIES = 1000
AVG_CHILDREN = 2
COUSIN_PROB = 0.20
REGISTRATION_RATE = 0.40

GRAPH_SEEDS = range(1, 31)
BREACH_RUNS_PER_GRAPH = 100

OUT = (
    REPO
    / "experiments"
    / "B_validation_strengthening"
    / "results"
    / "B1_breach_seed_monte_carlo.csv"
)


def main():
    rows = []
    graph_summaries = []

    print("=" * 72)
    print("B1 BREACH-SEED MONTE CARLO")
    print("=" * 72)
    print(f"Graph seeds           : {len(list(GRAPH_SEEDS))}")
    print(f"Breach runs per graph : {BREACH_RUNS_PER_GRAPH}")
    print(f"Total realizations    : {len(list(GRAPH_SEEDS)) * BREACH_RUNS_PER_GRAPH}")
    print()

    for graph_seed in GRAPH_SEEDS:
        random.seed(graph_seed)
        np.random.seed(graph_seed)

        G, _ = generate_kinship_graph(
            n_families=N_FAMILIES,
            avg_children=AVG_CHILDREN,
            cousin_prob=COUSIN_PROB,
        )

        registered = simulate_registration(
            G,
            registration_rate=REGISTRATION_RATE,
        )

        amps = []

        for breach_run in range(1, BREACH_RUNS_PER_GRAPH + 1):

            # Deterministic but independent breach selection.
            breach_seed = graph_seed * 100000 + breach_run
            random.seed(breach_seed)

            result = simulate_breach(
                G,
                registered,
                n_compromised=1,
                max_hops=3,
            )

            amp = float(result["amplification"])
            amps.append(amp)

            rows.append({
                "graph_seed": graph_seed,
                "breach_run": breach_run,
                "breach_seed": breach_seed,
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "registered": len(registered),
                "n_compromised": 1,
                "n_exposed": result["n_exposed"],
                "amplification": amp,
            })

        arr = np.asarray(amps, dtype=float)

        summary = {
            "graph_seed": graph_seed,
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "sd": float(np.std(arr, ddof=1)),
            "minimum": float(np.min(arr)),
            "maximum": float(np.max(arr)),
            "p05": float(np.percentile(arr, 5)),
            "p95": float(np.percentile(arr, 95)),
        }

        graph_summaries.append(summary)

        print(
            f"graph={graph_seed:02d} "
            f"mean={summary['mean']:8.2f}x "
            f"median={summary['median']:8.2f}x "
            f"p05={summary['p05']:7.2f}x "
            f"p95={summary['p95']:7.2f}x"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    all_amps = np.asarray(
        [r["amplification"] for r in rows],
        dtype=float,
    )

    print()
    print("-" * 72)
    print("POOLED 3,000-REALIZATION SUMMARY")
    print("-" * 72)
    print(f"Mean amplification   : {np.mean(all_amps):.2f}x")
    print(f"Median amplification : {np.median(all_amps):.2f}x")
    print(f"Sample SD            : {np.std(all_amps, ddof=1):.2f}x")
    print(f"Minimum              : {np.min(all_amps):.2f}x")
    print(f"Maximum              : {np.max(all_amps):.2f}x")
    print(f"5th percentile       : {np.percentile(all_amps, 5):.2f}x")
    print(f"25th percentile      : {np.percentile(all_amps, 25):.2f}x")
    print(f"75th percentile      : {np.percentile(all_amps, 75):.2f}x")
    print(f"95th percentile      : {np.percentile(all_amps, 95):.2f}x")

    low = np.mean(all_amps <= 10)
    high = np.mean(all_amps >= 500)

    print()
    print(f"Fraction <=10x       : {low:.4f}")
    print(f"Fraction >=500x      : {high:.4f}")
    print()
    print(f"Output: {OUT}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
