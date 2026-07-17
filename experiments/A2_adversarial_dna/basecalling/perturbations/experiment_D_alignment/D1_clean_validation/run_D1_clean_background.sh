#!/usr/bin/env bash

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

THREADS="$(nproc)"

REFERENCE_DIR="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB"
REFERENCE_NAME="GCA_000001405.15_GRCh38_no_alt_analysis_set"

REFERENCE_GZ="$REFERENCE_DIR/${REFERENCE_NAME}.fasta.gz"
REFERENCE_FASTA="$REFERENCE_DIR/${REFERENCE_NAME}.fasta"
REFERENCE_MMI="$REFERENCE_DIR/${REFERENCE_NAME}.map-ont.mmi"

CLEAN_BAM="$HOME/datasets/GenoPhylax/A2_signal_perturbations/gaussian_noise_1000reads/basecalls/hg002_1000reads_clean_hac_parent_normalized.bam"

EXP_D_DIR="$HOME/Project-GenoPhylax/experiments/A2_adversarial_dna/basecalling/perturbations/experiment_D_alignment"
D1_DIR="$EXP_D_DIR/D1_clean_validation"

FASTQ_DIR="$D1_DIR/fastq"
ALIGN_DIR="$D1_DIR/alignments"
LOG_DIR="$D1_DIR/logs"
METRICS_DIR="$D1_DIR/metrics"

CLEAN_FASTQ="$FASTQ_DIR/hg002_1000reads_clean.fastq"
CLEAN_ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_clean_GRCh38.sorted.bam"

REFERENCE_INDEX_LOG="$LOG_DIR/reference_minimap2_index.log"
CLEAN_FASTQ_LOG="$LOG_DIR/hg002_1000reads_clean_fastq.log"
CLEAN_ALIGN_LOG="$LOG_DIR/hg002_1000reads_clean_minimap2.log"

CLEAN_FLAGSTAT="$METRICS_DIR/hg002_1000reads_clean_flagstat.txt"
CLEAN_STATS="$METRICS_DIR/hg002_1000reads_clean_stats.txt"
CLEAN_IDXSTATS="$METRICS_DIR/hg002_1000reads_clean_idxstats.txt"
D1_SUMMARY="$METRICS_DIR/experiment_D1_clean_alignment_summary.txt"

COMPLETE_FILE="$D1_DIR/D1_CLEAN_VALIDATION_COMPLETE"
FAILED_FILE="$D1_DIR/D1_CLEAN_VALIDATION_FAILED"

mkdir -p \
    "$FASTQ_DIR" \
    "$ALIGN_DIR" \
    "$LOG_DIR" \
    "$METRICS_DIR"

rm -f "$FAILED_FILE"

trap '
    STATUS=$?
    echo
    echo "============================================================"
    echo "D1 background pipeline failed with exit status: $STATUS"
    echo "Time: $(date --iso-8601=seconds)"
    echo "============================================================"
    touch "$FAILED_FILE"
    exit "$STATUS"
' ERR

echo "============================================================"
echo "Experiment D1 background pipeline started"
echo "Time: $(date --iso-8601=seconds)"
echo "Threads: $THREADS"
echo "============================================================"
echo

echo "[1/10] Validating tools and inputs"
echo "------------------------------------------------------------"

for TOOL in minimap2 samtools gzip awk sort uniq cut grep; do
    if ! command -v "$TOOL" >/dev/null 2>&1; then
        echo "ERROR: Missing required tool: $TOOL"
        exit 1
    fi
done

if [[ ! -s "$REFERENCE_GZ" ]]; then
    echo "ERROR: Compressed reference not found:"
    echo "$REFERENCE_GZ"
    exit 1
fi

if ! gzip -t "$REFERENCE_GZ"; then
    echo "ERROR: Compressed reference failed gzip validation."
    exit 1
fi

if [[ ! -s "$CLEAN_BAM" ]]; then
    echo "ERROR: CLEAN normalized BAM not found:"
    echo "$CLEAN_BAM"
    exit 1
fi

echo "Input validation: PASS"
echo

echo "[2/10] Decompressing reference"
echo "------------------------------------------------------------"

if [[ -s "$REFERENCE_FASTA" ]]; then
    echo "Existing uncompressed FASTA found:"
    ls -lh "$REFERENCE_FASTA"
else
    rm -f "${REFERENCE_FASTA}.tmp"

    gzip -cd "$REFERENCE_GZ" > "${REFERENCE_FASTA}.tmp"

    if [[ ! -s "${REFERENCE_FASTA}.tmp" ]]; then
        echo "ERROR: Temporary decompressed FASTA is empty."
        exit 1
    fi

    mv "${REFERENCE_FASTA}.tmp" "$REFERENCE_FASTA"
fi

echo "Reference FASTA:"
ls -lh "$REFERENCE_FASTA"

echo
echo "Reference records:"
grep -c '^>' "$REFERENCE_FASTA"
echo

echo "[3/10] Validating contig naming"
echo "------------------------------------------------------------"

for CHROM in chr1 chr2 chr20 chrX chrY chrM; do
    if grep -q "^>${CHROM}\([[:space:]]\|$\)" "$REFERENCE_FASTA"; then
        echo "$CHROM FOUND"
    else
        echo "ERROR: $CHROM not found."
        exit 1
    fi
done

echo "Contig validation: PASS"
echo

echo "[4/10] Building samtools FASTA index"
echo "------------------------------------------------------------"

if [[ -s "${REFERENCE_FASTA}.fai" ]]; then
    echo "Existing FASTA index found:"
    ls -lh "${REFERENCE_FASTA}.fai"
else
    samtools faidx "$REFERENCE_FASTA"
fi

if [[ ! -s "${REFERENCE_FASTA}.fai" ]]; then
    echo "ERROR: FASTA index creation failed."
    exit 1
fi

echo "Indexed sequences:"
wc -l "${REFERENCE_FASTA}.fai"
echo

echo "[5/10] Building minimap2 map-ont index"
echo "------------------------------------------------------------"

if [[ -s "$REFERENCE_MMI" ]]; then
    echo "Existing minimap2 index found:"
    ls -lh "$REFERENCE_MMI"
else
    rm -f "${REFERENCE_MMI}.tmp"

    minimap2 \
        -x map-ont \
        -d "${REFERENCE_MMI}.tmp" \
        "$REFERENCE_FASTA" \
        2> "$REFERENCE_INDEX_LOG"

    if [[ ! -s "${REFERENCE_MMI}.tmp" ]]; then
        echo "ERROR: Temporary minimap2 index is empty."
        exit 1
    fi

    mv "${REFERENCE_MMI}.tmp" "$REFERENCE_MMI"
fi

echo "minimap2 index:"
ls -lh "$REFERENCE_MMI"

echo
echo "Index log tail:"
tail -30 "$REFERENCE_INDEX_LOG" 2>/dev/null || true
echo

echo "[6/10] Converting CLEAN BAM to FASTQ"
echo "------------------------------------------------------------"

if [[ -s "$CLEAN_FASTQ" ]]; then
    EXISTING_LINES="$(wc -l < "$CLEAN_FASTQ")"

    if [[ "$EXISTING_LINES" -eq 4000 ]]; then
        echo "Existing valid CLEAN FASTQ found."
    else
        echo "Existing FASTQ has unexpected line count; rebuilding."
        rm -f "$CLEAN_FASTQ"
    fi
fi

if [[ ! -s "$CLEAN_FASTQ" ]]; then
    rm -f "${CLEAN_FASTQ}.tmp"

    samtools fastq \
        -@ "$THREADS" \
        -n \
        "$CLEAN_BAM" \
        > "${CLEAN_FASTQ}.tmp" \
        2> "$CLEAN_FASTQ_LOG"

    mv "${CLEAN_FASTQ}.tmp" "$CLEAN_FASTQ"
fi

FASTQ_LINES="$(wc -l < "$CLEAN_FASTQ")"
FASTQ_READS=$((FASTQ_LINES / 4))

FASTQ_UNIQUE_IDS="$(
    awk 'NR % 4 == 1 {
        sub(/^@/, "", $1)
        print $1
    }' "$CLEAN_FASTQ" |
    sort -u |
    wc -l
)"

echo "FASTQ lines:      $FASTQ_LINES"
echo "FASTQ reads:      $FASTQ_READS"
echo "Unique read IDs:  $FASTQ_UNIQUE_IDS"

if [[ "$FASTQ_LINES" -ne 4000 ]]; then
    echo "ERROR: Expected 4,000 FASTQ lines."
    exit 1
fi

if [[ "$FASTQ_READS" -ne 1000 ]]; then
    echo "ERROR: Expected 1,000 FASTQ reads."
    exit 1
fi

if [[ "$FASTQ_UNIQUE_IDS" -ne 1000 ]]; then
    echo "ERROR: Expected 1,000 unique FASTQ IDs."
    exit 1
fi

echo "FASTQ validation: PASS"
echo

echo "[7/10] Aligning CLEAN reads"
echo "------------------------------------------------------------"

if [[ -s "$CLEAN_ALIGN_BAM" ]] &&
   [[ -s "${CLEAN_ALIGN_BAM}.bai" ]] &&
   samtools quickcheck "$CLEAN_ALIGN_BAM" 2>/dev/null; then

    echo "Existing valid CLEAN aligned BAM found:"
    ls -lh "$CLEAN_ALIGN_BAM" "${CLEAN_ALIGN_BAM}.bai"
else
    rm -f \
        "$CLEAN_ALIGN_BAM" \
        "${CLEAN_ALIGN_BAM}.bai" \
        "${CLEAN_ALIGN_BAM}.tmp"

    minimap2 \
        -a \
        -x map-ont \
        --MD \
        -t "$THREADS" \
        -R '@RG\tID:HG002_CLEAN\tSM:HG002\tPL:ONT\tLB:HG002_1000reads' \
        "$REFERENCE_MMI" \
        "$CLEAN_FASTQ" \
        2> "$CLEAN_ALIGN_LOG" |
    samtools sort \
        -@ "$THREADS" \
        -o "${CLEAN_ALIGN_BAM}.tmp" \
        -

    mv "${CLEAN_ALIGN_BAM}.tmp" "$CLEAN_ALIGN_BAM"

    samtools index \
        -@ "$THREADS" \
        "$CLEAN_ALIGN_BAM"
fi

echo "Aligned BAM:"
ls -lh "$CLEAN_ALIGN_BAM" "${CLEAN_ALIGN_BAM}.bai"

echo
echo "Alignment log tail:"
tail -40 "$CLEAN_ALIGN_LOG" 2>/dev/null || true
echo

echo "[8/10] Validating aligned BAM"
echo "------------------------------------------------------------"

samtools quickcheck -v "$CLEAN_ALIGN_BAM"

TOTAL_RECORDS="$(samtools view -c "$CLEAN_ALIGN_BAM")"
PRIMARY_RECORDS="$(samtools view -c -F 2304 "$CLEAN_ALIGN_BAM")"

UNIQUE_PRIMARY_IDS="$(
    samtools view -F 2304 "$CLEAN_ALIGN_BAM" |
    cut -f1 |
    sort -u |
    wc -l
)"

DUPLICATE_PRIMARY_IDS="$(
    samtools view -F 2304 "$CLEAN_ALIGN_BAM" |
    cut -f1 |
    sort |
    uniq -d |
    wc -l
)"

echo "Total alignment records:  $TOTAL_RECORDS"
echo "Primary records:          $PRIMARY_RECORDS"
echo "Unique primary IDs:       $UNIQUE_PRIMARY_IDS"
echo "Duplicate primary IDs:    $DUPLICATE_PRIMARY_IDS"

if [[ "$PRIMARY_RECORDS" -ne 1000 ]]; then
    echo "ERROR: Expected 1,000 primary records."
    exit 1
fi

if [[ "$UNIQUE_PRIMARY_IDS" -ne 1000 ]]; then
    echo "ERROR: Expected 1,000 unique primary IDs."
    exit 1
fi

if [[ "$DUPLICATE_PRIMARY_IDS" -ne 0 ]]; then
    echo "ERROR: Duplicate primary records detected."
    exit 1
fi

echo "Aligned BAM validation: PASS"
echo

echo "[9/10] Generating CLEAN alignment metrics"
echo "------------------------------------------------------------"

samtools flagstat \
    -@ "$THREADS" \
    "$CLEAN_ALIGN_BAM" \
    > "$CLEAN_FLAGSTAT"

samtools stats \
    -@ "$THREADS" \
    "$CLEAN_ALIGN_BAM" \
    > "$CLEAN_STATS"

samtools idxstats \
    "$CLEAN_ALIGN_BAM" \
    > "$CLEAN_IDXSTATS"

MAPPED_PRIMARY="$(samtools view -c -F 2308 "$CLEAN_ALIGN_BAM")"
UNMAPPED_PRIMARY="$(samtools view -c -f 4 -F 2304 "$CLEAN_ALIGN_BAM")"
SECONDARY_COUNT="$(samtools view -c -f 256 "$CLEAN_ALIGN_BAM")"
SUPPLEMENTARY_COUNT="$(samtools view -c -f 2048 "$CLEAN_ALIGN_BAM")"

MAPQ_GE_20="$(samtools view -c -F 2308 -q 20 "$CLEAN_ALIGN_BAM")"
MAPQ_GE_30="$(samtools view -c -F 2308 -q 30 "$CLEAN_ALIGN_BAM")"
MAPQ_GE_60="$(samtools view -c -F 2308 -q 60 "$CLEAN_ALIGN_BAM")"

MAPPED_PERCENT="$(
    awk \
        -v mapped="$MAPPED_PRIMARY" \
        -v total="$PRIMARY_RECORDS" \
        'BEGIN {
            if (total == 0) {
                print "0.000000"
            } else {
                printf "%.6f", 100 * mapped / total
            }
        }'
)"

MEAN_MAPQ="$(
    samtools view -F 2308 "$CLEAN_ALIGN_BAM" |
    awk '
        {
            sum += $5
            count++
        }
        END {
            if (count == 0) {
                print "NA"
            } else {
                printf "%.6f", sum / count
            }
        }
    '
)"

{
    echo "Experiment D1 — CLEAN alignment validation"
    echo
    echo "Reference assembly:"
    echo "$REFERENCE_NAME"
    echo
    echo "Reference FASTA:"
    echo "$REFERENCE_FASTA"
    echo
    echo "Aligner:"
    echo "minimap2 $(minimap2 --version)"
    echo
    echo "Preset:"
    echo "map-ont"
    echo
    echo "Input reads:"
    echo "$FASTQ_READS"
    echo
    echo "Total alignment records:"
    echo "$TOTAL_RECORDS"
    echo
    echo "Primary records:"
    echo "$PRIMARY_RECORDS"
    echo
    echo "Mapped primary reads:"
    echo "$MAPPED_PRIMARY"
    echo
    echo "Unmapped primary reads:"
    echo "$UNMAPPED_PRIMARY"
    echo
    echo "Mapped primary percentage:"
    echo "$MAPPED_PERCENT"
    echo
    echo "Secondary alignments:"
    echo "$SECONDARY_COUNT"
    echo
    echo "Supplementary alignments:"
    echo "$SUPPLEMENTARY_COUNT"
    echo
    echo "Mean mapped primary MAPQ:"
    echo "$MEAN_MAPQ"
    echo
    echo "Mapped primary reads with MAPQ >=20:"
    echo "$MAPQ_GE_20"
    echo
    echo "Mapped primary reads with MAPQ >=30:"
    echo "$MAPQ_GE_30"
    echo
    echo "Mapped primary reads with MAPQ >=60:"
    echo "$MAPQ_GE_60"
    echo
    echo "Unique primary IDs:"
    echo "$UNIQUE_PRIMARY_IDS"
    echo
    echo "Duplicate primary IDs:"
    echo "$DUPLICATE_PRIMARY_IDS"
} > "$D1_SUMMARY"

cat "$D1_SUMMARY"

echo
echo "samtools flagstat:"
cat "$CLEAN_FLAGSTAT"

echo
echo "Top reference sequences by mapped count:"
sort -k3,3nr "$CLEAN_IDXSTATS" |
awk '$3 > 0' |
head -20
echo

echo "[10/10] Final validation"
echo "------------------------------------------------------------"

[[ -s "$REFERENCE_FASTA" ]]
[[ -s "${REFERENCE_FASTA}.fai" ]]
[[ -s "$REFERENCE_MMI" ]]
[[ -s "$CLEAN_FASTQ" ]]
[[ -s "$CLEAN_ALIGN_BAM" ]]
[[ -s "${CLEAN_ALIGN_BAM}.bai" ]]
[[ "$FASTQ_READS" -eq 1000 ]]
[[ "$UNIQUE_PRIMARY_IDS" -eq 1000 ]]
[[ "$DUPLICATE_PRIMARY_IDS" -eq 0 ]]

rm -f "$FAILED_FILE"
touch "$COMPLETE_FILE"

echo "Experiment D1 validation: PASS"
echo "Completion marker:"
ls -l "$COMPLETE_FILE"

echo
echo "============================================================"
echo "Experiment D1 CLEAN alignment completed successfully"
echo "Time: $(date --iso-8601=seconds)"
echo "============================================================"
