import csv
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]

OUT = (
    REPO
    / "experiments"
    / "B_validation_strengthening"
    / "results"
    / "B2_unrecoverability_sensitivity.csv"
)

# Frozen development assumptions.
BASE_LEAKAGE = 0.420
BASE_COEFFICIENT = 3.5

# Sensitivity ranges around the development assumptions.
LEAKAGE_VALUES = np.arange(0.20, 0.651, 0.025)
COEFFICIENT_VALUES = np.arange(2.0, 5.01, 0.25)


def unrecoverability(leakage, coefficient):
    reconstruction_probability = (
        1.0 - math.exp(-coefficient * leakage)
    )

    return 1.0 - reconstruction_probability


def main():
    rows = []

    print("=" * 76)
    print("B2 PATHOGENIC-VARIANT UNRECOVERABILITY SENSITIVITY")
    print("=" * 76)
    print(
        "Sensitivity ranges are development scenarios, "
        "not empirical confidence intervals."
    )
    print()

    baseline = unrecoverability(
        BASE_LEAKAGE,
        BASE_COEFFICIENT,
    )

    print("FROZEN BASELINE REPRODUCTION")
    print("-" * 76)
    print(f"Leakage assumption       : {BASE_LEAKAGE:.3f}")
    print(f"Reconstruction coefficient: {BASE_COEFFICIENT:.2f}")
    print(f"Unrecoverability         : {baseline:.4f}")
    print()

    run_id = 0

    for leakage in LEAKAGE_VALUES:
        for coefficient in COEFFICIENT_VALUES:
            run_id += 1

            u = unrecoverability(
                float(leakage),
                float(coefficient),
            )

            rows.append({
                "run_id": run_id,
                "pathogenic_leakage": float(leakage),
                "reconstruction_coefficient": float(coefficient),
                "unrecoverability": u,
                "reconstruction_probability": 1.0 - u,
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    values = np.asarray(
        [r["unrecoverability"] for r in rows],
        dtype=float,
    )

    print("GLOBAL SENSITIVITY")
    print("-" * 76)
    print(f"Scenarios : {len(rows)}")
    print(f"Minimum   : {np.min(values):.4f}")
    print(f"P05       : {np.percentile(values, 5):.4f}")
    print(f"Median    : {np.median(values):.4f}")
    print(f"P95       : {np.percentile(values, 95):.4f}")
    print(f"Maximum   : {np.max(values):.4f}")

    # One-factor sensitivity around frozen baseline.
    leakage_only = np.asarray([
        unrecoverability(
            float(x),
            BASE_COEFFICIENT,
        )
        for x in LEAKAGE_VALUES
    ])

    coefficient_only = np.asarray([
        unrecoverability(
            BASE_LEAKAGE,
            float(x),
        )
        for x in COEFFICIENT_VALUES
    ])

    print()
    print("ONE-FACTOR SENSITIVITY AROUND FROZEN BASELINE")
    print("-" * 76)

    print(
        "Leakage varied, coefficient fixed at 3.5:"
    )
    print(
        f"  range = "
        f"{np.min(leakage_only):.4f} "
        f"to {np.max(leakage_only):.4f}"
    )

    print(
        "Coefficient varied, leakage fixed at 0.420:"
    )
    print(
        f"  range = "
        f"{np.min(coefficient_only):.4f} "
        f"to {np.max(coefficient_only):.4f}"
    )

    # Local perturbation around baseline.
    local_leakages = [
        BASE_LEAKAGE * 0.8,
        BASE_LEAKAGE,
        BASE_LEAKAGE * 1.2,
    ]

    local_coefficients = [
        BASE_COEFFICIENT * 0.8,
        BASE_COEFFICIENT,
        BASE_COEFFICIENT * 1.2,
    ]

    local = []

    for leakage in local_leakages:
        for coefficient in local_coefficients:
            local.append(
                unrecoverability(
                    leakage,
                    coefficient,
                )
            )

    local = np.asarray(local)

    print()
    print("LOCAL +/-20% ASSUMPTION CHECK")
    print("-" * 76)
    print(f"Minimum : {np.min(local):.4f}")
    print(f"Median  : {np.median(local):.4f}")
    print(f"Maximum : {np.max(local):.4f}")

    print()
    print("INTERPRETATION NOTE")
    print("-" * 76)
    print(
        "The 0.2299 frozen value is an output of the chosen "
        "leakage and exponential reconstruction assumptions. "
        "It is not an empirically measured universal "
        "unrecoverability constant."
    )

    print()
    print(f"Output: {OUT}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
