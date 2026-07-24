#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import importlib.util
from dataclasses import replace
from pathlib import Path

import numpy as np
import pod5


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate cross-locus off-target sham signal "
            "perturbations using a PM5-sized window shifted "
            "away from the true variant."
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

    parser.add_argument(
        "--offset-bases",
        type=int,
        default=20,
    )

    return parser.parse_args()


def load_source_module():
    source_path = (
        Path(__file__).resolve().parent
        / "generate_cross_locus_pm5_attack.py"
    )

    spec = importlib.util.spec_from_file_location(
        "cross_locus_pm5_source",
        source_path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to import source generator: {source_path}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def select_sham_center(
    target_index: int,
    interval_count: int,
    context_bases: int,
    offset_bases: int,
):
    target_first = max(
        0,
        target_index - context_bases,
    )

    target_last = min(
        interval_count - 1,
        target_index + context_bases,
    )

    preferred_center = target_index + offset_bases

    if (
        preferred_center - context_bases >= 0
        and preferred_center + context_bases
        < interval_count
    ):
        sham_center = preferred_center
        direction = "DOWNSTREAM"
    else:
        fallback_center = target_index - offset_bases

        if not (
            fallback_center - context_bases >= 0
            and fallback_center + context_bases
            < interval_count
        ):
            raise RuntimeError(
                "Unable to place full sham window without "
                "crossing sequence boundaries"
            )

        sham_center = fallback_center
        direction = "UPSTREAM"

    sham_first = sham_center - context_bases
    sham_last = sham_center + context_bases

    overlap = not (
        sham_last < target_first
        or sham_first > target_last
    )

    if overlap:
        raise RuntimeError(
            "Sham and target windows overlap: "
            f"target={target_first}-{target_last}, "
            f"sham={sham_first}-{sham_last}"
        )

    return {
        "target_first": target_first,
        "target_last": target_last,
        "sham_center": sham_center,
        "sham_first": sham_first,
        "sham_last": sham_last,
        "direction": direction,
    }


def process_candidate(
    source,
    candidate,
    input_pod5,
    unaligned_bam,
    output_pod5,
    windows,
    context_bases,
    offset_bases,
):
    bam_records = source.load_unaligned_records(
        unaligned_bam
    )

    expected_ids = {
        parent_id
        for candidate_name, parent_id in windows
        if candidate_name == candidate
    }

    if len(expected_ids) != 10:
        raise RuntimeError(
            f"{candidate}: expected 10 reads, "
            f"found {len(expected_ids)}"
        )

    if output_pod5.exists():
        output_pod5.unlink()

    rows = []
    observed = set()

    with pod5.Reader(input_pod5) as reader:
        with pod5.Writer(output_pod5) as writer:
            for record in reader.reads():
                read_id = str(record.read_id)

                if read_id not in expected_ids:
                    raise RuntimeError(
                        f"{candidate}: unexpected read {read_id}"
                    )

                if read_id in observed:
                    raise RuntimeError(
                        f"{candidate}: duplicate read {read_id}"
                    )

                observed.add(read_id)

                bam_record = bam_records.get(read_id)

                if bam_record is None:
                    raise RuntimeError(
                        f"{candidate}: missing BAM record "
                        f"{read_id}"
                    )

                window = windows[
                    (candidate, read_id)
                ]

                target_index = int(
                    window[
                        "original_base_index_0based"
                    ]
                )

                intervals, stride = (
                    source.build_base_intervals(
                        bam_record
                    )
                )

                placement = select_sham_center(
                    target_index=target_index,
                    interval_count=len(intervals),
                    context_bases=context_bases,
                    offset_bases=offset_bases,
                )

                sham_first = placement["sham_first"]
                sham_last = placement["sham_last"]

                attack_start = intervals[
                    sham_first
                ][0]

                attack_end = intervals[
                    sham_last
                ][1]

                original_signal = np.asarray(
                    record.signal
                )

                attack_start = max(
                    0,
                    int(attack_start),
                )

                attack_end = min(
                    len(original_signal),
                    int(attack_end),
                )

                attacked_signal = (
                    source.interpolate_window(
                        original_signal,
                        attack_start,
                        attack_end,
                    )
                )

                changed_mask = (
                    original_signal
                    != attacked_signal
                )

                changed_indices = np.flatnonzero(
                    changed_mask
                )

                inside_changed = int(
                    changed_mask[
                        attack_start:attack_end
                    ].sum()
                )

                outside_changed = int(
                    changed_mask[:attack_start].sum()
                    + changed_mask[attack_end:].sum()
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
                    status = (
                        "FAIL_CHANGE_OUTSIDE_WINDOW"
                    )
                else:
                    status = "PASS"

                attacked_read = replace(
                    record.to_read(),
                    signal=attacked_signal,
                )

                writer.add_read(attacked_read)

                rows.append(
                    {
                        "candidate": candidate,
                        "parent_id": read_id,
                        "context_bases": context_bases,
                        "offset_bases": offset_bases,
                        "sham_direction": (
                            placement["direction"]
                        ),
                        "target_base_index_0based": (
                            target_index
                        ),
                        "target_first_base_index": (
                            placement["target_first"]
                        ),
                        "target_last_base_index": (
                            placement["target_last"]
                        ),
                        "sham_center_base_index": (
                            placement["sham_center"]
                        ),
                        "sham_first_base_index": (
                            sham_first
                        ),
                        "sham_last_base_index": (
                            sham_last
                        ),
                        "sham_base_events": (
                            sham_last
                            - sham_first
                            + 1
                        ),
                        "base_window_overlap": 0,
                        "mv_stride": stride,
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

    missing = expected_ids - observed

    if missing:
        raise RuntimeError(
            f"{candidate}: missing reads: "
            + ",".join(sorted(missing))
        )

    return rows


def main():
    args = parse_args()
    source = load_source_module()

    windows = source.load_windows(
        Path(args.windows_tsv)
    )

    all_rows = []

    all_rows.extend(
        process_candidate(
            source=source,
            candidate="L2_chr1_20061156_A_T",
            input_pod5=Path(args.l2_pod5),
            unaligned_bam=Path(args.l2_bam),
            output_pod5=Path(args.l2_output),
            windows=windows,
            context_bases=args.context_bases,
            offset_bases=args.offset_bases,
        )
    )

    all_rows.extend(
        process_candidate(
            source=source,
            candidate="L3_chr4_40028853_A_G",
            input_pod5=Path(args.l3_pod5),
            unaligned_bam=Path(args.l3_bam),
            output_pod5=Path(args.l3_output),
            windows=windows,
            context_bases=args.context_bases,
            offset_bases=args.offset_bases,
        )
    )

    audit_path = Path(args.audit_tsv)
    summary_path = Path(args.summary_tsv)

    audit_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with audit_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(all_rows[0].keys()),
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(all_rows)

    summary_rows = []

    for candidate in sorted({
        row["candidate"]
        for row in all_rows
    }):
        rows = [
            row
            for row in all_rows
            if row["candidate"] == candidate
        ]

        passed = [
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

        outside_changed = sum(
            row["changed_samples_outside"]
            for row in rows
        )

        overlaps = sum(
            row["base_window_overlap"]
            for row in rows
        )

        status = (
            "PASS"
            if (
                len(rows) == 10
                and len(passed) == 10
                and total_changed > 0
                and outside_changed == 0
                and overlaps == 0
                and all(
                    row["sham_base_events"] == 11
                    for row in rows
                )
            )
            else "FAIL"
        )

        summary_rows.append(
            {
                "candidate": candidate,
                "context_bases": (
                    args.context_bases
                ),
                "offset_bases": (
                    args.offset_bases
                ),
                "reads_processed": len(rows),
                "reads_passed": len(passed),
                "sham_base_events_per_read": 11,
                "target_overlap_reads": overlaps,
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
                    outside_changed
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
        "w",
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
            "  sham events/read: "
            f'{row["sham_base_events_per_read"]}'
        )
        print(
            "  target overlaps: "
            f'{row["target_overlap_reads"]}'
        )
        print(
            "  changed samples: "
            f'{row["total_changed_samples"]}'
        )
        print(
            "  changed percent: "
            f'{row["changed_percent"]:.6f}%'
        )
        print(
            "  outside changed: "
            f'{row["outside_changed_samples"]}'
        )
        print(f'  status: {row["status"]}')

    if any(
        row["status"] != "PASS"
        for row in summary_rows
    ):
        raise SystemExit(1)

    print()
    print("OFF-TARGET SHAM GENERATION: PASS")


if __name__ == "__main__":
    main()
