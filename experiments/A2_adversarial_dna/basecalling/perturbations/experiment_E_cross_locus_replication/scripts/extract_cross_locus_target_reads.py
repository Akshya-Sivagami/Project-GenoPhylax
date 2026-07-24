#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pod5


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Extract selected raw reads from downloaded POD5 shards "
            "into locus-specific POD5 files."
        )
    )

    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--cohort-tsv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--audit-tsv", required=True)

    return parser.parse_args()


def main():
    args = parse_args()

    source_dir = Path(args.source_dir)
    cohort_path = Path(args.cohort_tsv)
    output_dir = Path(args.output_dir)
    audit_path = Path(args.audit_tsv)

    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    candidate_to_ids: dict[str, set[str]] = {}

    with cohort_path.open(
        "rt",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        required_columns = {
            "candidate",
            "read_id",
        }

        missing_columns = (
            required_columns - set(reader.fieldnames or [])
        )

        if missing_columns:
            raise SystemExit(
                "ERROR: Missing cohort columns: "
                + ", ".join(sorted(missing_columns))
            )

        for row in reader:
            candidate = row["candidate"].strip()
            read_id = row["read_id"].strip()

            if not candidate or not read_id:
                continue

            candidate_to_ids.setdefault(
                candidate,
                set(),
            ).add(read_id)

    if not candidate_to_ids:
        raise SystemExit(
            "ERROR: No target reads loaded from cohort TSV"
        )

    all_target_ids = set().union(
        *candidate_to_ids.values()
    )

    read_to_candidate = {}

    for candidate, read_ids in candidate_to_ids.items():
        for read_id in read_ids:
            if read_id in read_to_candidate:
                raise SystemExit(
                    "ERROR: Read ID appears in multiple cohorts: "
                    f"{read_id}"
                )

            read_to_candidate[read_id] = candidate

    pod5_files = sorted(
        source_dir.glob("*.pod5")
    )

    if not pod5_files:
        raise SystemExit(
            f"ERROR: No POD5 files found in {source_dir}"
        )

    output_paths = {
        candidate: output_dir / f"{candidate}.pod5"
        for candidate in candidate_to_ids
    }

    for output_path in output_paths.values():
        if output_path.exists():
            output_path.unlink()

    writers = {
        candidate: pod5.Writer(output_path)
        for candidate, output_path in output_paths.items()
    }

    found_ids: set[str] = set()
    audit_rows = []

    try:
        for pod5_path in pod5_files:
            print(f"Scanning: {pod5_path.name}")

            with pod5.Reader(pod5_path) as reader:
                for read in reader.reads():
                    read_id = str(read.read_id)

                    if read_id not in all_target_ids:
                        continue

                    candidate = read_to_candidate[read_id]

                    if read_id in found_ids:
                        raise SystemExit(
                            "ERROR: Duplicate target read encountered "
                            f"across source POD5 files: {read_id}"
                        )

                    writers[candidate].add_read(read.to_read())
                    found_ids.add(read_id)

                    audit_rows.append(
                        {
                            "candidate": candidate,
                            "read_id": read_id,
                            "source_pod5": pod5_path.name,
                            "signal_samples": len(read.signal),
                            "channel": read.pore.channel,
                            "read_number": read.read_number,
                            "status": "FOUND",
                        }
                    )

                    print(
                        f"FOUND: {candidate} "
                        f"{read_id} "
                        f"samples={len(read.signal)}"
                    )

    finally:
        for writer in writers.values():
            writer.close()

    missing_ids = sorted(
        all_target_ids - found_ids
    )

    for read_id in missing_ids:
        audit_rows.append(
            {
                "candidate": read_to_candidate[read_id],
                "read_id": read_id,
                "source_pod5": "",
                "signal_samples": "",
                "channel": "",
                "read_number": "",
                "status": "MISSING",
            }
        )

    fieldnames = [
        "candidate",
        "read_id",
        "source_pod5",
        "signal_samples",
        "channel",
        "read_number",
        "status",
    ]

    with audit_path.open(
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
        writer.writerows(
            sorted(
                audit_rows,
                key=lambda row: (
                    row["candidate"],
                    row["read_id"],
                ),
            )
        )

    print()
    print("=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Source POD5 files scanned: {len(pod5_files)}")
    print(f"Requested target reads: {len(all_target_ids)}")
    print(f"Extracted target reads: {len(found_ids)}")
    print(f"Missing target reads: {len(missing_ids)}")

    for candidate in sorted(candidate_to_ids):
        requested = candidate_to_ids[candidate]
        extracted = requested & found_ids

        print(
            f"{candidate}: "
            f"{len(extracted)}/{len(requested)}"
        )

        print(
            f"  Output: {output_paths[candidate]}"
        )

    if missing_ids:
        print()
        print("Missing IDs:")

        for read_id in missing_ids:
            print(
                f"{read_to_candidate[read_id]}\t{read_id}"
            )

        raise SystemExit(1)

    print()
    print("TARGET READ EXTRACTION: PASS")


if __name__ == "__main__":
    main()
