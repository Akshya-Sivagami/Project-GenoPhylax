#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import pysam


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("--condition", required=True)
    parser.add_argument("--source-background", required=True)
    parser.add_argument("--background-ids", required=True)
    parser.add_argument("--replacement-bam", required=True)
    parser.add_argument("--replacement-ids", required=True)
    parser.add_argument("--background-output", required=True)
    parser.add_argument("--replacement-output", required=True)
    parser.add_argument("--hybrid-unsorted", required=True)
    parser.add_argument("--audit-tsv", required=True)
    parser.add_argument("--parent-tsv", required=True)
    parser.add_argument("--chrom", required=True)
    parser.add_argument("--position", required=True, type=int)

    return parser.parse_args()


def load_ids(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def parent_id(record: pysam.AlignedSegment) -> str:
    if record.has_tag("pi"):
        return str(record.get_tag("pi"))

    return record.query_name


def target_state(
    record: pysam.AlignedSegment,
    chrom: str,
    position: int,
) -> tuple[str, str]:
    target0 = position - 1

    if record.is_unmapped:
        return "UNMAPPED", ""

    if record.reference_name != chrom:
        return "NO_COVERAGE", ""

    if (
        record.reference_start is None
        or record.reference_end is None
        or target0 < record.reference_start
        or target0 >= record.reference_end
    ):
        return "NO_COVERAGE", ""

    for query_pos, reference_pos in record.get_aligned_pairs(
        matches_only=False
    ):
        if reference_pos != target0:
            continue

        if query_pos is None:
            return "DEL", "-"

        sequence = record.query_sequence or ""

        if not 0 <= query_pos < len(sequence):
            return "OTHER", "?"

        base = sequence[query_pos].upper()

        if base == "G":
            return "REF", base

        if base == "T":
            return "ALT", base

        return "OTHER", base

    return "NO_ALIGNED_PAIR", ""


def write_selected_records(
    input_path: Path,
    selected_ids: set[str],
    output_path: Path,
    output_header,
    label: str,
) -> tuple[int, set[str]]:
    written = 0
    parents = set()

    with pysam.AlignmentFile(str(input_path), "rb") as input_bam:
        with pysam.AlignmentFile(
            str(output_path),
            "wb",
            header=output_header,
        ) as output_bam:
            for record in input_bam.fetch(until_eof=True):
                pid = parent_id(record)

                if (
                    pid not in selected_ids
                    and record.query_name not in selected_ids
                ):
                    continue

                output_bam.write(record)
                written += 1
                parents.add(pid)

    missing = selected_ids - parents

    if missing:
        raise RuntimeError(
            f"{label}: missing selected parents: "
            + ",".join(sorted(missing))
        )

    return written, parents


def main() -> None:
    args = parse_args()

    condition = args.condition

    background_ids = load_ids(Path(args.background_ids))
    replacement_ids = load_ids(Path(args.replacement_ids))

    if len(background_ids) != 10:
        raise RuntimeError(
            f"Expected 10 background IDs, found {len(background_ids)}"
        )

    if len(replacement_ids) != 14:
        raise RuntimeError(
            f"Expected 14 replacement IDs, found {len(replacement_ids)}"
        )

    source_background = Path(args.source_background)
    replacement_bam = Path(args.replacement_bam)

    background_output = Path(args.background_output)
    replacement_output = Path(args.replacement_output)
    hybrid_unsorted = Path(args.hybrid_unsorted)

    audit_path = Path(args.audit_tsv)
    parent_path = Path(args.parent_tsv)

    for path in [
        background_output,
        replacement_output,
        hybrid_unsorted,
        audit_path,
        parent_path,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    with pysam.AlignmentFile(str(source_background), "rb") as bam:
        header = bam.header.to_dict()

    background_written, background_parents = write_selected_records(
        input_path=source_background,
        selected_ids=background_ids,
        output_path=background_output,
        output_header=header,
        label="background",
    )

    replacement_written, replacement_parents = write_selected_records(
        input_path=replacement_bam,
        selected_ids=replacement_ids,
        output_path=replacement_output,
        output_header=header,
        label="replacement",
    )

    with pysam.AlignmentFile(
        str(hybrid_unsorted),
        "wb",
        header=header,
    ) as output:
        for path in [background_output, replacement_output]:
            with pysam.AlignmentFile(str(path), "rb") as source:
                for record in source.fetch(until_eof=True):
                    output.write(record)

    rows = []
    parent_states = defaultdict(list)
    source_by_parent = {}

    with pysam.AlignmentFile(str(hybrid_unsorted), "rb") as bam:
        for ordinal, record in enumerate(
            bam.fetch(until_eof=True),
            start=1,
        ):
            pid = parent_id(record)

            if pid in background_ids:
                source = "same_sample_REF_background"
            elif pid in replacement_ids:
                source = f"{condition}_replacement"
            else:
                source = "ERROR_UNKNOWN"

            state, base = target_state(
                record,
                args.chrom,
                args.position,
            )

            parent_states[pid].append(state)
            source_by_parent[pid] = source

            rows.append(
                {
                    "condition": condition,
                    "record_ordinal": ordinal,
                    "source": source,
                    "parent_read_id": pid,
                    "query_name": record.query_name,
                    "target_state": state,
                    "target_base": base,
                    "is_primary": int(
                        not record.is_secondary
                        and not record.is_supplementary
                    ),
                    "is_secondary": int(record.is_secondary),
                    "is_supplementary": int(
                        record.is_supplementary
                    ),
                    "is_reverse": int(record.is_reverse),
                    "mapq": record.mapping_quality,
                    "reference_name": record.reference_name or "",
                    "reference_start_1based": (
                        record.reference_start + 1
                        if record.reference_start is not None
                        and record.reference_start >= 0
                        else ""
                    ),
                    "reference_end_1based": (
                        record.reference_end
                        if record.reference_end is not None
                        else ""
                    ),
                    "cigar": record.cigarstring or "",
                }
            )

    priority = [
        "ALT",
        "REF",
        "DEL",
        "OTHER",
        "NO_ALIGNED_PAIR",
        "NO_COVERAGE",
        "UNMAPPED",
    ]

    parent_rows = []

    for pid in sorted(parent_states):
        states = parent_states[pid]

        final_state = next(
            state
            for state in priority
            if state in states
        )

        parent_rows.append(
            {
                "condition": condition,
                "source": source_by_parent[pid],
                "parent_read_id": pid,
                "record_count": len(states),
                "record_states": ",".join(states),
                "parent_state": final_state,
            }
        )

    expected_parents = background_ids | replacement_ids
    observed_parents = set(parent_states)

    if observed_parents != expected_parents:
        raise RuntimeError(
            f"Hybrid parent mismatch: "
            f"missing={sorted(expected_parents - observed_parents)}, "
            f"extra={sorted(observed_parents - expected_parents)}"
        )

    background_state_errors = [
        row
        for row in parent_rows
        if (
            row["source"] == "same_sample_REF_background"
            and row["parent_state"] != "REF"
        )
    ]

    if background_state_errors:
        raise RuntimeError(
            f"Background contains non-REF parents: "
            f"{background_state_errors}"
        )

    with audit_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    with parent_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(parent_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(parent_rows)

    counts = Counter(
        row["parent_state"]
        for row in parent_rows
    )

    print(f"Condition: {condition}")
    print(f"Background records written: {background_written}")
    print(f"Background parents: {len(background_parents)}")
    print(f"Replacement records written: {replacement_written}")
    print(f"Replacement parents: {len(replacement_parents)}")
    print(f"Hybrid records: {len(rows)}")
    print(f"Hybrid parents: {len(parent_rows)}")
    print(
        "Parent states: "
        + ",".join(
            f"{state}={counts[state]}"
            for state in priority
        )
    )


if __name__ == "__main__":
    main()
