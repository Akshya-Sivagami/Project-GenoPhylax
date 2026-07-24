from __future__ import annotations

import csv
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pod5


def main() -> int:
    if len(sys.argv) != 7:
        print(
            "Usage: create_local_interpolation_attack.py "
            "<clean.pod5> <intervals.tsv> <attacked.pod5> "
            "<metrics.tsv> <summary.txt> <validation.txt>",
            file=sys.stderr,
        )
        return 2

    clean_path = Path(sys.argv[1])
    intervals_path = Path(sys.argv[2])
    attacked_path = Path(sys.argv[3])
    metrics_path = Path(sys.argv[4])
    summary_path = Path(sys.argv[5])
    validation_path = Path(sys.argv[6])

    intervals: dict[str, dict[str, int]] = {}

    with intervals_path.open(
        "rt",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        required = {
            "raw_parent_id",
            "context_signal_start",
            "context_signal_end",
            "target_signal_start",
            "target_signal_end",
            "raw_signal_samples",
        }

        missing_columns = required - set(reader.fieldnames or [])

        if missing_columns:
            raise SystemExit(
                "ERROR: Missing interval columns: "
                + ", ".join(sorted(missing_columns))
            )

        for row in reader:
            read_id = row["raw_parent_id"]

            if read_id in intervals:
                raise SystemExit(
                    f"ERROR: Duplicate interval for {read_id}"
                )

            intervals[read_id] = {
                "context_start": int(row["context_signal_start"]),
                "context_end": int(row["context_signal_end"]),
                "target_start": int(row["target_signal_start"]),
                "target_end": int(row["target_signal_end"]),
                "raw_signal_samples": int(row["raw_signal_samples"]),
            }

    if len(intervals) != 10:
        raise SystemExit(
            f"ERROR: Expected 10 attack intervals, "
            f"found {len(intervals)}"
        )

    if attacked_path.exists():
        attacked_path.unlink()

    metrics_rows: list[dict[str, Any]] = []
    observed_ids: set[str] = set()
    attacked_ids: set[str] = set()
    untouched_ids: set[str] = set()

    clean_signals: dict[str, np.ndarray] = {}
    attacked_signals: dict[str, np.ndarray] = {}

    with pod5.Reader(clean_path) as reader, pod5.Writer(
        attacked_path,
        software_name=(
            "GenoPhylax Experiment E "
            "local interpolation attack"
        ),
    ) as writer:
        for record in reader.reads():
            read_id = str(record.read_id)

            if read_id in observed_ids:
                raise RuntimeError(
                    f"Duplicate raw read in clean POD5: {read_id}"
                )

            observed_ids.add(read_id)

            writable_read = record.to_read()
            clean_signal = np.asarray(
                writable_read.signal
            ).copy()

            attacked_signal = clean_signal.copy()

            clean_signals[read_id] = clean_signal

            if read_id in intervals:
                interval = intervals[read_id]

                start = interval["context_start"]
                end = interval["context_end"]

                if len(clean_signal) != interval["raw_signal_samples"]:
                    raise RuntimeError(
                        f"Signal-length mismatch for {read_id}: "
                        f"POD5={len(clean_signal)}, "
                        f"mapping={interval['raw_signal_samples']}"
                    )

                if not 0 <= start < end <= len(clean_signal):
                    raise RuntimeError(
                        f"Invalid interval for {read_id}: "
                        f"{start}:{end} of {len(clean_signal)}"
                    )

                window_length = end - start

                left_index = max(0, start - 1)
                right_index = min(
                    len(clean_signal) - 1,
                    end,
                )

                left_value = float(clean_signal[left_index])
                right_value = float(clean_signal[right_index])

                interpolated = np.linspace(
                    left_value,
                    right_value,
                    num=window_length + 2,
                    dtype=np.float64,
                )[1:-1]

                dtype = clean_signal.dtype

                if np.issubdtype(dtype, np.integer):
                    limits = np.iinfo(dtype)

                    interpolated = np.clip(
                        np.rint(interpolated),
                        limits.min,
                        limits.max,
                    )

                attacked_signal[start:end] = interpolated.astype(
                    dtype,
                    copy=False,
                )

                attacked_ids.add(read_id)

                changed_mask = (
                    attacked_signal[start:end]
                    != clean_signal[start:end]
                )

                changed_samples = int(
                    np.count_nonzero(changed_mask)
                )

                outside_identical = bool(
                    np.array_equal(
                        attacked_signal[:start],
                        clean_signal[:start],
                    )
                    and np.array_equal(
                        attacked_signal[end:],
                        clean_signal[end:],
                    )
                )

                metrics_rows.append(
                    {
                        "read_id": read_id,
                        "attack_type": "local_linear_interpolation",
                        "context_signal_start": start,
                        "context_signal_end": end,
                        "window_samples": window_length,
                        "changed_samples": changed_samples,
                        "changed_fraction_of_window": (
                            changed_samples / window_length
                        ),
                        "changed_fraction_of_read": (
                            changed_samples / len(clean_signal)
                        ),
                        "clean_window_mean": float(
                            np.mean(clean_signal[start:end])
                        ),
                        "attacked_window_mean": float(
                            np.mean(attacked_signal[start:end])
                        ),
                        "clean_window_std": float(
                            np.std(clean_signal[start:end])
                        ),
                        "attacked_window_std": float(
                            np.std(attacked_signal[start:end])
                        ),
                        "left_boundary_value": int(
                            clean_signal[left_index]
                        ),
                        "right_boundary_value": int(
                            clean_signal[right_index]
                        ),
                        "outside_window_identical": int(
                            outside_identical
                        ),
                        "raw_signal_samples": len(clean_signal),
                    }
                )
            else:
                untouched_ids.add(read_id)

            attacked_signals[read_id] = attacked_signal

            modified_read = replace(
                writable_read,
                signal=attacked_signal,
            )

            writer.add_read(modified_read)

    missing_attack_ids = sorted(
        set(intervals) - attacked_ids
    )

    unexpected_attack_ids = sorted(
        attacked_ids - set(intervals)
    )

    if missing_attack_ids:
        raise RuntimeError(
            "Attack IDs absent from POD5: "
            + ", ".join(missing_attack_ids)
        )

    if unexpected_attack_ids:
        raise RuntimeError(
            "Unexpected attacked IDs: "
            + ", ".join(unexpected_attack_ids)
        )

    metrics_rows.sort(
        key=lambda row: str(row["read_id"])
    )

    metrics_fields = [
        "read_id",
        "attack_type",
        "context_signal_start",
        "context_signal_end",
        "window_samples",
        "changed_samples",
        "changed_fraction_of_window",
        "changed_fraction_of_read",
        "clean_window_mean",
        "attacked_window_mean",
        "clean_window_std",
        "attacked_window_std",
        "left_boundary_value",
        "right_boundary_value",
        "outside_window_identical",
        "raw_signal_samples",
    ]

    with metrics_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=metrics_fields,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(metrics_rows)

    total_signal_samples = sum(
        len(signal)
        for signal in clean_signals.values()
    )

    total_attacked_read_samples = sum(
        len(clean_signals[read_id])
        for read_id in attacked_ids
    )

    total_window_samples = sum(
        int(row["window_samples"])
        for row in metrics_rows
    )

    total_changed_samples = sum(
        int(row["changed_samples"])
        for row in metrics_rows
    )

    outside_checks_pass = all(
        int(row["outside_window_identical"]) == 1
        for row in metrics_rows
    )

    untouched_checks: list[tuple[str, bool]] = []

    for read_id in sorted(untouched_ids):
        identical = np.array_equal(
            clean_signals[read_id],
            attacked_signals[read_id],
        )

        untouched_checks.append(
            (read_id, bool(identical))
        )

    untouched_pass = all(
        result
        for _, result in untouched_checks
    )

    summary = [
        "Experiment E local interpolation attack",
        "=======================================",
        "Attack: linear interpolation across mapped +/-5-base windows",
        f"Input raw reads: {len(observed_ids)}",
        f"Attacked raw reads: {len(attacked_ids)}",
        f"Untouched raw reads: {len(untouched_ids)}",
        f"Attack windows: {len(metrics_rows)}",
        f"Total signal samples in POD5: {total_signal_samples}",
        f"Total samples in attacked reads: "
        f"{total_attacked_read_samples}",
        f"Total mapped window samples: {total_window_samples}",
        f"Actually changed samples: {total_changed_samples}",
        f"Changed fraction of all POD5 signal: "
        f"{total_changed_samples / total_signal_samples:.10f}",
        f"Changed fraction of attacked-read signal: "
        f"{total_changed_samples / total_attacked_read_samples:.10f}",
        f"Outside-window identity checks: "
        f"{'PASS' if outside_checks_pass else 'FAIL'}",
        f"Untouched-read identity checks: "
        f"{'PASS' if untouched_pass else 'FAIL'}",
        "",
        "Untouched reads:",
    ]

    summary.extend(
        f"  {read_id}: "
        f"{'IDENTICAL' if result else 'CHANGED'}"
        for read_id, result in untouched_checks
    )

    summary_path.write_text(
        "\n".join(summary) + "\n",
        encoding="utf-8",
    )

    validation_lines = [
        "Experiment E attacked POD5 validation",
        "=====================================",
        f"Observed read IDs: {len(observed_ids)}",
        f"Expected attack IDs: {len(intervals)}",
        f"Applied attack IDs: {len(attacked_ids)}",
        f"Untouched IDs: {len(untouched_ids)}",
        f"Missing attack IDs: {len(missing_attack_ids)}",
        f"Unexpected attack IDs: {len(unexpected_attack_ids)}",
        f"Outside attack windows identical: "
        f"{outside_checks_pass}",
        f"Untouched reads identical: {untouched_pass}",
    ]

    validation_path.write_text(
        "\n".join(validation_lines) + "\n",
        encoding="utf-8",
    )

    print("\n".join(summary))

    if len(observed_ids) != 11:
        print("ERROR: Expected 11 reads in attacked POD5")
        return 1

    if len(attacked_ids) != 10:
        print("ERROR: Expected exactly 10 attacked reads")
        return 1

    if len(untouched_ids) != 1:
        print("ERROR: Expected exactly one untouched read")
        return 1

    if not outside_checks_pass:
        print("ERROR: Samples outside an attack window changed")
        return 1

    if not untouched_pass:
        print("ERROR: Untouched read changed")
        return 1

    if total_changed_samples == 0:
        print("ERROR: Attack changed zero samples")
        return 1

    print()
    print("Localized attack construction: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
