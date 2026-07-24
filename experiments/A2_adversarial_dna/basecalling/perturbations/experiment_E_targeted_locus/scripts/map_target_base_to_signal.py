from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import pod5
import pysam


def base_to_move_chunk(moves: list[int], base_index: int) -> int:
    """
    Return the move-table chunk that emits the requested zero-based base.

    The first element of the BAM mv tag is the stride. The remaining
    elements describe the number of bases emitted at each signal chunk.
    """
    if base_index < 0:
        raise ValueError(f"Negative base index: {base_index}")

    emitted = 0

    for chunk_index, move in enumerate(moves):
        next_emitted = emitted + int(move)

        if base_index < next_emitted:
            return chunk_index

        emitted = next_emitted

    raise ValueError(
        f"Base index {base_index} exceeds move-table base count {emitted}"
    )


def interval_for_base_range(
    moves: list[int],
    stride: int,
    sample_origin: int,
    first_base: int,
    last_base: int,
    query_length: int,
) -> tuple[int, int, int, int]:
    """
    Map an inclusive base range to a half-open raw-signal interval.
    """
    start_chunk = base_to_move_chunk(moves, first_base)

    if last_base + 1 < query_length:
        end_chunk = base_to_move_chunk(moves, last_base + 1)
    else:
        end_chunk = len(moves)

    if end_chunk <= start_chunk:
        end_chunk = start_chunk + 1

    signal_start = sample_origin + start_chunk * stride
    signal_end = sample_origin + end_chunk * stride

    return start_chunk, end_chunk, signal_start, signal_end


def main() -> int:
    if len(sys.argv) != 10:
        print(
            "Usage: map_target_base_to_signal.py "
            "<bam> <pod5> <chrom> <position> <alt> <context_bases> "
            "<output.tsv> <excluded.tsv> <summary.txt>",
            file=sys.stderr,
        )
        return 2

    bam_path = Path(sys.argv[1])
    pod5_path = Path(sys.argv[2])
    chrom = sys.argv[3]
    position = int(sys.argv[4])
    alt = sys.argv[5].upper()
    context_bases = int(sys.argv[6])
    output_path = Path(sys.argv[7])
    excluded_path = Path(sys.argv[8])
    summary_path = Path(sys.argv[9])

    raw_signal_lengths: dict[str, int] = {}

    with pod5.Reader(pod5_path) as reader:
        for read in reader.reads():
            raw_signal_lengths[str(read.read_id)] = int(
                read.num_samples
            )

    mapped_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []

    with pysam.AlignmentFile(str(bam_path), "rb") as bam:
        for column in bam.pileup(
            chrom,
            position - 1,
            position,
            truncate=True,
            stepper="all",
            min_base_quality=0,
            min_mapping_quality=0,
            ignore_overlaps=False,
            ignore_orphans=False,
            max_depth=100000,
        ):
            if column.reference_pos != position - 1:
                continue

            for pileup_read in column.pileups:
                alignment = pileup_read.alignment

                if alignment.is_secondary:
                    continue

                if alignment.is_supplementary:
                    continue

                parent_id = (
                    alignment.get_tag("pi")
                    if alignment.has_tag("pi")
                    else alignment.query_name
                )

                raw_signal_length = raw_signal_lengths.get(parent_id)

                if raw_signal_length is None:
                    raise RuntimeError(
                        f"Raw parent {parent_id} was not found in POD5"
                    )

                if pileup_read.is_del:
                    base = "-"
                    query_position = None
                    base_quality: int | str = ""
                elif pileup_read.is_refskip:
                    base = "REFSKIP"
                    query_position = None
                    base_quality = ""
                else:
                    query_position = pileup_read.query_position

                    if query_position is None:
                        base = "?"
                        base_quality = ""
                    else:
                        base = alignment.query_sequence[
                            query_position
                        ].upper()

                        base_quality = int(
                            alignment.query_qualities[query_position]
                        )

                exclusion_reason = ""

                if base != alt:
                    exclusion_reason = (
                        f"clean_base_is_{base}_not_{alt}"
                    )
                elif query_position is None:
                    exclusion_reason = "no_query_position"
                elif not alignment.has_tag("mv"):
                    exclusion_reason = "missing_move_table"

                if exclusion_reason:
                    excluded_rows.append(
                        {
                            "query_name": alignment.query_name,
                            "raw_parent_id": parent_id,
                            "clean_base": base,
                            "reason": exclusion_reason,
                            "strand": (
                                "reverse"
                                if alignment.is_reverse
                                else "forward"
                            ),
                            "mapping_quality": alignment.mapping_quality,
                            "cigar": alignment.cigarstring or "",
                        }
                    )
                    continue

                move_tag = list(alignment.get_tag("mv"))

                if len(move_tag) < 2:
                    raise RuntimeError(
                        f"Invalid mv tag for {alignment.query_name}"
                    )

                stride = int(move_tag[0])
                moves = [int(value) for value in move_tag[1:]]

                query_length = int(
                    alignment.query_length
                    or len(alignment.query_sequence)
                )

                move_base_count = sum(moves)

                if move_base_count != query_length:
                    raise RuntimeError(
                        f"Move/base count mismatch for "
                        f"{alignment.query_name}: "
                        f"moves={move_base_count}, "
                        f"query_length={query_length}"
                    )

                trim_samples = (
                    int(alignment.get_tag("ts"))
                    if alignment.has_tag("ts")
                    else 0
                )

                split_offset = (
                    int(alignment.get_tag("sp"))
                    if alignment.has_tag("sp")
                    else 0
                )

                # sp locates a split child inside the original raw parent.
                # ts locates the called sequence inside that child signal.
                sample_origin = split_offset + trim_samples

                context_first_base = max(
                    0,
                    query_position - context_bases,
                )

                context_last_base = min(
                    query_length - 1,
                    query_position + context_bases,
                )

                (
                    target_start_chunk,
                    target_end_chunk,
                    target_signal_start,
                    target_signal_end,
                ) = interval_for_base_range(
                    moves=moves,
                    stride=stride,
                    sample_origin=sample_origin,
                    first_base=query_position,
                    last_base=query_position,
                    query_length=query_length,
                )

                (
                    context_start_chunk,
                    context_end_chunk,
                    context_signal_start,
                    context_signal_end,
                ) = interval_for_base_range(
                    moves=moves,
                    stride=stride,
                    sample_origin=sample_origin,
                    first_base=context_first_base,
                    last_base=context_last_base,
                    query_length=query_length,
                )

                if not (
                    0
                    <= target_signal_start
                    < target_signal_end
                    <= raw_signal_length
                ):
                    raise RuntimeError(
                        f"Target signal interval out of bounds for "
                        f"{parent_id}: "
                        f"{target_signal_start}:{target_signal_end} "
                        f"of {raw_signal_length}"
                    )

                if not (
                    0
                    <= context_signal_start
                    < context_signal_end
                    <= raw_signal_length
                ):
                    raise RuntimeError(
                        f"Context signal interval out of bounds for "
                        f"{parent_id}: "
                        f"{context_signal_start}:{context_signal_end} "
                        f"of {raw_signal_length}"
                    )

                mapped_rows.append(
                    {
                        "query_name": alignment.query_name,
                        "raw_parent_id": parent_id,
                        "clean_base": base,
                        "base_quality": base_quality,
                        "mapping_quality": alignment.mapping_quality,
                        "strand": (
                            "reverse"
                            if alignment.is_reverse
                            else "forward"
                        ),
                        "query_position": query_position,
                        "query_length": query_length,
                        "move_base_count": move_base_count,
                        "move_stride": stride,
                        "trim_samples": trim_samples,
                        "split_offset_samples": split_offset,
                        "sample_origin": sample_origin,
                        "target_start_chunk": target_start_chunk,
                        "target_end_chunk": target_end_chunk,
                        "target_signal_start": target_signal_start,
                        "target_signal_end": target_signal_end,
                        "target_signal_samples": (
                            target_signal_end - target_signal_start
                        ),
                        "context_first_base": context_first_base,
                        "context_last_base": context_last_base,
                        "context_start_chunk": context_start_chunk,
                        "context_end_chunk": context_end_chunk,
                        "context_signal_start": context_signal_start,
                        "context_signal_end": context_signal_end,
                        "context_signal_samples": (
                            context_signal_end - context_signal_start
                        ),
                        "raw_signal_samples": raw_signal_length,
                        "cigar": alignment.cigarstring or "",
                    }
                )

    mapped_rows.sort(key=lambda row: str(row["raw_parent_id"]))
    excluded_rows.sort(key=lambda row: str(row["raw_parent_id"]))

    mapped_fields = [
        "query_name",
        "raw_parent_id",
        "clean_base",
        "base_quality",
        "mapping_quality",
        "strand",
        "query_position",
        "query_length",
        "move_base_count",
        "move_stride",
        "trim_samples",
        "split_offset_samples",
        "sample_origin",
        "target_start_chunk",
        "target_end_chunk",
        "target_signal_start",
        "target_signal_end",
        "target_signal_samples",
        "context_first_base",
        "context_last_base",
        "context_start_chunk",
        "context_end_chunk",
        "context_signal_start",
        "context_signal_end",
        "context_signal_samples",
        "raw_signal_samples",
        "cigar",
    ]

    with output_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=mapped_fields,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(mapped_rows)

    excluded_fields = [
        "query_name",
        "raw_parent_id",
        "clean_base",
        "reason",
        "strand",
        "mapping_quality",
        "cigar",
    ]

    with excluded_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=excluded_fields,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(excluded_rows)

    target_lengths = [
        int(row["target_signal_samples"])
        for row in mapped_rows
    ]

    context_lengths = [
        int(row["context_signal_samples"])
        for row in mapped_rows
    ]

    summary = [
        "Experiment E clean ALT signal mapping",
        "=====================================",
        f"Target locus: {chrom}:{position}",
        f"Required clean ALT base: {alt}",
        f"Mapped attack candidates: {len(mapped_rows)}",
        f"Excluded clean records: {len(excluded_rows)}",
        f"Context radius: +/-{context_bases} bases",
        "",
    ]

    if target_lengths:
        summary.extend(
            [
                "Target-base signal interval:",
                f"  minimum samples: {min(target_lengths)}",
                f"  maximum samples: {max(target_lengths)}",
                f"  mean samples: "
                f"{sum(target_lengths) / len(target_lengths):.2f}",
                "",
                "Context signal interval:",
                f"  minimum samples: {min(context_lengths)}",
                f"  maximum samples: {max(context_lengths)}",
                f"  mean samples: "
                f"{sum(context_lengths) / len(context_lengths):.2f}",
                "",
            ]
        )

    summary.append("Excluded records:")

    for row in excluded_rows:
        summary.append(
            f"  {row['raw_parent_id']}: "
            f"{row['reason']}"
        )

    summary_path.write_text(
        "\n".join(summary) + "\n",
        encoding="utf-8",
    )

    print("\n".join(summary))

    if len(mapped_rows) != 10:
        print(
            f"ERROR: Expected 10 clean G-supporting attack "
            f"candidates, found {len(mapped_rows)}"
        )
        return 1

    if len(excluded_rows) != 1:
        print(
            f"ERROR: Expected 1 excluded record, "
            f"found {len(excluded_rows)}"
        )
        return 1

    print()
    print("Signal-coordinate mapping validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
