import csv
from itertools import product
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]

OUT = (
    REPO
    / "experiments"
    / "B_validation_strengthening"
    / "results"
    / "B2_lifetime_sensitivity.csv"
)

YEARS = np.arange(0, 81)

# Frozen development baselines.
BASELINE = {
    "baseline_reid": 0.05,
    "baseline_disease": 0.10,
    "baseline_familial": 0.15,
    "doubling_time": 3.5,
    "db_saturation": 50.0,
    "inf_midpoint": 20.0,
    "inf_steepness": 0.20,
    "inf_max_factor": 8.0,
    "familial_scale": 0.40,
}

# Sensitivity ranges around development assumptions.
# These are scenario bounds, not empirical confidence intervals.
GRID = {
    "baseline_reid": [0.025, 0.05, 0.075],
    "baseline_disease": [0.05, 0.10, 0.15],
    "baseline_familial": [0.075, 0.15, 0.225],
    "doubling_time": [2.5, 3.5, 5.0],
    "db_saturation": [25.0, 50.0, 75.0],
    "inf_midpoint": [15.0, 20.0, 25.0],
    "inf_max_factor": [4.0, 8.0, 12.0],
}

# Hold these fixed in the main grid to keep the experiment manageable.
FIXED_STEEPNESS = 0.20
FIXED_FAMILIAL_SCALE = 0.40


def database_growth(years, doubling_time, saturation):
    return np.minimum(
        2 ** (years / doubling_time),
        saturation,
    )


def inference_expansion(
    years,
    midpoint,
    steepness,
    max_factor,
):
    sigmoid = 1.0 / (
        1.0 + np.exp(-steepness * (years - midpoint))
    )
    return 1.0 + (max_factor - 1.0) * sigmoid


def compute(params):
    db = database_growth(
        YEARS,
        params["doubling_time"],
        params["db_saturation"],
    )

    inf = inference_expansion(
        YEARS,
        params["inf_midpoint"],
        params["inf_steepness"],
        params["inf_max_factor"],
    )

    reid = np.minimum(
        params["baseline_reid"] * db * np.sqrt(inf),
        1.0,
    )

    disease = np.minimum(
        params["baseline_disease"] * inf,
        1.0,
    )

    familial = np.minimum(
        params["baseline_familial"]
        * db
        * params["familial_scale"],
        1.0,
    )

    composite = (reid + disease + familial) / 3.0
    d5 = np.minimum(composite * 10.0, 10.0)

    return reid, disease, familial, d5


def first_crossing(values, threshold):
    idx = np.where(values >= threshold)[0]

    if len(idx) == 0:
        return None

    return int(YEARS[idx[0]])


def summarize(run_id, params):
    reid, disease, familial, d5 = compute(params)

    return {
        "run_id": run_id,

        "baseline_reid": params["baseline_reid"],
        "baseline_disease": params["baseline_disease"],
        "baseline_familial": params["baseline_familial"],

        "doubling_time": params["doubling_time"],
        "db_saturation": params["db_saturation"],

        "inf_midpoint": params["inf_midpoint"],
        "inf_steepness": params["inf_steepness"],
        "inf_max_factor": params["inf_max_factor"],

        "familial_scale": params["familial_scale"],

        "reid_25_year": first_crossing(reid, 0.25),
        "reid_50_year": first_crossing(reid, 0.50),
        "reid_75_year": first_crossing(reid, 0.75),
        "reid_100_year": first_crossing(reid, 1.00),

        "disease_25_year": first_crossing(disease, 0.25),
        "disease_50_year": first_crossing(disease, 0.50),
        "disease_75_year": first_crossing(disease, 0.75),
        "disease_100_year": first_crossing(disease, 1.00),

        "familial_25_year": first_crossing(familial, 0.25),
        "familial_50_year": first_crossing(familial, 0.50),
        "familial_75_year": first_crossing(familial, 0.75),
        "familial_100_year": first_crossing(familial, 1.00),

        "d5_year_0": float(d5[0]),
        "d5_year_10": float(d5[10]),
        "d5_year_20": float(d5[20]),
        "d5_year_30": float(d5[30]),
        "d5_year_50": float(d5[50]),
        "d5_year_80": float(d5[80]),
    }


def finite(values):
    return np.array(
        [v for v in values if v is not None],
        dtype=float,
    )


def horizon_summary(rows, key):
    vals = finite([r[key] for r in rows])

    never = sum(
        1 for r in rows
        if r[key] is None
    )

    if len(vals) == 0:
        return "never in all scenarios"

    return (
        f"min={int(np.min(vals))}, "
        f"median={np.median(vals):.1f}, "
        f"max={int(np.max(vals))}, "
        f"never={never}/{len(rows)}"
    )


def main():
    rows = []

    keys = list(GRID.keys())
    combinations = list(
        product(*(GRID[k] for k in keys))
    )

    print("=" * 76)
    print("B2 LIFETIME PARAMETER SENSITIVITY")
    print("=" * 76)
    print(f"Parameter combinations: {len(combinations)}")
    print("These are model sensitivity scenarios, not empirical forecasts.")
    print()

    for i, values in enumerate(combinations, start=1):
        params = dict(zip(keys, values))

        params["inf_steepness"] = FIXED_STEEPNESS
        params["familial_scale"] = FIXED_FAMILIAL_SCALE

        rows.append(
            summarize(i, params)
        )

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

    # Exact frozen baseline reproduction.
    baseline = summarize(
        "baseline",
        BASELINE,
    )

    print("FROZEN BASELINE REPRODUCTION")
    print("-" * 76)
    print(
        f"Re-ID 100% year     : "
        f"{baseline['reid_100_year']}"
    )
    print(
        f"Familial 100% year  : "
        f"{baseline['familial_100_year']}"
    )
    print(
        f"Disease 100% year   : "
        f"{baseline['disease_100_year']}"
    )
    print(
        f"D5 year 50          : "
        f"{baseline['d5_year_50']:.4f}"
    )

    print()
    print("SENSITIVITY HORIZONS")
    print("-" * 76)

    for key, label in [
        ("reid_100_year", "Re-ID 100%"),
        ("familial_100_year", "Familial 100%"),
        ("disease_100_year", "Disease 100%"),
        ("reid_50_year", "Re-ID 50%"),
        ("familial_50_year", "Familial 50%"),
        ("disease_50_year", "Disease 50%"),
    ]:
        print(
            f"{label:<20}: "
            f"{horizon_summary(rows, key)}"
        )

    d5_50 = np.array(
        [r["d5_year_50"] for r in rows],
        dtype=float,
    )

    print()
    print("D5 YEAR-50 SENSITIVITY")
    print("-" * 76)
    print(f"Minimum : {np.min(d5_50):.4f}")
    print(f"P05     : {np.percentile(d5_50, 5):.4f}")
    print(f"Median  : {np.median(d5_50):.4f}")
    print(f"P95     : {np.percentile(d5_50, 95):.4f}")
    print(f"Maximum : {np.max(d5_50):.4f}")

    print()
    print("MODEL STRUCTURE NOTE")
    print("-" * 76)
    print(
        "The original lifetime model computes a technology-decay "
        "factor but does not use that factor in the reported "
        "re-identification, disease, familial, composite, or D5 "
        "equations."
    )

    print()
    print(f"Output: {OUT}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
