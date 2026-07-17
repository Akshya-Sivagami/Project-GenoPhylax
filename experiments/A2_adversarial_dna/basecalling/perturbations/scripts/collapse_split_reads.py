#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import pysam


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collapse Dorado split-read children into one parent-level "
            "record for paired basecall comparison."
        )
    )
    parser.add_argument("--input-bam", required=True, type=Path)
    parser.add_argument("--output-bam", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.input_bam.is_file():
        raise FileNotFoundError(args.input_bam)

    args.output_bam.parent.mkdir(parents=True, exist_ok=True)

    unsplit_records = []
    split_groups = defaultdict(list)

    with pysam.AlignmentFile(
        args.input_bam,
        "rb",
        check_sq=False,
    ) as source:
        header = source.header.to_dict()

        for record in source.fetch(until_eof=True):
            if record.has_tag("pi"):
                parent_id = record.get_tag("pi")
                split_start = (
                    int(record.get_tag("sp"))
                    if record.has_tag("sp")
                    else 0
                )
                split_groups[parent_id].append(
                    (split_start, record)
                )
            else:
                unsplit_records.append(record)

    with pysam.AlignmentFile(
        args.output_bam,
        "wb",
        header=header,
    ) as output:
        for record in unsplit_records:
            output.write(record)

        for parent_id, children in sorted(split_groups.items()):
            children.sort(key=lambda item: item[0])

            first = children[0][1]

            sequence = "".join(
                child.query_sequence or ""
                for _, child in children
            )

            qualities = []

            for _, child in children:
                if child.query_qualities is not None:
                    qualities.extend(child.query_qualities)

            collapsed = pysam.AlignedSegment(output.header)
            collapsed.query_name = parent_id
            collapsed.flag = 4
            collapsed.reference_id = -1
            collapsed.reference_start = -1
            collapsed.mapping_quality = 0
            collapsed.cigar = None
            collapsed.next_reference_id = -1
            collapsed.next_reference_start = -1
            collapsed.template_length = 0
            collapsed.query_sequence = sequence

            if len(qualities) == len(sequence):
                collapsed.query_qualities = qualities

            for tag, value, value_type in first.get_tags(
                with_value_type=True
            ):
                if tag not in {"pi", "sp", "ns", "ts", "du", "qs"}:
                    collapsed.set_tag(
                        tag,
                        value,
                        value_type=value_type,
                    )

            collapsed.set_tag("XC", len(children), value_type="i")
            collapsed.set_tag("XP", parent_id, value_type="Z")

            output.write(collapsed)

    print(f"Input BAM records:      {len(unsplit_records) + sum(len(v) for v in split_groups.values())}")
    print(f"Unsplit records:        {len(unsplit_records)}")
    print(f"Split parent groups:    {len(split_groups)}")
    print(f"Collapsed output count: {len(unsplit_records) + len(split_groups)}")
    print(f"Output:                 {args.output_bam}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
