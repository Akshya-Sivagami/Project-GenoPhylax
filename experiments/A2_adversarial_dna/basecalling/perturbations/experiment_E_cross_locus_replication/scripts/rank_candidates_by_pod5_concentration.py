#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--summary", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--candidate-tsv", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-per-region", type=int, default=40)
    parser.add_argument("--min-mapped-alt", type=int, default=10)

    return parser.parse_args()


def load_manifest(path: Path):
    sizes = {}

    with path.open("rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            size_text, remote_path = line.split(maxsplit=1)
            filename = Path(remote_path).name
            sizes[filename] = int(size_text)

    return sizes


def load_candidates(paths, top_per_region):
    candidates = []
    id_to_candidates = defaultdict(list)

    for path_text in paths:
        path = Path(path_text)

        with path.open("rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")

            passing = [
                row
                for row in reader
                if row["status"] == "PASS"
            ][:top_per_region]

        for row in passing:
            key = f'{row["chrom"]}:{row["pos"]}:{row["ref"]}>{row["alt"]}'

            alt_ids = {
                value
                for value in row["alt_read_ids"].split(",")
                if value
            }

            candidate = {
                "candidate_key": key,
                "source_file": path.name,
                "chrom": row["chrom"],
                "pos": row["pos"],
                "ref": row["ref"],
                "alt": row["alt"],
                "total_depth": row["total_depth"],
                "ref_count": row["ref_count"],
                "alt_count": row["alt_count"],
                "alt_fraction": row["alt_fraction"],
                "other_fraction": row["other_fraction"],
                "mean_base_quality": row["mean_base_quality"],
                "mean_mapping_quality": row["mean_mapping_quality"],
                "candidate_score": row["candidate_score"],
                "alt_ids": alt_ids,
            }

            candidates.append(candidate)

            for read_id in alt_ids:
                id_to_candidates[read_id].append(candidate)

    return candidates, id_to_candidates


def main():
    args = parse_args()

    summary_path = Path(args.summary)
    manifest_sizes = load_manifest(Path(args.manifest))

    candidates, id_to_candidates = load_candidates(
        args.candidate_tsv,
        args.top_per_region,
    )

    wanted_ids = set(id_to_candidates)

    candidate_files = defaultdict(set)
    candidate_matched_ids = defaultdict(set)

    with summary_path.open(
        "rt",
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        required = {"read_id", "parent_read_id", "filename_pod5"}
        missing = required - set(reader.fieldnames or [])

        if missing:
            raise SystemExit(
                "Missing sequencing-summary columns: "
                + ", ".join(sorted(missing))
            )

        for record in reader:
            read_id = record.get("read_id", "")
            parent_id = record.get("parent_read_id", "")
            filename = record.get("filename_pod5", "")

            matching_ids = []

            if read_id in wanted_ids:
                matching_ids.append(read_id)

            if parent_id in wanted_ids and parent_id != read_id:
                matching_ids.append(parent_id)

            for target_id in matching_ids:
                for candidate in id_to_candidates[target_id]:
                    key = candidate["candidate_key"]

                    candidate_matched_ids[key].add(target_id)

                    if filename:
                        candidate_files[key].add(filename)

    output_rows = []

    for candidate in candidates:
        key = candidate["candidate_key"]
        requested_ids = candidate["alt_ids"]
        matched_ids = candidate_matched_ids[key]
        files = candidate_files[key]

        total_bytes = sum(
            manifest_sizes.get(filename, 0)
            for filename in files
        )

        missing_manifest = sorted(
            filename
            for filename in files
            if filename not in manifest_sizes
        )

        mapped_alt = len(matched_ids)
        unique_files = len(files)

        if unique_files:
            alt_reads_per_file = mapped_alt / unique_files
        else:
            alt_reads_per_file = 0.0

        download_gib = total_bytes / 1024**3

        eligible = (
            mapped_alt >= args.min_mapped_alt
            and not missing_manifest
        )

        efficiency_score = (
            float(candidate["candidate_score"])
            + 8.0 * mapped_alt
            - 5.0 * unique_files
            - 1.5 * download_gib
        )

        output_rows.append(
            {
                **{
                    key_name: value
                    for key_name, value in candidate.items()
                    if key_name != "alt_ids"
                },
                "requested_alt_ids": len(requested_ids),
                "mapped_alt_ids": mapped_alt,
                "missing_alt_ids": len(requested_ids - matched_ids),
                "unique_pod5_files": unique_files,
                "alt_reads_per_file": alt_reads_per_file,
                "download_bytes": total_bytes,
                "download_GiB": download_gib,
                "eligible": "YES" if eligible else "NO",
                "efficiency_score": efficiency_score,
                "pod5_files": ",".join(sorted(files)),
            }
        )

    output_rows.sort(
        key=lambda row: (
            row["eligible"] != "YES",
            -row["efficiency_score"],
            int(row["unique_pod5_files"]),
            -int(row["mapped_alt_ids"]),
        )
    )

    fieldnames = [
        "candidate_key",
        "source_file",
        "chrom",
        "pos",
        "ref",
        "alt",
        "total_depth",
        "ref_count",
        "alt_count",
        "alt_fraction",
        "other_fraction",
        "mean_base_quality",
        "mean_mapping_quality",
        "candidate_score",
        "requested_alt_ids",
        "mapped_alt_ids",
        "missing_alt_ids",
        "unique_pod5_files",
        "alt_reads_per_file",
        "download_bytes",
        "download_GiB",
        "eligible",
        "efficiency_score",
        "pod5_files",
    ]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Candidates evaluated: {len(output_rows)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
