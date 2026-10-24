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
    calibrate_against_23andme,
)

# Frozen B1 development configuration.
N_FAMILIES = 1000
AVG_CHILDREN = 2
COUSIN_PROB = 0.20
REGISTRATION_RATE = 0.40

# Historical B1 calibration reference.
HISTORICAL_TARGET = 492.86

SEEDS = list(range(1, 31))

OUT = (
    REPO
    / "experiments"
    / "B_validation_strengthening"
    / "results"
    / "B1_multiseed_sensitivity.csv"
)


def run_seed(seed):
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

    result = calibrate_against_23andme(G, registered)

    amp = float(result["amplification"])

    return {
        "seed": seed,
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "registered": len(registered),
        "amplification": amp,
        "historical_target": HISTORICAL_TARGET,
        "absolute_delta": abs(amp - HISTORICAL_TARGET),
        "relative_error": abs(amp - HISTORICAL_TARGET)
        / HISTORICAL_TARGET,
    }


def main():
    rows = []

    print("=" * 68)
    print("B1 MULTI-SEED SENSITIVITY")
    print("=" * 68)
    print(f"cousin_prob       : {COUSIN_PROB}")
    print(f"registration_rate : {REGISTRATION_RATE}")
    print(f"runs              : {len(SEEDS)}")
    print()

    for seed in SEEDS:
        row = run_seed(seed)
        rows.append(row)

        print(
            f"seed={seed:02d} "
            f"nodes={row['nodes']:4d} "
            f"registered={row['registered']:4d} "
            f"amp={row['amplification']:8.2f}x"
        )

    amps = np.array(
        [r["amplification"] for r in rows],
        dtype=float,
    )

    mean = float(np.mean(amps))
    median = float(np.median(amps))
    sd = float(np.std(amps, ddof=1))
    minimum = float(np.min(amps))
    maximum = float(np.max(amps))
    p05 = float(np.percentile(amps, 5))
    p95 = float(np.percentile(amps, 95))
    cv = sd / mean if mean else float("nan")

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print("-" * 68)
    print("SUMMARY")
    print("-" * 68)
    print(f"Mean amplification   : {mean:.2f}x")
    print(f"Median amplification : {median:.2f}x")
    print(f"Sample SD            : {sd:.2f}x")
    print(f"Coefficient variation: {cv:.4f}")
    print(f"Minimum              : {minimum:.2f}x")
    print(f"Maximum              : {maximum:.2f}x")
    print(f"5th percentile       : {p05:.2f}x")
    print(f"95th percentile      : {p95:.2f}x")
    print(
        "Mean vs historical target relative difference: "
        f"{abs(mean - HISTORICAL_TARGET) / HISTORICAL_TARGET:.4%}"
    )
    print()
    print(f"Output: {OUT}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
