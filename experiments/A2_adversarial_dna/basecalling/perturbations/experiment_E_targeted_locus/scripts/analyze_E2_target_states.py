#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import pysam


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bam", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--chrom", required=True)
    parser.add_argument("--position", required=True, type=int)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--alt", required=True)
    parser.add_argument("--records-tsv", required=True)
    parser.add_argument("--parents-tsv", required=True)
    parser.add_argument("--summary-tsv", required=True)
    parser.add_argument("--parent-map")
    return parser.parse_args()


def get_parent_id(record: pysam.AlignedSegment) -> str:
    if record.has_tag("pi"):
        return str(record.get_tag("pi"))
    return record.query_name


def target_state(
    record: pysam.AlignedSegment,
    chrom: str,
    position: int,
    ref_base: str,
    alt_base: str,
) -> tuple[str, str]:
    if record.is_unmapped:
        return "UNMAPPED", "."

    if record.reference_name != chrom:
        return "NO_COVERAGE", "."

    target0 = position - 1

    if record.reference_start is None or record.reference_end is None:
        return "NO_COVERAGE", "."

    if not record.reference_start <= target0 < record.reference_end:
        return "NO_COVERAGE", "."

    for query_pos, reference_pos in record.get_aligned_pairs(
        matches_only=False
    ):
        if reference_pos != target0:
            continue

        if query_pos is None:
            return "DELETION", "*"

        if record.query_sequence is None:
            return "OTHER", "."

        base = record.query_sequence[query_pos].upper()

        if base == ref_base:
            return "REF", base

        if base == alt_base:
            return "ALT", base

        return "OTHER", base

    return "NO_COVERAGE", "."


def choose_parent_state(rows: list[dict[str, object]]) -> dict[str, object]:
    priority = {
        "ALT": 6,
        "REF": 5,
        "OTHER": 4,
        "DELETION": 3,
        "NO_COVERAGE": 2,
        "UNMAPPED": 1,
    }

    return max(
        rows,
        key=lambda row: (
            priority[str(row["target_state"])],
            int(bool(row["is_primary"])),
            int(row["mapq"]),
        ),
    )


def main() -> int:
    args = parse_args()

    ref_base = args.ref.upper()
    alt_base = args.alt.upper()

    parent_map: dict[str, str] = {}

    if args.parent_map:
        with Path(args.parent_map).open() as handle:
            reader = csv.DictReader(handle, delimiter="\t")

            for row in reader:
                parent_map[row["query_name"]] = row["parent_id"]

    record_rows: list[dict[str, object]] = []
    parent_groups: dict[str, list[dict[str, object]]] = {}

    with pysam.AlignmentFile(args.bam, "rb") as bam:
        for ordinal, record in enumerate(
            bam.fetch(until_eof=True),
            start=1,
        ):
            state, base = target_state(
                record,
                args.chrom,
                args.position,
                ref_base,
                alt_base,
            )

            parent = parent_map.get(
                record.query_name,
                get_parent_id(record),
            )

            row: dict[str, object] = {
                "condition": args.condition,
                "record_ordinal": ordinal,
                "query_name": record.query_name,
                "parent_id": parent,
                "flag": record.flag,
                "is_primary": int(
                    not record.is_secondary
                    and not record.is_supplementary
                ),
                "is_secondary": int(record.is_secondary),
                "is_supplementary": int(record.is_supplementary),
                "is_reverse": int(record.is_reverse),
                "is_unmapped": int(record.is_unmapped),
                "reference_name": record.reference_name or ".",
                "reference_start_1based": (
                    record.reference_start + 1
                    if record.reference_start is not None
                    else "."
                ),
                "mapq": record.mapping_quality,
                "cigar": record.cigarstring or ".",
                "target_state": state,
                "target_base": base,
            }

            record_rows.append(row)
            parent_groups.setdefault(parent, []).append(row)

    parent_rows: list[dict[str, object]] = []

    for parent_id in sorted(parent_groups):
        selected = choose_parent_state(parent_groups[parent_id])

        parent_rows.append(
            {
                "condition": args.condition,
                "parent_id": parent_id,
                "record_count": len(parent_groups[parent_id]),
                "selected_query_name": selected["query_name"],
                "selected_is_primary": selected["is_primary"],
                "selected_mapq": selected["mapq"],
                "target_state": selected["target_state"],
                "target_base": selected["target_base"],
            }
        )

    record_path = Path(args.records_tsv)
    parent_path = Path(args.parents_tsv)
    summary_path = Path(args.summary_tsv)

    record_path.parent.mkdir(parents=True, exist_ok=True)

    with record_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(record_rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(record_rows)

    with parent_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(parent_rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(parent_rows)

    record_counts = Counter(
        str(row["target_state"]) for row in record_rows
    )
    parent_counts = Counter(
        str(row["target_state"]) for row in parent_rows
    )

    mapped_records = sum(
        int(row["is_unmapped"]) == 0 for row in record_rows
    )

    primary_records = sum(
        int(row["is_primary"]) == 1 for row in record_rows
    )

    target_records = sum(
        str(row["target_state"])
        not in {"NO_COVERAGE", "UNMAPPED"}
        for row in record_rows
    )

    fields = [
        "condition",
        "total_records",
        "primary_records",
        "mapped_records",
        "target_overlapping_records",
        "raw_parent_count",
        "parent_ALT",
        "parent_REF",
        "parent_DELETION",
        "parent_OTHER",
        "parent_NO_COVERAGE",
        "parent_UNMAPPED",
        "record_ALT",
        "record_REF",
        "record_DELETION",
        "record_OTHER",
        "record_NO_COVERAGE",
        "record_UNMAPPED",
    ]

    summary_row = {
        "condition": args.condition,
        "total_records": len(record_rows),
        "primary_records": primary_records,
        "mapped_records": mapped_records,
        "target_overlapping_records": target_records,
        "raw_parent_count": len(parent_rows),
        "parent_ALT": parent_counts["ALT"],
        "parent_REF": parent_counts["REF"],
        "parent_DELETION": parent_counts["DELETION"],
        "parent_OTHER": parent_counts["OTHER"],
        "parent_NO_COVERAGE": parent_counts["NO_COVERAGE"],
        "parent_UNMAPPED": parent_counts["UNMAPPED"],
        "record_ALT": record_counts["ALT"],
        "record_REF": record_counts["REF"],
        "record_DELETION": record_counts["DELETION"],
        "record_OTHER": record_counts["OTHER"],
        "record_NO_COVERAGE": record_counts["NO_COVERAGE"],
        "record_UNMAPPED": record_counts["UNMAPPED"],
    }

    with summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerow(summary_row)

    print("\t".join(fields))
    print("\t".join(str(summary_row[field]) for field in fields))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
