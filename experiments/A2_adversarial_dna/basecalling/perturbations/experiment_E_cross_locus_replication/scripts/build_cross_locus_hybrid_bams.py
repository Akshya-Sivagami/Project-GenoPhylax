#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pysam


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--candidate", required=True)
    parser.add_argument("--background", required=True)
    parser.add_argument("--selected-ids", required=True)
    parser.add_argument("--replacement", required=True)
    parser.add_argument("--output-unsorted", required=True)
    parser.add_argument("--audit-tsv", required=True)

    return parser.parse_args()


def parent_id(record):
    if record.has_tag("pi"):
        return str(record.get_tag("pi"))

    return record.query_name


def main():
    args = parse_args()

    background_path = Path(args.background)
    selected_path = Path(args.selected_ids)
    replacement_path = Path(args.replacement)
    output_path = Path(args.output_unsorted)
    audit_path = Path(args.audit_tsv)

    selected_ids = {
        line.strip()
        for line in selected_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    }

    if len(selected_ids) != 10:
        raise SystemExit(
            f"Expected 10 selected IDs, found {len(selected_ids)}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    audit_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    background_total = 0
    background_retained = 0
    background_removed = 0

    removed_parent_ids = set()

    replacement_total = 0
    replacement_written = 0
    replacement_parent_ids = set()

    with pysam.AlignmentFile(
        str(background_path),
        "rb",
    ) as background:
        with pysam.AlignmentFile(
            str(output_path),
            "wb",
            header=background.header,
        ) as output:

            for record in background.fetch(
                until_eof=True
            ):
                background_total += 1

                pid = parent_id(record)

                if (
                    pid in selected_ids
                    or record.query_name in selected_ids
                ):
                    background_removed += 1
                    removed_parent_ids.add(pid)
                    continue

                output.write(record)
                background_retained += 1

            with pysam.AlignmentFile(
                str(replacement_path),
                "rb",
            ) as replacement:

                for record in replacement.fetch(
                    until_eof=True
                ):
                    replacement_total += 1

                    pid = parent_id(record)

                    if (
                        pid not in selected_ids
                        and record.query_name
                        not in selected_ids
                    ):
                        raise RuntimeError(
                            "Unexpected replacement record: "
                            f"{record.query_name}"
                        )

                    output.write(record)
                    replacement_written += 1
                    replacement_parent_ids.add(pid)

    missing_removed = (
        selected_ids - removed_parent_ids
    )

    missing_replacement = (
        selected_ids - replacement_parent_ids
    )

    status = (
        "PASS"
        if (
            not missing_removed
            and not missing_replacement
            and len(replacement_parent_ids) == 10
        )
        else "FAIL"
    )

    rows = [
        {
            "candidate": args.candidate,
            "background_total_records": background_total,
            "background_retained_records": background_retained,
            "background_removed_records": background_removed,
            "removed_unique_parent_ids": len(
                removed_parent_ids
            ),
            "replacement_total_records": replacement_total,
            "replacement_written_records": replacement_written,
            "replacement_unique_parent_ids": len(
                replacement_parent_ids
            ),
            "missing_removed_parent_ids": len(
                missing_removed
            ),
            "missing_replacement_parent_ids": len(
                missing_replacement
            ),
            "status": status,
        }
    ]

    with audit_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Candidate: {args.candidate}")
    print(f"Background records: {background_total}")
    print(f"Removed records: {background_removed}")
    print(
        "Removed unique parents: "
        f"{len(removed_parent_ids)}"
    )
    print(
        "Replacement records written: "
        f"{replacement_written}"
    )
    print(
        "Replacement unique parents: "
        f"{len(replacement_parent_ids)}"
    )
    print(f"Status: {status}")

    if status != "PASS":
        if missing_removed:
            print(
                "Missing from background: "
                + ",".join(sorted(missing_removed))
            )

        if missing_replacement:
            print(
                "Missing from replacement: "
                + ",".join(sorted(missing_replacement))
            )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
