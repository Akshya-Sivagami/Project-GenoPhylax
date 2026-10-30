# ============================================================================
# HISTORICAL / PRE-AUTHORITATIVE — superseded by commit d1a7de5
# ============================================================================
# This script predates the "Lock authoritative Module B results" commit
# (d180bd6) and the "Rebuild Module C from authoritative lifecycle evidence"
# commit (d1a7de5). Numbers produced here are NOT the canonical/reported
# GenoPhylax values.
#
# Canonical single-point values: experiments/B_final_audit/B1_authoritative_final.tsv
# Canonical multi-seed/multi-draw validation (B1+B3 unified graph):
#   demo/unified_b1_b3_multiseed_v2.py
# Canonical B3-internal multi-seed validation (original n_families=800 config):
#   experiments/B3_defense_validation/
#
# This script is kept for historical/provenance purposes only. Do not cite
# its output as a current GenoPhylax result.
# ============================================================================

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

COUSIN_PROBS = [0.05, 0.10, 0.20, 0.30]
REGISTRATION_RATES = [0.20, 0.40, 0.60]
HOPS = [1, 2, 3]

GRAPH_SEEDS = [1, 2, 3, 4, 5]
BREACH_RUNS = 50

OUT = (
    REPO
    / "experiments"
    / "B_validation_strengthening"
    / "results"
    / "B1_parameter_sensitivity.csv"
)


def main():
    rows = []

    total = (
        len(COUSIN_PROBS)
        * len(REGISTRATION_RATES)
        * len(HOPS)
        * len(GRAPH_SEEDS)
        * BREACH_RUNS
    )

    print("=" * 78)
    print("B1 PARAMETER SENSITIVITY GRID")
    print("=" * 78)
    print(f"Total breach realizations: {total}")
    print()

    for cp in COUSIN_PROBS:
        for reg_rate in REGISTRATION_RATES:

            # Build each graph only once for this cp/reg/seed.
            graph_data = []

            for graph_seed in GRAPH_SEEDS:
                seed = (
                    graph_seed
                    + int(cp * 1000) * 100
                    + int(reg_rate * 100) * 100000
                )

                random.seed(seed)
                np.random.seed(seed)

                G, _ = generate_kinship_graph(
                    n_families=N_FAMILIES,
                    avg_children=AVG_CHILDREN,
                    cousin_prob=cp,
                )

                registered = simulate_registration(
                    G,
                    registration_rate=reg_rate,
                )

                graph_data.append(
                    (graph_seed, G, registered)
                )

            for hops in HOPS:
                amps = []

                for graph_seed, G, registered in graph_data:

                    for breach_run in range(1, BREACH_RUNS + 1):

                        breach_seed = (
                            graph_seed * 1000000
                            + int(cp * 1000) * 1000
                            + int(reg_rate * 100) * 100
                            + hops * 10
                            + breach_run
                        )

                        random.seed(breach_seed)

                        result = simulate_breach(
                            G,
                            registered,
                            n_compromised=1,
                            max_hops=hops,
                        )

                        amps.append(
                            float(result["amplification"])
                        )

                arr = np.asarray(amps, dtype=float)

                row = {
                    "cousin_prob": cp,
                    "registration_rate": reg_rate,
                    "max_hops": hops,
                    "n_realizations": len(arr),
                    "mean_amplification": float(np.mean(arr)),
                    "median_amplification": float(np.median(arr)),
                    "sd_amplification": float(np.std(arr, ddof=1)),
                    "p05_amplification": float(np.percentile(arr, 5)),
                    "p25_amplification": float(np.percentile(arr, 25)),
                    "p75_amplification": float(np.percentile(arr, 75)),
                    "p95_amplification": float(np.percentile(arr, 95)),
                    "min_amplification": float(np.min(arr)),
                    "max_amplification": float(np.max(arr)),
                    "fraction_le_10x": float(np.mean(arr <= 10)),
                    "fraction_ge_500x": float(np.mean(arr >= 500)),
                }

                rows.append(row)

                print(
                    f"cp={cp:.2f} "
                    f"reg={reg_rate:.2f} "
                    f"hops={hops} | "
                    f"mean={row['mean_amplification']:8.2f}x "
                    f"median={row['median_amplification']:8.2f}x "
                    f"p05={row['p05_amplification']:7.2f}x "
                    f"p95={row['p95_amplification']:7.2f}x "
                    f">=500x={row['fraction_ge_500x']:.3f}"
                )

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    print()
    print("=" * 78)
    print("GLOBAL SUMMARY")
    print("=" * 78)

    means = np.asarray(
        [r["mean_amplification"] for r in rows],
        dtype=float,
    )

    print(f"Parameter combinations : {len(rows)}")
    print(f"Lowest scenario mean   : {np.min(means):.2f}x")
    print(f"Highest scenario mean  : {np.max(means):.2f}x")

    low = min(
        rows,
        key=lambda r: r["mean_amplification"],
    )

    high = max(
        rows,
        key=lambda r: r["mean_amplification"],
    )

    print()
    print("Lowest mean scenario:")
    print(
        f"  cp={low['cousin_prob']} "
        f"reg={low['registration_rate']} "
        f"hops={low['max_hops']} "
        f"mean={low['mean_amplification']:.2f}x"
    )

    print("Highest mean scenario:")
    print(
        f"  cp={high['cousin_prob']} "
        f"reg={high['registration_rate']} "
        f"hops={high['max_hops']} "
        f"mean={high['mean_amplification']:.2f}x"
    )

    print()
    print(f"Output: {OUT}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
