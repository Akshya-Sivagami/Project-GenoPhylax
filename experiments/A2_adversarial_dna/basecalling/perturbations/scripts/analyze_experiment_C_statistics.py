#!/usr/bin/env python3

import argparse
import csv
import math
from pathlib import Path

import numpy as np


LEVELS = ["GN01", "GN05", "GN10"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Aggregate and statistically analyze Experiment C."
    )

    parser.add_argument(
        "--metrics-dir",
        required=True,
        help="Directory containing Experiment C per-read TSV files.",
    )

    parser.add_argument(
        "--output-summary",
        required=True,
        help="Output aggregate TSV.",
    )

    parser.add_argument(
        "--output-pairwise",
        required=True,
        help="Output paired-condition comparison TSV.",
    )

    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=10000,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    return parser.parse_args()


def read_per_read(path):
    rows = []

    with open(path, newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            converted = {}

            for key, value in row.items():
                if key == "read_id":
                    converted[key] = value
                    continue

                try:
                    converted[key] = float(value)
                except (TypeError, ValueError):
                    converted[key] = value

            rows.append(converted)

    return rows


def percentile_ci(values, rng, iterations):
    values = np.asarray(values, dtype=float)
    n = len(values)

    bootstrap_means = np.empty(iterations, dtype=float)

    for index in range(iterations):
        sample_indices = rng.integers(0, n, size=n)
        bootstrap_means[index] = values[sample_indices].mean()

    lower, upper = np.percentile(
        bootstrap_means,
        [2.5, 97.5],
    )

    return float(lower), float(upper)


def sample_standard_deviation(values):
    values = np.asarray(values, dtype=float)

    if len(values) < 2:
        return float("nan")

    return float(np.std(values, ddof=1))


def standardized_paired_effect(values_a, values_b):
    differences = np.asarray(values_b) - np.asarray(values_a)

    standard_deviation = np.std(differences, ddof=1)

    if standard_deviation == 0:
        return 0.0

    return float(np.mean(differences) / standard_deviation)


def sign_test_two_sided(differences):
    differences = np.asarray(differences, dtype=float)
    nonzero = differences[differences != 0]

    n = len(nonzero)

    if n == 0:
        return 1.0

    positive = int(np.count_nonzero(nonzero > 0))
    smaller_tail = min(positive, n - positive)

    probability = sum(
        math.comb(n, k)
        for k in range(smaller_tail + 1)
    ) / (2 ** n)

    return min(1.0, 2 * probability)


def get_column(rows, candidate_names):
    for name in candidate_names:
        if name in rows[0]:
            return name

    raise KeyError(
        f"None of the columns exist: {candidate_names}"
    )


def main():
    args = parse_args()

    metrics_dir = Path(args.metrics_dir)
    rng = np.random.default_rng(args.seed)

    data = {}

    for level in LEVELS:
        path = metrics_dir / (
            f"hg002_1000reads_clean_vs_{level}_seed42_per_read.tsv"
        )

        if not path.is_file():
            raise FileNotFoundError(path)

        data[level] = read_per_read(path)

    first_rows = data["GN01"]

    identity_column = get_column(
        first_rows,
        [
            "sequence_identity_percent",
            "identity_percent",
            "sequence_identity",
        ],
    )

    edit_column = get_column(
        first_rows,
        [
            "edit_distance",
            "total_edit_distance",
        ],
    )

    normalized_edit_column = get_column(
        first_rows,
        [
            "normalized_edit_distance",
        ],
    )

    qscore_change_column = get_column(
        first_rows,
        [
            "qscore_change",
            "mean_qscore_change",
        ],
    )

    length_change_column = get_column(
        first_rows,
        [
            "length_change",
        ],
    )

    summary_fields = [
        "condition",
        "paired_reads",
        "changed_reads",
        "changed_fraction",
        "exact_matches",
        "mean_identity_percent",
        "identity_sd",
        "identity_ci95_lower",
        "identity_ci95_upper",
        "mean_edit_distance",
        "edit_distance_sd",
        "edit_distance_ci95_lower",
        "edit_distance_ci95_upper",
        "median_edit_distance",
        "p95_edit_distance",
        "mean_normalized_edit_distance",
        "mean_qscore_change",
        "qscore_change_sd",
        "qscore_change_ci95_lower",
        "qscore_change_ci95_upper",
        "mean_length_change",
        "reads_edit_distance_ge_100",
        "reads_edit_distance_ge_500",
        "reads_edit_distance_ge_1000",
        "reads_identity_below_95_percent",
        "reads_qscore_drop_ge_5",
        "reads_qscore_drop_ge_10",
    ]

    summary_rows = []

    for level in LEVELS:
        rows = data[level]

        identities = np.asarray(
            [row[identity_column] for row in rows],
            dtype=float,
        )

        edits = np.asarray(
            [row[edit_column] for row in rows],
            dtype=float,
        )

        normalized_edits = np.asarray(
            [row[normalized_edit_column] for row in rows],
            dtype=float,
        )

        qscore_changes = np.asarray(
            [row[qscore_change_column] for row in rows],
            dtype=float,
        )

        length_changes = np.asarray(
            [row[length_change_column] for row in rows],
            dtype=float,
        )

        identity_ci = percentile_ci(
            identities,
            rng,
            args.bootstrap_iterations,
        )

        edit_ci = percentile_ci(
            edits,
            rng,
            args.bootstrap_iterations,
        )

        qscore_ci = percentile_ci(
            qscore_changes,
            rng,
            args.bootstrap_iterations,
        )

        exact_matches = int(np.count_nonzero(edits == 0))
        changed_reads = len(edits) - exact_matches

        summary_rows.append(
            {
                "condition": level,
                "paired_reads": len(rows),
                "changed_reads": changed_reads,
                "changed_fraction": changed_reads / len(rows),
                "exact_matches": exact_matches,
                "mean_identity_percent": identities.mean(),
                "identity_sd": sample_standard_deviation(identities),
                "identity_ci95_lower": identity_ci[0],
                "identity_ci95_upper": identity_ci[1],
                "mean_edit_distance": edits.mean(),
                "edit_distance_sd": sample_standard_deviation(edits),
                "edit_distance_ci95_lower": edit_ci[0],
                "edit_distance_ci95_upper": edit_ci[1],
                "median_edit_distance": np.median(edits),
                "p95_edit_distance": np.percentile(edits, 95),
                "mean_normalized_edit_distance": normalized_edits.mean(),
                "mean_qscore_change": qscore_changes.mean(),
                "qscore_change_sd": sample_standard_deviation(
                    qscore_changes
                ),
                "qscore_change_ci95_lower": qscore_ci[0],
                "qscore_change_ci95_upper": qscore_ci[1],
                "mean_length_change": length_changes.mean(),
                "reads_edit_distance_ge_100": int(
                    np.count_nonzero(edits >= 100)
                ),
                "reads_edit_distance_ge_500": int(
                    np.count_nonzero(edits >= 500)
                ),
                "reads_edit_distance_ge_1000": int(
                    np.count_nonzero(edits >= 1000)
                ),
                "reads_identity_below_95_percent": int(
                    np.count_nonzero(identities < 95)
                ),
                "reads_qscore_drop_ge_5": int(
                    np.count_nonzero(qscore_changes <= -5)
                ),
                "reads_qscore_drop_ge_10": int(
                    np.count_nonzero(qscore_changes <= -10)
                ),
            }
        )

    output_summary = Path(args.output_summary)
    output_summary.parent.mkdir(parents=True, exist_ok=True)

    with open(output_summary, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=summary_fields,
            delimiter="\t",
        )
        writer.writeheader()

        for row in summary_rows:
            writer.writerow(row)

    pairwise_fields = [
        "comparison",
        "metric",
        "mean_difference_second_minus_first",
        "paired_standardized_effect",
        "positive_differences",
        "negative_differences",
        "ties",
        "sign_test_p_value",
    ]

    pairwise_rows = []

    comparisons = [
        ("GN01", "GN05"),
        ("GN05", "GN10"),
        ("GN01", "GN10"),
    ]

    metric_columns = {
        "edit_distance": edit_column,
        "normalized_edit_distance": normalized_edit_column,
        "identity_percent": identity_column,
        "qscore_change": qscore_change_column,
    }

    for first, second in comparisons:
        first_by_id = {
            row["read_id"]: row
            for row in data[first]
        }

        second_by_id = {
            row["read_id"]: row
            for row in data[second]
        }

        common_ids = sorted(
            set(first_by_id) & set(second_by_id)
        )

        if len(common_ids) != 1000:
            raise RuntimeError(
                f"{first} and {second} have "
                f"{len(common_ids)} common IDs"
            )

        for metric_name, column_name in metric_columns.items():
            first_values = np.asarray(
                [
                    first_by_id[read_id][column_name]
                    for read_id in common_ids
                ],
                dtype=float,
            )

            second_values = np.asarray(
                [
                    second_by_id[read_id][column_name]
                    for read_id in common_ids
                ],
                dtype=float,
            )

            differences = second_values - first_values

            pairwise_rows.append(
                {
                    "comparison": f"{first}_vs_{second}",
                    "metric": metric_name,
                    "mean_difference_second_minus_first": (
                        differences.mean()
                    ),
                    "paired_standardized_effect": (
                        standardized_paired_effect(
                            first_values,
                            second_values,
                        )
                    ),
                    "positive_differences": int(
                        np.count_nonzero(differences > 0)
                    ),
                    "negative_differences": int(
                        np.count_nonzero(differences < 0)
                    ),
                    "ties": int(
                        np.count_nonzero(differences == 0)
                    ),
                    "sign_test_p_value": sign_test_two_sided(
                        differences
                    ),
                }
            )

    output_pairwise = Path(args.output_pairwise)

    with open(output_pairwise, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=pairwise_fields,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(pairwise_rows)

    print(f"Aggregate summary: {output_summary}")
    print(f"Pairwise results:  {output_pairwise}")
    print()
    print("Experiment C statistical analysis complete.")


if __name__ == "__main__":
    main()
