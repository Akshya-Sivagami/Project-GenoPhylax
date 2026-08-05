#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

VENV="experiments/A2_adversarial_dna/basecalling/environment/pod5_env"
source "$VENV/bin/activate"

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate/ONT_target_retrieval"
MAPPING_DIR="$RESULTS_DIR/POD5_mapping"
LOG_DIR="$A3_DIR/logs"
MARKER_DIR="$A3_DIR/markers"

mkdir -p "$MAPPING_DIR" "$LOG_DIR" "$MARKER_DIR"

COMPLETE_MARKER="$MARKER_DIR/A3_F11_READ_TO_POD5_MAPPING.COMPLETE"
FAILED_MARKER="$MARKER_DIR/A3_F11_READ_TO_POD5_MAPPING.FAILED"

PER_PARENT_TSV="$RESULTS_DIR/F11_target_per_parent_states.tsv"

ALT_READ_IDS="$MAPPING_DIR/F11_ALT_parent_read_ids.txt"
REF_READ_IDS="$MAPPING_DIR/F11_REF_parent_read_ids.txt"
ALL_READ_IDS="$MAPPING_DIR/F11_all_target_parent_read_ids.txt"

DISCOVERED_FILES="$MAPPING_DIR/F11_candidate_mapping_files.txt"
FILE_SCHEMAS="$MAPPING_DIR/F11_candidate_mapping_file_schemas.txt"
RAW_MATCHES="$MAPPING_DIR/F11_raw_manifest_matches.tsv"

NORMALIZED_MAPPING="$MAPPING_DIR/F11_read_to_pod5_mapping.tsv"
ALT_MAPPING="$MAPPING_DIR/F11_ALT_read_to_pod5_mapping.tsv"
UNMAPPED_ALT_IDS="$MAPPING_DIR/F11_unmapped_ALT_read_ids.txt"

POD5_MANIFEST="$MAPPING_DIR/F11_required_POD5_manifest.tsv"
SUMMARY_FILE="$MAPPING_DIR/F11_read_to_POD5_mapping_summary.txt"

POD5_ROOT_URL="https://ont-open-data.s3.amazonaws.com/giab_2023.05/flowcells/hg002/20230424_1302_3H_PAO89685_2264ba8c/pod5_pass"

rm -f "$FAILED_MARKER"

trap 'status=$?;
      echo;
      echo "ERROR: F11 read-to-POD5 mapping failed with status ${status}";
      date -Is > "$FAILED_MARKER";
      echo "Exit status: ${status}" >> "$FAILED_MARKER";
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — READ-TO-POD5 MAPPING"
echo "============================================================"
echo "Started: $(date -Is)"
echo
echo "Python: $(command -v python)"
echo "Input:  $PER_PARENT_TSV"
echo

echo "[1/9] Validating required input"

if [[ ! -s "$PER_PARENT_TSV" ]]; then
    echo "ERROR: Per-parent F11 target-state table is missing or empty:"
    echo "$PER_PARENT_TSV"
    exit 1
fi

echo "Input rows:"
awk 'END {print NR-1}' "$PER_PARENT_TSV"

echo
echo "[2/9] Exporting ALT, REF and all target parent read IDs"

awk -F '\t' '
    NR > 1 && $3 == "ALT" {
        print $1
    }
' "$PER_PARENT_TSV" \
    | sort -u \
    > "$ALT_READ_IDS"

awk -F '\t' '
    NR > 1 && $3 == "REF" {
        print $1
    }
' "$PER_PARENT_TSV" \
    | sort -u \
    > "$REF_READ_IDS"

awk -F '\t' '
    NR > 1 && $1 != "" {
        print $1
    }
' "$PER_PARENT_TSV" \
    | sort -u \
    > "$ALL_READ_IDS"

ALT_COUNT="$(awk 'NF {n++} END {print n+0}' "$ALT_READ_IDS")"
REF_COUNT="$(awk 'NF {n++} END {print n+0}' "$REF_READ_IDS")"
ALL_COUNT="$(awk 'NF {n++} END {print n+0}' "$ALL_READ_IDS")"

echo "ALT parents: $ALT_COUNT"
echo "REF parents: $REF_COUNT"
echo "All parents: $ALL_COUNT"

if [[ "$ALT_COUNT" -eq 0 ]]; then
    echo "ERROR: No ALT parent read IDs were found."
    exit 1
fi

echo
echo "[3/9] Discovering reusable A2 scripts and manifests"

{
    find experiments/A2_adversarial_dna \
        -type f \
        \( \
            -iname '*.tsv' \
            -o -iname '*.csv' \
            -o -iname '*.txt' \
            -o -iname '*.manifest' \
            -o -iname '*.sh' \
            -o -iname '*.py' \
        \) \
        2>/dev/null \
        | grep -Ei \
            'pod5|sequenc|summary|manifest|read.mapping|read_to|download|shard' \
        | sort -u
} > "$DISCOVERED_FILES"

echo "Candidate files discovered:"
wc -l "$DISCOVERED_FILES"
echo
head -50 "$DISCOVERED_FILES"

echo
echo "[4/9] Recording candidate file schemas"

{
    while IFS= read -r file; do
        [[ -f "$file" ]] || continue

        printf '\n============================================================\n'
        printf 'FILE: %s\n' "$file"
        printf 'SIZE_BYTES: %s\n' "$(stat -c '%s' "$file" 2>/dev/null || echo UNKNOWN)"
        printf '%s\n' 'FIRST_NONEMPTY_LINES:'

        awk 'NF {print; n++} n == 4 {exit}' "$file" 2>/dev/null || true
    done < "$DISCOVERED_FILES"
} > "$FILE_SCHEMAS"

echo "Schema audit written to:"
echo "$FILE_SCHEMAS"

echo
echo "[5/9] Searching discovered manifests for all F11 read IDs"

export ALL_READ_IDS
export DISCOVERED_FILES
export RAW_MATCHES

python <<'PY_EOF'
import csv
import gzip
import os
import re
from pathlib import Path

read_ids_path = Path(os.environ["ALL_READ_IDS"])
candidate_files_path = Path(os.environ["DISCOVERED_FILES"])
output_path = Path(os.environ["RAW_MATCHES"])

read_ids = {
    line.strip()
    for line in read_ids_path.read_text(errors="replace").splitlines()
    if line.strip()
}

candidate_files = [
    Path(line.strip())
    for line in candidate_files_path.read_text(errors="replace").splitlines()
    if line.strip()
]

pod5_pattern = re.compile(
    r"""(?ix)
    (
        (?:https?://|s3://)?[^\t ,"']*
        [A-Za-z0-9._/-]+
        \.pod5
    )
    """
)

rows = []

def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", errors="replace")
    return path.open("r", errors="replace")

for path in candidate_files:
    if not path.is_file():
        continue

    try:
        size = path.stat().st_size
    except OSError:
        continue

    # Avoid scanning enormous binary/data files accidentally.
    if size > 2_000_000_000:
        continue

    try:
        with open_text(path) as handle:
            for line_number, line in enumerate(handle, start=1):
                matching_ids = [read_id for read_id in read_ids if read_id in line]

                if not matching_ids:
                    continue

                pod5_values = sorted(set(pod5_pattern.findall(line)))

                for read_id in matching_ids:
                    rows.append(
                        {
                            "read_id": read_id,
                            "source_file": str(path),
                            "line_number": line_number,
                            "pod5_candidates": ";".join(pod5_values),
                            "matched_line": line.rstrip("\n")[:10000],
                        }
                    )
    except (OSError, UnicodeError):
        continue

with output_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "read_id",
            "source_file",
            "line_number",
            "pod5_candidates",
            "matched_line",
        ],
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Target read IDs: {len(read_ids)}")
print(f"Candidate files scanned: {len(candidate_files)}")
print(f"Raw matching rows: {len(rows)}")
print(f"Unique matched reads: {len({row['read_id'] for row in rows})}")
PY_EOF

echo
echo "[6/9] Normalizing read-to-POD5 mappings"

export PER_PARENT_TSV
export RAW_MATCHES
export NORMALIZED_MAPPING
export ALT_MAPPING
export UNMAPPED_ALT_IDS
export POD5_MANIFEST
export POD5_ROOT_URL

python <<'PY_EOF'
import csv
import os
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

parent_path = Path(os.environ["PER_PARENT_TSV"])
raw_path = Path(os.environ["RAW_MATCHES"])
normalized_path = Path(os.environ["NORMALIZED_MAPPING"])
alt_mapping_path = Path(os.environ["ALT_MAPPING"])
unmapped_alt_path = Path(os.environ["UNMAPPED_ALT_IDS"])
pod5_manifest_path = Path(os.environ["POD5_MANIFEST"])
pod5_root_url = os.environ["POD5_ROOT_URL"].rstrip("/")

parent_state = {}

with parent_path.open(newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    for row in reader:
        read_id = row.get("read_id", "").strip()
        state = row.get("parent_state", "").strip()

        if read_id:
            parent_state[read_id] = state

pod5_regex = re.compile(
    r"""(?ix)
    (
        (?:
            https?://[^\s\t,"']+
            |
            s3://[^\s\t,"']+
            |
            [A-Za-z0-9._/-]*[A-Za-z0-9._-]+\.pod5
        )
    )
    """
)

matches = defaultdict(list)

if raw_path.exists():
    with raw_path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        for row in reader:
            read_id = row.get("read_id", "").strip()

            if not read_id:
                continue

            text = "\t".join(
                [
                    row.get("pod5_candidates", ""),
                    row.get("matched_line", ""),
                ]
            )

            candidates = pod5_regex.findall(text)

            for candidate in candidates:
                candidate = candidate.strip(";,\"' ")

                if not candidate.endswith(".pod5"):
                    continue

                pod5_name = Path(urlparse(candidate).path).name

                if candidate.startswith("http://") or candidate.startswith("https://"):
                    pod5_url = candidate
                elif candidate.startswith("s3://"):
                    s3_without_scheme = candidate[len("s3://"):]
                    bucket_and_key = s3_without_scheme.split("/", 1)

                    if len(bucket_and_key) == 2:
                        bucket, key = bucket_and_key
                        pod5_url = f"https://{bucket}.s3.amazonaws.com/{key}"
                    else:
                        pod5_url = ""
                else:
                    pod5_url = f"{pod5_root_url}/{pod5_name}"

                matches[read_id].append(
                    {
                        "pod5_name": pod5_name,
                        "pod5_url": pod5_url,
                        "source_file": row.get("source_file", ""),
                        "source_line": row.get("line_number", ""),
                    }
                )

normalized_rows = []

for read_id in sorted(parent_state):
    unique = {}

    for item in matches.get(read_id, []):
        key = (item["pod5_name"], item["pod5_url"])

        if key not in unique:
            unique[key] = item

    items = list(unique.values())

    if not items:
        normalized_rows.append(
            {
                "read_id": read_id,
                "parent_state": parent_state[read_id],
                "mapping_status": "UNMAPPED",
                "pod5_name": "",
                "pod5_url": "",
                "source_file": "",
                "source_line": "",
            }
        )
    else:
        status = "UNIQUE" if len(items) == 1 else "MULTIPLE"

        for item in items:
            normalized_rows.append(
                {
                    "read_id": read_id,
                    "parent_state": parent_state[read_id],
                    "mapping_status": status,
                    "pod5_name": item["pod5_name"],
                    "pod5_url": item["pod5_url"],
                    "source_file": item["source_file"],
                    "source_line": item["source_line"],
                }
            )

fields = [
    "read_id",
    "parent_state",
    "mapping_status",
    "pod5_name",
    "pod5_url",
    "source_file",
    "source_line",
]

with normalized_path.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
    writer.writeheader()
    writer.writerows(normalized_rows)

alt_rows = [
    row for row in normalized_rows
    if row["parent_state"] == "ALT"
]

with alt_mapping_path.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
    writer.writeheader()
    writer.writerows(alt_rows)

mapped_alt_ids = {
    row["read_id"]
    for row in alt_rows
    if row["mapping_status"] in {"UNIQUE", "MULTIPLE"}
    and row["pod5_name"]
}

all_alt_ids = {
    read_id
    for read_id, state in parent_state.items()
    if state == "ALT"
}

unmapped_alt_ids = sorted(all_alt_ids - mapped_alt_ids)

unmapped_alt_path.write_text(
    "".join(f"{read_id}\n" for read_id in unmapped_alt_ids)
)

pod5_to_reads = defaultdict(set)
pod5_to_url = {}

for row in alt_rows:
    pod5_name = row["pod5_name"]
    pod5_url = row["pod5_url"]

    if not pod5_name:
        continue

    pod5_to_reads[pod5_name].add(row["read_id"])

    if pod5_url:
        pod5_to_url[pod5_name] = pod5_url

with pod5_manifest_path.open("w", newline="") as handle:
    fields = [
        "pod5_name",
        "pod5_url",
        "ALT_read_count",
        "ALT_read_ids",
    ]

    writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
    writer.writeheader()

    for pod5_name in sorted(pod5_to_reads):
        read_ids = sorted(pod5_to_reads[pod5_name])

        writer.writerow(
            {
                "pod5_name": pod5_name,
                "pod5_url": pod5_to_url.get(pod5_name, ""),
                "ALT_read_count": len(read_ids),
                "ALT_read_ids": ",".join(read_ids),
            }
        )

print(f"All parent reads: {len(parent_state)}")
print(f"ALT parent reads: {len(all_alt_ids)}")
print(f"Mapped ALT reads: {len(mapped_alt_ids)}")
print(f"Unmapped ALT reads: {len(unmapped_alt_ids)}")
print(f"Required POD5 shards: {len(pod5_to_reads)}")
PY_EOF

echo
echo "[7/9] Checking remote POD5 shard sizes without downloading"

SIZE_RESULTS="$MAPPING_DIR/F11_required_POD5_remote_sizes.tsv"
SIZE_LOG="$MAPPING_DIR/F11_required_POD5_remote_size_checks.log"

{
    printf 'pod5_name\tpod5_url\tremote_size_bytes\tremote_size_gib\thttp_status\n'

    tail -n +2 "$POD5_MANIFEST" |
    while IFS=$'\t' read -r pod5_name pod5_url alt_count alt_ids; do
        [[ -n "$pod5_name" ]] || continue
        [[ -n "$pod5_url" ]] || continue

        headers="$(
            curl \
                -L \
                -sS \
                -I \
                --connect-timeout 30 \
                --max-time 90 \
                "$pod5_url" \
                2>> "$SIZE_LOG" || true
        )"

        status="$(
            printf '%s\n' "$headers" \
                | awk '/^HTTP\// {code=$2} END {print code}'
        )"

        size="$(
            printf '%s\n' "$headers" \
                | awk '
                    BEGIN {IGNORECASE=1}
                    /^content-length:/ {
                        gsub("\r", "", $2)
                        size=$2
                    }
                    END {print size}
                '
        )"

        if [[ "$size" =~ ^[0-9]+$ ]]; then
            gib="$(
                awk -v bytes="$size" \
                    'BEGIN {printf "%.4f", bytes/1024/1024/1024}'
            )"
        else
            size=""
            gib=""
        fi

        printf '%s\t%s\t%s\t%s\t%s\n' \
            "$pod5_name" \
            "$pod5_url" \
            "$size" \
            "$gib" \
            "$status"
    done
} > "$SIZE_RESULTS"

echo "Remote-size check:"
column -t -s $'\t' "$SIZE_RESULTS" 2>/dev/null || cat "$SIZE_RESULTS"

echo
echo "[8/9] Creating mapping summary"

TOTAL_ALT="$(awk 'NF {n++} END {print n+0}' "$ALT_READ_IDS")"

MAPPED_ALT="$(
    awk -F '\t' '
        NR > 1 &&
        $2 == "ALT" &&
        ($3 == "UNIQUE" || $3 == "MULTIPLE") &&
        $4 != "" {
            ids[$1]=1
        }
        END {
            for (id in ids) n++
            print n+0
        }
    ' "$NORMALIZED_MAPPING"
)"

UNMAPPED_ALT="$(
    awk 'NF {n++} END {print n+0}' "$UNMAPPED_ALT_IDS"
)"

UNIQUE_POD5="$(
    awk -F '\t' 'NR > 1 && $1 != "" {n++} END {print n+0}' \
        "$POD5_MANIFEST"
)"

TOTAL_BYTES="$(
    awk -F '\t' '
        NR > 1 && $3 ~ /^[0-9]+$/ {
            total += $3
        }
        END {
            printf "%.0f", total+0
        }
    ' "$SIZE_RESULTS"
)"

TOTAL_GIB="$(
    awk -v bytes="$TOTAL_BYTES" \
        'BEGIN {printf "%.4f", bytes/1024/1024/1024}'
)"

{
    echo "A3 F11 Read-to-POD5 Mapping Summary"
    echo "===================================="
    echo
    echo "Completed: $(date -Is)"
    echo
    echo "F11 target:"
    echo "chr4:186274193 G>T"
    echo
    echo "Target parents:"
    echo "All target parents: $ALL_COUNT"
    echo "ALT parents: $TOTAL_ALT"
    echo "REF parents: $REF_COUNT"
    echo
    echo "ALT POD5 mapping:"
    echo "Mapped ALT parents: $MAPPED_ALT"
    echo "Unmapped ALT parents: $UNMAPPED_ALT"
    echo "Required unique POD5 shards: $UNIQUE_POD5"
    echo
    echo "Remote download estimate:"
    echo "Known total bytes: $TOTAL_BYTES"
    echo "Known total GiB: $TOTAL_GIB"
    echo
    if [[ "$UNMAPPED_ALT" -eq 0 && "$MAPPED_ALT" -eq "$TOTAL_ALT" ]]; then
        echo "Overall status: ALL_ALT_READS_MAPPED"
        echo
        echo "All F11 ALT-supporting parents were mapped to source POD5 shards."
        echo "The POD5 download stage can proceed."
    elif [[ "$MAPPED_ALT" -gt 0 ]]; then
        echo "Overall status: PARTIAL_ALT_MAPPING"
        echo
        echo "Some F11 ALT-supporting parents were mapped, but additional"
        echo "sequencing-summary lookup is required before downloading."
    else
        echo "Overall status: NO_ALT_READS_MAPPED"
        echo
        echo "The currently available local manifests do not contain the F11"
        echo "read-to-POD5 mapping. A remote sequencing-summary lookup is required."
    fi
    echo
    echo "Generated files:"
    echo "$ALT_READ_IDS"
    echo "$REF_READ_IDS"
    echo "$DISCOVERED_FILES"
    echo "$FILE_SCHEMAS"
    echo "$RAW_MATCHES"
    echo "$NORMALIZED_MAPPING"
    echo "$ALT_MAPPING"
    echo "$UNMAPPED_ALT_IDS"
    echo "$POD5_MANIFEST"
    echo "$SIZE_RESULTS"
} > "$SUMMARY_FILE"

cat "$SUMMARY_FILE"

echo
echo "[9/9] Final validation and marker creation"

for required in \
    "$ALT_READ_IDS" \
    "$REF_READ_IDS" \
    "$ALL_READ_IDS" \
    "$DISCOVERED_FILES" \
    "$FILE_SCHEMAS" \
    "$RAW_MATCHES" \
    "$NORMALIZED_MAPPING" \
    "$ALT_MAPPING" \
    "$UNMAPPED_ALT_IDS" \
    "$POD5_MANIFEST" \
    "$SIZE_RESULTS" \
    "$SUMMARY_FILE"; do

    if [[ ! -e "$required" ]]; then
        echo "ERROR: Expected output was not created:"
        echo "$required"
        exit 1
    fi
done

{
    echo "Completed: $(date -Is)"
    echo "Target: chr4:186274193 G>T"
    echo "ALT parents: $TOTAL_ALT"
    echo "Mapped ALT parents: $MAPPED_ALT"
    echo "Unmapped ALT parents: $UNMAPPED_ALT"
    echo "Required POD5 shards: $UNIQUE_POD5"
    echo "Estimated download GiB: $TOTAL_GIB"
    echo "Summary: $SUMMARY_FILE"
} > "$COMPLETE_MARKER"

rm -f "$FAILED_MARKER"

echo
echo "============================================================"
echo "A3 F11 READ-TO-POD5 MAPPING COMPLETE"
echo "============================================================"
echo "Completed: $(date -Is)"
echo "Marker: $COMPLETE_MARKER"
echo "Summary: $SUMMARY_FILE"
