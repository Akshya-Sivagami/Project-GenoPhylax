#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

source \
    experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate/ONT_target_retrieval"
BASE_DIR="$RESULTS_DIR/POD5_mapping/resumable_remote_lookup"
PARTS_DIR="$BASE_DIR/summary_parts"
MARKER_DIR="$A3_DIR/markers"

mkdir -p "$BASE_DIR" "$PARTS_DIR" "$MARKER_DIR"

SUMMARY_URL="https://ont-open-data.s3.amazonaws.com/giab_2023.05/flowcells/hg002/20230424_1302_3H_PAO89685_2264ba8c/sequencing_summary_PAO89685_2264ba8c_afee3a87.txt"

POD5_ROOT_URL="https://ont-open-data.s3.amazonaws.com/giab_2023.05/flowcells/hg002/20230424_1302_3H_PAO89685_2264ba8c/pod5_pass"

TOTAL_BYTES=3602275623
NUM_PARTS=16
PARALLEL_JOBS=8

ALT_IDS="$RESULTS_DIR/POD5_mapping/F11_ALT_parent_read_ids.txt"

PART_MANIFEST="$BASE_DIR/sequencing_summary_part_manifest.tsv"
SUMMARY_FILE="$BASE_DIR/sequencing_summary_PAO89685.txt"

RAW_MATCHES="$BASE_DIR/F11_summary_raw_matches.tsv"
NORMALIZED_MAPPING="$BASE_DIR/F11_read_to_POD5_mapping.tsv"
UNRESOLVED_IDS="$BASE_DIR/F11_unresolved_ALT_read_ids.txt"
POD5_MANIFEST="$BASE_DIR/F11_required_POD5_manifest.tsv"
POD5_SIZES="$BASE_DIR/F11_required_POD5_remote_sizes.tsv"
FINAL_SUMMARY="$BASE_DIR/F11_resumable_metadata_lookup_summary.txt"

COMPLETE_MARKER="$MARKER_DIR/A3_F11_RESUMABLE_METADATA_LOOKUP.COMPLETE"
FAILED_MARKER="$MARKER_DIR/A3_F11_RESUMABLE_METADATA_LOOKUP.FAILED"

rm -f "$FAILED_MARKER"

trap 'status=$?;
      {
          echo "Failed: $(date -Is)"
          echo "Exit status: ${status}"
      } > "$FAILED_MARKER";
      echo "ERROR: Workflow failed with status ${status}";
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — RESUMABLE PARALLEL METADATA LOOKUP"
echo "============================================================"
echo "Started: $(date -Is)"
echo

echo "[1/10] Validating inputs and tools"

for tool in curl python awk sort xargs stat split cat; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "ERROR: Missing tool: $tool"
        exit 1
    }
done

if [[ ! -s "$ALT_IDS" ]]; then
    echo "ERROR: ALT UUID file missing:"
    echo "$ALT_IDS"
    exit 1
fi

ALT_COUNT="$(
    awk 'NF {n++} END {print n+0}' "$ALT_IDS"
)"

echo "ALT UUIDs: $ALT_COUNT"
echo "Remote summary bytes: $TOTAL_BYTES"
echo "Parts: $NUM_PARTS"
echo "Parallel downloads: $PARALLEL_JOBS"

echo
echo "[2/10] Creating deterministic range manifest"

python - <<'PY_EOF'
from pathlib import Path

total = 3_602_275_623
parts = 16

base = Path(
    "experiments/A3_clinical_consequence_mapping/"
    "results/F11_candidate/ONT_target_retrieval/"
    "POD5_mapping/resumable_remote_lookup"
)

parts_dir = base / "summary_parts"
manifest = base / "sequencing_summary_part_manifest.tsv"

parts_dir.mkdir(parents=True, exist_ok=True)

chunk = (total + parts - 1) // parts

with manifest.open("w") as handle:
    handle.write(
        "part_number\tstart_byte\tend_byte\texpected_bytes\tpart_path\n"
    )

    for index in range(parts):
        start = index * chunk

        if start >= total:
            break

        end = min(total - 1, start + chunk - 1)
        expected = end - start + 1
        part_path = parts_dir / f"part_{index:02d}.bin"

        handle.write(
            f"{index}\t{start}\t{end}\t{expected}\t{part_path}\n"
        )
PY_EOF

column -t -s $'\t' "$PART_MANIFEST"

echo
echo "[3/10] Downloading ranges in parallel with per-part resume"

export SUMMARY_URL

tail -n +2 "$PART_MANIFEST" \
    | xargs -P "$PARALLEL_JOBS" -n 5 bash -c '
        set -Eeuo pipefail

        part_number="$1"
        start_byte="$2"
        end_byte="$3"
        expected_bytes="$4"
        part_path="$5"

        mkdir -p "$(dirname "$part_path")"

        current_size=0

        if [[ -f "$part_path" ]]; then
            current_size="$(stat -c "%s" "$part_path")"
        fi

        if [[ "$current_size" -eq "$expected_bytes" ]]; then
            echo "PART $part_number already complete: $current_size bytes"
            exit 0
        fi

        if [[ "$current_size" -gt "$expected_bytes" ]]; then
            echo "PART $part_number oversized; deleting corrupt part."
            rm -f "$part_path"
            current_size=0
        fi

        resume_start=$((start_byte + current_size))

        echo \
            "PART $part_number downloading bytes " \
            "$resume_start-$end_byte " \
            "(existing=$current_size expected=$expected_bytes)"

        temp_headers="${part_path}.headers"

        curl \
            -L \
            -sS \
            --fail \
            --retry 20 \
            --retry-delay 10 \
            --retry-all-errors \
            --connect-timeout 30 \
            --range "${resume_start}-${end_byte}" \
            -D "$temp_headers" \
            -o "${part_path}.new" \
            "$SUMMARY_URL"

        status="$(
            awk "/^HTTP\\// {code=\$2} END {print code}" "$temp_headers"
        )"

        if [[ "$status" != "206" && "$status" != "200" ]]; then
            echo "PART $part_number invalid HTTP status: $status"
            exit 1
        fi

        cat "${part_path}.new" >> "$part_path"

        rm -f "${part_path}.new" "$temp_headers"

        final_size="$(stat -c "%s" "$part_path")"

        if [[ "$final_size" -ne "$expected_bytes" ]]; then
            echo \
                "PART $part_number size mismatch: " \
                "$final_size != $expected_bytes"
            exit 1
        fi

        echo "PART $part_number COMPLETE: $final_size bytes"
    ' _

echo
echo "[4/10] Validating every downloaded part"

PART_FAILURES=0

while IFS=$'\t' read -r \
    part_number start_byte end_byte expected_bytes part_path; do

    [[ "$part_number" == "part_number" ]] && continue

    if [[ ! -f "$part_path" ]]; then
        echo "MISSING: part $part_number"
        PART_FAILURES=$((PART_FAILURES + 1))
        continue
    fi

    actual_bytes="$(stat -c '%s' "$part_path")"

    if [[ "$actual_bytes" -ne "$expected_bytes" ]]; then
        echo \
            "SIZE ERROR: part $part_number " \
            "$actual_bytes != $expected_bytes"

        PART_FAILURES=$((PART_FAILURES + 1))
    else
        echo "PASS: part $part_number — $actual_bytes bytes"
    fi
done < "$PART_MANIFEST"

if [[ "$PART_FAILURES" -ne 0 ]]; then
    echo "ERROR: $PART_FAILURES part validations failed."
    exit 1
fi

echo
echo "[5/10] Concatenating verified parts"

rm -f "$SUMMARY_FILE"

while IFS=$'\t' read -r \
    part_number start_byte end_byte expected_bytes part_path; do

    [[ "$part_number" == "part_number" ]] && continue

    cat "$part_path" >> "$SUMMARY_FILE"
done < "$PART_MANIFEST"

FINAL_SIZE="$(stat -c '%s' "$SUMMARY_FILE")"

echo "Concatenated size: $FINAL_SIZE"

if [[ "$FINAL_SIZE" -ne "$TOTAL_BYTES" ]]; then
    echo "ERROR: Final summary size mismatch."
    echo "Expected: $TOTAL_BYTES"
    echo "Observed: $FINAL_SIZE"
    exit 1
fi

echo "Concatenation validation: PASS"

echo
echo "[6/10] Validating sequencing-summary schema"

head -1 "$SUMMARY_FILE"

export SUMMARY_FILE
export ALT_IDS
export RAW_MATCHES

python <<'PY_EOF'
import csv
import os
from pathlib import Path

summary_path = Path(os.environ["SUMMARY_FILE"])
targets_path = Path(os.environ["ALT_IDS"])
output_path = Path(os.environ["RAW_MATCHES"])

targets = {
    line.strip()
    for line in targets_path.read_text().splitlines()
    if line.strip()
}

fields = [
    "target_uuid",
    "matched_via",
    "summary_read_id",
    "summary_parent_read_id",
    "source_filename",
    "channel",
    "start_time",
    "sequence_length_template",
    "passes_filtering",
]

matches = []
found = set()
rows_scanned = 0

with summary_path.open(errors="replace", newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")

    if reader.fieldnames is None:
        raise SystemExit("No sequencing-summary header.")

    required = {
        "read_id",
        "parent_read_id",
        "filename_pod5",
    }

    missing = required - set(reader.fieldnames)

    if missing:
        raise SystemExit(
            f"Missing required columns: {sorted(missing)}"
        )

    for row in reader:
        rows_scanned += 1

        read_id = (row.get("read_id") or "").strip()
        parent_id = (row.get("parent_read_id") or "").strip()

        if read_id in targets:
            target_uuid = read_id
            matched_via = "read_id"
        elif parent_id in targets:
            target_uuid = parent_id
            matched_via = "parent_read_id"
        else:
            continue

        found.add(target_uuid)

        matches.append(
            {
                "target_uuid": target_uuid,
                "matched_via": matched_via,
                "summary_read_id": read_id,
                "summary_parent_read_id": parent_id,
                "source_filename": (
                    row.get("filename_pod5") or ""
                ).strip(),
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
    writer = csv.DictWriter(
        handle,
        fieldnames=fields,
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(matches)

print(f"Rows scanned: {rows_scanned}")
print(f"Target UUIDs: {len(targets)}")
print(f"Resolved UUIDs: {len(found)}")
print(f"Matching rows: {len(matches)}")
PY_EOF

echo
echo "[7/10] Normalizing read-to-POD5 mapping"

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
        pod5_name = Path(row["source_filename"].strip()).name

        if not target_uuid or not pod5_name.endswith(".pod5"):
            continue

        matches[target_uuid].append(
            {
                "matched_via": row["matched_via"],
                "summary_read_id": row["summary_read_id"],
                "summary_parent_read_id": row["summary_parent_read_id"],
                "pod5_name": pod5_name,
                "pod5_url": f"{pod5_root}/{pod5_name}",
            }
        )

fields = [
    "target_uuid",
    "mapping_status",
    "matched_via",
    "summary_read_id",
    "summary_parent_read_id",
    "pod5_name",
    "pod5_url",
]

rows = []

for target_uuid in sorted(alt_ids):
    unique = {}

    for item in matches.get(target_uuid, []):
        key = (item["summary_read_id"], item["pod5_name"])
        unique[key] = item

    items = list(unique.values())

    if not items:
        rows.append(
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
        continue

    pod5_names = {item["pod5_name"] for item in items}
    status = (
        "UNIQUE_POD5"
        if len(pod5_names) == 1
        else "MULTIPLE_POD5"
    )

    for item in items:
        rows.append(
            {
                "target_uuid": target_uuid,
                "mapping_status": status,
                **item,
            }
        )

with mapping_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=fields,
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(rows)

resolved = {
    row["target_uuid"]
    for row in rows
    if row["pod5_name"]
}

unresolved = sorted(alt_ids - resolved)

unresolved_path.write_text(
    "".join(f"{read_id}\n" for read_id in unresolved)
)

pod5_reads = defaultdict(set)
pod5_urls = {}

for row in rows:
    if not row["pod5_name"]:
        continue

    pod5_reads[row["pod5_name"]].add(row["target_uuid"])
    pod5_urls[row["pod5_name"]] = row["pod5_url"]

with manifest_path.open("w", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")

    writer.writerow(
        [
            "pod5_name",
            "pod5_url",
            "ALT_parent_count",
            "ALT_parent_UUIDs",
        ]
    )

    for pod5_name in sorted(pod5_reads):
        read_ids = sorted(pod5_reads[pod5_name])

        writer.writerow(
            [
                pod5_name,
                pod5_urls[pod5_name],
                len(read_ids),
                ",".join(read_ids),
            ]
        )

print(f"Resolved ALT UUIDs: {len(resolved)}")
print(f"Unresolved ALT UUIDs: {len(unresolved)}")
print(f"Required POD5 shards: {len(pod5_reads)}")
PY_EOF

echo
echo "[8/10] Checking POD5 URLs and sizes"

{
    printf \
        'pod5_name\tpod5_url\tALT_parent_count\tremote_size_bytes\tremote_size_gib\thttp_status\n'

    tail -n +2 "$POD5_MANIFEST" |
    while IFS=$'\t' read -r \
        pod5_name pod5_url alt_count alt_read_ids; do

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

        HTTP_STATUS="$(
            printf '%s\n' "$HEADERS" \
                | awk '/^HTTP\// {code=$2} END {print code}'
        )"

        REMOTE_SIZE="$(
            printf '%s\n' "$HEADERS" \
                | awk '
                    BEGIN {IGNORECASE=1}
                    /^content-length:/ {
                        gsub("\r", "", $2)
                        bytes=$2
                    }
                    END {print bytes}
                '
        )"

        if [[ "$REMOTE_SIZE" =~ ^[0-9]+$ ]]; then
            GIB="$(
                awk -v bytes="$REMOTE_SIZE" \
                    'BEGIN {printf "%.4f", bytes/1024/1024/1024}'
            )"
        else
            REMOTE_SIZE=""
            GIB=""
        fi

        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$pod5_name" \
            "$pod5_url" \
            "$alt_count" \
            "$REMOTE_SIZE" \
            "$GIB" \
            "$HTTP_STATUS"
    done
} > "$POD5_SIZES"

column -t -s $'\t' "$POD5_SIZES" 2>/dev/null ||
    cat "$POD5_SIZES"

echo
echo "[9/10] Creating final summary"

RESOLVED_COUNT="$(
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

UNRESOLVED_COUNT="$(
    awk 'NF {n++} END {print n+0}' "$UNRESOLVED_IDS"
)"

POD5_COUNT="$(
    awk -F '\t' 'NR > 1 && $1 != "" {n++} END {print n+0}' \
        "$POD5_MANIFEST"
)"

VALID_POD5_COUNT="$(
    awk -F '\t' 'NR > 1 && $6 == "200" {n++} END {print n+0}' \
        "$POD5_SIZES"
)"

TOTAL_POD5_BYTES="$(
    awk -F '\t' '
        NR > 1 && $4 ~ /^[0-9]+$/ {
            total += $4
        }
        END {
            printf "%.0f", total+0
        }
    ' "$POD5_SIZES"
)"

TOTAL_POD5_GIB="$(
    awk -v bytes="$TOTAL_POD5_BYTES" \
        'BEGIN {printf "%.4f", bytes/1024/1024/1024}'
)"

{
    echo "A3 F11 Resumable Metadata Lookup Summary"
    echo "========================================="
    echo
    echo "Completed: $(date -Is)"
    echo
    echo "ALT parent UUIDs: $ALT_COUNT"
    echo "Resolved ALT UUIDs: $RESOLVED_COUNT"
    echo "Unresolved ALT UUIDs: $UNRESOLVED_COUNT"
    echo "Required POD5 shards: $POD5_COUNT"
    echo "Reachable POD5 shards: $VALID_POD5_COUNT"
    echo
    echo "Estimated POD5 download:"
    echo "Bytes: $TOTAL_POD5_BYTES"
    echo "GiB: $TOTAL_POD5_GIB"
    echo

    if [[ "$RESOLVED_COUNT" -eq "$ALT_COUNT" ]] &&
       [[ "$UNRESOLVED_COUNT" -eq 0 ]] &&
       [[ "$VALID_POD5_COUNT" -eq "$POD5_COUNT" ]]; then

        echo "Overall status: ALL_ALT_READS_RESOLVED"
    elif [[ "$RESOLVED_COUNT" -gt 0 ]]; then
        echo "Overall status: PARTIAL_ALT_RESOLUTION"
    else
        echo "Overall status: NO_ALT_READS_RESOLVED"
    fi
} > "$FINAL_SUMMARY"

cat "$FINAL_SUMMARY"

echo
echo "[10/10] Creating completion marker"

{
    echo "Completed: $(date -Is)"
    echo "ALT UUIDs: $ALT_COUNT"
    echo "Resolved ALT UUIDs: $RESOLVED_COUNT"
    echo "Required POD5 shards: $POD5_COUNT"
    echo "Estimated POD5 download GiB: $TOTAL_POD5_GIB"
    echo "Summary: $FINAL_SUMMARY"
} > "$COMPLETE_MARKER"

rm -f "$FAILED_MARKER"

echo
echo "============================================================"
echo "A3 F11 RESUMABLE METADATA LOOKUP COMPLETE"
echo "============================================================"
