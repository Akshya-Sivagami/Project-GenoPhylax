#!/usr/bin/env python3

import argparse
import csv
import statistics
from pathlib import Path


LEVELS = ["GN01", "GN05", "GN10"]
SEEDS = [1, 2, 3]

SIGMA = {
    "GN01": 0.01,
    "GN05": 0.05,
    "GN10": 0.10,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Aggregate Experiment C2 multi-seed results."
    )

    parser.add_argument("--metrics-dir", required=True)
    parser.add_argument("--run-table", required=True)
    parser.add_argument("--aggregate-table", required=True)
    parser.add_argument("--split-table", required=True)
    parser.add_argument("--monotonicity-table", required=True)

    return parser.parse_args()


def read_metric_tsv(path):
    values = {}

    with open(path, newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        next(reader, None)

        for row in reader:
            if len(row) >= 2:
                values[row[0].strip()] = row[1].strip()

    return values


def as_int(values, key):
    return int(float(values[key]))


def as_float(values, key):
    return float(values[key])


def mean_sd(values):
    mean = statistics.mean(values)

    if len(values) >= 2:
        sd = statistics.stdev(values)
    else:
        sd = 0.0

    return mean, sd


def write_tsv(path, fields, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()
    metrics_dir = Path(args.metrics_dir)

    run_rows = []
    split_rows = []

    by_level = {
        level: []
        for level in LEVELS
    }

    by_seed = {
        seed: {}
        for seed in SEEDS
    }

    for seed in SEEDS:
        for level in LEVELS:
            condition = f"{level}_seed{seed}"

            summary_path = metrics_dir / (
                f"hg002_1000reads_clean_vs_{condition}_summary.tsv"
            )

            signal_path = metrics_dir / (
                f"hg002_1000reads_{condition}_signal_metrics.tsv"
            )

            split_path = metrics_dir / (
                f"hg002_1000reads_{condition}_split_summary.tsv"
            )

            for path in (summary_path, signal_path, split_path):
                if not path.is_file():
                    raise FileNotFoundError(path)

            summary = read_metric_tsv(summary_path)
            signal = read_metric_tsv(signal_path)
            split = read_metric_tsv(split_path)

            run = {
                "condition": level,
                "seed": seed,
                "sigma_fraction": SIGMA[level],
                "paired_reads": as_int(summary, "paired_reads"),
                "exact_sequence_matches": as_int(
                    summary,
                    "exact_sequence_matches",
                ),
                "changed_sequences": as_int(
                    summary,
                    "changed_sequences",
                ),
                "changed_sequence_fraction": as_float(
                    summary,
                    "changed_sequence_fraction",
                ),
                "mean_sequence_identity_percent": as_float(
                    summary,
                    "mean_sequence_identity_percent",
                ),
                "mean_edit_distance": as_float(
                    summary,
                    "mean_edit_distance",
                ),
                "median_edit_distance": as_float(
                    summary,
                    "median_edit_distance",
                ),
                "p95_edit_distance": as_float(
                    summary,
                    "p95_edit_distance",
                ),
                "mean_normalized_edit_distance": as_float(
                    summary,
                    "mean_normalized_edit_distance",
                ),
                "mean_qscore_change": as_float(
                    summary,
                    "mean_qscore_change",
                ),
                "mean_length_change": as_float(
                    summary,
                    "mean_length_change",
                ),
                "changed_sample_fraction": as_float(
                    signal,
                    "changed_sample_fraction",
                ),
                "clipped_signal_samples": as_int(
                    signal,
                    "clipped_signal_samples",
                ),
                "operational_bam_records": as_int(
                    split,
                    "total_bam_records",
                ),
                "split_parent_groups": as_int(
                    split,
                    "split_parent_groups",
                ),
                "quickcheck": split["quickcheck"],
            }

            run_rows.append(run)
            by_level[level].append(run)
            by_seed[seed][level] = run

            split_rows.append(
                {
                    "condition": level,
                    "seed": seed,
                    "physical_reads": 1000,
                    "operational_bam_records": run[
                        "operational_bam_records"
                    ],
                    "split_parent_groups": run[
                        "split_parent_groups"
                    ],
                    "split_parent_rate": (
                        run["split_parent_groups"] / 1000
                    ),
                    "extra_bam_records": as_int(
                        split,
                        "extra_bam_records",
                    ),
                    "normalized_bam_records": 1000,
                    "quickcheck": split["quickcheck"],
                }
            )

    run_fields = [
        "condition",
        "seed",
        "sigma_fraction",
        "paired_reads",
        "exact_sequence_matches",
        "changed_sequences",
        "changed_sequence_fraction",
        "mean_sequence_identity_percent",
        "mean_edit_distance",
        "median_edit_distance",
        "p95_edit_distance",
        "mean_normalized_edit_distance",
        "mean_qscore_change",
        "mean_length_change",
        "changed_sample_fraction",
        "clipped_signal_samples",
        "operational_bam_records",
        "split_parent_groups",
        "quickcheck",
    ]

    write_tsv(
        args.run_table,
        run_fields,
        run_rows,
    )

    aggregate_rows = []

    aggregate_metrics = [
        "changed_sequence_fraction",
        "mean_sequence_identity_percent",
        "mean_edit_distance",
        "mean_normalized_edit_distance",
        "mean_qscore_change",
        "mean_length_change",
        "changed_sample_fraction",
        "split_parent_groups",
    ]

    for level in LEVELS:
        rows = by_level[level]

        aggregate = {
            "condition": level,
            "sigma_fraction": SIGMA[level],
            "seeds": len(rows),
        }

        for metric in aggregate_metrics:
            values = [
                float(row[metric])
                for row in rows
            ]

            metric_mean, metric_sd = mean_sd(values)

            aggregate[f"{metric}_mean"] = metric_mean
            aggregate[f"{metric}_sd"] = metric_sd
            aggregate[f"{metric}_min"] = min(values)
            aggregate[f"{metric}_max"] = max(values)

        aggregate_rows.append(aggregate)

    aggregate_fields = [
        "condition",
        "sigma_fraction",
        "seeds",
    ]

    for metric in aggregate_metrics:
        aggregate_fields.extend(
            [
                f"{metric}_mean",
                f"{metric}_sd",
                f"{metric}_min",
                f"{metric}_max",
            ]
        )

    write_tsv(
        args.aggregate_table,
        aggregate_fields,
        aggregate_rows,
    )

    split_fields = [
        "condition",
        "seed",
        "physical_reads",
        "operational_bam_records",
        "split_parent_groups",
        "split_parent_rate",
        "extra_bam_records",
        "normalized_bam_records",
        "quickcheck",
    ]

    write_tsv(
        args.split_table,
        split_fields,
        split_rows,
    )

    monotonicity_rows = []

    for seed in SEEDS:
        gn01 = by_seed[seed]["GN01"]
        gn05 = by_seed[seed]["GN05"]
        gn10 = by_seed[seed]["GN10"]

        identity_monotonic = (
            gn01["mean_sequence_identity_percent"]
            > gn05["mean_sequence_identity_percent"]
            > gn10["mean_sequence_identity_percent"]
        )

        edit_monotonic = (
            gn01["mean_edit_distance"]
            < gn05["mean_edit_distance"]
            < gn10["mean_edit_distance"]
        )

        normalized_edit_monotonic = (
            gn01["mean_normalized_edit_distance"]
            < gn05["mean_normalized_edit_distance"]
            < gn10["mean_normalized_edit_distance"]
        )

        qscore_monotonic = (
            gn01["mean_qscore_change"]
            > gn05["mean_qscore_change"]
            > gn10["mean_qscore_change"]
        )

        changed_fraction_monotonic = (
            gn01["changed_sequence_fraction"]
            <= gn05["changed_sequence_fraction"]
            <= gn10["changed_sequence_fraction"]
        )

        all_primary = (
            identity_monotonic
            and edit_monotonic
            and normalized_edit_monotonic
            and qscore_monotonic
        )

        monotonicity_rows.append(
            {
                "seed": seed,
                "identity_decreases": identity_monotonic,
                "edit_distance_increases": edit_monotonic,
                "normalized_edit_distance_increases": (
                    normalized_edit_monotonic
                ),
                "qscore_change_worsens": qscore_monotonic,
                "changed_fraction_nondecreasing": (
                    changed_fraction_monotonic
                ),
                "all_primary_metrics_monotonic": all_primary,
            }
        )

    monotonicity_fields = [
        "seed",
        "identity_decreases",
        "edit_distance_increases",
        "normalized_edit_distance_increases",
        "qscore_change_worsens",
        "changed_fraction_nondecreasing",
        "all_primary_metrics_monotonic",
    ]

    write_tsv(
        args.monotonicity_table,
        monotonicity_fields,
        monotonicity_rows,
    )

    print("Experiment C2 aggregation complete.")
    print(f"Run table:          {args.run_table}")
    print(f"Aggregate table:    {args.aggregate_table}")
    print(f"Split table:        {args.split_table}")
    print(f"Monotonicity table: {args.monotonicity_table}")


if __name__ == "__main__":
    main()
