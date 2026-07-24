#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pysam


ORIGINAL_CHROM = "chr20"
ORIGINAL_POS = 10003468
ORIGINAL_ALT_IDS = {
    "00533577-803b-48cd-814e-adfa3e058d91",
    "199fcf4a-a100-4779-b89e-c80f4793cdfc",
    "1de25dab-c1cd-4c85-9b97-0104f8f411a5",
    "26efcc36-d025-471e-933a-e57a2447c465",
    "72209365-d223-4c87-9ba5-63376a9170fd",
    "7c1164dc-2545-441b-ab5d-11227989dfe6",
    "9a90548e-31da-4b38-aba0-8b9f7a75e936",
    "9d796ae7-6945-4d1e-abb4-7bdce517a96d",
    "a634b28d-7579-4d22-b746-c799d1222281",
    "cb0e7285-3c4a-461b-8540-7f0a3fda312c",
    "e7f01a96-5fbc-463c-9f12-f4e323ea44f3",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Add sequence-context and read-overlap metrics to ranked "
            "heterozygous SNV candidates."
        )
    )

    parser.add_argument("--input-tsv", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output-tsv", required=True)
    parser.add_argument("--shortlist-tsv", required=True)
    parser.add_argument("--shortlist-size", type=int, default=5)

    return parser.parse_args()


def parse_ids(value: str) -> set[str]:
    if not value.strip():
        return set()

    return {
        item.strip()
        for item in value.split(",")
        if item.strip()
    }


def longest_identical_run(sequence: str) -> int:
    if not sequence:
        return 0

    longest = 1
    current = 1

    for previous, current_base in zip(sequence, sequence[1:]):
        if current_base == previous:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


def target_base_run(sequence: str, center_index: int) -> int:
    if not sequence:
        return 0

    base = sequence[center_index]

    left = center_index
    right = center_index

    while left > 0 and sequence[left - 1] == base:
        left -= 1

    while right + 1 < len(sequence) and sequence[right + 1] == base:
        right += 1

    return right - left + 1


def jaccard(first: set[str], second: set[str]) -> float:
    union = first | second

    if not union:
        return 0.0

    return len(first & second) / len(union)


def suitability_score(row: dict[str, str]) -> float:
    balance_distance = float(row["balance_distance"])
    mean_base_quality = float(row["mean_base_quality"])
    mean_mapping_quality = float(row["mean_mapping_quality"])
    usable_depth = int(row["usable_ref_alt_depth"])
    other_count = int(row["other_count"])
    strand_supported = int(row["strand_supported"])
    target_run = int(row["target_homopolymer_run"])
    max_run = int(row["max_context_homopolymer"])
    overlap = float(row["original_alt_jaccard"])
    distance = int(row["distance_from_original"])

    score = 100.0

    score -= balance_distance * 100.0
    score += min(mean_base_quality, 40.0) * 0.8
    score += min(mean_mapping_quality, 60.0) * 0.2
    score += min(usable_depth, 40) * 0.4

    score -= other_count * 8.0
    score += strand_supported * 10.0

    score -= max(0, target_run - 1) * 12.0
    score -= max(0, max_run - 3) * 5.0

    score -= overlap * 25.0

    if distance >= 3000:
        score += 8.0
    elif distance >= 1000:
        score += 4.0

    return score


def main() -> int:
    args = parse_args()

    input_path = Path(args.input_tsv)
    output_path = Path(args.output_tsv)
    shortlist_path = Path(args.shortlist_tsv)

    reference = pysam.FastaFile(args.reference)

    with input_path.open() as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)

    enriched: list[dict[str, str]] = []

    for row in rows:
        chrom = row["chrom"]
        pos = int(row["pos"])

        start = max(0, pos - 11)
        end = pos + 10

        context = reference.fetch(chrom, start, end).upper()

        if len(context) != 21:
            row["sequence_context_21bp"] = context
            row["target_homopolymer_run"] = "NA"
            row["max_context_homopolymer"] = "NA"
            row["context_gc_fraction"] = "NA"
            row["distance_from_original"] = str(
                abs(pos - ORIGINAL_POS)
                if chrom == ORIGINAL_CHROM
                else -1
            )
            row["original_alt_overlap_count"] = "NA"
            row["original_alt_jaccard"] = "NA"
            row["candidate_score"] = "-999"
            row["selection_status"] = "FAIL_CONTEXT"
            enriched.append(row)
            continue

        observed_ref = context[10]
        expected_ref = row["ref"].upper()

        alt_ids = parse_ids(row["alt_read_ids"])

        overlap_count = len(alt_ids & ORIGINAL_ALT_IDS)
        overlap_jaccard = jaccard(alt_ids, ORIGINAL_ALT_IDS)

        distance = (
            abs(pos - ORIGINAL_POS)
            if chrom == ORIGINAL_CHROM
            else -1
        )

        row["sequence_context_21bp"] = context
        row["target_homopolymer_run"] = str(
            target_base_run(context, 10)
        )
        row["max_context_homopolymer"] = str(
            longest_identical_run(context)
        )
        row["context_gc_fraction"] = (
            f"{(context.count('G') + context.count('C')) / len(context):.6f}"
        )
        row["distance_from_original"] = str(distance)
        row["original_alt_overlap_count"] = str(overlap_count)
        row["original_alt_jaccard"] = f"{overlap_jaccard:.6f}"

        context_ok = observed_ref == expected_ref
        depth_ok = int(row["usable_ref_alt_depth"]) >= 20
        allele_ok = int(row["ref_count"]) >= 8 and int(row["alt_count"]) >= 8
        quality_ok = (
            float(row["mean_base_quality"]) >= 25
            and float(row["mean_mapping_quality"]) >= 50
        )
        strand_ok = int(row["strand_supported"]) == 1
        noise_ok = int(row["other_count"]) == 0
        homopolymer_ok = (
            int(row["target_homopolymer_run"]) <= 2
            and int(row["max_context_homopolymer"]) <= 4
        )
        different_locus = not (
            chrom == ORIGINAL_CHROM and pos == ORIGINAL_POS
        )

        row["selection_status"] = (
            "PASS"
            if all(
                [
                    context_ok,
                    depth_ok,
                    allele_ok,
                    quality_ok,
                    strand_ok,
                    noise_ok,
                    homopolymer_ok,
                    different_locus,
                ]
            )
            else "REVIEW"
        )

        row["candidate_score"] = f"{suitability_score(row):.6f}"

        enriched.append(row)

    enriched.sort(
        key=lambda item: (
            item["selection_status"] == "PASS",
            float(item["candidate_score"]),
        ),
        reverse=True,
    )

    extra_fields = [
        "sequence_context_21bp",
        "target_homopolymer_run",
        "max_context_homopolymer",
        "context_gc_fraction",
        "distance_from_original",
        "original_alt_overlap_count",
        "original_alt_jaccard",
        "candidate_score",
        "selection_status",
    ]

    fieldnames = list(rows[0].keys())

    for field in extra_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(enriched)

    passing = [
        row
        for row in enriched
        if row["selection_status"] == "PASS"
    ]

    shortlist = passing[: args.shortlist_size]

    shortlist_fields = [
        "rank",
        "chrom",
        "pos",
        "ref",
        "alt",
        "truth_gt",
        "total_depth",
        "ref_count",
        "alt_count",
        "other_count",
        "alt_fraction",
        "mean_base_quality",
        "mean_mapping_quality",
        "ref_forward",
        "ref_reverse",
        "alt_forward",
        "alt_reverse",
        "sequence_context_21bp",
        "target_homopolymer_run",
        "max_context_homopolymer",
        "distance_from_original",
        "original_alt_overlap_count",
        "original_alt_jaccard",
        "candidate_score",
        "selection_status",
    ]

    with shortlist_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=shortlist_fields,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()

        for rank, row in enumerate(shortlist, start=1):
            output_row = dict(row)
            output_row["rank"] = rank
            writer.writerow(output_row)

    print(f"Input candidates: {len(rows)}")
    print(f"Passing candidates: {len(passing)}")
    print(f"Shortlisted candidates: {len(shortlist)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
