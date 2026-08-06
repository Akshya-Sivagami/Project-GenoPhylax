#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

source \
    experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate/ONT_target_retrieval"
MAPPING_DIR="$RESULTS_DIR/POD5_mapping/remote_lookup"
MARKER_DIR="$A3_DIR/markers"

mkdir -p "$MAPPING_DIR" "$MARKER_DIR"

ALT_IDS="$RESULTS_DIR/POD5_mapping/F11_ALT_parent_read_ids.txt"

SUMMARY_URL="https://ont-open-data.s3.amazonaws.com/giab_2023.05/flowcells/hg002/20230424_1302_3H_PAO89685_2264ba8c/sequencing_summary_PAO89685_2264ba8c_afee3a87.txt"

POD5_ROOT_URL="https://ont-open-data.s3.amazonaws.com/giab_2023.05/flowcells/hg002/20230424_1302_3H_PAO89685_2264ba8c/pod5_pass"

RAW_MATCHES="$MAPPING_DIR/F11_remote_summary_raw_matches.tsv"
NORMALIZED_MAPPING="$MAPPING_DIR/F11_remote_read_to_POD5_mapping.tsv"
UNRESOLVED_IDS="$MAPPING_DIR/F11_remote_unresolved_ALT_read_ids.txt"
POD5_MANIFEST="$MAPPING_DIR/F11_required_POD5_manifest.tsv"
SIZE_RESULTS="$MAPPING_DIR/F11_required_POD5_remote_sizes.tsv"
LOOKUP_SUMMARY="$MAPPING_DIR/F11_remote_POD5_lookup_summary.txt"
HEADER_FILE="$MAPPING_DIR/PAO89685_sequencing_summary_header.txt"
HTTP_AUDIT="$MAPPING_DIR/PAO89685_sequencing_summary_HTTP_audit.txt"

COMPLETE_MARKER="$MARKER_DIR/A3_F11_REMOTE_POD5_LOOKUP.COMPLETE"
FAILED_MARKER="$MARKER_DIR/A3_F11_REMOTE_POD5_LOOKUP.FAILED"

rm -f "$FAILED_MARKER"

trap 'status=$?;
      echo;
      echo "ERROR: Remote POD5 lookup failed with status ${status}";
      {
          echo "Failed: $(date -Is)"
          echo "Exit status: ${status}"
      } > "$FAILED_MARKER";
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — REMOTE SEQUENCING-SUMMARY LOOKUP"
echo "============================================================"
echo "Started: $(date -Is)"
echo
echo "Summary URL:"
echo "$SUMMARY_URL"
echo

echo "[1/8] Checking tools and ALT UUID input"

for tool in python curl awk sort stat; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "ERROR: Missing required tool: $tool"
        exit 1
    fi
done

if [[ ! -s "$ALT_IDS" ]]; then
    echo "ERROR: ALT UUID file is missing or empty:"
    echo "$ALT_IDS"
    exit 1
fi

ALT_COUNT="$(
    awk 'NF {n++} END {print n+0}' "$ALT_IDS"
)"

echo "ALT UUID count: $ALT_COUNT"

if [[ "$ALT_COUNT" -ne 17 ]]; then
    echo "WARNING: Expected 17 ALT UUIDs but found $ALT_COUNT."
fi

echo
echo "[2/8] Validating remote sequencing-summary access"

curl \
    -L \
    -sS \
    -I \
    --retry 5 \
    --retry-delay 10 \
    --connect-timeout 30 \
    --max-time 120 \
    "$SUMMARY_URL" \
    > "$HTTP_AUDIT"

cat "$HTTP_AUDIT"

HTTP_STATUS="$(
    awk '/^HTTP\// {status=$2} END {print status}' "$HTTP_AUDIT"
)"

CONTENT_LENGTH="$(
    awk '
        BEGIN {IGNORECASE=1}
        /^content-length:/ {
            gsub("\r", "", $2)
            content_bytes=$2
        }
        END {print content_bytes}
    ' "$HTTP_AUDIT"
)"

if [[ "$HTTP_STATUS" != "200" ]]; then
    echo "ERROR: Sequencing summary returned HTTP $HTTP_STATUS"
    exit 1
fi

echo
echo "Remote content length: ${CONTENT_LENGTH:-UNKNOWN} bytes"

echo
echo "[3/8] Reading and validating the TSV header"

HEADER_CHUNK="$MAPPING_DIR/PAO89685_sequencing_summary_header_chunk.bin"

curl \
    -L \
    -sS \
    --retry 5 \
    --retry-delay 10 \
    --retry-all-errors \
    --connect-timeout 30 \
    --max-time 120 \
    --range 0-65535 \
    -o "$HEADER_CHUNK" \
    "$SUMMARY_URL"

head -1 "$HEADER_CHUNK" > "$HEADER_FILE"

rm -f "$HEADER_CHUNK"

cat "$HEADER_FILE"

export HEADER_FILE

python <<'PY_EOF'
import os
from pathlib import Path

header_path = Path(os.environ["HEADER_FILE"])
header = header_path.read_text(errors="replace").strip().split("\t")

required = {"read_id"}
filename_options = {"filename_pod5", "input_filename", "filename_fast5"}

missing = required - set(header)

if missing:
    raise SystemExit(
        f"Required sequencing-summary columns missing: {sorted(missing)}"
    )

if not filename_options.intersection(header):
    raise SystemExit(
        "No POD5/input filename column was found in the sequencing summary."
    )

print(f"Header columns: {len(header)}")
print("Header validation: PASS")
print(
    "Available identifier columns:",
    [name for name in ("read_id", "parent_read_id") if name in header],
)
print(
    "Available source-file columns:",
    [name for name in filename_options if name in header],
)
PY_EOF

echo
echo "[4/8] Streaming sequencing summary and matching ALT UUIDs"
echo "This reads the remote summary once without saving the 3.6-GB file."

export ALT_IDS
export RAW_MATCHES

set +o pipefail

curl \
    -L \
    -sS \
    --retry 10 \
    --retry-delay 15 \
    --retry-all-errors \
    --connect-timeout 30 \
    "$SUMMARY_URL" \
    | python -c '
import csv
import os
import sys
from pathlib import Path

target_path = Path(os.environ["ALT_IDS"])
output_path = Path(os.environ["RAW_MATCHES"])

targets = {
    line.strip()
    for line in target_path.read_text().splitlines()
    if line.strip()
}

reader = csv.DictReader(sys.stdin, delimiter="\t")

if reader.fieldnames is None:
    raise SystemExit("Sequencing summary has no header.")

filename_column = None

for candidate in ("filename_pod5", "input_filename", "filename_fast5"):
    if candidate in reader.fieldnames:
        filename_column = candidate
        break

if filename_column is None:
    raise SystemExit("No source filename column found.")

has_parent = "parent_read_id" in reader.fieldnames

fields = [
    "target_uuid",
    "matched_via",
    "summary_read_id",
    "summary_parent_read_id",
    "source_filename_column",
    "source_filename",
    "channel",
    "start_time",
    "sequence_length_template",
    "passes_filtering",
]

found_rows = []
found_targets = set()
row_number = 1

for row in reader:
    row_number += 1

    read_id = (row.get("read_id") or "").strip()
    parent_id = (row.get("parent_read_id") or "").strip() if has_parent else ""

    matches = []

    if read_id in targets:
        matches.append((read_id, "read_id"))

    if parent_id in targets and parent_id != read_id:
        matches.append((parent_id, "parent_read_id"))

    for target_uuid, matched_via in matches:
        found_targets.add(target_uuid)

        found_rows.append(
            {
                "target_uuid": target_uuid,
                "matched_via": matched_via,
                "summary_read_id": read_id,
                "summary_parent_read_id": parent_id,
                "source_filename_column": filename_column,
                "source_filename": (row.get(filename_column) or "").strip(),
                "channel": (row.get("channel") or "").strip(),
                "start_time": (row.get("start_time") or "").strip(),
                "sequence_length_template": (
                    row.get("sequence_length_template") or ""
                ).strip(),
                "passes_filtering": (
                    row.get("passes_filtering") or ""
                ).strip(),
            }
        )

with output_path.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
    writer.writeheader()
    writer.writerows(found_rows)

print(f"Sequencing-summary rows scanned: {row_number - 1}")
print(f"Target ALT UUIDs: {len(targets)}")
print(f"Matched target UUIDs: {len(found_targets)}")
print(f"Matching summary rows: {len(found_rows)}")
'

PIPE_STATUS=("${PIPESTATUS[@]}")
set -o pipefail

CURL_STATUS="${PIPE_STATUS[0]}"
PYTHON_STATUS="${PIPE_STATUS[1]}"

echo "curl status: $CURL_STATUS"
echo "parser status: $PYTHON_STATUS"

if [[ "$PYTHON_STATUS" -ne 0 ]]; then
    echo "ERROR: Sequencing-summary parser failed."
    exit "$PYTHON_STATUS"
fi

if [[ "$CURL_STATUS" -ne 0 ]]; then
    echo "ERROR: Remote stream failed or was incomplete."
    exit "$CURL_STATUS"
fi

echo
echo "Raw mapping output:"
column -t -s $'\t' "$RAW_MATCHES" 2>/dev/null ||
    cat "$RAW_MATCHES"

echo
echo "[5/8] Normalizing POD5 mappings and unresolved UUIDs"

export POD5_ROOT_URL
export NORMALIZED_MAPPING
export UNRESOLVED_IDS
export POD5_MANIFEST

python <<'PY_EOF'
import csv
import os
from collections import defaultdict
from pathlib import Path

alt_ids_path = Path(os.environ["ALT_IDS"])
raw_path = Path(os.environ["RAW_MATCHES"])
mapping_path = Path(os.environ["NORMALIZED_MAPPING"])
unresolved_path = Path(os.environ["UNRESOLVED_IDS"])
manifest_path = Path(os.environ["POD5_MANIFEST"])
pod5_root = os.environ["POD5_ROOT_URL"].rstrip("/")

alt_ids = {
    line.strip()
    for line in alt_ids_path.read_text().splitlines()
    if line.strip()
}

matches = defaultdict(list)

with raw_path.open(newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")

    for row in reader:
        target_uuid = row["target_uuid"].strip()
        source_filename = Path(row["source_filename"].strip()).name

        if not target_uuid or not source_filename:
            continue

        # The source column should normally already contain a .pod5 name.
        if not source_filename.endswith(".pod5"):
            continue

        matches[target_uuid].append(
            {
                "matched_via": row["matched_via"],
                "summary_read_id": row["summary_read_id"],
                "summary_parent_read_id": row["summary_parent_read_id"],
                "pod5_name": source_filename,
                "pod5_url": f"{pod5_root}/{source_filename}",
            }
        )

mapping_fields = [
    "target_uuid",
    "mapping_status",
    "matched_via",
    "summary_read_id",
    "summary_parent_read_id",
    "pod5_name",
    "pod5_url",
]

mapping_rows = []

for target_uuid in sorted(alt_ids):
    unique = {}

    for item in matches.get(target_uuid, []):
        key = (
            item["summary_read_id"],
            item["pod5_name"],
        )
        unique[key] = item

    items = list(unique.values())

    if not items:
        mapping_rows.append(
            {
                "target_uuid": target_uuid,
                "mapping_status": "UNRESOLVED",
                "matched_via": "",
                "summary_read_id": "",
                "summary_parent_read_id": "",
                "pod5_name": "",
                "pod5_url": "",
            }
        )
    else:
        pod5_names = {item["pod5_name"] for item in items}
        status = "UNIQUE_POD5" if len(pod5_names) == 1 else "MULTIPLE_POD5"

        for item in items:
            mapping_rows.append(
                {
                    "target_uuid": target_uuid,
                    "mapping_status": status,
                    **item,
                }
            )

with mapping_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=mapping_fields,
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(mapping_rows)

resolved_ids = {
    row["target_uuid"]
    for row in mapping_rows
    if row["pod5_name"]
}

unresolved_ids = sorted(alt_ids - resolved_ids)

unresolved_path.write_text(
    "".join(f"{read_id}\n" for read_id in unresolved_ids)
)

pod5_reads = defaultdict(set)
pod5_urls = {}

for row in mapping_rows:
    pod5_name = row["pod5_name"]

    if not pod5_name:
        continue

    pod5_reads[pod5_name].add(row["target_uuid"])
    pod5_urls[pod5_name] = row["pod5_url"]

manifest_fields = [
    "pod5_name",
    "pod5_url",
    "ALT_parent_count",
    "ALT_parent_UUIDs",
]

with manifest_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=manifest_fields,
        delimiter="\t",
    )
    writer.writeheader()

    for pod5_name in sorted(pod5_reads):
        read_ids = sorted(pod5_reads[pod5_name])

        writer.writerow(
            {
                "pod5_name": pod5_name,
                "pod5_url": pod5_urls[pod5_name],
                "ALT_parent_count": len(read_ids),
                "ALT_parent_UUIDs": ",".join(read_ids),
            }
        )

print(f"ALT parent UUIDs: {len(alt_ids)}")
print(f"Resolved ALT UUIDs: {len(resolved_ids)}")
print(f"Unresolved ALT UUIDs: {len(unresolved_ids)}")
print(f"Unique required POD5 shards: {len(pod5_reads)}")
PY_EOF

echo
echo "[6/8] Checking POD5 URLs and sizes without downloading"

{
    printf \
        'pod5_name\tpod5_url\tALT_parent_count\tremote_size_bytes\tremote_size_gib\thttp_status\n'

    tail -n +2 "$POD5_MANIFEST" |
    while IFS=$'\t' read -r pod5_name pod5_url alt_count alt_ids; do
        [[ -n "$pod5_name" ]] || continue

        HEADERS="$(
            curl \
                -L \
                -sS \
                -I \
                --retry 5 \
                --retry-delay 10 \
                --connect-timeout 30 \
                --max-time 120 \
                "$pod5_url" || true
        )"

        STATUS="$(
            printf '%s\n' "$HEADERS" \
                | awk '/^HTTP\// {status=$2} END {print status}'
        )"

        SIZE="$(
            printf '%s\n' "$HEADERS" \
                | awk '
                    BEGIN {IGNORECASE=1}
                    /^content-length:/ {
                        gsub("\r", "", $2)
                        size=$2
                    }
                    END {print size}
                '
        )"

        if [[ "$SIZE" =~ ^[0-9]+$ ]]; then
            GIB="$(
                awk -v bytes="$SIZE" \
                    'BEGIN {printf "%.4f", bytes/1024/1024/1024}'
            )"
        else
            SIZE=""
            GIB=""
        fi

        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$pod5_name" \
            "$pod5_url" \
            "$alt_count" \
            "$SIZE" \
            "$GIB" \
            "$STATUS"
    done
} > "$SIZE_RESULTS"

column -t -s $'\t' "$SIZE_RESULTS" 2>/dev/null ||
    cat "$SIZE_RESULTS"

echo
echo "[7/8] Creating final lookup summary"

TOTAL_ALT="$(
    awk 'NF {n++} END {print n+0}' "$ALT_IDS"
)"

RESOLVED_ALT="$(
    awk -F '\t' '
        NR > 1 && $6 != "" {
            seen[$1]=1
        }
        END {
            for (id in seen) n++
            print n+0
        }
    ' "$NORMALIZED_MAPPING"
)"

UNRESOLVED_ALT="$(
    awk 'NF {n++} END {print n+0}' "$UNRESOLVED_IDS"
)"

POD5_COUNT="$(
    awk -F '\t' 'NR > 1 && $1 != "" {n++} END {print n+0}' \
        "$POD5_MANIFEST"
)"

VALID_POD5_COUNT="$(
    awk -F '\t' 'NR > 1 && $6 == "200" {n++} END {print n+0}' \
        "$SIZE_RESULTS"
)"

TOTAL_BYTES="$(
    awk -F '\t' '
        NR > 1 && $4 ~ /^[0-9]+$/ {
            total += $4
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
    echo "A3 F11 Remote POD5 Lookup Summary"
    echo "=================================="
    echo
    echo "Completed: $(date -Is)"
    echo
    echo "Target:"
    echo "chr4:186274193 G>T"
    echo
    echo "Remote sequencing summary:"
    echo "$SUMMARY_URL"
    echo
    echo "ALT parent UUIDs: $TOTAL_ALT"
    echo "Resolved ALT UUIDs: $RESOLVED_ALT"
    echo "Unresolved ALT UUIDs: $UNRESOLVED_ALT"
    echo "Required POD5 shards: $POD5_COUNT"
    echo "POD5 URLs returning HTTP 200: $VALID_POD5_COUNT"
    echo
    echo "Estimated download:"
    echo "Total known bytes: $TOTAL_BYTES"
    echo "Total known GiB: $TOTAL_GIB"
    echo

    if [[ "$RESOLVED_ALT" -eq "$TOTAL_ALT" ]] &&
       [[ "$UNRESOLVED_ALT" -eq 0 ]] &&
       [[ "$VALID_POD5_COUNT" -eq "$POD5_COUNT" ]]; then

        echo "Overall status: ALL_ALT_READS_RESOLVED"
        echo
        echo "All F11 ALT parent reads were mapped to reachable POD5 shards."
        echo "The selective POD5 download may proceed."

    elif [[ "$RESOLVED_ALT" -gt 0 ]]; then
        echo "Overall status: PARTIAL_ALT_RESOLUTION"
        echo
        echo "Some ALT reads were resolved, but unresolved UUIDs or invalid"
        echo "POD5 URLs require inspection before downloading."

    else
        echo "Overall status: NO_ALT_READS_RESOLVED"
        echo
        echo "The sequencing-summary schema or read identifiers require"
        echo "additional investigation."
    fi

    echo
    echo "Generated files:"
    echo "$RAW_MATCHES"
    echo "$NORMALIZED_MAPPING"
    echo "$UNRESOLVED_IDS"
    echo "$POD5_MANIFEST"
    echo "$SIZE_RESULTS"
} > "$LOOKUP_SUMMARY"

cat "$LOOKUP_SUMMARY"

echo
echo "[8/8] Validating outputs and creating marker"

for file in \
    "$HTTP_AUDIT" \
    "$HEADER_FILE" \
    "$RAW_MATCHES" \
    "$NORMALIZED_MAPPING" \
    "$UNRESOLVED_IDS" \
    "$POD5_MANIFEST" \
    "$SIZE_RESULTS" \
    "$LOOKUP_SUMMARY"; do

    if [[ ! -e "$file" ]]; then
        echo "ERROR: Expected output missing:"
        echo "$file"
        exit 1
    fi
done

{
    echo "Completed: $(date -Is)"
    echo "Target: chr4:186274193 G>T"
    echo "ALT UUIDs: $TOTAL_ALT"
    echo "Resolved ALT UUIDs: $RESOLVED_ALT"
    echo "Unresolved ALT UUIDs: $UNRESOLVED_ALT"
    echo "Required POD5 shards: $POD5_COUNT"
    echo "Estimated download GiB: $TOTAL_GIB"
    echo "Summary: $LOOKUP_SUMMARY"
} > "$COMPLETE_MARKER"

rm -f "$FAILED_MARKER"

echo
echo "============================================================"
echo "A3 F11 REMOTE POD5 LOOKUP COMPLETE"
echo "============================================================"
