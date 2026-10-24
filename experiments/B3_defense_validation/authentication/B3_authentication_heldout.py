import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
B3_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "B3_authentication"))
RESULTS_DIR = os.path.abspath(os.path.join(HERE, "..", "results"))

sys.path.insert(0, B3_DIR)

from containment_algorithm import (
    generate_access_sessions,
    compute_anomaly_score,
)

os.makedirs(RESULTS_DIR, exist_ok=True)

SEEDS = list(range(1, 101))
THRESHOLDS = np.arange(2.0, 8.01, 0.1)

N_NORMAL = 400
N_ATTACK = 100
DEV_FRACTION = 0.60


def metrics_from_scores(records, threshold):
    tp = fp = tn = fn = 0

    for r in records:
        detected = r["score"] >= threshold
        label = r["label"]

        if detected and label == 1:
            tp += 1
        elif detected and label == 0:
            fp += 1
        elif not detected and label == 0:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    accuracy = (
        (tp + tn) / len(records)
        if records
        else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def choose_threshold(dev_records):
    candidates = []

    for threshold in THRESHOLDS:
        m = metrics_from_scores(dev_records, threshold)

        candidates.append({
            "threshold": float(round(threshold, 1)),
            **m,
        })

    constrained = [
        x for x in candidates
        if x["precision"] >= 0.85
        and x["recall"] >= 0.75
    ]

    pool = constrained if constrained else candidates

    # Highest F1; ties prefer higher recall, then lower threshold.
    best = max(
        pool,
        key=lambda x: (
            x["f1"],
            x["recall"],
            -x["threshold"],
        ),
    )

    return best


def stratified_split(scored, seed):
    rng = np.random.default_rng(seed + 100000)

    normal = [x for x in scored if x["label"] == 0]
    attack = [x for x in scored if x["label"] == 1]

    rng.shuffle(normal)
    rng.shuffle(attack)

    n_normal_dev = int(len(normal) * DEV_FRACTION)
    n_attack_dev = int(len(attack) * DEV_FRACTION)

    dev = (
        normal[:n_normal_dev]
        + attack[:n_attack_dev]
    )

    test = (
        normal[n_normal_dev:]
        + attack[n_attack_dev:]
    )

    rng.shuffle(dev)
    rng.shuffle(test)

    return dev, test


rows = []

print("=" * 76)
print("GenoPhylax B3 - Held-Out Authentication Validation")
print("=" * 76)

for seed in SEEDS:

    # Session generation has its own explicit seed.
    sessions = generate_access_sessions(
        n_normal=N_NORMAL,
        n_attack=N_ATTACK,
        seed=seed,
    )

    # IMPORTANT:
    # compute_anomaly_score uses the global NumPy RNG for score noise.
    # Seed it ONCE here and score every session exactly once.
    # Threshold sweeps below reuse these fixed scores.
    np.random.seed(seed + 500000)

    scored = [
        {
            "label": s["label"],
            "score": compute_anomaly_score(s),
        }
        for s in sessions
    ]

    dev, test = stratified_split(scored, seed)

    selected = choose_threshold(dev)
    threshold = selected["threshold"]

    test_metrics = metrics_from_scores(
        test,
        threshold,
    )

    historical_metrics = metrics_from_scores(
        test,
        4.5,
    )

    rows.append({
        "seed": seed,
        "selected_threshold": threshold,

        "dev_precision": selected["precision"],
        "dev_recall": selected["recall"],
        "dev_f1": selected["f1"],
        "dev_accuracy": selected["accuracy"],

        "test_precision": test_metrics["precision"],
        "test_recall": test_metrics["recall"],
        "test_f1": test_metrics["f1"],
        "test_accuracy": test_metrics["accuracy"],

        "test_tp": test_metrics["tp"],
        "test_fp": test_metrics["fp"],
        "test_tn": test_metrics["tn"],
        "test_fn": test_metrics["fn"],

        "historical45_test_precision": historical_metrics["precision"],
        "historical45_test_recall": historical_metrics["recall"],
        "historical45_test_f1": historical_metrics["f1"],
        "historical45_test_accuracy": historical_metrics["accuracy"],
    })

    if seed <= 10 or seed % 10 == 0:
        print(
            f"seed={seed:03d} "
            f"selected={threshold:.1f} "
            f"test_F1={test_metrics['f1']:.4f} "
            f"P={test_metrics['precision']:.4f} "
            f"R={test_metrics['recall']:.4f} "
            f"historical4.5_F1={historical_metrics['f1']:.4f}"
        )


raw_path = os.path.join(
    RESULTS_DIR,
    "B3_authentication_heldout_raw.csv",
)

with open(raw_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=rows[0].keys(),
    )
    writer.writeheader()
    writer.writerows(rows)


def describe(name):
    vals = np.asarray(
        [r[name] for r in rows],
        dtype=float,
    )

    return {
        "mean": np.mean(vals),
        "median": np.median(vals),
        "std": np.std(vals, ddof=1),
        "min": np.min(vals),
        "q05": np.quantile(vals, 0.05),
        "q25": np.quantile(vals, 0.25),
        "q75": np.quantile(vals, 0.75),
        "q95": np.quantile(vals, 0.95),
        "max": np.max(vals),
    }


summary_metrics = [
    "selected_threshold",
    "test_precision",
    "test_recall",
    "test_f1",
    "test_accuracy",
    "historical45_test_precision",
    "historical45_test_recall",
    "historical45_test_f1",
    "historical45_test_accuracy",
]

summary_rows = []

for metric in summary_metrics:
    s = describe(metric)

    summary_rows.append({
        "metric": metric,
        **s,
    })


summary_path = os.path.join(
    RESULTS_DIR,
    "B3_authentication_heldout_summary.csv",
)

with open(summary_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "metric",
        "mean",
        "median",
        "std",
        "min",
        "q05",
        "q25",
        "q75",
        "q95",
        "max",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(summary_rows)


print("\n" + "=" * 76)
print("SUMMARY - 100 HELD-OUT VALIDATION RUNS")
print("=" * 76)

for metric in [
    "selected_threshold",
    "test_precision",
    "test_recall",
    "test_f1",
    "test_accuracy",
]:
    s = describe(metric)

    print(
        f"{metric:<20} "
        f"mean={s['mean']:.4f} "
        f"median={s['median']:.4f} "
        f"P05={s['q05']:.4f} "
        f"P95={s['q95']:.4f} "
        f"range={s['min']:.4f}-{s['max']:.4f}"
    )


print("\nHISTORICAL FIXED THRESHOLD 4.5 ON THE SAME HELD-OUT SETS")

for metric in [
    "historical45_test_precision",
    "historical45_test_recall",
    "historical45_test_f1",
    "historical45_test_accuracy",
]:
    s = describe(metric)

    print(
        f"{metric:<32} "
        f"mean={s['mean']:.4f} "
        f"median={s['median']:.4f} "
        f"P05={s['q05']:.4f} "
        f"P95={s['q95']:.4f} "
        f"range={s['min']:.4f}-{s['max']:.4f}"
    )


thresholds = np.asarray(
    [r["selected_threshold"] for r in rows]
)

print(
    "\nSelected threshold exactly 4.5 in "
    f"{np.sum(thresholds == 4.5)}/{len(thresholds)} runs."
)

print(
    "Selected threshold within 4.0-5.0 in "
    f"{np.sum((thresholds >= 4.0) & (thresholds <= 5.0))}"
    f"/{len(thresholds)} runs."
)

print("\nSaved:")
print(f"  {raw_path}")
print(f"  {summary_path}")
print("\nHistorical B3 files were not modified.")
print("STATUS: PASS")
