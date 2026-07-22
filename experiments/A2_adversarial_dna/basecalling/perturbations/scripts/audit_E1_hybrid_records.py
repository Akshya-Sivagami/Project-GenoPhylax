#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Optional

import pysam


TARGET_REF = "C"
TARGET_ALT = "G"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit every record in matched clean and attacked E1 hybrid BAMs."
        )
    )

    parser.add_argument("--clean-hybrid", required=True)
    parser.add_argument("--attacked-hybrid", required=True)
    parser.add_argument("--background", required=True)
    parser.add_argument("--clean-replacements", required=True)
    parser.add_argument("--attacked-replacements", required=True)
    parser.add_argument("--chrom", required=True)
    parser.add_argument("--position", required=True, type=int)
    parser.add_argument("--output-table", required=True)
    parser.add_argument("--output-summary", required=True)
    parser.add_argument("--output-validation", required=True)

    return parser.parse_args()


def parent_id(record: pysam.AlignedSegment) -> str:
    if record.has_tag("pi"):
        return str(record.get_tag("pi"))

    return record.query_name


def record_key(record: pysam.AlignedSegment) -> tuple:
    return (
        record.query_name,
        parent_id(record),
        record.flag,
        record.reference_name,
        record.reference_start,
        record.cigarstring,
    )


def load_record_keys(path: str) -> set[tuple]:
    keys: set[tuple] = set()

    with pysam.AlignmentFile(path, "rb") as bam:
        for record in bam.fetch(until_eof=True):
            keys.add(record_key(record))

    return keys


def target_state(
    record: pysam.AlignedSegment,
    chrom: str,
    position_1based: int,
) -> tuple[str, str, str]:
    if record.is_unmapped:
        return "NO_COVERAGE", ".", "unmapped"

    if record.reference_name != chrom:
        return "NO_COVERAGE", ".", "different_contig"

    target_0based = position_1based - 1

    if (
        record.reference_start is None
        or record.reference_end is None
        or target_0based < record.reference_start
        or target_0based >= record.reference_end
    ):
        return "NO_COVERAGE", ".", "outside_alignment_span"

    for query_pos, reference_pos in record.get_aligned_pairs(
        matches_only=False
    ):
        if reference_pos != target_0based:
            continue

        if query_pos is None:
            return "DELETION", "*", "cigar_deletion_or_refskip"

        if record.query_sequence is None:
            return "OTHER", ".", "missing_query_sequence"

        base = record.query_sequence[query_pos].upper()

        if base == TARGET_REF:
            return "REF", base, "aligned_base"

        if base == TARGET_ALT:
            return "ALT", base, "aligned_base"

        if base in {"A", "T", "N"}:
            return "OTHER", base, "aligned_base"

        return "OTHER", base, "aligned_base"

    return "NO_COVERAGE", ".", "no_aligned_pair_at_target"


def classify_background(target_class: str) -> str:
    if target_class == "REF":
        return "background-REF"

    if target_class == "ALT":
        return "background-ALT(B)"

    return "background-other"


def audit_hybrid(
    *,
    condition: str,
    hybrid_path: str,
    background_keys: set[tuple],
    replacement_keys: set[tuple],
    replacement_label: str,
    chrom: str,
    position: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    with pysam.AlignmentFile(hybrid_path, "rb") as bam:
        for ordinal, record in enumerate(
            bam.fetch(until_eof=True),
            start=1,
        ):
            key = record_key(record)

            in_background = key in background_keys
            in_replacement = key in replacement_keys

            if in_background and in_replacement:
                source_membership = "ERROR_BOTH"
            elif in_background:
                source_membership = "background"
            elif in_replacement:
                source_membership = replacement_label
            else:
                source_membership = "ERROR_UNKNOWN"

            target_class, target_base, target_reason = target_state(
                record,
                chrom,
                position,
            )

            if source_membership == "background":
                requested_category = classify_background(target_class)
            elif source_membership == "swap-cohort-clean":
                requested_category = "swap-cohort-clean"
            elif source_membership == "swap-cohort-attacked":
                requested_category = "swap-cohort-attacked"
            else:
                requested_category = source_membership

            rows.append(
                {
                    "condition": condition,
                    "record_ordinal": str(ordinal),
                    "requested_category": requested_category,
                    "source_membership": source_membership,
                    "qname": record.query_name,
                    "parent_id": parent_id(record),
                    "flag": str(record.flag),
                    "is_primary": str(
                        not record.is_secondary
                        and not record.is_supplementary
                    ),
                    "is_secondary": str(record.is_secondary),
                    "is_supplementary": str(
                        record.is_supplementary
                    ),
                    "is_reverse": str(record.is_reverse),
                    "reference_name": (
                        record.reference_name
                        if record.reference_name is not None
                        else "."
                    ),
                    "reference_start_1based": (
                        str(record.reference_start + 1)
                        if record.reference_start is not None
                        else "."
                    ),
                    "reference_end_1based_inclusive": (
                        str(record.reference_end)
                        if record.reference_end is not None
                        else "."
                    ),
                    "mapq": str(record.mapping_quality),
                    "cigar": record.cigarstring or ".",
                    "covers_target": str(
                        target_class != "NO_COVERAGE"
                    ),
                    "target_class": target_class,
                    "target_base": target_base,
                    "target_reason": target_reason,
                }
            )

    return rows


def write_table(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise RuntimeError("Audit produced no rows.")

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    counters: Counter[tuple[str, str, str]] = Counter()

    for row in rows:
        counters[
            (
                row["condition"],
                row["source_membership"],
                row["target_class"],
            )
        ] += 1

    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "condition",
                "source_membership",
                "target_class",
                "record_count",
            ]
        )

        for key in sorted(counters):
            writer.writerow([*key, counters[key]])


def main() -> int:
    args = parse_args()

    background_keys = load_record_keys(args.background)
    clean_replacement_keys = load_record_keys(
        args.clean_replacements
    )
    attacked_replacement_keys = load_record_keys(
        args.attacked_replacements
    )

    clean_rows = audit_hybrid(
        condition="clean_dorado_controlled",
        hybrid_path=args.clean_hybrid,
        background_keys=background_keys,
        replacement_keys=clean_replacement_keys,
        replacement_label="swap-cohort-clean",
        chrom=args.chrom,
        position=args.position,
    )

    attacked_rows = audit_hybrid(
        condition="attacked_dorado_controlled",
        hybrid_path=args.attacked_hybrid,
        background_keys=background_keys,
        replacement_keys=attacked_replacement_keys,
        replacement_label="swap-cohort-attacked",
        chrom=args.chrom,
        position=args.position,
    )

    rows = clean_rows + attacked_rows

    table_path = Path(args.output_table)
    summary_path = Path(args.output_summary)
    validation_path = Path(args.output_validation)

    write_table(table_path, rows)
    write_summary(summary_path, rows)

    validations: list[tuple[str, bool, str]] = []

    validations.append(
        (
            "clean_hybrid_record_count",
            len(clean_rows) == 63,
            f"observed={len(clean_rows)} expected=63",
        )
    )

    validations.append(
        (
            "attacked_hybrid_record_count",
            len(attacked_rows) == 63,
            f"observed={len(attacked_rows)} expected=63",
        )
    )

    clean_background = [
        row
        for row in clean_rows
        if row["source_membership"] == "background"
    ]

    attacked_background = [
        row
        for row in attacked_rows
        if row["source_membership"] == "background"
    ]

    clean_swaps = [
        row
        for row in clean_rows
        if row["source_membership"] == "swap-cohort-clean"
    ]

    attacked_swaps = [
        row
        for row in attacked_rows
        if row["source_membership"] == "swap-cohort-attacked"
    ]

    validations.extend(
        [
            (
                "clean_background_count",
                len(clean_background) == 51,
                f"observed={len(clean_background)} expected=51",
            ),
            (
                "attacked_background_count",
                len(attacked_background) == 51,
                f"observed={len(attacked_background)} expected=51",
            ),
            (
                "clean_swap_count",
                len(clean_swaps) == 12,
                f"observed={len(clean_swaps)} expected=12",
            ),
            (
                "attacked_swap_count",
                len(attacked_swaps) == 12,
                f"observed={len(attacked_swaps)} expected=12",
            ),
        ]
    )

    unknown_rows = [
        row
        for row in rows
        if row["source_membership"].startswith("ERROR")
    ]

    validations.append(
        (
            "no_unknown_or_double_membership",
            len(unknown_rows) == 0,
            f"error_rows={len(unknown_rows)}",
        )
    )

    def background_signature(row: dict[str, str]) -> tuple:
        return (
            row["qname"],
            row["parent_id"],
            row["flag"],
            row["reference_name"],
            row["reference_start_1based"],
            row["cigar"],
            row["target_class"],
            row["target_base"],
        )

    clean_background_signatures = sorted(
        background_signature(row)
        for row in clean_background
    )

    attacked_background_signatures = sorted(
        background_signature(row)
        for row in attacked_background
    )

    validations.append(
        (
            "background_records_and_target_states_identical",
            clean_background_signatures
            == attacked_background_signatures,
            (
                f"clean={len(clean_background_signatures)} "
                f"attacked={len(attacked_background_signatures)}"
            ),
        )
    )

    clean_background_alt = sum(
        row["target_class"] == "ALT"
        for row in clean_background
    )

    attacked_background_alt = sum(
        row["target_class"] == "ALT"
        for row in attacked_background
    )

    validations.append(
        (
            "background_alt_raw_record_count_identical",
            clean_background_alt == attacked_background_alt,
            (
                f"clean={clean_background_alt} "
                f"attacked={attacked_background_alt}"
            ),
        )
    )

    clean_target_records = sum(
        row["target_class"] != "NO_COVERAGE"
        for row in clean_rows
    )

    attacked_target_records = sum(
        row["target_class"] != "NO_COVERAGE"
        for row in attacked_rows
    )

    validations.append(
        (
            "target_overlapping_record_count_identical",
            clean_target_records == attacked_target_records == 39,
            (
                f"clean={clean_target_records} "
                f"attacked={attacked_target_records} expected=39"
            ),
        )
    )

    clean_swap_counts = Counter(
        row["target_class"] for row in clean_swaps
    )

    attacked_swap_counts = Counter(
        row["target_class"] for row in attacked_swaps
    )

    validation_lines = [
        "Experiment E1 — Per-Record Hybrid Audit Validation",
        "===================================================",
        "",
    ]

    all_passed = True

    for name, passed, detail in validations:
        status = "PASS" if passed else "FAIL"
        all_passed = all_passed and passed
        validation_lines.append(
            f"{status}\t{name}\t{detail}"
        )

    validation_lines.extend(
        [
            "",
            "Raw per-record background target states:",
            (
                f"clean_background_ALT="
                f"{clean_background_alt}"
            ),
            (
                f"attacked_background_ALT="
                f"{attacked_background_alt}"
            ),
            "",
            "Raw clean swap-cohort target states:",
            repr(dict(sorted(clean_swap_counts.items()))),
            "",
            "Raw attacked swap-cohort target states:",
            repr(dict(sorted(attacked_swap_counts.items()))),
            "",
            (
                "OVERALL: PASS"
                if all_passed
                else "OVERALL: FAIL"
            ),
        ]
    )

    validation_path.write_text(
        "\n".join(validation_lines) + "\n"
    )

    print("\n".join(validation_lines))

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
