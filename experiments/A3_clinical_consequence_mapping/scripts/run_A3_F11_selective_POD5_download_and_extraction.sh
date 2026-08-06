#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

source \
    experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate/ONT_target_retrieval"
BASE_DIR="$RESULTS_DIR/POD5_mapping/resumable_remote_lookup"
DOWNLOAD_DIR="$RESULTS_DIR/F11_required_POD5_shards"
EXTRACT_DIR="$RESULTS_DIR/F11_extracted_signal"
MARKER_DIR="$A3_DIR/markers"

mkdir -p "$DOWNLOAD_DIR" "$EXTRACT_DIR" "$MARKER_DIR"

REPAIRED_MAPPING="$BASE_DIR/F11_read_to_POD5_mapping_repaired.tsv"
REPAIRED_SIZES="$BASE_DIR/F11_required_POD5_remote_sizes_repaired.tsv"

DOWNLOAD_MANIFEST="$EXTRACT_DIR/F11_reachable_POD5_download_manifest.tsv"
RESOLVED_ALT_IDS="$EXTRACT_DIR/F11_resolved_ALT_parent_read_ids.txt"
UNAVAILABLE_ALT_IDS="$EXTRACT_DIR/F11_unavailable_ALT_parent_read_ids.txt"

TARGET_POD5="$EXTRACT_DIR/F11_ALT_reads.pod5"
EXTRACTED_READ_IDS="$EXTRACT_DIR/F11_extracted_ALT_read_ids.txt"
MISSING_AFTER_EXTRACTION="$EXTRACT_DIR/F11_missing_after_POD5_extraction.txt"
VALIDATION="$EXTRACT_DIR/F11_POD5_extraction_validation.txt"
SUMMARY="$EXTRACT_DIR/F11_selective_POD5_extraction_summary.txt"

COMPLETE_MARKER="$MARKER_DIR/A3_F11_SELECTIVE_POD5_EXTRACTION.COMPLETE"
FAILED_MARKER="$MARKER_DIR/A3_F11_SELECTIVE_POD5_EXTRACTION.FAILED"

rm -f "$FAILED_MARKER"

trap 'status=$?;
      {
          echo "Failed: $(date -Is)"
          echo "Exit status: ${status}"
      } > "$FAILED_MARKER";
      echo "ERROR: Workflow failed with status ${status}";
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — SELECTIVE POD5 DOWNLOAD AND EXTRACTION"
echo "============================================================"
echo "Started: $(date -Is)"
echo

echo "[1/10] Validating required tools and metadata"

for tool in curl python awk sort comm stat pod5; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "ERROR: Missing required tool: $tool"
        exit 1
    }
done

for file in "$REPAIRED_MAPPING" "$REPAIRED_SIZES"; do
    if [[ ! -s "$file" ]]; then
        echo "ERROR: Required metadata file missing:"
        echo "$file"
        exit 1
    fi
done

pod5 --version || true

echo
echo "[2/10] Building reachable shard and resolved-read manifests"

python - <<'PY_EOF'
import csv
from pathlib import Path

base = Path(
    "experiments/A3_clinical_consequence_mapping/"
    "results/F11_candidate/ONT_target_retrieval/"
    "POD5_mapping/resumable_remote_lookup"
)

extract = Path(
    "experiments/A3_clinical_consequence_mapping/"
    "results/F11_candidate/ONT_target_retrieval/"
    "F11_extracted_signal"
)

sizes_path = base / "F11_required_POD5_remote_sizes_repaired.tsv"
mapping_path = base / "F11_read_to_POD5_mapping_repaired.tsv"

download_manifest = extract / "F11_reachable_POD5_download_manifest.tsv"
resolved_ids = extract / "F11_resolved_ALT_parent_read_ids.txt"
unavailable_ids = extract / "F11_unavailable_ALT_parent_read_ids.txt"

extract.mkdir(parents=True, exist_ok=True)

reachable = {}

with sizes_path.open(newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")

    for row in reader:
        if row.get("http_status", "").strip() != "200":
            continue

        name = row["pod5_name"].strip()
        reachable[name] = {
            "pod5_name": name,
            "pod5_url": row["pod5_url"].strip(),
            "remote_size_bytes": row["remote_size_bytes"].strip(),
        }

mapped_ids = set()
available_ids = set()
unavailable = set()

with mapping_path.open(newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")

    for row in reader:
        read_id = row.get("target_uuid", "").strip()
        pod5_name = row.get("pod5_name", "").strip()

        if not read_id:
            continue

        mapped_ids.add(read_id)

        if pod5_name in reachable:
            available_ids.add(read_id)
        else:
            unavailable.add(read_id)

with download_manifest.open("w", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(
        [
            "pod5_name",
            "pod5_url",
            "remote_size_bytes",
            "local_path",
        ]
    )

    for name in sorted(reachable):
        item = reachable[name]

        writer.writerow(
            [
                name,
                item["pod5_url"],
                item["remote_size_bytes"],
                str(
                    Path(
                        "experiments/A3_clinical_consequence_mapping/"
                        "results/F11_candidate/ONT_target_retrieval/"
                        "F11_required_POD5_shards"
                    )
                    / name
                ),
            ]
        )

resolved_ids.write_text(
    "".join(f"{read_id}\n" for read_id in sorted(available_ids))
)

unavailable_ids.write_text(
    "".join(f"{read_id}\n" for read_id in sorted(unavailable))
)

print(f"Reachable POD5 shards: {len(reachable)}")
print(f"Resolved extractable ALT UUIDs: {len(available_ids)}")
print(f"Mapped but unavailable ALT UUIDs: {len(unavailable)}")
PY_EOF

echo
echo "Download manifest:"
column -t -s $'\t' "$DOWNLOAD_MANIFEST"

echo
echo "Resolved extractable ALT IDs:"
cat "$RESOLVED_ALT_IDS"

echo
echo "Unavailable mapped ALT IDs:"
if [[ -s "$UNAVAILABLE_ALT_IDS" ]]; then
    cat "$UNAVAILABLE_ALT_IDS"
else
    echo "None."
fi

echo
echo "[3/10] Downloading 14 reachable POD5 shards in parallel"

export DOWNLOAD_DIR

tail -n +2 "$DOWNLOAD_MANIFEST" \
    | xargs -P 6 -n 4 bash -c '
        set -Eeuo pipefail

        pod5_name="$1"
        pod5_url="$2"
        expected_bytes="$3"
        local_path="$4"

        mkdir -p "$(dirname "$local_path")"

        current_bytes=0

        if [[ -f "$local_path" ]]; then
            current_bytes="$(stat -c "%s" "$local_path")"
        fi

        if [[ "$current_bytes" -eq "$expected_bytes" ]]; then
            echo "ALREADY COMPLETE: $pod5_name"
            exit 0
        fi

        if [[ "$current_bytes" -gt "$expected_bytes" ]]; then
            echo "Deleting oversized file: $pod5_name"
            rm -f "$local_path"
            current_bytes=0
        fi

        echo \
            "DOWNLOADING: $pod5_name " \
            "existing=$current_bytes expected=$expected_bytes"

        curl \
            -L \
            --fail \
            --retry 20 \
            --retry-delay 10 \
            --retry-all-errors \
            --connect-timeout 30 \
            -C - \
            -o "$local_path" \
            "$pod5_url"

        final_bytes="$(stat -c "%s" "$local_path")"

        if [[ "$final_bytes" -ne "$expected_bytes" ]]; then
            echo \
                "ERROR: Size mismatch for $pod5_name: " \
                "$final_bytes != $expected_bytes"
            exit 1
        fi

        echo "COMPLETE: $pod5_name — $final_bytes bytes"
    ' _

echo
echo "[4/10] Validating all downloaded shards"

DOWNLOAD_FAILURES=0

while IFS=$'\t' read -r \
    pod5_name pod5_url expected_bytes local_path; do

    [[ "$pod5_name" == "pod5_name" ]] && continue

    if [[ ! -f "$local_path" ]]; then
        echo "MISSING: $pod5_name"
        DOWNLOAD_FAILURES=$((DOWNLOAD_FAILURES + 1))
        continue
    fi

    actual_bytes="$(stat -c '%s' "$local_path")"

    if [[ "$actual_bytes" -ne "$expected_bytes" ]]; then
        echo \
            "SIZE ERROR: $pod5_name " \
            "$actual_bytes != $expected_bytes"

        DOWNLOAD_FAILURES=$((DOWNLOAD_FAILURES + 1))
    else
        echo "PASS: $pod5_name — $actual_bytes bytes"
    fi
done < "$DOWNLOAD_MANIFEST"

if [[ "$DOWNLOAD_FAILURES" -ne 0 ]]; then
    echo "ERROR: $DOWNLOAD_FAILURES shard validations failed."
    exit 1
fi

echo
echo "[5/10] Inspecting source POD5 collection"

pod5 inspect summary \
    "$DOWNLOAD_DIR"/*.pod5 \
    > "$EXTRACT_DIR/F11_source_POD5_inspection.tsv"

head -20 "$EXTRACT_DIR/F11_source_POD5_inspection.tsv"

echo
echo "[6/10] Extracting only the resolved F11 ALT reads"

rm -f "$TARGET_POD5"

pod5 subset \
    "$DOWNLOAD_DIR"/*.pod5 \
    --output "$TARGET_POD5" \
    --read-id "$RESOLVED_ALT_IDS" \
    --missing-ok

if [[ ! -s "$TARGET_POD5" ]]; then
    echo "ERROR: Extracted target POD5 is missing or empty."
    exit 1
fi

echo
echo "Extracted target POD5:"
ls -lh "$TARGET_POD5"

echo
echo "[7/10] Enumerating extracted read IDs"

pod5 inspect reads \
    "$TARGET_POD5" \
    | awk -F ',' '
        NR == 1 {
            for (i=1; i<=NF; i++) {
                gsub(/"/, "", $i)
                if ($i == "read_id") {
                    column=i
                    break
                }
            }
            next
        }

        {
            value=$column
            gsub(/"/, "", value)

            if (value != "")
                print value
        }
    ' \
    | sort -u \
    > "$EXTRACTED_READ_IDS"

sort -u "$RESOLVED_ALT_IDS" \
    > "$EXTRACT_DIR/F11_resolved_ALT_parent_read_ids.sorted.txt"

comm -23 \
    "$EXTRACT_DIR/F11_resolved_ALT_parent_read_ids.sorted.txt" \
    "$EXTRACTED_READ_IDS" \
    > "$MISSING_AFTER_EXTRACTION"

EXPECTED_READS="$(
    awk 'NF {n++} END {print n+0}' "$RESOLVED_ALT_IDS"
)"

EXTRACTED_READS="$(
    awk 'NF {n++} END {print n+0}' "$EXTRACTED_READ_IDS"
)"

MISSING_READS="$(
    awk 'NF {n++} END {print n+0}' "$MISSING_AFTER_EXTRACTION"
)"

echo "Expected resolved ALT reads: $EXPECTED_READS"
echo "Extracted ALT reads: $EXTRACTED_READS"
echo "Missing after extraction: $MISSING_READS"

echo
echo "[8/10] Validating extracted POD5"

pod5 inspect summary \
    "$TARGET_POD5" \
    > "$VALIDATION"

cat "$VALIDATION"

if [[ "$EXTRACTED_READS" -ne "$EXPECTED_READS" ]]; then
    echo "ERROR: Not all resolved ALT reads were extracted."
    echo
    echo "Missing reads:"
    cat "$MISSING_AFTER_EXTRACTION"
    exit 1
fi

echo
echo "[9/10] Creating experimental summary"

TOTAL_DOWNLOAD_BYTES="$(
    awk -F '\t' '
        NR > 1 && $3 ~ /^[0-9]+$/ {
            total += $3
        }
        END {
            printf "%.0f", total+0
        }
    ' "$DOWNLOAD_MANIFEST"
)"

TOTAL_DOWNLOAD_GIB="$(
    awk -v bytes="$TOTAL_DOWNLOAD_BYTES" \
        'BEGIN {printf "%.4f", bytes/1024/1024/1024}'
)"

TARGET_POD5_BYTES="$(stat -c '%s' "$TARGET_POD5")"

TARGET_POD5_MIB="$(
    awk -v bytes="$TARGET_POD5_BYTES" \
        'BEGIN {printf "%.4f", bytes/1024/1024}'
)"

{
    echo "A3 F11 Selective POD5 Extraction Summary"
    echo "========================================="
    echo
    echo "Completed: $(date -Is)"
    echo
    echo "Clinical target: chr4:186274193 G>T"
    echo
    echo "Original ALT parent UUIDs: 17"
    echo "Resolved and extractable ALT UUIDs: $EXPECTED_READS"
    echo "Extracted ALT reads: $EXTRACTED_READS"
    echo "Unavailable ALT UUIDs: $((17 - EXPECTED_READS))"
    echo
    echo "Downloaded POD5 shards: 14"
    echo "Downloaded shard volume GiB: $TOTAL_DOWNLOAD_GIB"
    echo "Extracted target POD5 MiB: $TARGET_POD5_MIB"
    echo
    echo "Dataset limitation:"
    echo "One aligned ALT parent was absent from the sequencing summary,"
    echo "and one mapped fail-POD5 shard was unavailable at the published"
    echo "pass-POD5 location. The attack experiment therefore proceeds"
    echo "with the fully traceable and validated recoverable ALT subset."
    echo
    echo "Overall status: READY_FOR_CLEAN_REBASECALLING"
    echo
    echo "Target POD5:"
    echo "$TARGET_POD5"
} > "$SUMMARY"

cat "$SUMMARY"

echo
echo "[10/10] Creating completion marker"

{
    echo "Completed: $(date -Is)"
    echo "Resolved ALT reads: $EXPECTED_READS"
    echo "Extracted ALT reads: $EXTRACTED_READS"
    echo "Downloaded shards: 14"
    echo "Target POD5: $TARGET_POD5"
    echo "Summary: $SUMMARY"
} > "$COMPLETE_MARKER"

rm -f "$FAILED_MARKER"

echo
echo "============================================================"
echo "A3 F11 SELECTIVE POD5 EXTRACTION COMPLETE"
echo "============================================================"
