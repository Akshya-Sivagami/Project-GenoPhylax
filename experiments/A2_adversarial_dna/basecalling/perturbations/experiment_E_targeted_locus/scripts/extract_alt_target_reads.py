from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

import pod5


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "Usage: extract_alt_target_reads.py "
            "<source_dir> <read_ids.txt> <output.pod5> "
            "<manifest.tsv> <validation.txt>",
            file=sys.stderr,
        )
        return 2

    source_dir = Path(sys.argv[1])
    read_ids_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    manifest_path = Path(sys.argv[4])
    validation_path = Path(sys.argv[5])

    wanted = {
        line.strip()
        for line in read_ids_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    source_files = sorted(source_dir.glob("*.pod5"))

    if not source_files:
        raise SystemExit("ERROR: No source POD5 files found.")

    if output_path.exists():
        output_path.unlink()

    found_counts: Counter[str] = Counter()
    manifest_rows: list[dict[str, object]] = []

    with pod5.Writer(
        output_path,
        software_name="GenoPhylax Experiment E ALT read extraction",
    ) as writer:
        for source_path in source_files:
            print(f"Scanning: {source_path.name}")

            with pod5.Reader(source_path) as reader:
                for read in reader.reads():
                    read_id = str(read.read_id)

                    if read_id not in wanted:
                        continue

                    found_counts[read_id] += 1

                    if found_counts[read_id] > 1:
                        print(
                            f"WARNING: duplicate occurrence of {read_id} "
                            f"in {source_path.name}"
                        )
                        continue

                    writer.add_read(read.to_read())

                    manifest_rows.append(
                        {
                            "read_id": read_id,
                            "source_pod5": source_path.name,
                            "signal_samples": len(read.signal),
                            "sample_rate": read.run_info.sample_rate,
                            "channel": read.pore.channel,
                            "well": read.pore.well,
                            "read_number": read.read_number,
                        }
                    )

    found = set(found_counts)
    missing = sorted(wanted - found)
    duplicates = sorted(
        read_id
        for read_id, count in found_counts.items()
        if count > 1
    )
    unexpected = sorted(found - wanted)

    manifest_rows.sort(key=lambda row: str(row["read_id"]))

    with manifest_path.open(
        "wt",
        encoding="utf-8",
        newline="",
    ) as handle:
        fieldnames = [
            "read_id",
            "source_pod5",
            "signal_samples",
            "sample_rate",
            "channel",
            "well",
            "read_number",
        ]

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(manifest_rows)

    validation_lines = [
        "Experiment E ALT raw-read extraction",
        "====================================",
        f"Requested IDs: {len(wanted)}",
        f"Found unique IDs: {len(found)}",
        f"Written reads: {len(manifest_rows)}",
        f"Missing IDs: {len(missing)}",
        f"Duplicated source IDs: {len(duplicates)}",
        f"Unexpected IDs: {len(unexpected)}",
        "",
        "Missing:",
    ]

    validation_lines.extend(
        f"  {read_id}" for read_id in missing
    )

    validation_lines.extend(
        [
            "",
            "Duplicates:",
        ]
    )

    validation_lines.extend(
        f"  {read_id}: {found_counts[read_id]}"
        for read_id in duplicates
    )

    validation_lines.extend(
        [
            "",
            "Extracted reads:",
        ]
    )

    validation_lines.extend(
        f"  {row['read_id']} <- {row['source_pod5']}"
        for row in manifest_rows
    )

    validation_path.write_text(
        "\n".join(validation_lines) + "\n",
        encoding="utf-8",
    )

    print()
    print("Extraction result")
    print("-----------------")
    print(f"Requested IDs: {len(wanted)}")
    print(f"Found unique IDs: {len(found)}")
    print(f"Written reads: {len(manifest_rows)}")
    print(f"Missing IDs: {len(missing)}")
    print(f"Duplicate source IDs: {len(duplicates)}")
    print(f"Output POD5: {output_path}")

    if missing or duplicates or unexpected:
        print("Extraction validation: FAIL")
        return 1

    if len(manifest_rows) != len(wanted):
        print("Extraction validation: FAIL")
        return 1

    print("Extraction validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
