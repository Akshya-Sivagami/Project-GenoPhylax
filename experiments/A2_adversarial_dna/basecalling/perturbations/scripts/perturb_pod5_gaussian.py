#!/usr/bin/env python3
"""
Apply deterministic Gaussian noise to raw POD5 signal.

The perturbation applied independently to each read is:

    noisy_signal = original_signal + N(0, sigma^2)

where:

    sigma = sigma_fraction * standard_deviation(original_signal)

All POD5 read metadata is retained. Only the raw int16 signal array changes.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import sys
from pathlib import Path

import numpy as np
import pod5


INT16_INFO = np.iinfo(np.int16)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply reproducible Gaussian noise to POD5 raw signal."
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input POD5 file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output perturbed POD5 file.",
    )
    parser.add_argument(
        "--sigma-fraction",
        required=True,
        type=float,
        help=(
            "Noise sigma as a fraction of each read's signal standard "
            "deviation. Example: 0.05."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed. Default: 42.",
    )
    parser.add_argument(
        "--max-reads",
        type=int,
        default=None,
        help="Optional maximum number of reads to process.",
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=None,
        help="Optional TSV file for summary metrics.",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.input.is_file():
        raise FileNotFoundError(f"Input POD5 does not exist: {args.input}")

    if args.input.suffix.lower() != ".pod5":
        raise ValueError(f"Input file does not end in .pod5: {args.input}")

    if args.output.exists():
        raise FileExistsError(
            f"Output already exists and will not be overwritten: {args.output}"
        )

    if args.sigma_fraction < 0:
        raise ValueError("--sigma-fraction must be non-negative")

    if args.max_reads is not None and args.max_reads <= 0:
        raise ValueError("--max-reads must be greater than zero")


def perturb_signal(
    signal: np.ndarray,
    sigma_fraction: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, float, int, float]:
    signal_float = signal.astype(np.float64)

    signal_std = float(np.std(signal_float))
    noise_sigma = sigma_fraction * signal_std

    if noise_sigma == 0.0:
        noise = np.zeros(signal.shape, dtype=np.float64)
    else:
        noise = rng.normal(
            loc=0.0,
            scale=noise_sigma,
            size=signal.shape,
        )

    perturbed_float = signal_float + noise

    clipped_low = perturbed_float < INT16_INFO.min
    clipped_high = perturbed_float > INT16_INFO.max
    clipped_samples = int(np.count_nonzero(clipped_low | clipped_high))

    perturbed_signal = np.clip(
        np.rint(perturbed_float),
        INT16_INFO.min,
        INT16_INFO.max,
    ).astype(np.int16)

    mean_absolute_change = float(
        np.mean(
            np.abs(
                perturbed_signal.astype(np.int32)
                - signal.astype(np.int32)
            )
        )
    )

    return (
        perturbed_signal,
        noise_sigma,
        clipped_samples,
        mean_absolute_change,
    )


def write_metrics(
    metrics_path: Path,
    args: argparse.Namespace,
    processed_reads: int,
    total_samples: int,
    changed_samples: int,
    clipped_samples: int,
    mean_noise_sigma: float,
    mean_absolute_change: float,
) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    changed_fraction = (
        changed_samples / total_samples if total_samples else 0.0
    )
    clipped_fraction = (
        clipped_samples / total_samples if total_samples else 0.0
    )

    rows = [
        ("input_pod5", str(args.input.resolve())),
        ("output_pod5", str(args.output.resolve())),
        ("sigma_fraction", args.sigma_fraction),
        ("seed", args.seed),
        ("max_reads", args.max_reads if args.max_reads is not None else "all"),
        ("processed_reads", processed_reads),
        ("total_signal_samples", total_samples),
        ("changed_signal_samples", changed_samples),
        ("changed_sample_fraction", f"{changed_fraction:.10f}"),
        ("clipped_signal_samples", clipped_samples),
        ("clipped_sample_fraction", f"{clipped_fraction:.10f}"),
        ("mean_noise_sigma", f"{mean_noise_sigma:.6f}"),
        ("mean_absolute_signal_change", f"{mean_absolute_change:.6f}"),
    ]

    with metrics_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "value"])
        writer.writerows(rows)


def main() -> int:
    args = parse_args()

    try:
        validate_args(args)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(args.seed)

        processed_reads = 0
        total_samples = 0
        changed_samples = 0
        total_clipped_samples = 0
        noise_sigma_sum = 0.0
        absolute_change_sum = 0.0

        with pod5.Reader(args.input) as reader:
            with pod5.Writer(args.output) as writer:
                for record in reader.reads():
                    if (
                        args.max_reads is not None
                        and processed_reads >= args.max_reads
                    ):
                        break

                    original_read = record.to_read()
                    original_signal = original_read.signal

                    (
                        perturbed_signal,
                        noise_sigma,
                        clipped_samples,
                        mean_absolute_change,
                    ) = perturb_signal(
                        signal=original_signal,
                        sigma_fraction=args.sigma_fraction,
                        rng=rng,
                    )

                    perturbed_read = dataclasses.replace(
                        original_read,
                        signal=perturbed_signal,
                    )

                    writer.add_read(perturbed_read)

                    sample_count = int(original_signal.size)
                    changed_count = int(
                        np.count_nonzero(
                            perturbed_signal != original_signal
                        )
                    )

                    processed_reads += 1
                    total_samples += sample_count
                    changed_samples += changed_count
                    total_clipped_samples += clipped_samples
                    noise_sigma_sum += noise_sigma
                    absolute_change_sum += (
                        mean_absolute_change * sample_count
                    )

                    if processed_reads % 25 == 0:
                        print(
                            f"Processed {processed_reads} reads",
                            file=sys.stderr,
                        )

        if processed_reads == 0:
            raise RuntimeError("No reads were processed")

        mean_noise_sigma = noise_sigma_sum / processed_reads
        mean_absolute_change = absolute_change_sum / total_samples

        if args.metrics is not None:
            write_metrics(
                metrics_path=args.metrics,
                args=args,
                processed_reads=processed_reads,
                total_samples=total_samples,
                changed_samples=changed_samples,
                clipped_samples=total_clipped_samples,
                mean_noise_sigma=mean_noise_sigma,
                mean_absolute_change=mean_absolute_change,
            )

        print("Gaussian POD5 perturbation complete")
        print(f"Input:                 {args.input}")
        print(f"Output:                {args.output}")
        print(f"Sigma fraction:        {args.sigma_fraction}")
        print(f"Seed:                  {args.seed}")
        print(f"Processed reads:       {processed_reads}")
        print(f"Total signal samples:  {total_samples}")
        print(f"Changed samples:       {changed_samples}")
        print(f"Clipped samples:       {total_clipped_samples}")
        print(f"Mean noise sigma:      {mean_noise_sigma:.6f}")
        print(
            "Mean absolute change:  "
            f"{mean_absolute_change:.6f}"
        )

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)

        if args.output.exists():
            try:
                args.output.unlink()
                print(
                    f"Removed incomplete output: {args.output}",
                    file=sys.stderr,
                )
            except OSError:
                pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
