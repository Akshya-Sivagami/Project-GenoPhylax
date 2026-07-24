#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pod5
import pysam


def reverse_complement(sequence: str) -> str:
    table = str.maketrans(
        "ACGTNacgtn",
        "TGCANtgcan",
    )
    return sequence.translate(table)[::-1]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Map reference-locus positions through clean alignments "
            "and Dorado move tables to raw POD5 signal intervals."
        )
    )

    parser.add_argument("--l2-unaligned", required=True)
    parser.add_argument("--l2-aligned", required=True)
    parser.add_argument("--l2-pod5", required=True)

    parser.add_argument("--l3-unaligned", required=True)
    parser.add_argument("--l3-aligned", required=True)
    parser.add_argument("--l3-pod5", required=True)

    parser.add_argument("--output-tsv", required=True)
    parser.add_argument("--summary-tsv", required=True)

    return parser.parse_args()


def read_pod5_metadata(path: Path):
    metadata = {}

    with pod5.Reader(path) as reader:
        for record in reader.reads():
            read_id = str(record.read_id)

            metadata[read_id] = {
                "signal_samples": len(record.signal),
                "sample_rate": record.run_info.sample_rate,
            }

    return metadata


def load_unaligned_bam(path: Path):
    records = {}

    with pysam.AlignmentFile(
        str(path),
        "rb",
        check_sq=False,
    ) as bam:
        for record in bam.fetch(until_eof=True):
            if record.query_name in records:
                raise RuntimeError(
                    "Duplicate read ID in unaligned BAM: "
                    f"{record.query_name}"
                )

            records[record.query_name] = record

    return records


def get_primary_target_records(
    path: Path,
    chrom: str,
    position: int,
):
    target0 = position - 1
    records = {}

    with pysam.AlignmentFile(str(path), "rb") as bam:
        for record in bam.fetch(
            chrom,
            target0,
            target0 + 1,
        ):
            if record.is_secondary or record.is_supplementary:
                continue

            parent_id = (
                str(record.get_tag("pi"))
                if record.has_tag("pi")
                else record.query_name
            )

            target_query_position = None

            for query_pos, reference_pos in (
                record.get_aligned_pairs(
                    matches_only=False
                )
            ):
                if reference_pos == target0:
                    target_query_position = query_pos
                    break

            if target_query_position is None:
                continue

            if parent_id in records:
                raise RuntimeError(
                    "Multiple primary target records for parent: "
                    f"{parent_id}"
                )

            records[parent_id] = {
                "record": record,
                "aligned_query_position": (
                    target_query_position
                ),
            }

    return records


def move_table_intervals(
    moves: list[int],
    stride: int,
    trimmed_samples: int,
    sequence_length: int,
):
    """
    Return one signal interval per basecalled sequence base.

    Dorado's mv tag consists of:
      mv[0]   = model stride
      mv[1:]  = moves associated with signal blocks

    A non-zero move advances the emitted sequence. The interval
    for a base extends from its move block until the block where
    the next sequence base begins.
    """

    starts = []

    emitted_bases = 0

    for block_index, move in enumerate(moves):
        move_value = int(move)

        if move_value <= 0:
            continue

        for _ in range(move_value):
            if emitted_bases >= sequence_length:
                break

            starts.append(
                trimmed_samples
                + block_index * stride
            )

            emitted_bases += 1

    if len(starts) < sequence_length:
        raise RuntimeError(
            "Move table emitted fewer bases than sequence: "
            f"{len(starts)} < {sequence_length}"
        )

    # Dorado can occasionally expose additional move emissions.
    starts = starts[:sequence_length]

    intervals = []

    for base_index, start in enumerate(starts):
        if base_index + 1 < len(starts):
            end = starts[base_index + 1]
        else:
            end = (
                trimmed_samples
                + len(moves) * stride
            )

        if end <= start:
            end = start + stride

        intervals.append((start, end))

    return intervals


def process_candidate(
    candidate: str,
    chrom: str,
    position: int,
    ref: str,
    alt: str,
    unaligned_path: Path,
    aligned_path: Path,
    pod5_path: Path,
):
    unaligned_records = load_unaligned_bam(
        unaligned_path
    )

    aligned_records = get_primary_target_records(
        aligned_path,
        chrom,
        position,
    )

    pod5_metadata = read_pod5_metadata(pod5_path)

    rows = []

    for parent_id in sorted(aligned_records):
        aligned_record = aligned_records[parent_id][
            "record"
        ]

        aligned_query_position = aligned_records[
            parent_id
        ]["aligned_query_position"]

        unaligned_record = unaligned_records.get(
            parent_id
        )

        pod5_info = pod5_metadata.get(parent_id)

        status_reasons = []

        if unaligned_record is None:
            status_reasons.append(
                "MISSING_UNALIGNED_RECORD"
            )

        if pod5_info is None:
            status_reasons.append(
                "MISSING_POD5_READ"
            )

        if unaligned_record is None or pod5_info is None:
            rows.append(
                {
                    "candidate": candidate,
                    "parent_id": parent_id,
                    "chrom": chrom,
                    "position": position,
                    "ref": ref,
                    "alt": alt,
                    "strand": (
                        "REVERSE"
                        if aligned_record.is_reverse
                        else "FORWARD"
                    ),
                    "aligned_query_position_0based": (
                        aligned_query_position
                    ),
                    "original_base_index_0based": "",
                    "sequence_length": "",
                    "observed_target_base": "",
                    "base_quality": "",
                    "mv_stride": "",
                    "mv_blocks": "",
                    "mv_emitted_bases": "",
                    "ts_trimmed_samples": "",
                    "ns_tag_samples": "",
                    "pod5_signal_samples": (
                        pod5_info["signal_samples"]
                        if pod5_info
                        else ""
                    ),
                    "target_signal_start": "",
                    "target_signal_end": "",
                    "target_signal_samples": "",
                    "status": ";".join(
                        status_reasons
                    ),
                }
            )

            continue

        if not unaligned_record.has_tag("mv"):
            status_reasons.append("MISSING_MV")

        if not unaligned_record.has_tag("ts"):
            status_reasons.append("MISSING_TS")

        if not unaligned_record.has_tag("ns"):
            status_reasons.append("MISSING_NS")

        sequence = (
            unaligned_record.query_sequence or ""
        )

        sequence_length = len(sequence)

        if aligned_record.is_reverse:
            original_base_index = (
                sequence_length
                - 1
                - aligned_query_position
            )
        else:
            original_base_index = (
                aligned_query_position
            )

        if not (
            0 <= original_base_index
            < sequence_length
        ):
            status_reasons.append(
                "BASE_INDEX_OUT_OF_RANGE"
            )

        if status_reasons:
            rows.append(
                {
                    "candidate": candidate,
                    "parent_id": parent_id,
                    "chrom": chrom,
                    "position": position,
                    "ref": ref,
                    "alt": alt,
                    "strand": (
                        "REVERSE"
                        if aligned_record.is_reverse
                        else "FORWARD"
                    ),
                    "aligned_query_position_0based": (
                        aligned_query_position
                    ),
                    "original_base_index_0based": (
                        original_base_index
                    ),
                    "sequence_length": sequence_length,
                    "observed_target_base": "",
                    "base_quality": "",
                    "mv_stride": "",
                    "mv_blocks": "",
                    "mv_emitted_bases": "",
                    "ts_trimmed_samples": "",
                    "ns_tag_samples": "",
                    "pod5_signal_samples": (
                        pod5_info["signal_samples"]
                    ),
                    "target_signal_start": "",
                    "target_signal_end": "",
                    "target_signal_samples": "",
                    "status": ";".join(
                        status_reasons
                    ),
                }
            )

            continue

        mv = list(unaligned_record.get_tag("mv"))

        if len(mv) < 2:
            raise RuntimeError(
                f"Invalid mv tag for {parent_id}"
            )

        stride = int(mv[0])
        moves = [int(value) for value in mv[1:]]

        trimmed_samples = int(
            unaligned_record.get_tag("ts")
        )

        ns_tag_samples = int(
            unaligned_record.get_tag("ns")
        )

        intervals = move_table_intervals(
            moves=moves,
            stride=stride,
            trimmed_samples=trimmed_samples,
            sequence_length=sequence_length,
        )

        signal_start, signal_end = intervals[
            original_base_index
        ]

        signal_start = max(0, signal_start)

        signal_end = min(
            pod5_info["signal_samples"],
            signal_end,
        )

        if signal_end <= signal_start:
            status_reasons.append(
                "INVALID_SIGNAL_INTERVAL"
            )

        observed_original_base = sequence[
            original_base_index
        ].upper()

        expected_original_alt = (
            alt
            if not aligned_record.is_reverse
            else reverse_complement(alt)
        )

        if observed_original_base != expected_original_alt:
            status_reasons.append(
                "ORIGINAL_BASE_NOT_EXPECTED_ALT"
            )

        aligned_base = (
            aligned_record.query_sequence[
                aligned_query_position
            ].upper()
        )

        if aligned_base != alt:
            status_reasons.append(
                "ALIGNED_BASE_NOT_ALT"
            )

        base_quality = ""

        if aligned_record.query_qualities is not None:
            base_quality = (
                aligned_record.query_qualities[
                    aligned_query_position
                ]
            )

        if signal_start >= pod5_info["signal_samples"]:
            status_reasons.append(
                "SIGNAL_START_OUT_OF_RANGE"
            )

        mv_emitted_bases = sum(
            max(0, value)
            for value in moves
        )

        status = (
            "PASS"
            if not status_reasons
            else ";".join(status_reasons)
        )

        rows.append(
            {
                "candidate": candidate,
                "parent_id": parent_id,
                "chrom": chrom,
                "position": position,
                "ref": ref,
                "alt": alt,
                "strand": (
                    "REVERSE"
                    if aligned_record.is_reverse
                    else "FORWARD"
                ),
                "aligned_query_position_0based": (
                    aligned_query_position
                ),
                "original_base_index_0based": (
                    original_base_index
                ),
                "sequence_length": sequence_length,
                "observed_target_base": (
                    observed_original_base
                ),
                "base_quality": base_quality,
                "mv_stride": stride,
                "mv_blocks": len(moves),
                "mv_emitted_bases": (
                    mv_emitted_bases
                ),
                "ts_trimmed_samples": (
                    trimmed_samples
                ),
                "ns_tag_samples": ns_tag_samples,
                "pod5_signal_samples": (
                    pod5_info["signal_samples"]
                ),
                "target_signal_start": signal_start,
                "target_signal_end": signal_end,
                "target_signal_samples": (
                    signal_end - signal_start
                ),
                "status": status,
            }
        )

    return rows


def main():
    args = parse_args()

    rows = []

    rows.extend(
        process_candidate(
            candidate="L2_chr1_20061156_A_T",
            chrom="chr1",
            position=20061156,
            ref="A",
            alt="T",
            unaligned_path=Path(
                args.l2_unaligned
            ),
            aligned_path=Path(
                args.l2_aligned
            ),
            pod5_path=Path(args.l2_pod5),
        )
    )

    rows.extend(
        process_candidate(
            candidate="L3_chr4_40028853_A_G",
            chrom="chr4",
            position=40028853,
            ref="A",
            alt="G",
            unaligned_path=Path(
                args.l3_unaligned
            ),
            aligned_path=Path(
                args.l3_aligned
            ),
            pod5_path=Path(args.l3_pod5),
        )
    )

    output_path = Path(args.output_tsv)
    summary_path = Path(args.summary_tsv)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "candidate",
        "parent_id",
        "chrom",
        "position",
        "ref",
        "alt",
        "strand",
        "aligned_query_position_0based",
        "original_base_index_0based",
        "sequence_length",
        "observed_target_base",
        "base_quality",
        "mv_stride",
        "mv_blocks",
        "mv_emitted_bases",
        "ts_trimmed_samples",
        "ns_tag_samples",
        "pod5_signal_samples",
        "target_signal_start",
        "target_signal_end",
        "target_signal_samples",
        "status",
    ]

    with output_path.open(
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
        writer.writerows(rows)

    grouped = defaultdict(list)

    for row in rows:
        grouped[row["candidate"]].append(row)

    summary_rows = []

    overall_pass = True

    for candidate, candidate_rows in grouped.items():
        pass_rows = [
            row
            for row in candidate_rows
            if row["status"] == "PASS"
        ]

        target_sizes = [
            int(row["target_signal_samples"])
            for row in pass_rows
        ]

        forward = sum(
            row["strand"] == "FORWARD"
            for row in candidate_rows
        )

        reverse = sum(
            row["strand"] == "REVERSE"
            for row in candidate_rows
        )

        status = (
            "PASS"
            if (
                len(candidate_rows) == 10
                and len(pass_rows) == 10
            )
            else "FAIL"
        )

        if status != "PASS":
            overall_pass = False

        summary_rows.append(
            {
                "candidate": candidate,
                "expected_parents": 10,
                "mapped_parents": len(
                    candidate_rows
                ),
                "valid_signal_windows": len(
                    pass_rows
                ),
                "forward_reads": forward,
                "reverse_reads": reverse,
                "minimum_target_samples": (
                    min(target_sizes)
                    if target_sizes
                    else 0
                ),
                "maximum_target_samples": (
                    max(target_sizes)
                    if target_sizes
                    else 0
                ),
                "mean_target_samples": (
                    round(
                        sum(target_sizes)
                        / len(target_sizes),
                        3,
                    )
                    if target_sizes
                    else 0
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

    for summary in summary_rows:
        print()
        print(summary["candidate"])
        print(
            "  mapped parents: "
            f'{summary["mapped_parents"]}/10'
        )
        print(
            "  valid signal windows: "
            f'{summary["valid_signal_windows"]}/10'
        )
        print(
            "  strand distribution: "
            f'forward={summary["forward_reads"]}, '
            f'reverse={summary["reverse_reads"]}'
        )
        print(
            "  target interval samples: "
            f'min={summary["minimum_target_samples"]}, '
            f'mean={summary["mean_target_samples"]}, '
            f'max={summary["maximum_target_samples"]}'
        )
        print(
            f'  status: {summary["status"]}'
        )

    print()
    print("=" * 60)

    if overall_pass:
        print("RAW-SIGNAL WINDOW MAPPING: PASS")
    else:
        print("RAW-SIGNAL WINDOW MAPPING: FAIL")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
