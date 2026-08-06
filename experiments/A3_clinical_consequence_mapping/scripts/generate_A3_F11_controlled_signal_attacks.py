#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pod5


CONDITIONS = {
    0: "W0",
    2: "PM2",
    5: "PM5",
    10: "PM10",
    20: "PM20",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate F11 local-linear-interpolation POD5 attacks "
            "for W0, PM2, PM5, PM10 and PM20."
        )
    )

    parser.add_argument(
        "--source-pod5",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--window-map",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--attack-ids",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--summary-tsv",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--summary-txt",
        required=True,
        type=Path,
    )

    return parser.parse_args()


def load_attack_ids(path: Path) -> set[str]:
    attack_ids = {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    if len(attack_ids) != 14:
        raise RuntimeError(
            f"Expected 14 attack IDs, found {len(attack_ids)}."
        )

    return attack_ids


def load_windows(
    path: Path,
    attack_ids: set[str],
) -> dict[int, dict[str, dict[str, int]]]:
    grouped: dict[int, dict[str, dict[str, int]]] = defaultdict(dict)

    with path.open(
        "rt",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        required = {
            "parent_read_id",
            "context_bases_each_side",
            "window_signal_start_sample",
            "window_signal_end_sample_exclusive",
            "window_signal_span_samples",
            "total_signal_samples",
        }

        missing = required - set(reader.fieldnames or [])

        if missing:
            raise RuntimeError(
                "Window map is missing columns: "
                + ", ".join(sorted(missing))
            )

        for row in reader:
            read_id = row["parent_read_id"].strip()
            context = int(row["context_bases_each_side"])

            if context not in CONDITIONS:
                raise RuntimeError(
                    f"Unexpected context value: {context}"
                )

            if read_id not in attack_ids:
                raise RuntimeError(
                    f"Window map contains non-attack ID: {read_id}"
                )

            if read_id in grouped[context]:
                raise RuntimeError(
                    f"Duplicate window for {read_id}, context {context}"
                )

            start = int(row["window_signal_start_sample"])
            end = int(row["window_signal_end_sample_exclusive"])
            span = int(row["window_signal_span_samples"])
            total = int(row["total_signal_samples"])

            if not 0 <= start < end <= total:
                raise RuntimeError(
                    f"Invalid window for {read_id}/PM{context}: "
                    f"{start}:{end} of {total}"
                )

            if end - start != span:
                raise RuntimeError(
                    f"Window-span mismatch for {read_id}/PM{context}"
                )

            grouped[context][read_id] = {
                "start": start,
                "end": end,
                "span": span,
                "total": total,
            }

    if set(grouped) != set(CONDITIONS):
        raise RuntimeError(
            "Window contexts do not match "
            f"{sorted(CONDITIONS)}: observed {sorted(grouped)}"
        )

    for context in CONDITIONS:
        observed = set(grouped[context])

        if observed != attack_ids:
            missing = sorted(attack_ids - observed)
            extra = sorted(observed - attack_ids)

            raise RuntimeError(
                f"Context {context} ID mismatch; "
                f"missing={missing}, extra={extra}"
            )

        if len(grouped[context]) != 14:
            raise RuntimeError(
                f"Expected 14 windows for context {context}, "
                f"found {len(grouped[context])}."
            )

    return grouped


def interpolate_window(
    original: np.ndarray,
    start: int,
    end: int,
) -> np.ndarray:
    attacked = original.copy()

    if not 0 <= start < end <= len(original):
        raise ValueError(
            f"Invalid interpolation interval: "
            f"{start}:{end} of {len(original)}"
        )

    left_index = max(0, start - 1)
    right_index = min(len(original) - 1, end)

    left_value = float(original[left_index])
    right_value = float(original[right_index])

    window_length = end - start

    interpolated = np.linspace(
        left_value,
        right_value,
        num=window_length + 2,
        dtype=np.float64,
    )[1:-1]

    if np.issubdtype(original.dtype, np.integer):
        limits = np.iinfo(original.dtype)

        interpolated = np.clip(
            np.rint(interpolated),
            limits.min,
            limits.max,
        )

    attacked[start:end] = interpolated.astype(
        original.dtype,
        copy=False,
    )

    return attacked


def generate_condition(
    source_pod5: Path,
    output_pod5: Path,
    audit_path: Path,
    context: int,
    condition: str,
    condition_windows: dict[str, dict[str, int]],
    attack_ids: set[str],
) -> dict[str, Any]:
    if output_pod5.exists():
        output_pod5.unlink()

    observed_ids: set[str] = set()
    attacked_ids: set[str] = set()
    untouched_ids: set[str] = set()

    audit_rows: list[dict[str, Any]] = []

    clean_signals: dict[str, np.ndarray] = {}
    output_signals: dict[str, np.ndarray] = {}

    with pod5.Reader(source_pod5) as reader, pod5.Writer(
        output_pod5,
        software_name=(
            "GenoPhylax A3 F11 controlled local "
            f"interpolation attack {condition}"
        ),
    ) as writer:
        for record in reader.reads():
            read_id = str(record.read_id)

            if read_id in observed_ids:
                raise RuntimeError(
                    f"Duplicate source POD5 read: {read_id}"
                )

            observed_ids.add(read_id)

            writable_read = record.to_read()

            original_signal = np.asarray(
                writable_read.signal
            ).copy()

            clean_signals[read_id] = original_signal

            if read_id in attack_ids:
                window = condition_windows.get(read_id)

                if window is None:
                    raise RuntimeError(
                        f"Missing {condition} window for {read_id}"
                    )

                mapped_total = int(window["total"])
                pod5_total = int(len(original_signal))
                signal_length_delta = pod5_total - mapped_total

                start = int(window["start"])
                end = int(window["end"])

                # The Dorado ns tag and the physical POD5 signal can differ
                # by a few trailing samples. The POD5 array is authoritative
                # for writing. The mapped interval remains valid only when it
                # lies completely inside the actual POD5 signal.
                if not 0 <= start < end <= pod5_total:
                    raise RuntimeError(
                        f"Mapped window is outside actual POD5 signal for "
                        f"{read_id}: window={start}:{end}, "
                        f"POD5={pod5_total}, mapped_total={mapped_total}"
                    )

                attacked_signal = interpolate_window(
                    original_signal,
                    start,
                    end,
                )

                changed_mask = (
                    original_signal != attacked_signal
                )

                inside_changed = int(
                    changed_mask[start:end].sum()
                )

                outside_changed = int(
                    changed_mask[:start].sum()
                    + changed_mask[end:].sum()
                )

                total_changed = int(
                    changed_mask.sum()
                )

                changed_indices = np.flatnonzero(
                    changed_mask
                )

                if outside_changed != 0:
                    status = "FAIL_OUTSIDE_CHANGED"
                elif total_changed == 0:
                    status = "FAIL_NO_CHANGE"
                elif (
                    changed_indices.size > 0
                    and (
                        int(changed_indices.min()) < start
                        or int(changed_indices.max()) >= end
                    )
                ):
                    status = "FAIL_CHANGE_OUTSIDE_WINDOW"
                else:
                    status = "PASS"

                attacked_ids.add(read_id)

                audit_rows.append(
                    {
                        "condition": condition,
                        "context_bases_each_side": context,
                        "parent_read_id": read_id,
                        "attack_signal_start": start,
                        "attack_signal_end_exclusive": end,
                        "attack_window_samples": end - start,
                        "changed_samples_inside": inside_changed,
                        "changed_samples_outside": outside_changed,
                        "total_changed_samples": total_changed,
                        "mapped_total_signal_samples": mapped_total,
                        "pod5_total_signal_samples": pod5_total,
                        "signal_length_delta_samples": signal_length_delta,
                        "total_signal_samples": pod5_total,
                        "changed_fraction_of_window": (
                            total_changed / (end - start)
                        ),
                        "changed_fraction_of_read": (
                            total_changed / len(original_signal)
                        ),
                        "clean_window_mean": float(
                            np.mean(original_signal[start:end])
                        ),
                        "attacked_window_mean": float(
                            np.mean(attacked_signal[start:end])
                        ),
                        "clean_window_std": float(
                            np.std(original_signal[start:end])
                        ),
                        "attacked_window_std": float(
                            np.std(attacked_signal[start:end])
                        ),
                        "outside_window_identical": int(
                            outside_changed == 0
                        ),
                        "status": status,
                    }
                )
            else:
                attacked_signal = original_signal.copy()
                untouched_ids.add(read_id)

            output_signals[read_id] = attacked_signal

            attacked_read = replace(
                writable_read,
                signal=attacked_signal,
            )

            writer.add_read(attacked_read)

    if observed_ids != attack_ids | untouched_ids:
        raise RuntimeError(
            f"{condition}: inconsistent observed-ID accounting"
        )

    if attacked_ids != attack_ids:
        missing = sorted(attack_ids - attacked_ids)
        extra = sorted(attacked_ids - attack_ids)

        raise RuntimeError(
            f"{condition}: attack-ID mismatch; "
            f"missing={missing}, extra={extra}"
        )

    if len(observed_ids) != 15:
        raise RuntimeError(
            f"{condition}: expected 15 source reads, "
            f"found {len(observed_ids)}."
        )

    if len(attacked_ids) != 14:
        raise RuntimeError(
            f"{condition}: expected 14 attacked reads, "
            f"found {len(attacked_ids)}."
        )

    if len(untouched_ids) != 1:
        raise RuntimeError(
            f"{condition}: expected 1 untouched read, "
            f"found {len(untouched_ids)}."
        )

    untouched_pass = all(
        np.array_equal(
            clean_signals[read_id],
            output_signals[read_id],
        )
        for read_id in untouched_ids
    )

    pass_rows = [
        row
        for row in audit_rows
        if row["status"] == "PASS"
    ]

    status_counts = Counter(
        row["status"]
        for row in audit_rows
    )

    total_changed = sum(
        int(row["total_changed_samples"])
        for row in audit_rows
    )

    total_window_samples = sum(
        int(row["attack_window_samples"])
        for row in audit_rows
    )

    total_attacked_signal = sum(
        len(clean_signals[read_id])
        for read_id in attacked_ids
    )

    outside_changed = sum(
        int(row["changed_samples_outside"])
        for row in audit_rows
    )

    condition_status = (
        "PASS"
        if (
            len(audit_rows) == 14
            and len(pass_rows) == 14
            and outside_changed == 0
            and untouched_pass
            and total_changed > 0
        )
        else "FAIL"
    )

    audit_fields = [
        "condition",
        "context_bases_each_side",
        "parent_read_id",
        "attack_signal_start",
        "attack_signal_end_exclusive",
        "attack_window_samples",
        "changed_samples_inside",
        "changed_samples_outside",
        "total_changed_samples",
        "mapped_total_signal_samples",
        "pod5_total_signal_samples",
        "signal_length_delta_samples",
        "total_signal_samples",
        "changed_fraction_of_window",
        "changed_fraction_of_read",
        "clean_window_mean",
        "attacked_window_mean",
        "clean_window_std",
        "attacked_window_std",
        "outside_window_identical",
        "status",
    ]

    with audit_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=audit_fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(
            sorted(
                audit_rows,
                key=lambda row: row["parent_read_id"],
            )
        )

    # Re-open the generated POD5 to confirm all written IDs.
    output_ids: set[str] = set()

    with pod5.Reader(output_pod5) as reader:
        for record in reader.reads():
            output_ids.add(str(record.read_id))

    if output_ids != observed_ids:
        raise RuntimeError(
            f"{condition}: generated POD5 ID mismatch"
        )

    return {
        "condition": condition,
        "context_bases_each_side": context,
        "source_reads": len(observed_ids),
        "attacked_reads": len(attacked_ids),
        "untouched_reads": len(untouched_ids),
        "audit_rows": len(audit_rows),
        "pass_rows": len(pass_rows),
        "total_window_samples": total_window_samples,
        "total_changed_samples": total_changed,
        "changed_fraction_of_windows": (
            total_changed / total_window_samples
        ),
        "changed_fraction_of_attacked_signal": (
            total_changed / total_attacked_signal
        ),
        "outside_changed_samples": outside_changed,
        "minimum_window_samples": min(
            int(row["attack_window_samples"])
            for row in audit_rows
        ),
        "maximum_window_samples": max(
            int(row["attack_window_samples"])
            for row in audit_rows
        ),
        "untouched_read_identity": (
            "PASS" if untouched_pass else "FAIL"
        ),
        "status_counts": ",".join(
            f"{key}:{status_counts[key]}"
            for key in sorted(status_counts)
        ),
        "output_pod5": str(output_pod5),
        "audit_tsv": str(audit_path),
        "status": condition_status,
    }


def main() -> int:
    args = parse_args()

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    attack_ids = load_attack_ids(args.attack_ids)

    windows = load_windows(
        args.window_map,
        attack_ids,
    )

    summary_rows = []

    for context, condition in CONDITIONS.items():
        condition_dir = args.output_dir / condition

        condition_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pod5 = (
            condition_dir
            / f"F11_{condition}_local_interpolation.pod5"
        )

        audit_path = (
            condition_dir
            / f"F11_{condition}_attack_audit.tsv"
        )

        print()
        print("=" * 60)
        print(f"Generating {condition}")
        print("=" * 60)

        summary = generate_condition(
            source_pod5=args.source_pod5,
            output_pod5=output_pod5,
            audit_path=audit_path,
            context=context,
            condition=condition,
            condition_windows=windows[context],
            attack_ids=attack_ids,
        )

        summary_rows.append(summary)

        print(
            f"Reads passed: "
            f"{summary['pass_rows']}/"
            f"{summary['audit_rows']}"
        )
        print(
            f"Changed samples: "
            f"{summary['total_changed_samples']}"
        )
        print(
            f"Outside changed samples: "
            f"{summary['outside_changed_samples']}"
        )
        print(
            f"Window range: "
            f"{summary['minimum_window_samples']}–"
            f"{summary['maximum_window_samples']} samples"
        )
        print(f"Status: {summary['status']}")

    summary_fields = [
        "condition",
        "context_bases_each_side",
        "source_reads",
        "attacked_reads",
        "untouched_reads",
        "audit_rows",
        "pass_rows",
        "total_window_samples",
        "total_changed_samples",
        "changed_fraction_of_windows",
        "changed_fraction_of_attacked_signal",
        "outside_changed_samples",
        "minimum_window_samples",
        "maximum_window_samples",
        "untouched_read_identity",
        "status_counts",
        "output_pod5",
        "audit_tsv",
        "status",
    ]

    with args.summary_tsv.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=summary_fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(summary_rows)

    overall_pass = all(
        row["status"] == "PASS"
        for row in summary_rows
    )

    lines = [
        "A3 F11 Controlled Signal Attack Generation",
        "==========================================",
        "",
        "Attack method: local linear interpolation",
        "Source raw-signal reads: 15",
        "Attacked clean ALT parents per condition: 14",
        "Untouched excluded parent per condition: 1",
        "Conditions: W0, PM2, PM5, PM10, PM20",
        "",
    ]

    for row in summary_rows:
        lines.extend(
            [
                f"{row['condition']}:",
                f"  Context bases each side: "
                f"{row['context_bases_each_side']}",
                f"  Reads passed: "
                f"{row['pass_rows']}/{row['audit_rows']}",
                f"  Window samples: "
                f"{row['minimum_window_samples']}–"
                f"{row['maximum_window_samples']}",
                f"  Changed samples: "
                f"{row['total_changed_samples']}",
                f"  Outside changed samples: "
                f"{row['outside_changed_samples']}",
                f"  Untouched read identity: "
                f"{row['untouched_read_identity']}",
                f"  Status: {row['status']}",
                "",
            ]
        )

    lines.append(
        "Overall status: "
        + (
            "READY_FOR_ATTACKED_REBASECALLING"
            if overall_pass
            else "ATTACK_GENERATION_REQUIRES_REVIEW"
        )
    )

    args.summary_txt.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print()
    print(args.summary_txt.read_text(encoding="utf-8"))

    if not overall_pass:
        raise SystemExit(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
