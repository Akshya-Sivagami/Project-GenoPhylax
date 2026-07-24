#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

source experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

EXP_E_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_targeted_locus"
LOCUS_DIR="$EXP_E_DIR/locus_selection"
MAP_DIR="$EXP_E_DIR/read_mapping"

S3_FLOWCELL="s3://ont-open-data/giab_2023.05/flowcells/hg002/20230424_1302_3H_PAO89685_2264ba8c"
REMOTE_SUMMARY="$S3_FLOWCELL/sequencing_summary_PAO89685_2264ba8c_afee3a87.txt"

ALL_IDS="$LOCUS_DIR/provisional_target_all_read_ids.txt"
REF_IDS="$LOCUS_DIR/provisional_target_ref_read_ids.txt"
ALT_IDS="$LOCUS_DIR/provisional_target_alt_read_ids.txt"

RAW_MATCHES="$MAP_DIR/target_reads_sequencing_summary_matches.tsv"
PARSED_OUTPUT="$MAP_DIR/target_read_to_pod5_mapping.tsv"
UNIQUE_POD5="$MAP_DIR/target_unique_pod5_files.txt"
ALT_POD5="$MAP_DIR/target_alt_unique_pod5_files.txt"
REF_POD5="$MAP_DIR/target_ref_unique_pod5_files.txt"
MISSING_IDS="$MAP_DIR/target_read_ids_missing_from_summary.txt"
SUMMARY_REPORT="$MAP_DIR/target_read_mapping_summary.txt"

mkdir -p "$MAP_DIR"

for required_file in "$ALL_IDS" "$REF_IDS" "$ALT_IDS"; do
    if [[ ! -s "$required_file" ]]; then
        echo "ERROR: Missing or empty file: $required_file"
        exit 1
    fi
done

echo "============================================================"
echo "EXPERIMENT E — STREAMING SEQUENCING SUMMARY"
echo "============================================================"
date

echo
echo "Requested target read IDs:"
wc -l "$ALL_IDS"

TMP_MATCHES="${RAW_MATCHES}.tmp"
rm -f "$TMP_MATCHES"

echo
echo "Streaming remote sequencing summary and matching target IDs..."

aws s3 cp \
  "$REMOTE_SUMMARY" \
  - \
  --no-sign-request \
  | awk \
      -F '\t' \
      -v ids_file="$ALL_IDS" \
      '
      BEGIN {
          while ((getline line < ids_file) > 0) {
              gsub(/\r/, "", line);
              if (line != "") {
                  wanted[line] = 1;
              }
          }
          close(ids_file);
      }

      NR == 1 {
          for (i = 1; i <= NF; i++) {
              header[$i] = i;
          }

          parent_col = header["parent_read_id"];
          read_col = header["read_id"];

          print $0;
          next;
      }

      {
          parent_id = (parent_col > 0 ? $parent_col : "");
          read_id = (read_col > 0 ? $read_col : "");

          if ((parent_id in wanted) || (read_id in wanted)) {
              print $0;
          }
      }
      ' \
  > "$TMP_MATCHES"

mv "$TMP_MATCHES" "$RAW_MATCHES"

echo
echo "Raw sequencing-summary matches:"
wc -l "$RAW_MATCHES"

python - \
  "$RAW_MATCHES" \
  "$ALL_IDS" \
  "$REF_IDS" \
  "$ALT_IDS" \
  "$PARSED_OUTPUT" \
  "$UNIQUE_POD5" \
  "$ALT_POD5" \
  "$REF_POD5" \
  "$MISSING_IDS" \
  "$SUMMARY_REPORT" <<'PY'
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

raw_matches = Path(sys.argv[1])
all_ids_path = Path(sys.argv[2])
ref_ids_path = Path(sys.argv[3])
alt_ids_path = Path(sys.argv[4])
parsed_output = Path(sys.argv[5])
unique_pod5_output = Path(sys.argv[6])
alt_pod5_output = Path(sys.argv[7])
ref_pod5_output = Path(sys.argv[8])
missing_output = Path(sys.argv[9])
summary_output = Path(sys.argv[10])


def read_ids(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


all_ids = read_ids(all_ids_path)
ref_ids = read_ids(ref_ids_path)
alt_ids = read_ids(alt_ids_path)

rows: list[dict[str, str]] = []

with raw_matches.open("rt", encoding="utf-8", errors="replace") as handle:
    reader = csv.DictReader(handle, delimiter="\t")

    required_columns = {
        "filename_pod5",
        "parent_read_id",
        "read_id",
        "passes_filtering",
        "sequence_length_template",
        "mean_qscore_template",
    }

    present_columns = set(reader.fieldnames or [])
    missing_columns = sorted(required_columns - present_columns)

    if missing_columns:
        raise SystemExit(
            "ERROR: Required sequencing-summary columns missing: "
            + ", ".join(missing_columns)
        )

    for record in reader:
        parent_id = record.get("parent_read_id", "")
        read_id = record.get("read_id", "")

        matched_targets = []

        if parent_id in all_ids:
            matched_targets.append((parent_id, "parent_read_id"))

        if read_id in all_ids and read_id != parent_id:
            matched_targets.append((read_id, "read_id"))
        elif read_id in all_ids and not matched_targets:
            matched_targets.append((read_id, "read_id"))

        for target_id, matched_column in matched_targets:
            allele = (
                "REF"
                if target_id in ref_ids
                else "ALT"
                if target_id in alt_ids
                else "UNKNOWN"
            )

            rows.append(
                {
                    "target_read_id": target_id,
                    "allele": allele,
                    "matched_column": matched_column,
                    "parent_read_id": parent_id,
                    "read_id": read_id,
                    "filename_pod5": record.get("filename_pod5", ""),
                    "filename_fastq": record.get("filename_fastq", ""),
                    "passes_filtering": record.get("passes_filtering", ""),
                    "channel": record.get("channel", ""),
                    "mux": record.get("mux", ""),
                    "start_time": record.get("start_time", ""),
                    "duration": record.get("duration", ""),
                    "sequence_length_template": record.get(
                        "sequence_length_template", ""
                    ),
                    "mean_qscore_template": record.get(
                        "mean_qscore_template", ""
                    ),
                    "end_reason": record.get("end_reason", ""),
                }
            )

fieldnames = [
    "target_read_id",
    "allele",
    "matched_column",
    "parent_read_id",
    "read_id",
    "filename_pod5",
    "filename_fastq",
    "passes_filtering",
    "channel",
    "mux",
    "start_time",
    "duration",
    "sequence_length_template",
    "mean_qscore_template",
    "end_reason",
]

with parsed_output.open("wt", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)

matched_ids = {row["target_read_id"] for row in rows}
missing_ids = sorted(all_ids - matched_ids)

missing_output.write_text(
    "\n".join(missing_ids) + ("\n" if missing_ids else ""),
    encoding="utf-8",
)

all_pod5 = sorted(
    {
        row["filename_pod5"]
        for row in rows
        if row["filename_pod5"]
    }
)

alt_pod5 = sorted(
    {
        row["filename_pod5"]
        for row in rows
        if row["allele"] == "ALT" and row["filename_pod5"]
    }
)

ref_pod5 = sorted(
    {
        row["filename_pod5"]
        for row in rows
        if row["allele"] == "REF" and row["filename_pod5"]
    }
)

unique_pod5_output.write_text(
    "\n".join(all_pod5) + ("\n" if all_pod5 else ""),
    encoding="utf-8",
)

alt_pod5_output.write_text(
    "\n".join(alt_pod5) + ("\n" if alt_pod5 else ""),
    encoding="utf-8",
)

ref_pod5_output.write_text(
    "\n".join(ref_pod5) + ("\n" if ref_pod5 else ""),
    encoding="utf-8",
)

rows_per_target = Counter(row["target_read_id"] for row in rows)
allele_counts = Counter(row["allele"] for row in rows)
match_column_counts = Counter(row["matched_column"] for row in rows)

pod5_to_targets: dict[str, set[str]] = defaultdict(set)

for row in rows:
    if row["filename_pod5"]:
        pod5_to_targets[row["filename_pod5"]].add(row["target_read_id"])

summary_lines = [
    "Experiment E target-read sequencing-summary mapping",
    "====================================================",
    f"Requested target IDs: {len(all_ids)}",
    f"Matched target IDs: {len(matched_ids)}",
    f"Missing target IDs: {len(missing_ids)}",
    f"Total matched metadata rows: {len(rows)}",
    f"Unique POD5 files: {len(all_pod5)}",
    f"ALT-associated POD5 files: {len(alt_pod5)}",
    f"REF-associated POD5 files: {len(ref_pod5)}",
    "",
    "Matched rows by allele:",
]

for allele, count in sorted(allele_counts.items()):
    summary_lines.append(f"  {allele}: {count}")

summary_lines.extend(
    [
        "",
        "Matched rows by sequencing-summary column:",
    ]
)

for column, count in sorted(match_column_counts.items()):
    summary_lines.append(f"  {column}: {count}")

summary_lines.extend(
    [
        "",
        "Rows per target ID:",
    ]
)

for target_id in sorted(all_ids):
    summary_lines.append(
        f"  {target_id}: {rows_per_target.get(target_id, 0)}"
    )

summary_lines.extend(
    [
        "",
        "POD5 files and target counts:",
    ]
)

for pod5_name in all_pod5:
    summary_lines.append(
        f"  {pod5_name}: {len(pod5_to_targets[pod5_name])} target IDs"
    )

if missing_ids:
    summary_lines.extend(
        [
            "",
            "Missing target IDs:",
        ]
    )
    summary_lines.extend(f"  {read_id}" for read_id in missing_ids)

summary_output.write_text(
    "\n".join(summary_lines) + "\n",
    encoding="utf-8",
)

print()
print("Mapping results")
print("---------------")
print(f"Requested target IDs: {len(all_ids)}")
print(f"Matched target IDs: {len(matched_ids)}")
print(f"Missing target IDs: {len(missing_ids)}")
print(f"Matched metadata rows: {len(rows)}")
print(f"Unique POD5 files: {len(all_pod5)}")
print(f"ALT-associated POD5 files: {len(alt_pod5)}")
print(f"REF-associated POD5 files: {len(ref_pod5)}")

print()
print("Target mappings:")

for row in rows:
    print(
        f"{row['allele']}\t"
        f"{row['target_read_id']}\t"
        f"{row['matched_column']}\t"
        f"{row['filename_pod5']}\t"
        f"pass={row['passes_filtering']}\t"
        f"length={row['sequence_length_template']}\t"
        f"q={row['mean_qscore_template']}"
    )
PY

echo
echo "============================================================"
echo "STREAMING SUMMARY MAPPING COMPLETE"
echo "============================================================"

cat "$SUMMARY_REPORT"

echo
echo "Generated files:"
find "$MAP_DIR" \
  -maxdepth 1 \
  -type f \
  -printf "%f\t%s bytes\n" \
  | sort

echo
date
