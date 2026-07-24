#!/usr/bin/env python3

import argparse
import csv
import statistics
from pathlib import Path

import pysam


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rank GIAB heterozygous SNVs using observed BAM support."
    )

    parser.add_argument("--bam", required=True)
    parser.add_argument("--truth-vcf", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)

    parser.add_argument("--min-depth", type=int, default=20)
    parser.add_argument("--max-depth", type=int, default=60)
    parser.add_argument("--min-ref", type=int, default=7)
    parser.add_argument("--min-alt", type=int, default=7)
    parser.add_argument("--min-mapq", type=int, default=20)
    parser.add_argument("--min-baseq", type=int, default=10)
    parser.add_argument("--max-other-fraction", type=float, default=0.15)

    return parser.parse_args()


def get_truth_variants(vcf_path, region):
    variants = []

    with pysam.VariantFile(vcf_path) as vcf:
        for record in vcf.fetch(region=region):
            if len(record.ref) != 1:
                continue

            if not record.alts or len(record.alts) != 1:
                continue

            alt = record.alts[0]

            if len(alt) != 1:
                continue

            if record.filter.keys() and "PASS" not in record.filter.keys():
                continue

            sample = next(iter(record.samples.values()))
            gt = sample.get("GT")

            if gt not in {(0, 1), (1, 0)}:
                continue

            variants.append(
                {
                    "chrom": record.chrom,
                    "pos": record.pos,
                    "ref": record.ref.upper(),
                    "alt": alt.upper(),
                    "truth_gt": "0/1",
                    "truth_qual": (
                        record.qual if record.qual is not None else "."
                    ),
                }
            )

    return variants


def analyze_variant(bam, variant, args):
    chrom = variant["chrom"]
    pos = variant["pos"]
    ref = variant["ref"]
    alt = variant["alt"]

    ref_ids = []
    alt_ids = []
    other_ids = []
    deletion_ids = []

    base_qualities = []
    mapping_qualities = []

    ref_forward = 0
    ref_reverse = 0
    alt_forward = 0
    alt_reverse = 0

    seen_reads = set()

    for column in bam.pileup(
        chrom,
        pos - 1,
        pos,
        truncate=True,
        stepper="all",
        min_base_quality=0,
        max_depth=100000,
    ):
        if column.reference_pos != pos - 1:
            continue

        for pileup_read in column.pileups:
            read = pileup_read.alignment

            if read.is_unmapped:
                continue

            if read.is_secondary or read.is_supplementary:
                continue

            if read.is_duplicate or read.is_qcfail:
                continue

            if read.mapping_quality < args.min_mapq:
                continue

            read_id = read.query_name

            if read_id in seen_reads:
                continue

            seen_reads.add(read_id)
            mapping_qualities.append(read.mapping_quality)

            if pileup_read.is_del or pileup_read.is_refskip:
                deletion_ids.append(read_id)
                continue

            query_position = pileup_read.query_position

            if query_position is None:
                deletion_ids.append(read_id)
                continue

            if read.query_sequence is None:
                continue

            base = read.query_sequence[query_position].upper()

            if read.query_qualities is not None:
                baseq = read.query_qualities[query_position]
            else:
                baseq = 0

            if baseq < args.min_baseq:
                continue

            base_qualities.append(baseq)

            if base == ref:
                ref_ids.append(read_id)

                if read.is_reverse:
                    ref_reverse += 1
                else:
                    ref_forward += 1

            elif base == alt:
                alt_ids.append(read_id)

                if read.is_reverse:
                    alt_reverse += 1
                else:
                    alt_forward += 1

            else:
                other_ids.append(read_id)

    ref_count = len(ref_ids)
    alt_count = len(alt_ids)
    other_count = len(other_ids)
    deletion_count = len(deletion_ids)

    usable_depth = ref_count + alt_count + other_count
    total_depth = usable_depth + deletion_count

    alt_fraction = (
        alt_count / (ref_count + alt_count)
        if ref_count + alt_count
        else 0.0
    )

    balance_distance = abs(alt_fraction - 0.5)

    other_fraction = (
        (other_count + deletion_count) / total_depth
        if total_depth
        else 1.0
    )

    strand_supported = int(
        ref_forward > 0
        and ref_reverse > 0
        and alt_forward > 0
        and alt_reverse > 0
    )

    mean_base_quality = (
        statistics.mean(base_qualities)
        if base_qualities
        else 0.0
    )

    mean_mapping_quality = (
        statistics.mean(mapping_qualities)
        if mapping_qualities
        else 0.0
    )

    passes = (
        args.min_depth <= total_depth <= args.max_depth
        and ref_count >= args.min_ref
        and alt_count >= args.min_alt
        and other_fraction <= args.max_other_fraction
        and strand_supported == 1
    )

    score = (
        100.0
        - 100.0 * balance_distance
        + min(total_depth, 40)
        + min(mean_base_quality, 45)
        + min(mean_mapping_quality, 60) / 2.0
        + 10.0 * strand_supported
        - 50.0 * other_fraction
    )

    return {
        **variant,
        "total_depth": total_depth,
        "usable_ref_alt_depth": ref_count + alt_count,
        "ref_count": ref_count,
        "alt_count": alt_count,
        "other_count": other_count,
        "deletion_count": deletion_count,
        "alt_fraction": alt_fraction,
        "balance_distance": balance_distance,
        "ref_forward": ref_forward,
        "ref_reverse": ref_reverse,
        "alt_forward": alt_forward,
        "alt_reverse": alt_reverse,
        "strand_supported": strand_supported,
        "mean_base_quality": mean_base_quality,
        "mean_mapping_quality": mean_mapping_quality,
        "other_fraction": other_fraction,
        "candidate_score": score,
        "status": "PASS" if passes else "FAIL",
        "ref_read_ids": ",".join(sorted(ref_ids)),
        "alt_read_ids": ",".join(sorted(alt_ids)),
        "other_read_ids": ",".join(sorted(other_ids)),
        "deletion_read_ids": ",".join(sorted(deletion_ids)),
    }


def main():
    args = parse_args()

    output_path = Path(args.output)
    summary_path = Path(args.summary)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    variants = get_truth_variants(args.truth_vcf, args.region)

    with pysam.AlignmentFile(
        args.bam,
        "rb",
        reference_filename=args.reference,
    ) as bam:
        results = [
            analyze_variant(bam, variant, args)
            for variant in variants
        ]

    results.sort(
        key=lambda row: (
            row["status"] != "PASS",
            -row["candidate_score"],
            row["chrom"],
            row["pos"],
        )
    )

    fieldnames = [
        "chrom",
        "pos",
        "ref",
        "alt",
        "truth_gt",
        "truth_qual",
        "total_depth",
        "usable_ref_alt_depth",
        "ref_count",
        "alt_count",
        "other_count",
        "deletion_count",
        "alt_fraction",
        "balance_distance",
        "ref_forward",
        "ref_reverse",
        "alt_forward",
        "alt_reverse",
        "strand_supported",
        "mean_base_quality",
        "mean_mapping_quality",
        "other_fraction",
        "candidate_score",
        "status",
        "ref_read_ids",
        "alt_read_ids",
        "other_read_ids",
        "deletion_read_ids",
    ]

    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(results)

    passing = [row for row in results if row["status"] == "PASS"]

    with summary_path.open("w") as handle:
        handle.write(f"region={args.region}\n")
        handle.write(f"truth_het_snvs={len(variants)}\n")
        handle.write(f"evaluated_candidates={len(results)}\n")
        handle.write(f"passing_candidates={len(passing)}\n")

        if passing:
            best = passing[0]

            handle.write(
                "best_candidate="
                f'{best["chrom"]}:{best["pos"]} '
                f'{best["ref"]}>{best["alt"]}\n'
            )
            handle.write(
                f'best_depth={best["total_depth"]}\n'
            )
            handle.write(
                f'best_ref_count={best["ref_count"]}\n'
            )
            handle.write(
                f'best_alt_count={best["alt_count"]}\n'
            )
            handle.write(
                f'best_score={best["candidate_score"]:.6f}\n'
            )

    print(f"Truth heterozygous SNVs: {len(variants)}")
    print(f"Passing candidates: {len(passing)}")
    print(f"Output: {output_path}")

    if passing:
        best = passing[0]
        print(
            "Best candidate: "
            f'{best["chrom"]}:{best["pos"]} '
            f'{best["ref"]}>{best["alt"]} '
            f'depth={best["total_depth"]} '
            f'REF={best["ref_count"]} '
            f'ALT={best["alt_count"]} '
            f'score={best["candidate_score"]:.3f}'
        )


if __name__ == "__main__":
    main()
