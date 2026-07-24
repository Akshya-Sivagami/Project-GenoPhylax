#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pysam


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--l2-clean", required=True)
    parser.add_argument("--l2-w0", required=True)
    parser.add_argument("--l3-clean", required=True)
    parser.add_argument("--l3-w0", required=True)
    parser.add_argument("--per-read", required=True)
    parser.add_argument("--summary", required=True)
    return parser.parse_args()


def parent_id(record):
    return record.query_name.split()[0]


def classify_record(record, chrom, position, ref, alt):
    if record.is_unmapped:
        return {
            "state": "UNMAPPED",
            "base": "",
            "base_quality": "",
            "mapq": record.mapping_quality,
            "flag": record.flag,
            "is_primary": int(
                not record.is_secondary
                and not record.is_supplementary
            ),
            "query_position": "",
        }

    if record.reference_name != chrom:
        return {
            "state": "NO_COVERAGE",
            "base": "",
            "base_quality": "",
            "mapq": record.mapping_quality,
            "flag": record.flag,
            "is_primary": int(
                not record.is_secondary
                and not record.is_supplementary
            ),
            "query_position": "",
        }

    target_zero_based = position - 1

    if (
        record.reference_start > target_zero_based
        or record.reference_end <= target_zero_based
    ):
        return {
            "state": "NO_COVERAGE",
            "base": "",
            "base_quality": "",
            "mapq": record.mapping_quality,
            "flag": record.flag,
            "is_primary": int(
                not record.is_secondary
                and not record.is_supplementary
            ),
            "query_position": "",
        }

    for query_pos, reference_pos in record.get_aligned_pairs(
        matches_only=False
    ):
        if reference_pos != target_zero_based:
            continue

        if query_pos is None:
            return {
                "state": "DELETION",
                "base": "",
                "base_quality": "",
                "mapq": record.mapping_quality,
                "flag": record.flag,
                "is_primary": int(
                    not record.is_secondary
                    and not record.is_supplementary
                ),
                "query_position": "",
            }

        base = record.query_sequence[query_pos].upper()

        quality = ""
        if record.query_qualities is not None:
            quality = int(record.query_qualities[query_pos])

        if base == alt:
            state = "ALT"
        elif base == ref:
            state = "REF"
        else:
            state = "OTHER"

        return {
            "state": state,
            "base": base,
            "base_quality": quality,
            "mapq": record.mapping_quality,
            "flag": record.flag,
            "is_primary": int(
                not record.is_secondary
                and not record.is_supplementary
            ),
            "query_position": query_pos,
        }

    return {
        "state": "NO_COVERAGE",
        "base": "",
        "base_quality": "",
        "mapq": record.mapping_quality,
        "flag": record.flag,
        "is_primary": int(
            not record.is_secondary
            and not record.is_supplementary
        ),
        "query_position": "",
    }


STATE_PRIORITY = {
    "ALT": 6,
    "REF": 5,
    "OTHER": 4,
    "DELETION": 3,
    "NO_COVERAGE": 2,
    "UNMAPPED": 1,
}


def select_parent_state(records, chrom, position, ref, alt):
    observations = [
        classify_record(
            record,
            chrom,
            position,
            ref,
            alt,
        )
        for record in records
    ]

    primary_observations = [
        observation
        for observation in observations
        if observation["is_primary"] == 1
    ]

    candidates = (
        primary_observations
        if primary_observations
        else observations
    )

    selected = max(
        candidates,
        key=lambda observation: (
            STATE_PRIORITY[observation["state"]],
            observation["mapq"],
        ),
    )

    selected = dict(selected)
    selected["record_count"] = len(records)
    selected["primary_record_count"] = len(
        primary_observations
    )

    return selected


def load_parent_states(
    bam_path,
    chrom,
    position,
    ref,
    alt,
):
    grouped = defaultdict(list)

    with pysam.AlignmentFile(
        bam_path,
        "rb",
    ) as bam:
        for record in bam.fetch(until_eof=True):
            grouped[parent_id(record)].append(record)

    return {
        read_id: select_parent_state(
            records,
            chrom,
            position,
            ref,
            alt,
        )
        for read_id, records in grouped.items()
    }


def transition(clean_state, attacked_state):
    if clean_state == attacked_state:
        return f"{clean_state}_UNCHANGED"

    return f"{clean_state}_TO_{attacked_state}"


def analyse_locus(
    locus,
    chrom,
    position,
    ref,
    alt,
    clean_bam,
    attacked_bam,
):
    clean = load_parent_states(
        clean_bam,
        chrom,
        position,
        ref,
        alt,
    )

    attacked = load_parent_states(
        attacked_bam,
        chrom,
        position,
        ref,
        alt,
    )

    all_parents = sorted(set(clean) | set(attacked))

    rows = []

    for read_id in all_parents:
        clean_obs = clean.get(
            read_id,
            {
                "state": "MISSING",
                "base": "",
                "base_quality": "",
                "mapq": "",
                "flag": "",
                "is_primary": "",
                "query_position": "",
                "record_count": 0,
                "primary_record_count": 0,
            },
        )

        attacked_obs = attacked.get(
            read_id,
            {
                "state": "MISSING",
                "base": "",
                "base_quality": "",
                "mapq": "",
                "flag": "",
                "is_primary": "",
                "query_position": "",
                "record_count": 0,
                "primary_record_count": 0,
            },
        )

        rows.append(
            {
                "locus": locus,
                "chrom": chrom,
                "position": position,
                "ref": ref,
                "alt": alt,
                "parent_read_id": read_id,
                "clean_state": clean_obs["state"],
                "attacked_state": attacked_obs["state"],
                "transition": transition(
                    clean_obs["state"],
                    attacked_obs["state"],
                ),
                "clean_base": clean_obs["base"],
                "attacked_base": attacked_obs["base"],
                "clean_base_quality": (
                    clean_obs["base_quality"]
                ),
                "attacked_base_quality": (
                    attacked_obs["base_quality"]
                ),
                "clean_mapq": clean_obs["mapq"],
                "attacked_mapq": attacked_obs["mapq"],
                "clean_flag": clean_obs["flag"],
                "attacked_flag": attacked_obs["flag"],
                "clean_query_position": (
                    clean_obs["query_position"]
                ),
                "attacked_query_position": (
                    attacked_obs["query_position"]
                ),
                "clean_record_count": (
                    clean_obs["record_count"]
                ),
                "attacked_record_count": (
                    attacked_obs["record_count"]
                ),
                "clean_primary_record_count": (
                    clean_obs["primary_record_count"]
                ),
                "attacked_primary_record_count": (
                    attacked_obs["primary_record_count"]
                ),
            }
        )

    clean_alt_rows = [
        row
        for row in rows
        if row["clean_state"] == "ALT"
    ]

    attacked_counts = defaultdict(int)

    for row in clean_alt_rows:
        attacked_counts[row["attacked_state"]] += 1

    changed = sum(
        row["attacked_state"] != "ALT"
        for row in clean_alt_rows
    )

    summary = {
        "locus": locus,
        "chrom": chrom,
        "position": position,
        "ref": ref,
        "alt": alt,
        "clean_parent_count": len(clean),
        "attacked_parent_count": len(attacked),
        "clean_alt_parent_count": len(clean_alt_rows),
        "attacked_alt": attacked_counts["ALT"],
        "attacked_ref": attacked_counts["REF"],
        "attacked_deletion": attacked_counts["DELETION"],
        "attacked_other": attacked_counts["OTHER"],
        "attacked_no_coverage": (
            attacked_counts["NO_COVERAGE"]
        ),
        "attacked_unmapped": attacked_counts["UNMAPPED"],
        "attacked_missing": attacked_counts["MISSING"],
        "alt_changed_parents": changed,
        "alt_changed_percent": (
            changed * 100 / len(clean_alt_rows)
            if clean_alt_rows
            else 0
        ),
        "alt_retained_parents": (
            attacked_counts["ALT"]
        ),
        "status": (
            "EFFECT_OBSERVED"
            if changed > 0
            else "NO_EFFECT"
        ),
    }

    return rows, summary


def main():
    args = parse_args()

    loci = [
        (
            "L2_chr1_20061156_A_T",
            "chr1",
            20061156,
            "A",
            "T",
            args.l2_clean,
            args.l2_w0,
        ),
        (
            "L3_chr4_40028853_A_G",
            "chr4",
            40028853,
            "A",
            "G",
            args.l3_clean,
            args.l3_w0,
        ),
    ]

    all_rows = []
    summaries = []

    for locus in loci:
        rows, summary = analyse_locus(*locus)
        all_rows.extend(rows)
        summaries.append(summary)

    per_read_path = Path(args.per_read)
    summary_path = Path(args.summary)

    per_read_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    summary_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with per_read_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(all_rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(all_rows)

    with summary_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(summaries[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(summaries)

    for summary in summaries:
        print()
        print(summary["locus"])
        print(
            "  clean ALT parents: "
            f'{summary["clean_alt_parent_count"]}'
        )
        print(
            "  attacked ALT: "
            f'{summary["attacked_alt"]}'
        )
        print(
            "  attacked REF: "
            f'{summary["attacked_ref"]}'
        )
        print(
            "  attacked deletion: "
            f'{summary["attacked_deletion"]}'
        )
        print(
            "  attacked other: "
            f'{summary["attacked_other"]}'
        )
        print(
            "  ALT changed: "
            f'{summary["alt_changed_parents"]}/'
            f'{summary["clean_alt_parent_count"]} '
            f'({summary["alt_changed_percent"]:.2f}%)'
        )
        print(
            "  status: "
            f'{summary["status"]}'
        )


if __name__ == "__main__":
    main()
