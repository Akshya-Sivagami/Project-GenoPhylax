import csv
import random
import sys
from pathlib import Path

import networkx as nx
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
)

N_FAMILIES = 1000
AVG_CHILDREN = 2
COUSIN_PROB = 0.20
REGISTRATION_RATE = 0.40
GRAPH_SEEDS = range(1, 31)

OUT = (
    REPO
    / "experiments"
    / "B_validation_strengthening"
    / "results"
    / "B1_topology_diagnostic.csv"
)


def reachable_within_hops(G, source, max_hops=3):
    lengths = nx.single_source_shortest_path_length(
        G,
        source,
        cutoff=max_hops,
    )
    return len(lengths)


def main():
    rows = []

    print("=" * 74)
    print("B1 REGISTERED-GRAPH TOPOLOGY DIAGNOSTIC")
    print("=" * 74)

    for seed in GRAPH_SEEDS:
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

        # Exposure only propagates through registered nodes,
        # so this is the graph that actually governs B1 spread.
        R = G.subgraph(registered).copy()

        components = sorted(
            nx.connected_components(R),
            key=len,
            reverse=True,
        )

        component_sizes = np.array(
            [len(c) for c in components],
            dtype=float,
        )

        largest = int(component_sizes[0]) if len(component_sizes) else 0
        giant_fraction = largest / len(registered) if registered else 0.0

        isolated = sum(1 for n in R.nodes() if R.degree(n) == 0)
        isolated_fraction = isolated / len(registered) if registered else 0.0

        small_nodes = sum(
            len(c) for c in components if len(c) <= 10
        )
        small_fraction = small_nodes / len(registered) if registered else 0.0

        reach3 = np.array(
            [reachable_within_hops(R, n, 3) for n in R.nodes()],
            dtype=float,
        )

        row = {
            "graph_seed": seed,
            "registered": len(registered),
            "components": len(components),
            "largest_component": largest,
            "giant_component_fraction": giant_fraction,
            "isolated_nodes": isolated,
            "isolated_fraction": isolated_fraction,
            "nodes_in_components_le_10": small_nodes,
            "small_component_fraction": small_fraction,
            "mean_3hop_reach": float(np.mean(reach3)),
            "median_3hop_reach": float(np.median(reach3)),
            "p05_3hop_reach": float(np.percentile(reach3, 5)),
            "p95_3hop_reach": float(np.percentile(reach3, 95)),
            "max_3hop_reach": float(np.max(reach3)),
        }

        rows.append(row)

        print(
            f"seed={seed:02d} "
            f"components={row['components']:4d} "
            f"giant={row['giant_component_fraction']:.3f} "
            f"isolated={row['isolated_fraction']:.3f} "
            f"small<=10={row['small_component_fraction']:.3f} "
            f"mean3hop={row['mean_3hop_reach']:8.2f}"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    def arr(key):
        return np.array([r[key] for r in rows], dtype=float)

    print()
    print("-" * 74)
    print("30-GRAPH SUMMARY")
    print("-" * 74)

    for key, label in [
        ("components", "Connected components"),
        ("giant_component_fraction", "Giant component fraction"),
        ("isolated_fraction", "Isolated-node fraction"),
        ("small_component_fraction", "Nodes in <=10-node components"),
        ("mean_3hop_reach", "Mean 3-hop reach"),
        ("median_3hop_reach", "Median 3-hop reach"),
    ]:
        values = arr(key)
        print(
            f"{label:<30}: "
            f"mean={np.mean(values):.4f} "
            f"min={np.min(values):.4f} "
            f"max={np.max(values):.4f}"
        )

    print()
    print(f"Output: {OUT}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
