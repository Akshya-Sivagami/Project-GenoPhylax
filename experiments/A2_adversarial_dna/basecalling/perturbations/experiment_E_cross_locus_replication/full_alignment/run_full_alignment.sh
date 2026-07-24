#!/usr/bin/env bash

set -Eeuo pipefail

cd ~/Project-GenoPhylax

source experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

NEXT_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication"
ALIGN_DIR="$NEXT_DIR/full_alignment"

INPUT_BAM="experiments/A2_adversarial_dna/basecalling/dorado/results/baseline/hg002_three_pod5_hac.bam"

REF="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"
MMI="/home/admin/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.map-ont.mmi"

FASTQ="$ALIGN_DIR/hg002_three_pod5_hac.fastq"
UNSORTED_BAM="$ALIGN_DIR/hg002_three_pod5_GRCh38.unsorted.bam"
SORTED_BAM="$ALIGN_DIR/hg002_three_pod5_GRCh38.sorted.bam"
SUMMARY="$ALIGN_DIR/full_alignment_summary.txt"
DONE="$ALIGN_DIR/FULL_ALIGNMENT.COMPLETE"

rm -f "$DONE"

echo "============================================================"
echo "FULL THREE-POD5 ALIGNMENT"
echo "Started: $(date -Is)"
echo "============================================================"

for FILE in "$INPUT_BAM" "$REF" "$MMI"; do
    [[ -s "$FILE" ]] || {
        echo "ERROR: Missing file: $FILE"
        exit 1
    }
done

echo
echo "[1/4] Extract FASTQ"

samtools fastq \
    -0 "$FASTQ" \
    -s /dev/null \
    -n \
    "$INPUT_BAM"

FASTQ_RECORDS=$(awk 'END {print NR/4}' "$FASTQ")

echo "FASTQ records: $FASTQ_RECORDS"

[[ "$FASTQ_RECORDS" -gt 12000 ]] || {
    echo "ERROR: Too few FASTQ records"
    exit 1
}

echo
echo "[2/4] Align with minimap2"

minimap2 \
    -ax map-ont \
    -t 16 \
    "$MMI" \
    "$FASTQ" \
| samtools view \
    -@ 4 \
    -b \
    -o "$UNSORTED_BAM" -

echo
echo "[3/4] Sort and index"

samtools sort \
    -@ 8 \
    -o "$SORTED_BAM" \
    "$UNSORTED_BAM"

samtools index \
    -@ 4 \
    "$SORTED_BAM"

echo
echo "[4/4] Validate"

TOTAL=$(samtools view -c "$SORTED_BAM")
PRIMARY=$(samtools view -c -F 2304 "$SORTED_BAM")
MAPPED_PRIMARY=$(samtools view -c -F 2308 "$SORTED_BAM")
UNMAPPED_PRIMARY=$(samtools view -c -f 4 -F 2304 "$SORTED_BAM")

MAPPED_PERCENT=$(
    awk -v mapped="$MAPPED_PRIMARY" -v primary="$PRIMARY" \
        'BEGIN {printf "%.4f", 100*mapped/primary}'
)

{
    echo "input_bam=$INPUT_BAM"
    echo "fastq_records=$FASTQ_RECORDS"
    echo "total_alignment_records=$TOTAL"
    echo "primary_records=$PRIMARY"
    echo "mapped_primary=$MAPPED_PRIMARY"
    echo "unmapped_primary=$UNMAPPED_PRIMARY"
    echo "mapped_primary_percent=$MAPPED_PERCENT"
    echo "sorted_bam=$SORTED_BAM"
} > "$SUMMARY"

cat "$SUMMARY"

samtools quickcheck "$SORTED_BAM"

touch "$DONE"

echo
echo "Finished: $(date -Is)"
echo "FULL ALIGNMENT: COMPLETE"
