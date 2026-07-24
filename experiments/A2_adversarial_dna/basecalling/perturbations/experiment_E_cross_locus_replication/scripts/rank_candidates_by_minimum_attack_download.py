#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Find the minimum-size POD5 cohort containing a required "
            "number of ALT-supporting reads for each candidate."
        )
    )

    parser.add_argument("--summary", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument(
        "--candidate-tsv",
        action="append",
        required=True,
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-per-region", type=int, default=40)
    parser.add_argument("--required-alt-reads", type=int, default=10)

    return parser.parse_args()


def load_manifest(path: Path):
    records = {}

    with path.open("rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            size_text, remote_path = line.split(maxsplit=1)
            filename = Path(remote_path).name

            records[filename] = {
                "size_bytes": int(size_text),
                "remote_path": remote_path,
            }

    return records


def load_candidates(paths, top_per_region):
    candidates = []
    wanted_ids = set()

    for path_text in paths:
        path = Path(path_text)

        with path.open(
            "rt",
            encoding="utf-8",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle, delimiter="\t")

            passing_rows = [
                row
                for row in reader
                if row["status"] == "PASS"
            ][:top_per_region]

        for row in passing_rows:
            alt_ids = {
                value
                for value in row["alt_read_ids"].split(",")
                if value
            }

            wanted_ids.update(alt_ids)

            candidates.append(
                {
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
                    "mean_base_quality": row[
                        "mean_base_quality"
                    ],
                    "mean_mapping_quality": row[
                        "mean_mapping_quality"
                    ],
                    "candidate_score": row[
                        "candidate_score"
                    ],
                    "alt_ids": alt_ids,
                }
            )

    return candidates, wanted_ids


def map_reads_to_files(summary_path: Path, wanted_ids):
    read_to_files = defaultdict(set)

    with summary_path.open(
        "rt",
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        required = {
            "read_id",
            "parent_read_id",
            "filename_pod5",
        }

        missing = required - set(reader.fieldnames or [])

        if missing:
            raise SystemExit(
                "ERROR: Missing sequencing-summary columns: "
                + ", ".join(sorted(missing))
            )

        for record in reader:
            filename = record.get("filename_pod5", "")
            read_id = record.get("read_id", "")
            parent_id = record.get("parent_read_id", "")

            if not filename:
                continue

            if read_id in wanted_ids:
                read_to_files[read_id].add(filename)

            if parent_id in wanted_ids:
                read_to_files[parent_id].add(filename)

    return read_to_files


def minimum_file_cohort(
    alt_ids,
    read_to_files,
    manifest,
    required_reads,
):
    usable_read_to_file = {}
    ambiguous_ids = []
    missing_ids = []

    for read_id in sorted(alt_ids):
        files = {
            filename
            for filename in read_to_files.get(read_id, set())
            if filename in manifest
        }

        if len(files) == 1:
            usable_read_to_file[read_id] = next(iter(files))
        elif len(files) == 0:
            missing_ids.append(read_id)
        else:
            ambiguous_ids.append(read_id)

    file_to_reads = defaultdict(set)

    for read_id, filename in usable_read_to_file.items():
        file_to_reads[filename].add(read_id)

    if len(usable_read_to_file) < required_reads:
        return {
            "eligible": False,
            "usable_ids": sorted(usable_read_to_file),
            "missing_ids": missing_ids,
            "ambiguous_ids": ambiguous_ids,
            "selected_files": [],
            "selected_ids": [],
            "selected_bytes": 0,
        }

    items = []

    for filename, read_ids in file_to_reads.items():
        items.append(
            (
                filename,
                manifest[filename]["size_bytes"],
                sorted(read_ids),
            )
        )

    # Since every usable read has exactly one POD5 filename,
    # file-associated read groups are disjoint. Dynamic programming
    # over capped read coverage therefore gives the exact minimum.
    dp = {
        0: {
            "bytes": 0,
            "files": [],
            "ids": [],
        }
    }

    for filename, size_bytes, read_ids in items:
        updated = dict(dp)

        for covered, state in dp.items():
            new_covered = min(
                required_reads,
                covered + len(read_ids),
            )

            candidate_state = {
                "bytes": state["bytes"] + size_bytes,
                "files": state["files"] + [filename],
                "ids": state["ids"] + read_ids,
            }

            current = updated.get(new_covered)

            if (
                current is None
                or candidate_state["bytes"] < current["bytes"]
                or (
                    candidate_state["bytes"] == current["bytes"]
                    and len(candidate_state["files"])
                    < len(current["files"])
                )
            ):
                updated[new_covered] = candidate_state

        dp = updated

    selected = dp.get(required_reads)

    if selected is None:
        raise RuntimeError(
            "Internal error: eligible candidate has no DP solution"
        )

    selected_ids = selected["ids"][:required_reads]

    return {
        "eligible": True,
        "usable_ids": sorted(usable_read_to_file),
        "missing_ids": missing_ids,
        "ambiguous_ids": ambiguous_ids,
        "selected_files": sorted(selected["files"]),
        "selected_ids": sorted(selected_ids),
        "selected_bytes": selected["bytes"],
    }


def main():
    args = parse_args()

    manifest = load_manifest(Path(args.manifest))

    candidates, wanted_ids = load_candidates(
        args.candidate_tsv,
        args.top_per_region,
    )

    read_to_files = map_reads_to_files(
        Path(args.summary),
        wanted_ids,
    )

    rows = []

    for candidate in candidates:
        result = minimum_file_cohort(
            candidate["alt_ids"],
            read_to_files,
            manifest,
            args.required_alt_reads,
        )

        ref_count = int(candidate["ref_count"])
        alt_count = int(candidate["alt_count"])
        balance_difference = abs(ref_count - alt_count)

        selected_gib = (
            result["selected_bytes"] / 1024**3
        )

        rows.append(
            {
                "candidate_key": (
                    f'{candidate["chrom"]}:'
                    f'{candidate["pos"]}:'
                    f'{candidate["ref"]}>'
                    f'{candidate["alt"]}'
                ),
                "source_file": candidate["source_file"],
                "chrom": candidate["chrom"],
                "pos": candidate["pos"],
                "ref": candidate["ref"],
                "alt": candidate["alt"],
                "total_depth": candidate["total_depth"],
                "ref_count": candidate["ref_count"],
                "alt_count": candidate["alt_count"],
                "balance_difference": balance_difference,
                "alt_fraction": candidate["alt_fraction"],
                "other_fraction": candidate["other_fraction"],
                "mean_base_quality": candidate[
                    "mean_base_quality"
                ],
                "mean_mapping_quality": candidate[
                    "mean_mapping_quality"
                ],
                "candidate_score": candidate[
                    "candidate_score"
                ],
                "requested_alt_ids": len(candidate["alt_ids"]),
                "usable_alt_ids": len(result["usable_ids"]),
                "missing_alt_ids": len(result["missing_ids"]),
                "ambiguous_alt_ids": len(
                    result["ambiguous_ids"]
                ),
                "required_attack_reads": (
                    args.required_alt_reads
                ),
                "minimum_pod5_files": len(
                    result["selected_files"]
                ),
                "minimum_download_bytes": (
                    result["selected_bytes"]
                ),
                "minimum_download_GiB": selected_gib,
                "eligible": (
                    "YES" if result["eligible"] else "NO"
                ),
                "selected_pod5_files": ",".join(
                    result["selected_files"]
                ),
                "selected_attack_read_ids": ",".join(
                    result["selected_ids"]
                ),
                "missing_read_ids": ",".join(
                    result["missing_ids"]
                ),
                "ambiguous_read_ids": ",".join(
                    result["ambiguous_ids"]
                ),
            }
        )

    # Correct priority:
    # 1. Candidate must have enough downloadable reads.
    # 2. Minimize download size.
    # 3. Minimize number of POD5 files.
    # 4. Prefer balanced REF/ALT evidence.
    # 5. Prefer stronger biological candidate score.
    rows.sort(
        key=lambda row: (
            row["eligible"] != "YES",
            float(row["minimum_download_GiB"]),
            int(row["minimum_pod5_files"]),
            int(row["balance_difference"]),
            -float(row["candidate_score"]),
        )
    )

    fieldnames = list(rows[0].keys())

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Candidates evaluated: {len(rows)}")
    print(
        "Eligible candidates: "
        f"{sum(row['eligible'] == 'YES' for row in rows)}"
    )
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
