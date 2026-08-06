#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

source \
    experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate"
INPUT_DIR="$RESULTS_DIR/ONT_target_retrieval/F11_extracted_signal"
OUTPUT_DIR="$RESULTS_DIR/clean_rebasecalling"
MARKER_DIR="$A3_DIR/markers"

mkdir -p "$OUTPUT_DIR" "$MARKER_DIR"

INPUT_POD5="$INPUT_DIR/F11_ALT_reads.pod5"
EXPECTED_IDS="$INPUT_DIR/F11_extracted_ALT_read_ids.txt"

REFERENCE="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"

RAW_BAM="$OUTPUT_DIR/F11_clean_dorado_raw.bam"
RAW_FASTQ="$OUTPUT_DIR/F11_clean_dorado.fastq"
ALIGNED_BAM="$OUTPUT_DIR/F11_clean_dorado_GRCh38.sorted.bam"

BASECALL_STDERR="$OUTPUT_DIR/F11_clean_dorado.stderr.log"
ALIGN_STDERR="$OUTPUT_DIR/F11_clean_alignment.stderr.log"

RECORD_AUDIT="$OUTPUT_DIR/F11_clean_target_record_audit.tsv"
PARENT_AUDIT="$OUTPUT_DIR/F11_clean_target_parent_audit.tsv"
SUMMARY="$OUTPUT_DIR/F11_clean_rebasecalling_summary.txt"
COMMAND_AUDIT="$OUTPUT_DIR/F11_clean_command_audit.txt"

COMPLETE="$MARKER_DIR/A3_F11_CLEAN_REBASECALLING.COMPLETE"
FAILED="$MARKER_DIR/A3_F11_CLEAN_REBASECALLING.FAILED"

TARGET_CONTIG="chr4"
TARGET_POS=186274193
REF_BASE="G"
ALT_BASE="T"

rm -f "$FAILED"

trap 'status=$?;
      {
          echo "Failed: $(date -Is)"
          echo "Exit status: ${status}"
      } > "$FAILED";
      echo "ERROR: F11 clean rebasecalling failed with status ${status}";
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — CLEAN DORADO REBASECALLING"
echo "============================================================"
echo "Started: $(date -Is)"
echo

echo "[1/10] Resolving required tools"

DORADO="$(command -v dorado 2>/dev/null || true)"

if [[ -z "$DORADO" ]]; then
    DORADO="$(
        find "$HOME" \
            -type f \
            -path '*/bin/dorado' \
            -perm -111 \
            2>/dev/null \
            | head -1
    )"
fi

if [[ -z "$DORADO" || ! -x "$DORADO" ]]; then
    echo "ERROR: Dorado executable could not be located."
    exit 1
fi

for tool in samtools minimap2 python nvidia-smi; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "ERROR: Missing required tool: $tool"
        exit 1
    }
done

echo "Dorado: $DORADO"
"$DORADO" --version

echo
echo "samtools:"
samtools --version | head -2

echo
echo "minimap2:"
minimap2 --version

echo
echo "GPU:"
nvidia-smi \
    --query-gpu=name,driver_version,memory.total,memory.free \
    --format=csv,noheader

echo
echo "[2/10] Resolving Dorado HAC model"

MODEL_NAME="dna_r10.4.1_e8.2_400bps_hac@v6.0.0"

MODEL_PATH="$(
    find "$HOME" \
        -type d \
        -name "$MODEL_NAME" \
        2>/dev/null \
        | head -1
)"

if [[ -z "$MODEL_PATH" ]]; then
    echo "ERROR: Dorado model directory not found:"
    echo "$MODEL_NAME"
    exit 1
fi

echo "Model: $MODEL_PATH"

if [[ ! -s "$REFERENCE" ]]; then
    echo "ERROR: GRCh38 reference is missing:"
    echo "$REFERENCE"
    exit 1
fi

if [[ ! -s "$REFERENCE.fai" ]]; then
    echo "Reference index missing; creating it."
    samtools faidx "$REFERENCE"
fi

echo
echo "[3/10] Recording exact command configuration"

{
    echo "Started: $(date -Is)"
    echo "Dorado: $DORADO"
    echo "Model: $MODEL_PATH"
    echo "Input POD5: $INPUT_POD5"
    echo "Reference: $REFERENCE"
    echo "Target: $TARGET_CONTIG:$TARGET_POS $REF_BASE>$ALT_BASE"
    echo "Device: cuda:all"
} > "$COMMAND_AUDIT"

cat "$COMMAND_AUDIT"

echo
echo "[4/10] Running clean Dorado basecalling"

rm -f "$RAW_BAM" "$BASECALL_STDERR"

"$DORADO" basecaller \
    "$MODEL_PATH" \
    "$INPUT_POD5" \
    --device cuda:all \
    --emit-moves \
    > "$RAW_BAM" \
    2> "$BASECALL_STDERR"

if [[ ! -s "$RAW_BAM" ]]; then
    echo "ERROR: Dorado output BAM is missing or empty."
    exit 1
fi

# Dorado emits an unaligned BAM without @SQ reference targets.
# samtools quickcheck treats the absence of targets as an error, even
# though the BAM can be valid. Validate by parsing the header and records.

if ! samtools view -H "$RAW_BAM" >/dev/null; then
    echo "ERROR: Dorado BAM header could not be parsed."
    exit 1
fi

if ! samtools view "$RAW_BAM" >/dev/null; then
    echo "ERROR: Dorado BAM records could not be parsed."
    exit 1
fi

RAW_RECORDS="$(samtools view -c "$RAW_BAM")"

echo "Raw Dorado BAM records: $RAW_RECORDS"

if [[ "$RAW_RECORDS" -lt 15 ]]; then
    echo "ERROR: Dorado emitted fewer than the expected 15 records."
    exit 1
fi

echo "Unaligned Dorado BAM validation: PASS"

echo
echo "Dorado log tail:"
tail -30 "$BASECALL_STDERR"

echo
echo "[5/10] Converting clean calls to FASTQ"

rm -f "$RAW_FASTQ"

samtools fastq \
    -n \
    "$RAW_BAM" \
    > "$RAW_FASTQ"

FASTQ_READS="$(
    awk 'END {print NR/4}' "$RAW_FASTQ"
)"

echo "FASTQ reads: $FASTQ_READS"

if [[ "$FASTQ_READS" -lt 15 ]]; then
    echo "ERROR: Fewer than 15 reads were emitted by Dorado."
    exit 1
fi

echo
echo "[6/10] Aligning clean calls to GRCh38"

rm -f "$ALIGNED_BAM" "$ALIGNED_BAM.bai" "$ALIGN_STDERR"

minimap2 \
    -ax map-ont \
    -t 16 \
    "$REFERENCE" \
    "$RAW_FASTQ" \
    2> "$ALIGN_STDERR" \
    | samtools sort \
        -@ 8 \
        -o "$ALIGNED_BAM" \
        -

samtools index "$ALIGNED_BAM"
samtools quickcheck -v "$ALIGNED_BAM"

TOTAL_ALIGNMENT_RECORDS="$(samtools view -c "$ALIGNED_BAM")"
MAPPED_RECORDS="$(samtools view -c -F 4 "$ALIGNED_BAM")"
PRIMARY_MAPPED_RECORDS="$(samtools view -c -F 2308 "$ALIGNED_BAM")"

echo "Total alignment records: $TOTAL_ALIGNMENT_RECORDS"
echo "Mapped alignment records: $MAPPED_RECORDS"
echo "Primary mapped records: $PRIMARY_MAPPED_RECORDS"

echo
echo "[7/10] Auditing the F11 target per alignment record"

export ALIGNED_BAM
export EXPECTED_IDS
export RECORD_AUDIT
export PARENT_AUDIT
export TARGET_CONTIG
export TARGET_POS
export REF_BASE
export ALT_BASE

python <<'PY_EOF'
import csv
import os
from collections import defaultdict
from pathlib import Path

import pysam

bam_path = Path(os.environ["ALIGNED_BAM"])
ids_path = Path(os.environ["EXPECTED_IDS"])
record_output = Path(os.environ["RECORD_AUDIT"])
parent_output = Path(os.environ["PARENT_AUDIT"])

contig = os.environ["TARGET_CONTIG"]
position = int(os.environ["TARGET_POS"])
target_zero = position - 1
ref_base = os.environ["REF_BASE"].upper()
alt_base = os.environ["ALT_BASE"].upper()

expected_ids = {
    line.strip()
    for line in ids_path.read_text().splitlines()
    if line.strip()
}

record_fields = [
    "parent_read_id",
    "record_index",
    "flag",
    "is_primary",
    "is_supplementary",
    "is_secondary",
    "is_reverse",
    "is_unmapped",
    "reference_name",
    "reference_start_1based",
    "reference_end_1based",
    "mapq",
    "target_status",
    "target_base",
    "query_position_0based",
    "cigar",
]

record_rows = []
parent_statuses = defaultdict(list)
observed_parents = set()

with pysam.AlignmentFile(str(bam_path), "rb") as bam:
    record_index = 0

    for record in bam.fetch(until_eof=True):
        parent_id = record.query_name

        if parent_id not in expected_ids:
            continue

        observed_parents.add(parent_id)
        record_index += 1

        status = "NO_COVERAGE"
        target_base = ""
        query_position = ""

        if record.is_unmapped:
            status = "UNMAPPED"
        elif record.reference_name == contig:
            found_target = False

            for query_pos, reference_pos in record.get_aligned_pairs(
                matches_only=False
            ):
                if reference_pos != target_zero:
                    continue

                found_target = True

                if query_pos is None:
                    status = "DEL"
                    target_base = "-"
                else:
                    sequence = record.query_sequence or ""

                    if query_pos >= len(sequence):
                        status = "OTHER"
                        target_base = ""
                    else:
                        target_base = sequence[query_pos].upper()

                        if target_base == alt_base:
                            status = "ALT"
                        elif target_base == ref_base:
                            status = "REF"
                        else:
                            status = "OTHER"

                    query_position = query_pos

                break

            if not found_target:
                status = "NO_COVERAGE"

        parent_statuses[parent_id].append(status)

        record_rows.append(
            {
                "parent_read_id": parent_id,
                "record_index": record_index,
                "flag": record.flag,
                "is_primary": int(
                    not record.is_secondary
                    and not record.is_supplementary
                ),
                "is_supplementary": int(record.is_supplementary),
                "is_secondary": int(record.is_secondary),
                "is_reverse": int(record.is_reverse),
                "is_unmapped": int(record.is_unmapped),
                "reference_name": (
                    record.reference_name
                    if record.reference_name is not None
                    else ""
                ),
                "reference_start_1based": (
                    record.reference_start + 1
                    if record.reference_start is not None
                    and record.reference_start >= 0
                    else ""
                ),
                "reference_end_1based": (
                    record.reference_end
                    if record.reference_end is not None
                    else ""
                ),
                "mapq": record.mapping_quality,
                "target_status": status,
                "target_base": target_base,
                "query_position_0based": query_position,
                "cigar": record.cigarstring or "",
            }
        )

with record_output.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=record_fields,
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(record_rows)

priority = [
    "ALT",
    "REF",
    "DEL",
    "OTHER",
    "NO_COVERAGE",
    "UNMAPPED",
]

parent_fields = [
    "parent_read_id",
    "record_count",
    "record_statuses",
    "parent_status",
]

parent_rows = []

for parent_id in sorted(expected_ids):
    statuses = parent_statuses.get(parent_id, [])

    if not statuses:
        parent_status = "NO_DORADO_RECORD"
    else:
        parent_status = next(
            (
                candidate
                for candidate in priority
                if candidate in statuses
            ),
            "OTHER",
        )

    parent_rows.append(
        {
            "parent_read_id": parent_id,
            "record_count": len(statuses),
            "record_statuses": ",".join(statuses),
            "parent_status": parent_status,
        }
    )

with parent_output.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=parent_fields,
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(parent_rows)

print(f"Expected parents: {len(expected_ids)}")
print(f"Parents with Dorado records: {len(observed_parents)}")
print(f"Alignment records audited: {len(record_rows)}")
PY_EOF

echo
echo "Parent-level target audit:"
column -t -s $'\t' "$PARENT_AUDIT"

echo
echo "[8/10] Calculating clean target counts"

EXPECTED_PARENTS="$(
    awk 'NF {n++} END {print n+0}' "$EXPECTED_IDS"
)"

DORADO_PARENTS="$(
    awk -F '\t' '
        NR > 1 && $4 != "NO_DORADO_RECORD" {
            n++
        }
        END {print n+0}
    ' "$PARENT_AUDIT"
)"

count_parent_status() {
    local requested="$1"

    awk -F '\t' -v status="$requested" '
        NR > 1 && $4 == status {
            n++
        }
        END {print n+0}
    ' "$PARENT_AUDIT"
}

PARENT_ALT="$(count_parent_status ALT)"
PARENT_REF="$(count_parent_status REF)"
PARENT_DEL="$(count_parent_status DEL)"
PARENT_OTHER="$(count_parent_status OTHER)"
PARENT_NO_COVERAGE="$(count_parent_status NO_COVERAGE)"
PARENT_UNMAPPED="$(count_parent_status UNMAPPED)"
PARENT_NO_RECORD="$(count_parent_status NO_DORADO_RECORD)"

count_record_status() {
    local requested="$1"

    awk -F '\t' -v status="$requested" '
        NR > 1 && $13 == status {
            n++
        }
        END {print n+0}
    ' "$RECORD_AUDIT"
}

RECORD_ALT="$(count_record_status ALT)"
RECORD_REF="$(count_record_status REF)"
RECORD_DEL="$(count_record_status DEL)"
RECORD_OTHER="$(count_record_status OTHER)"
RECORD_NO_COVERAGE="$(count_record_status NO_COVERAGE)"
RECORD_UNMAPPED="$(count_record_status UNMAPPED)"

echo "Parent ALT: $PARENT_ALT"
echo "Parent REF: $PARENT_REF"
echo "Parent DEL: $PARENT_DEL"
echo "Parent OTHER: $PARENT_OTHER"
echo "Parent NO_COVERAGE: $PARENT_NO_COVERAGE"
echo "Parent UNMAPPED: $PARENT_UNMAPPED"
echo "Parent NO_DORADO_RECORD: $PARENT_NO_RECORD"

echo
echo "[9/10] Creating clean baseline summary"

{
    echo "A3 F11 Clean Dorado Rebasecalling Summary"
    echo "=========================================="
    echo
    echo "Completed: $(date -Is)"
    echo
    echo "Target: chr4:186274193 G>T"
    echo
    echo "Input raw-signal reads: $EXPECTED_PARENTS"
    echo "Dorado BAM records: $RAW_RECORDS"
    echo "FASTQ reads: $FASTQ_READS"
    echo "Total alignment records: $TOTAL_ALIGNMENT_RECORDS"
    echo "Mapped alignment records: $MAPPED_RECORDS"
    echo "Primary mapped records: $PRIMARY_MAPPED_RECORDS"
    echo
    echo "Parent-level clean target states:"
    echo "ALT: $PARENT_ALT"
    echo "REF: $PARENT_REF"
    echo "DEL: $PARENT_DEL"
    echo "OTHER: $PARENT_OTHER"
    echo "NO_COVERAGE: $PARENT_NO_COVERAGE"
    echo "UNMAPPED: $PARENT_UNMAPPED"
    echo "NO_DORADO_RECORD: $PARENT_NO_RECORD"
    echo
    echo "Record-level clean target states:"
    echo "ALT: $RECORD_ALT"
    echo "REF: $RECORD_REF"
    echo "DEL: $RECORD_DEL"
    echo "OTHER: $RECORD_OTHER"
    echo "NO_COVERAGE: $RECORD_NO_COVERAGE"
    echo "UNMAPPED: $RECORD_UNMAPPED"
    echo
    echo "Input-data limitation:"
    echo "15 of 17 original aligned ALT parents were recoverable"
    echo "as validated public raw-signal reads."
    echo

    if [[ "$DORADO_PARENTS" -eq "$EXPECTED_PARENTS" ]] &&
       [[ "$PARENT_ALT" -gt 0 ]]; then

        echo "Overall status: CLEAN_BASELINE_VALIDATED"
    else
        echo "Overall status: CLEAN_BASELINE_REQUIRES_REVIEW"
    fi
} > "$SUMMARY"

cat "$SUMMARY"

echo
echo "[10/10] Creating completion marker"

{
    echo "Completed: $(date -Is)"
    echo "Input reads: $EXPECTED_PARENTS"
    echo "Dorado records: $RAW_RECORDS"
    echo "Parent ALT: $PARENT_ALT"
    echo "Parent REF: $PARENT_REF"
    echo "Parent DEL: $PARENT_DEL"
    echo "Parent OTHER: $PARENT_OTHER"
    echo "Parent NO_COVERAGE: $PARENT_NO_COVERAGE"
    echo "Parent UNMAPPED: $PARENT_UNMAPPED"
    echo "Summary: $SUMMARY"
    echo "Aligned BAM: $ALIGNED_BAM"
    echo "Parent audit: $PARENT_AUDIT"
} > "$COMPLETE"

rm -f "$FAILED"

echo
echo "============================================================"
echo "A3 F11 CLEAN DORADO REBASECALLING COMPLETE"
echo "============================================================"
