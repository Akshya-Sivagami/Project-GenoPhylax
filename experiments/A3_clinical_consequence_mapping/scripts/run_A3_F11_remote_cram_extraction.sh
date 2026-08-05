#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

VENV="experiments/A2_adversarial_dna/basecalling/environment/pod5_env"
source "$VENV/bin/activate"

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate/ONT_target_retrieval"
LOG_DIR="$A3_DIR/logs"
MARKER_DIR="$A3_DIR/markers"

mkdir -p "$RESULTS_DIR" "$LOG_DIR" "$MARKER_DIR"

COMPLETE_MARKER="$MARKER_DIR/A3_F11_REMOTE_CRAM_EXTRACTION.COMPLETE"
FAILED_MARKER="$MARKER_DIR/A3_F11_REMOTE_CRAM_EXTRACTION.FAILED"

REFERENCE="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"

REMOTE_CRAM="https://ont-open-data.s3.amazonaws.com/giab_2023.05/analysis/hg002/hac/PAO89685.pass.cram"

TARGET_CHROM="chr4"
TARGET_POS="186274193"
TARGET_REF="G"
TARGET_ALT="T"

REGION_START="186264193"
REGION_END="186284193"
REGION="${TARGET_CHROM}:${REGION_START}-${REGION_END}"
TARGET_REGION="${TARGET_CHROM}:${TARGET_POS}-${TARGET_POS}"

REGIONAL_UNSORTED_BAM="$RESULTS_DIR/F11_PAO89685_region.unsorted.bam"
REGIONAL_BAM="$RESULTS_DIR/F11_PAO89685_region.sorted.bam"

TARGET_RECORDS_SAM="$RESULTS_DIR/F11_target_overlapping_records.sam"
TARGET_RECORD_IDS="$RESULTS_DIR/F11_target_overlapping_record_ids.txt"
TARGET_PARENT_IDS="$RESULTS_DIR/F11_target_parent_read_ids.txt"

PER_RECORD_TSV="$RESULTS_DIR/F11_target_per_record_states.tsv"
PER_PARENT_TSV="$RESULTS_DIR/F11_target_per_parent_states.tsv"
SUMMARY_FILE="$RESULTS_DIR/F11_remote_CRAM_extraction_summary.txt"
REMOTE_CHECK_FILE="$RESULTS_DIR/F11_remote_CRAM_access_check.txt"

rm -f "$FAILED_MARKER"

trap 'status=$?;
      echo;
      echo "ERROR: F11 remote CRAM extraction failed with status ${status}";
      date -Is > "$FAILED_MARKER";
      echo "Exit status: ${status}" >> "$FAILED_MARKER";
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — REMOTE ONT CRAM REGIONAL EXTRACTION"
echo "============================================================"
echo "Started: $(date -Is)"
echo
echo "Python:    $(command -v python)"
echo "Samtools:  $(command -v samtools || true)"
echo "Reference: $REFERENCE"
echo "CRAM:      $REMOTE_CRAM"
echo "Region:    $REGION"
echo "Target:    $TARGET_CHROM:$TARGET_POS $TARGET_REF>$TARGET_ALT"
echo

echo "[1/9] Checking required programs"

for tool in samtools python; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "ERROR: Required program not found: $tool"
        exit 1
    fi
done

samtools --version | head -2
python --version

echo
echo "[2/9] Validating reference files"

if [[ ! -s "$REFERENCE" ]]; then
    echo "ERROR: Reference FASTA is missing or empty:"
    echo "$REFERENCE"
    exit 1
fi

if [[ ! -s "${REFERENCE}.fai" ]]; then
    echo "Reference FASTA index is missing. Creating it now."
    samtools faidx "$REFERENCE"
fi

REFERENCE_BASE="$(
    samtools faidx "$REFERENCE" "$TARGET_REGION" \
        | awk 'NR > 1 {printf "%s", $0}' \
        | tr '[:lower:]' '[:upper:]'
)"

echo "Reference base at $TARGET_REGION: $REFERENCE_BASE"

if [[ "$REFERENCE_BASE" != "$TARGET_REF" ]]; then
    echo "ERROR: Expected reference base $TARGET_REF but found $REFERENCE_BASE"
    exit 1
fi

echo
echo "[3/9] Testing remote CRAM access"

{
    echo "Checked: $(date -Is)"
    echo "Remote CRAM: $REMOTE_CRAM"
    echo "Requested region: $TARGET_REGION"
    echo

    samtools view \
        -T "$REFERENCE" \
        "$REMOTE_CRAM" \
        "$TARGET_REGION" \
        | head -5 || true
} > "$REMOTE_CHECK_FILE" 2>&1

if grep -qiE \
    'failed to open|could not open|error opening|connection refused|temporary failure|resolve host|unauthorized|forbidden' \
    "$REMOTE_CHECK_FILE"; then

    echo "ERROR: Remote CRAM access check reported a failure."
    cat "$REMOTE_CHECK_FILE"
    exit 1
fi

echo "Remote access check completed."
cat "$REMOTE_CHECK_FILE"

echo
echo "[4/9] Extracting approximately +/-10 kb around F11"

if [[ -s "$REGIONAL_BAM" ]] &&
   samtools quickcheck "$REGIONAL_BAM" &&
   [[ -s "${REGIONAL_BAM}.bai" ]]; then

    echo "Valid sorted regional BAM already exists."
    echo "Skipping remote extraction."

else
    rm -f \
        "$REGIONAL_UNSORTED_BAM" \
        "$REGIONAL_BAM" \
        "${REGIONAL_BAM}.bai"

    samtools view \
        -T "$REFERENCE" \
        -b \
        -o "$REGIONAL_UNSORTED_BAM" \
        "$REMOTE_CRAM" \
        "$REGION"

    samtools sort \
        -@ 4 \
        -o "$REGIONAL_BAM" \
        "$REGIONAL_UNSORTED_BAM"

    samtools index \
        -@ 4 \
        "$REGIONAL_BAM"

    rm -f "$REGIONAL_UNSORTED_BAM"
fi

samtools quickcheck -v "$REGIONAL_BAM"

echo
echo "[5/9] Counting regional and target-overlapping alignment records"

REGIONAL_RECORD_COUNT="$(
    samtools view -c "$REGIONAL_BAM"
)"

TARGET_RECORD_COUNT="$(
    samtools view -c "$REGIONAL_BAM" "$TARGET_REGION"
)"

echo "Regional alignment records: $REGIONAL_RECORD_COUNT"
echo "Target-overlapping records: $TARGET_RECORD_COUNT"

echo
echo "[6/9] Exporting target-overlapping records and read IDs"

{
    samtools view -H "$REGIONAL_BAM"
    samtools view "$REGIONAL_BAM" "$TARGET_REGION"
} > "$TARGET_RECORDS_SAM"

samtools view "$REGIONAL_BAM" "$TARGET_REGION" \
    | cut -f1 \
    > "$TARGET_RECORD_IDS"

sort -u "$TARGET_RECORD_IDS" \
    > "$TARGET_PARENT_IDS"

TARGET_PARENT_COUNT="$(
    awk 'NF {n++} END {print n+0}' "$TARGET_PARENT_IDS"
)"

echo "Unique target parent read IDs: $TARGET_PARENT_COUNT"

echo
echo "[7/9] Classifying target allele states per alignment and parent"

export REGIONAL_BAM
export TARGET_CHROM
export TARGET_POS
export TARGET_REF
export TARGET_ALT
export PER_RECORD_TSV
export PER_PARENT_TSV

python <<'PY_EOF'
import csv
import os
from collections import Counter, defaultdict

import pysam

bam_path = os.environ["REGIONAL_BAM"]
chrom = os.environ["TARGET_CHROM"]
target_pos_1based = int(os.environ["TARGET_POS"])
target_pos_0based = target_pos_1based - 1
ref_base = os.environ["TARGET_REF"].upper()
alt_base = os.environ["TARGET_ALT"].upper()
per_record_path = os.environ["PER_RECORD_TSV"]
per_parent_path = os.environ["PER_PARENT_TSV"]

record_rows = []
parent_states = defaultdict(list)

with pysam.AlignmentFile(bam_path, "rb") as bam:
    for read in bam.fetch(chrom, target_pos_0based, target_pos_1based):
        if read.is_unmapped:
            state = "UNMAPPED"
            observed = ""
            query_position = ""
        else:
            state = "NO_COVERAGE"
            observed = ""
            query_position = ""

            for query_pos, reference_pos in read.get_aligned_pairs(matches_only=False):
                if reference_pos != target_pos_0based:
                    continue

                if query_pos is None:
                    state = "DEL"
                    observed = "-"
                    query_position = ""
                elif read.query_sequence is None:
                    state = "NO_SEQUENCE"
                    observed = ""
                    query_position = query_pos
                else:
                    observed = read.query_sequence[query_pos].upper()
                    query_position = query_pos

                    if observed == alt_base:
                        state = "ALT"
                    elif observed == ref_base:
                        state = "REF"
                    else:
                        state = "OTHER"

                break

        row = {
            "read_id": read.query_name,
            "flag": read.flag,
            "reference_name": read.reference_name or "",
            "reference_start_1based": (
                read.reference_start + 1
                if read.reference_start is not None and read.reference_start >= 0
                else ""
            ),
            "reference_end_1based": read.reference_end or "",
            "mapping_quality": read.mapping_quality,
            "query_position_0based": query_position,
            "observed_base": observed,
            "target_state": state,
            "is_primary": int(not read.is_secondary and not read.is_supplementary),
            "is_secondary": int(read.is_secondary),
            "is_supplementary": int(read.is_supplementary),
            "is_reverse": int(read.is_reverse),
        }

        record_rows.append(row)
        parent_states[read.query_name].append(state)

record_fields = [
    "read_id",
    "flag",
    "reference_name",
    "reference_start_1based",
    "reference_end_1based",
    "mapping_quality",
    "query_position_0based",
    "observed_base",
    "target_state",
    "is_primary",
    "is_secondary",
    "is_supplementary",
    "is_reverse",
]

with open(per_record_path, "w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=record_fields, delimiter="\t")
    writer.writeheader()
    writer.writerows(record_rows)

priority = [
    "ALT",
    "REF",
    "DEL",
    "OTHER",
    "NO_SEQUENCE",
    "NO_COVERAGE",
    "UNMAPPED",
]

parent_rows = []

for read_id in sorted(parent_states):
    states = parent_states[read_id]
    counts = Counter(states)

    nonempty_states = [
        state for state in priority
        if counts[state] > 0
    ]

    if len(nonempty_states) == 1:
        parent_state = nonempty_states[0]
    elif not nonempty_states:
        parent_state = "UNKNOWN"
    else:
        parent_state = "MIXED:" + ",".join(nonempty_states)

    parent_rows.append(
        {
            "read_id": read_id,
            "record_count": len(states),
            "parent_state": parent_state,
            "ALT_records": counts["ALT"],
            "REF_records": counts["REF"],
            "DEL_records": counts["DEL"],
            "OTHER_records": counts["OTHER"],
            "NO_COVERAGE_records": counts["NO_COVERAGE"],
            "NO_SEQUENCE_records": counts["NO_SEQUENCE"],
            "UNMAPPED_records": counts["UNMAPPED"],
        }
    )

parent_fields = [
    "read_id",
    "record_count",
    "parent_state",
    "ALT_records",
    "REF_records",
    "DEL_records",
    "OTHER_records",
    "NO_COVERAGE_records",
    "NO_SEQUENCE_records",
    "UNMAPPED_records",
]

with open(per_parent_path, "w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=parent_fields, delimiter="\t")
    writer.writeheader()
    writer.writerows(parent_rows)

record_counts = Counter(row["target_state"] for row in record_rows)
parent_counts = Counter(row["parent_state"] for row in parent_rows)

print("Per-record target states:")
for state, count in sorted(record_counts.items()):
    print(f"  {state}: {count}")

print("Per-parent target states:")
for state, count in sorted(parent_counts.items()):
    print(f"  {state}: {count}")
PY_EOF

echo
echo "[8/9] Creating summary"

RECORD_ALT_COUNT="$(
    awk -F '\t' 'NR > 1 && $9 == "ALT" {n++} END {print n+0}' "$PER_RECORD_TSV"
)"

RECORD_REF_COUNT="$(
    awk -F '\t' 'NR > 1 && $9 == "REF" {n++} END {print n+0}' "$PER_RECORD_TSV"
)"

RECORD_DEL_COUNT="$(
    awk -F '\t' 'NR > 1 && $9 == "DEL" {n++} END {print n+0}' "$PER_RECORD_TSV"
)"

RECORD_OTHER_COUNT="$(
    awk -F '\t' 'NR > 1 && $9 == "OTHER" {n++} END {print n+0}' "$PER_RECORD_TSV"
)"

PARENT_ALT_COUNT="$(
    awk -F '\t' 'NR > 1 && $3 == "ALT" {n++} END {print n+0}' "$PER_PARENT_TSV"
)"

PARENT_REF_COUNT="$(
    awk -F '\t' 'NR > 1 && $3 == "REF" {n++} END {print n+0}' "$PER_PARENT_TSV"
)"

PARENT_DEL_COUNT="$(
    awk -F '\t' 'NR > 1 && $3 == "DEL" {n++} END {print n+0}' "$PER_PARENT_TSV"
)"

PARENT_OTHER_COUNT="$(
    awk -F '\t' 'NR > 1 && $3 == "OTHER" {n++} END {print n+0}' "$PER_PARENT_TSV"
)"

PARENT_MIXED_COUNT="$(
    awk -F '\t' 'NR > 1 && $3 ~ /^MIXED:/ {n++} END {print n+0}' "$PER_PARENT_TSV"
)"

{
    echo "A3 F11 Remote ONT CRAM Extraction Summary"
    echo "=========================================="
    echo
    echo "Completed: $(date -Is)"
    echo
    echo "Remote CRAM:"
    echo "$REMOTE_CRAM"
    echo
    echo "Reference:"
    echo "$REFERENCE"
    echo
    echo "Clinical candidate:"
    echo "$TARGET_CHROM:$TARGET_POS $TARGET_REF>$TARGET_ALT"
    echo
    echo "Extraction region:"
    echo "$REGION"
    echo
    echo "Reference validation:"
    echo "Observed reference base: $REFERENCE_BASE"
    echo "Expected reference base: $TARGET_REF"
    echo "Status: PASS"
    echo
    echo "Alignment counts:"
    echo "Regional alignment records: $REGIONAL_RECORD_COUNT"
    echo "Target-overlapping records: $TARGET_RECORD_COUNT"
    echo "Unique target parent reads: $TARGET_PARENT_COUNT"
    echo
    echo "Per-record target states:"
    echo "ALT: $RECORD_ALT_COUNT"
    echo "REF: $RECORD_REF_COUNT"
    echo "DEL: $RECORD_DEL_COUNT"
    echo "OTHER: $RECORD_OTHER_COUNT"
    echo
    echo "Unambiguous per-parent target states:"
    echo "ALT: $PARENT_ALT_COUNT"
    echo "REF: $PARENT_REF_COUNT"
    echo "DEL: $PARENT_DEL_COUNT"
    echo "OTHER: $PARENT_OTHER_COUNT"
    echo "MIXED: $PARENT_MIXED_COUNT"
    echo
    if [[ "$TARGET_RECORD_COUNT" -eq 0 ]]; then
        echo "Overall status: NO_TARGET_COVERAGE"
        echo
        echo "The PAO89685 remote CRAM returned no alignment records at the F11 target."
    elif [[ "$PARENT_ALT_COUNT" -eq 0 ]]; then
        echo "Overall status: COVERAGE_PRESENT_BUT_NO_UNAMBIGUOUS_ALT_PARENT"
        echo
        echo "ONT reads cover the target, but no unambiguous ALT-supporting parent was found."
    else
        echo "Overall status: ALT_SUPPORT_CONFIRMED"
        echo
        echo "The PAO89685 flowcell contains target reads supporting the F11 ALT allele."
        echo "These parent read IDs can now be mapped to source POD5 shards."
    fi
    echo
    echo "Generated files:"
    echo "$REGIONAL_BAM"
    echo "${REGIONAL_BAM}.bai"
    echo "$TARGET_RECORDS_SAM"
    echo "$TARGET_RECORD_IDS"
    echo "$TARGET_PARENT_IDS"
    echo "$PER_RECORD_TSV"
    echo "$PER_PARENT_TSV"
} > "$SUMMARY_FILE"

cat "$SUMMARY_FILE"

echo
echo "[9/9] Final validation and marker creation"

for output in \
    "$REGIONAL_BAM" \
    "${REGIONAL_BAM}.bai" \
    "$TARGET_RECORDS_SAM" \
    "$TARGET_RECORD_IDS" \
    "$TARGET_PARENT_IDS" \
    "$PER_RECORD_TSV" \
    "$PER_PARENT_TSV" \
    "$SUMMARY_FILE"; do

    if [[ ! -e "$output" ]]; then
        echo "ERROR: Expected output was not created:"
        echo "$output"
        exit 1
    fi
done

{
    echo "Completed: $(date -Is)"
    echo "Target: $TARGET_CHROM:$TARGET_POS $TARGET_REF>$TARGET_ALT"
    echo "Region: $REGION"
    echo "Regional records: $REGIONAL_RECORD_COUNT"
    echo "Target records: $TARGET_RECORD_COUNT"
    echo "Target parents: $TARGET_PARENT_COUNT"
    echo "Unambiguous ALT parents: $PARENT_ALT_COUNT"
    echo "Summary: $SUMMARY_FILE"
} > "$COMPLETE_MARKER"

rm -f "$FAILED_MARKER"

echo
echo "============================================================"
echo "A3 F11 REMOTE CRAM EXTRACTION COMPLETE"
echo "============================================================"
echo "Completed: $(date -Is)"
echo "Marker: $COMPLETE_MARKER"
echo "Summary: $SUMMARY_FILE"
