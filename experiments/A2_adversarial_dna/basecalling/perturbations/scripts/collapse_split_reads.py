#!/usr/bin/env python3

"""
Collapse Dorado split-read children into one parent-level BAM record.

The original operational BAM is not modified.

Split children are identified using:
    pi: parent read ID
    sp: child start position

Children belonging to the same parent are ordered by sp, then their sequences
and qualities are concatenated.

Dorado signal-coordinate tags such as mv, pi, sp, ts, and ns are not copied to
the synthetic parent record because they describe individual child records and
are not valid after concatenation.
"""

import argparse
from collections import defaultdict
from pathlib import Path

import pysam


# Tags that describe child-specific signal segmentation or read identity.
# These must not be copied to a synthetic concatenated parent record.
EXCLUDED_COLLAPSED_TAGS = {
    "pi",
    "sp",
    "mv",
    "ts",
    "ns",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Collapse Dorado split-read children into one parent-level "
            "record for paired basecall comparison."
        )
    )

    parser.add_argument(
        "--input-bam",
        required=True,
        help="Input Dorado unaligned BAM.",
    )

    parser.add_argument(
        "--output-bam",
        required=True,
        help="Output parent-normalized BAM.",
    )

    return parser.parse_args()


def child_sort_key(record):
    if record.has_tag("sp"):
        return int(record.get_tag("sp"))

    return 0


def safe_scalar_tags(record):
    """
    Return scalar tags that remain meaningful for a synthetic parent record.

    BAM array tags are omitted because concatenating child records invalidates
    child-level arrays such as Dorado's move table.
    """

    safe_tags = []

    for tag, value, value_type in record.get_tags(with_value_type=True):
        if tag in EXCLUDED_COLLAPSED_TAGS:
            continue

        # Skip all BAM array tags.
        if value_type == "B":
            continue

        safe_tags.append((tag, value, value_type))

    return safe_tags


def make_collapsed_record(parent_id, children, header):
    ordered_children = sorted(children, key=child_sort_key)

    sequences = []
    qualities = []

    for child in ordered_children:
        if child.query_sequence is None:
            raise ValueError(
                f"Child {child.query_name} has no query sequence"
            )

        sequences.append(child.query_sequence)

        if child.query_qualities is None:
            qualities.extend([0] * len(child.query_sequence))
        else:
            qualities.extend(child.query_qualities)

    sequence = "".join(sequences)

    if len(sequence) != len(qualities):
        raise ValueError(
            f"Sequence/quality length mismatch for parent {parent_id}: "
            f"{len(sequence)} sequence bases versus "
            f"{len(qualities)} quality values"
        )

    collapsed = pysam.AlignedSegment(header)

    collapsed.query_name = parent_id
    collapsed.query_sequence = sequence
    collapsed.flag = 4
    collapsed.reference_id = -1
    collapsed.reference_start = -1
    collapsed.mapping_quality = 0
    collapsed.cigar = None
    collapsed.next_reference_id = -1
    collapsed.next_reference_start = -1
    collapsed.template_length = 0
    collapsed.query_qualities = qualities

    # Copy only safe scalar metadata from the first child.
    for tag, value, value_type in safe_scalar_tags(ordered_children[0]):
        try:
            collapsed.set_tag(
                tag,
                value,
                value_type=value_type,
                replace=True,
            )
        except (TypeError, ValueError):
            # A nonessential metadata tag must never prevent creation of the
            # parent-level sequence record used for paired comparison.
            continue

    return collapsed


def main():
    args = parse_args()

    input_path = Path(args.input_bam)
    output_path = Path(args.output_bam)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input BAM not found: {input_path}")

    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input and output BAM paths must differ")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    unsplit_records = []
    split_children = defaultdict(list)

    with pysam.AlignmentFile(
        str(input_path),
        "rb",
        check_sq=False,
    ) as input_bam:
        header_dict = input_bam.header.to_dict()

        for record in input_bam:
            if record.has_tag("pi"):
                parent_id = str(record.get_tag("pi"))
                split_children[parent_id].append(record)
            else:
                unsplit_records.append(record)

    input_records = len(unsplit_records) + sum(
        len(children)
        for children in split_children.values()
    )

    with pysam.AlignmentFile(
        str(output_path),
        "wb",
        header=header_dict,
    ) as output_bam:
        for record in unsplit_records:
            output_bam.write(record)

        for parent_id in sorted(split_children):
            children = split_children[parent_id]

            collapsed = make_collapsed_record(
                parent_id=parent_id,
                children=children,
                header=output_bam.header,
            )

            output_bam.write(collapsed)

    output_records = len(unsplit_records) + len(split_children)

    print(f"Input records:           {input_records}")
    print(f"Unsplit records:         {len(unsplit_records)}")
    print(f"Split parent groups:     {len(split_children)}")
    print(
        "Split child records:     "
        f"{sum(len(children) for children in split_children.values())}"
    )
    print(f"Collapsed output count:  {output_records}")
    print(f"Output BAM:              {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
