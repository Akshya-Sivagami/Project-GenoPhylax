#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from pathlib import Path

import numpy as np
import pod5
import pysam


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate PM5 local-interpolation signal attacks "
            "for the L2 and L3 cross-locus cohorts."
        )
    )

    parser.add_argument("--windows-tsv", required=True)

    parser.add_argument("--l2-pod5", required=True)
    parser.add_argument("--l2-bam", required=True)
    parser.add_argument("--l2-output", required=True)

    parser.add_argument("--l3-pod5", required=True)
    parser.add_argument("--l3-bam", required=True)
    parser.add_argument("--l3-output", required=True)

    parser.add_argument("--audit-tsv", required=True)
    parser.add_argument("--summary-tsv", required=True)

    parser.add_argument(
        "--context-bases",
        type=int,
        default=5,
    )

    return parser.parse_args()


def load_windows(path: Path):
    rows = {}

    with path.open(
        "rt",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        for row in reader:
            if row["status"] != "PASS":
                raise RuntimeError(
                    "Non-PASS window row encountered: "
                    f'{row["candidate"]} '
                    f'{row["parent_id"]} '
                    f'{row["status"]}'
                )

            key = (
                row["candidate"],
                row["parent_id"],
            )

            if key in rows:
                raise RuntimeError(
                    f"Duplicate window key: {key}"
                )

            rows[key] = row

    return rows


def load_unaligned_records(path: Path):
    records = {}

    with pysam.AlignmentFile(
        str(path),
        "rb",
        check_sq=False,
    ) as bam:
        for record in bam.fetch(until_eof=True):
            read_id = record.query_name

            if read_id in records:
                raise RuntimeError(
                    "Duplicate unaligned BAM record: "
                    f"{read_id}"
                )

            records[read_id] = record

    return records


def build_base_intervals(
    record: pysam.AlignedSegment,
):
    if not record.has_tag("mv"):
        raise RuntimeError(
            f"Missing mv tag: {record.query_name}"
        )

    if not record.has_tag("ts"):
        raise RuntimeError(
            f"Missing ts tag: {record.query_name}"
        )

    sequence = record.query_sequence or ""
    sequence_length = len(sequence)

    mv = list(record.get_tag("mv"))

    if len(mv) < 2:
        raise RuntimeError(
            f"Invalid mv tag: {record.query_name}"
        )

    stride = int(mv[0])
    moves = [int(value) for value in mv[1:]]
    trimmed_samples = int(record.get_tag("ts"))

    starts = []
    emitted = 0

    for block_index, move in enumerate(moves):
        if move <= 0:
            continue

        for _ in range(move):
            if emitted >= sequence_length:
                break

            starts.append(
                trimmed_samples
                + block_index * stride
            )

            emitted += 1

    if len(starts) < sequence_length:
        raise RuntimeError(
            "Move table emitted fewer bases than sequence "
            f"for {record.query_name}: "
            f"{len(starts)} < {sequence_length}"
        )

    starts = starts[:sequence_length]

    intervals = []

    move_table_end = (
        trimmed_samples
        + len(moves) * stride
    )

    for index, start in enumerate(starts):
        if index + 1 < len(starts):
            end = starts[index + 1]
        else:
            end = move_table_end

        if end <= start:
            end = start + stride

        intervals.append((start, end))

    return intervals, stride


def interpolate_window(
    original: np.ndarray,
    start: int,
    end: int,
):
    if not (0 <= start < end <= len(original)):
        raise RuntimeError(
            "Invalid interpolation interval: "
            f"{start}:{end} of {len(original)}"
        )

    attacked = original.copy()

    left_index = start - 1
    right_index = end

    if left_index >= 0 and right_index < len(original):
        left_value = float(original[left_index])
        right_value = float(original[right_index])

        replacement = np.linspace(
            left_value,
            right_value,
            num=(end - start) + 2,
            dtype=np.float64,
        )[1:-1]

    elif left_index >= 0:
        replacement = np.full(
            end - start,
            float(original[left_index]),
            dtype=np.float64,
        )

    elif right_index < len(original):
        replacement = np.full(
            end - start,
            float(original[right_index]),
            dtype=np.float64,
        )

    else:
        raise RuntimeError(
            "Attack interval covers entire signal"
        )

    dtype = original.dtype
    limits = np.iinfo(dtype)

    replacement = np.rint(replacement)
    replacement = np.clip(
        replacement,
        limits.min,
        limits.max,
    ).astype(dtype)

    attacked[start:end] = replacement

    return attacked


def attack_candidate(
    candidate: str,
    input_pod5: Path,
    unaligned_bam: Path,
    output_pod5: Path,
    window_rows: dict,
    context_bases: int,
):
    bam_records = load_unaligned_records(
        unaligned_bam
    )

    expected_ids = {
        parent_id
        for candidate_name, parent_id
        in window_rows
        if candidate_name == candidate
    }

    if len(expected_ids) != 10:
        raise RuntimeError(
            f"{candidate}: expected 10 windows, "
            f"found {len(expected_ids)}"
        )

    if output_pod5.exists():
        output_pod5.unlink()

    audit_rows = []
    observed_ids = set()

    with pod5.Reader(input_pod5) as reader:
        with pod5.Writer(output_pod5) as writer:
            for record in reader.reads():
                read_id = str(record.read_id)

                if read_id not in expected_ids:
                    raise RuntimeError(
                        f"{candidate}: unexpected POD5 read "
                        f"{read_id}"
                    )

                if read_id in observed_ids:
                    raise RuntimeError(
                        f"{candidate}: duplicate POD5 read "
                        f"{read_id}"
                    )

                observed_ids.add(read_id)

                bam_record = bam_records.get(read_id)

                if bam_record is None:
                    raise RuntimeError(
                        f"{candidate}: missing BAM record "
                        f"{read_id}"
                    )

                window = window_rows[
                    (candidate, read_id)
                ]

                target_base_index = int(
                    window[
                        "original_base_index_0based"
                    ]
                )

                intervals, stride = (
                    build_base_intervals(bam_record)
                )

                first_base = max(
                    0,
                    target_base_index
                    - context_bases,
                )

                last_base = min(
                    len(intervals) - 1,
                    target_base_index
                    + context_bases,
                )

                attack_start = intervals[
                    first_base
                ][0]

                attack_end = intervals[
                    last_base
                ][1]

                original_signal = np.asarray(
                    record.signal
                )

                attack_start = max(
                    0,
                    attack_start,
                )

                attack_end = min(
                    len(original_signal),
                    attack_end,
                )

                attacked_signal = interpolate_window(
                    original_signal,
                    attack_start,
                    attack_end,
                )

                changed_mask = (
                    original_signal
                    != attacked_signal
                )

                changed_indices = np.flatnonzero(
                    changed_mask
                )

                outside_changed = int(
                    changed_mask[:attack_start].sum()
                    + changed_mask[attack_end:].sum()
                )

                inside_changed = int(
                    changed_mask[
                        attack_start:attack_end
                    ].sum()
                )

                total_changed = int(
                    changed_mask.sum()
                )

                if outside_changed != 0:
                    status = "FAIL_OUTSIDE_CHANGED"
                elif total_changed == 0:
                    status = "FAIL_NO_CHANGE"
                elif (
                    changed_indices.size > 0
                    and (
                        changed_indices.min()
                        < attack_start
                        or changed_indices.max()
                        >= attack_end
                    )
                ):
                    status = "FAIL_CHANGE_OUTSIDE_WINDOW"
                else:
                    status = "PASS"

                writable_read = record.to_read()

                attacked_read = replace(
                    writable_read,
                    signal=attacked_signal,
                )

                writer.add_read(attacked_read)

                audit_rows.append(
                    {
                        "candidate": candidate,
                        "parent_id": read_id,
                        "context_bases": context_bases,
                        "target_base_index_0based": (
                            target_base_index
                        ),
                        "first_attacked_base_index": (
                            first_base
                        ),
                        "last_attacked_base_index": (
                            last_base
                        ),
                        "attacked_base_events": (
                            last_base
                            - first_base
                            + 1
                        ),
                        "mv_stride": stride,
                        "target_signal_start": int(
                            window[
                                "target_signal_start"
                            ]
                        ),
                        "target_signal_end": int(
                            window[
                                "target_signal_end"
                            ]
                        ),
                        "attack_signal_start": (
                            attack_start
                        ),
                        "attack_signal_end": (
                            attack_end
                        ),
                        "attack_window_samples": (
                            attack_end
                            - attack_start
                        ),
                        "changed_samples_inside": (
                            inside_changed
                        ),
                        "changed_samples_outside": (
                            outside_changed
                        ),
                        "total_changed_samples": (
                            total_changed
                        ),
                        "total_signal_samples": (
                            len(original_signal)
                        ),
                        "changed_fraction": (
                            total_changed
                            / len(original_signal)
                        ),
                        "status": status,
                    }
                )

    missing_ids = expected_ids - observed_ids

    if missing_ids:
        raise RuntimeError(
            f"{candidate}: missing POD5 IDs: "
            + ", ".join(sorted(missing_ids))
        )

    return audit_rows


def main():
    args = parse_args()

    window_rows = load_windows(
        Path(args.windows_tsv)
    )

    all_rows = []

    all_rows.extend(
        attack_candidate(
            candidate="L2_chr1_20061156_A_T",
            input_pod5=Path(args.l2_pod5),
            unaligned_bam=Path(args.l2_bam),
            output_pod5=Path(args.l2_output),
            window_rows=window_rows,
            context_bases=args.context_bases,
        )
    )

    all_rows.extend(
        attack_candidate(
            candidate="L3_chr4_40028853_A_G",
            input_pod5=Path(args.l3_pod5),
            unaligned_bam=Path(args.l3_bam),
            output_pod5=Path(args.l3_output),
            window_rows=window_rows,
            context_bases=args.context_bases,
        )
    )

    audit_path = Path(args.audit_tsv)
    summary_path = Path(args.summary_tsv)

    audit_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "candidate",
        "parent_id",
        "context_bases",
        "target_base_index_0based",
        "first_attacked_base_index",
        "last_attacked_base_index",
        "attacked_base_events",
        "mv_stride",
        "target_signal_start",
        "target_signal_end",
        "attack_signal_start",
        "attack_signal_end",
        "attack_window_samples",
        "changed_samples_inside",
        "changed_samples_outside",
        "total_changed_samples",
        "total_signal_samples",
        "changed_fraction",
        "status",
    ]

    with audit_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(all_rows)

    candidates = sorted({
        row["candidate"]
        for row in all_rows
    })

    summary_rows = []
    overall_pass = True

    for candidate in candidates:
        rows = [
            row
            for row in all_rows
            if row["candidate"] == candidate
        ]

        pass_rows = [
            row
            for row in rows
            if row["status"] == "PASS"
        ]

        total_changed = sum(
            row["total_changed_samples"]
            for row in rows
        )

        total_signal = sum(
            row["total_signal_samples"]
            for row in rows
        )

        total_outside_changed = sum(
            row["changed_samples_outside"]
            for row in rows
        )

        status = (
            "PASS"
            if (
                len(rows) == 10
                and len(pass_rows) == 10
                and total_outside_changed == 0
                and total_changed > 0
            )
            else "FAIL"
        )

        if status != "PASS":
            overall_pass = False

        summary_rows.append(
            {
                "candidate": candidate,
                "context_bases": (
                    args.context_bases
                ),
                "reads_processed": len(rows),
                "reads_passed": len(pass_rows),
                "total_changed_samples": (
                    total_changed
                ),
                "total_signal_samples": (
                    total_signal
                ),
                "changed_fraction": (
                    total_changed / total_signal
                ),
                "changed_percent": (
                    total_changed
                    * 100
                    / total_signal
                ),
                "outside_changed_samples": (
                    total_outside_changed
                ),
                "minimum_attack_window_samples": min(
                    row["attack_window_samples"]
                    for row in rows
                ),
                "maximum_attack_window_samples": max(
                    row["attack_window_samples"]
                    for row in rows
                ),
                "status": status,
            }
        )

    with summary_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(
                summary_rows[0].keys()
            ),
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(summary_rows)

    for row in summary_rows:
        print()
        print(row["candidate"])
        print(
            f'  reads passed: '
            f'{row["reads_passed"]}/'
            f'{row["reads_processed"]}'
        )
        print(
            f'  changed samples: '
            f'{row["total_changed_samples"]}'
        )
        print(
            f'  changed percent: '
            f'{row["changed_percent"]:.6f}%'
        )
        print(
            f'  outside changed: '
            f'{row["outside_changed_samples"]}'
        )
        print(
            f'  attack window range: '
            f'{row["minimum_attack_window_samples"]}'
            f'–'
            f'{row["maximum_attack_window_samples"]}'
            f' samples'
        )
        print(
            f'  status: {row["status"]}'
        )

    print()
    print("=" * 60)

    if overall_pass:
        print("PM5 ATTACK GENERATION: PASS")
    else:
        print("PM5 ATTACK GENERATION: FAIL")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
