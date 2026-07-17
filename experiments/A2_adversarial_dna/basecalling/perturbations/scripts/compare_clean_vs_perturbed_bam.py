#!/usr/bin/env python3
"""
Compare paired clean and perturbed Dorado unaligned BAM outputs.

Reads are matched by query name. Exact global sequence alignment is performed
using Edlib's native implementation.

Outputs:
  1. Per-read TSV
  2. Summary TSV

Insertions and deletions describe the transformation:
    clean sequence -> perturbed sequence
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from pathlib import Path

import edlib
import pysam


CIGAR_PATTERN = re.compile(r"(\d+)([=XID])")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare clean and perturbed Dorado unaligned BAM files."
    )

    parser.add_argument("--clean-bam", required=True, type=Path)
    parser.add_argument("--perturbed-bam", required=True, type=Path)
    parser.add_argument("--per-read-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)

    return parser.parse_args()


def load_reads(path: Path) -> dict[str, pysam.AlignedSegment]:
    reads: dict[str, pysam.AlignedSegment] = {}

    with pysam.AlignmentFile(path, "rb", check_sq=False) as bam:
        for record in bam.fetch(until_eof=True):
            name = record.query_name

            if not name:
                raise RuntimeError(f"Record without query name in {path}")

            if name in reads:
                raise RuntimeError(
                    f"Duplicate query name encountered in {path}: {name}"
                )

            reads[name] = record

    return reads


def mean_quality(record: pysam.AlignedSegment) -> float:
    qualities = record.query_qualities

    if qualities is None or len(qualities) == 0:
        return math.nan

    return float(sum(qualities) / len(qualities))


def parse_extended_cigar(cigar: str | None) -> tuple[int, int, int, int]:
    """
    Return matches, substitutions, insertions, deletions.

    Extended Edlib CIGAR operations:
      = match
      X substitution
      I insertion
      D deletion
    """

    if not cigar:
        return 0, 0, 0, 0

    matches = 0
    substitutions = 0
    insertions = 0
    deletions = 0

    consumed = 0

    for match in CIGAR_PATTERN.finditer(cigar):
        length = int(match.group(1))
        operation = match.group(2)
        consumed += len(match.group(0))

        if operation == "=":
            matches += length
        elif operation == "X":
            substitutions += length
        # Edlib CIGAR operations are expressed relative to its target.
        # For our reported transformation clean -> perturbed:
        #   Edlib I corresponds to a deletion from the clean sequence.
        #   Edlib D corresponds to an insertion into the perturbed sequence.
        elif operation == "I":
            deletions += length
        elif operation == "D":
            insertions += length

    if consumed != len(cigar):
        raise RuntimeError(f"Unexpected Edlib CIGAR: {cigar}")

    return matches, substitutions, insertions, deletions


def align_sequences(
    clean_sequence: str,
    perturbed_sequence: str,
) -> dict[str, int | float]:
    result = edlib.align(
        clean_sequence,
        perturbed_sequence,
        mode="NW",
        task="path",
    )

    edit_distance = int(result["editDistance"])

    if edit_distance < 0:
        raise RuntimeError("Edlib failed to produce an alignment")

    matches, substitutions, insertions, deletions = parse_extended_cigar(
        result["cigar"]
    )

    operation_total = substitutions + insertions + deletions

    if operation_total != edit_distance:
        raise RuntimeError(
            "CIGAR operation total does not match edit distance: "
            f"{operation_total} != {edit_distance}"
        )

    alignment_columns = matches + substitutions + insertions + deletions
    denominator = max(
        len(clean_sequence),
        len(perturbed_sequence),
        1,
    )

    normalized_edit_distance = edit_distance / denominator
    sequence_identity = 1.0 - normalized_edit_distance

    alignment_identity = (
        matches / alignment_columns
        if alignment_columns
        else 1.0
    )

    return {
        "edit_distance": edit_distance,
        "matches": matches,
        "substitutions": substitutions,
        "insertions": insertions,
        "deletions": deletions,
        "normalized_edit_distance": normalized_edit_distance,
        "sequence_identity": sequence_identity,
        "alignment_identity": alignment_identity,
    }


def valid_values(values: list[float]) -> list[float]:
    return [value for value in values if not math.isnan(value)]


def safe_mean(values: list[float]) -> float:
    valid = valid_values(values)
    return statistics.mean(valid) if valid else math.nan


def safe_median(values: list[float]) -> float:
    valid = valid_values(values)
    return statistics.median(valid) if valid else math.nan


def percentile(values: list[float], fraction: float) -> float:
    valid = sorted(valid_values(values))

    if not valid:
        return math.nan

    if len(valid) == 1:
        return valid[0]

    position = fraction * (len(valid) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return valid[lower]

    weight = position - lower

    return (
        valid[lower] * (1.0 - weight)
        + valid[upper] * weight
    )


def main() -> int:
    args = parse_args()

    for path in (args.clean_bam, args.perturbed_bam):
        if not path.is_file():
            raise FileNotFoundError(f"BAM not found: {path}")

    args.per_read_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)

    clean_reads = load_reads(args.clean_bam)
    perturbed_reads = load_reads(args.perturbed_bam)

    clean_names = set(clean_reads)
    perturbed_names = set(perturbed_reads)

    paired_names = sorted(clean_names & perturbed_names)
    clean_only = sorted(clean_names - perturbed_names)
    perturbed_only = sorted(perturbed_names - clean_names)

    rows: list[dict[str, object]] = []

    edit_distances: list[float] = []
    normalized_distances: list[float] = []
    sequence_identities: list[float] = []
    alignment_identities: list[float] = []

    clean_lengths: list[float] = []
    perturbed_lengths: list[float] = []
    length_changes: list[float] = []

    clean_qscores: list[float] = []
    perturbed_qscores: list[float] = []
    qscore_changes: list[float] = []

    total_matches = 0
    total_substitutions = 0
    total_insertions = 0
    total_deletions = 0

    exact_sequence_matches = 0

    for index, name in enumerate(paired_names, start=1):
        clean = clean_reads[name]
        perturbed = perturbed_reads[name]

        clean_sequence = clean.query_sequence or ""
        perturbed_sequence = perturbed.query_sequence or ""

        clean_length = len(clean_sequence)
        perturbed_length = len(perturbed_sequence)
        length_change = perturbed_length - clean_length

        clean_qscore = mean_quality(clean)
        perturbed_qscore = mean_quality(perturbed)
        qscore_change = perturbed_qscore - clean_qscore

        alignment = align_sequences(
            clean_sequence,
            perturbed_sequence,
        )

        sequence_identical = int(clean_sequence == perturbed_sequence)
        exact_sequence_matches += sequence_identical

        edit_distance = int(alignment["edit_distance"])
        normalized_distance = float(
            alignment["normalized_edit_distance"]
        )
        sequence_identity = float(alignment["sequence_identity"])
        alignment_identity = float(alignment["alignment_identity"])

        matches = int(alignment["matches"])
        substitutions = int(alignment["substitutions"])
        insertions = int(alignment["insertions"])
        deletions = int(alignment["deletions"])

        total_matches += matches
        total_substitutions += substitutions
        total_insertions += insertions
        total_deletions += deletions

        edit_distances.append(edit_distance)
        normalized_distances.append(normalized_distance)
        sequence_identities.append(sequence_identity)
        alignment_identities.append(alignment_identity)

        clean_lengths.append(clean_length)
        perturbed_lengths.append(perturbed_length)
        length_changes.append(length_change)

        clean_qscores.append(clean_qscore)
        perturbed_qscores.append(perturbed_qscore)
        qscore_changes.append(qscore_change)

        rows.append(
            {
                "read_id": name,
                "clean_length": clean_length,
                "perturbed_length": perturbed_length,
                "length_change": length_change,
                "clean_mean_qscore": f"{clean_qscore:.6f}",
                "perturbed_mean_qscore": f"{perturbed_qscore:.6f}",
                "mean_qscore_change": f"{qscore_change:.6f}",
                "sequence_identical": sequence_identical,
                "edit_distance": edit_distance,
                "normalized_edit_distance": f"{normalized_distance:.10f}",
                "sequence_identity_percent": f"{sequence_identity * 100:.6f}",
                "alignment_identity_percent": f"{alignment_identity * 100:.6f}",
                "matches": matches,
                "substitutions": substitutions,
                "insertions": insertions,
                "deletions": deletions,
            }
        )

        if index % 25 == 0 or index == len(paired_names):
            print(
                f"Aligned {index}/{len(paired_names)} paired reads",
                flush=True,
            )

    fields = [
        "read_id",
        "clean_length",
        "perturbed_length",
        "length_change",
        "clean_mean_qscore",
        "perturbed_mean_qscore",
        "mean_qscore_change",
        "sequence_identical",
        "edit_distance",
        "normalized_edit_distance",
        "sequence_identity_percent",
        "alignment_identity_percent",
        "matches",
        "substitutions",
        "insertions",
        "deletions",
    ]

    with args.per_read_output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    changed_sequences = len(paired_names) - exact_sequence_matches

    summary = [
        ("metric", "value"),
        ("comparison_engine", "edlib_global_NW_extended"),
        ("clean_bam_records", len(clean_reads)),
        ("perturbed_bam_records", len(perturbed_reads)),
        ("paired_reads", len(paired_names)),
        ("clean_only_reads", len(clean_only)),
        ("perturbed_only_reads", len(perturbed_only)),
        ("exact_sequence_matches", exact_sequence_matches),
        ("changed_sequences", changed_sequences),
        (
            "changed_sequence_fraction",
            f"{changed_sequences / len(paired_names):.10f}"
            if paired_names
            else "nan",
        ),
        ("total_edit_distance", int(sum(edit_distances))),
        ("mean_edit_distance", f"{safe_mean(edit_distances):.6f}"),
        ("median_edit_distance", f"{safe_median(edit_distances):.6f}"),
        (
            "p95_edit_distance",
            f"{percentile(edit_distances, 0.95):.6f}",
        ),
        (
            "mean_normalized_edit_distance",
            f"{safe_mean(normalized_distances):.10f}",
        ),
        (
            "median_normalized_edit_distance",
            f"{safe_median(normalized_distances):.10f}",
        ),
        (
            "p95_normalized_edit_distance",
            f"{percentile(normalized_distances, 0.95):.10f}",
        ),
        (
            "mean_sequence_identity_percent",
            f"{safe_mean(sequence_identities) * 100:.6f}",
        ),
        (
            "median_sequence_identity_percent",
            f"{safe_median(sequence_identities) * 100:.6f}",
        ),
        (
            "mean_alignment_identity_percent",
            f"{safe_mean(alignment_identities) * 100:.6f}",
        ),
        ("total_matches", total_matches),
        ("total_substitutions", total_substitutions),
        ("total_insertions", total_insertions),
        ("total_deletions", total_deletions),
        ("mean_clean_length", f"{safe_mean(clean_lengths):.6f}"),
        (
            "mean_perturbed_length",
            f"{safe_mean(perturbed_lengths):.6f}",
        ),
        ("mean_length_change", f"{safe_mean(length_changes):.6f}"),
        (
            "median_absolute_length_change",
            f"{safe_median([abs(v) for v in length_changes]):.6f}",
        ),
        (
            "reads_with_length_change",
            sum(value != 0 for value in length_changes),
        ),
        ("mean_clean_qscore", f"{safe_mean(clean_qscores):.6f}"),
        (
            "mean_perturbed_qscore",
            f"{safe_mean(perturbed_qscores):.6f}",
        ),
        (
            "mean_qscore_change",
            f"{safe_mean(qscore_changes):.6f}",
        ),
        (
            "median_qscore_change",
            f"{safe_median(qscore_changes):.6f}",
        ),
        (
            "reads_with_qscore_decrease",
            sum(value < 0 for value in qscore_changes),
        ),
        (
            "reads_with_qscore_increase",
            sum(value > 0 for value in qscore_changes),
        ),
        (
            "reads_with_unchanged_qscore",
            sum(value == 0 for value in qscore_changes),
        ),
    ]

    with args.summary_output.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows(summary)

    print("\nPaired BAM comparison complete")
    print(f"Paired reads:             {len(paired_names)}")
    print(f"Changed sequences:        {changed_sequences}")
    print(f"Total edit distance:      {int(sum(edit_distances))}")
    print(
        "Mean sequence identity:  "
        f"{safe_mean(sequence_identities) * 100:.4f}%"
    )
    print(
        "Mean Q-score change:      "
        f"{safe_mean(qscore_changes):.6f}"
    )
    print(f"Per-read output:          {args.per_read_output}")
    print(f"Summary output:           {args.summary_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
