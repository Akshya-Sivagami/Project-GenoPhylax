#!/usr/bin/env bash

set -Eeuo pipefail

cd "/home/admin/Project-GenoPhylax"

INPUT_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_basecalls/W0"
OUTPUT_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_alignments/W0"
LOG_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/logs"
REFERENCE_MMI="/home/admin/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.map-ont.mmi"

COMPLETE="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_W0_ALIGNMENT.COMPLETE"
FAILED="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_W0_ALIGNMENT.FAILED"

trap '
    STATUS=$?
    echo
    echo "W0 alignment failed with exit status $STATUS"
    date
    touch "$FAILED"
    exit $STATUS
' ERR

rm -f "$FAILED"

align_condition() {
    local LABEL="$1"
    local INPUT_BAM="$2"
    local PREFIX="$3"
    local EXPECTED_CHROM="$4"
    local TARGET_POS="$5"

    local FASTQ="$OUTPUT_DIR/${PREFIX}.fastq"
    local UNSORTED="$OUTPUT_DIR/${PREFIX}.aligned.unsorted.bam"
    local SORTED="$OUTPUT_DIR/${PREFIX}.aligned.sorted.bam"
    local FASTQ_LOG="$LOG_DIR/${PREFIX}_samtools_fastq.log"
    local ALIGN_LOG="$LOG_DIR/${PREFIX}_alignment.log"
    local MARKER="$OUTPUT_DIR/${PREFIX}_ALIGNMENT.COMPLETE"

    echo
    echo "============================================================"
    echo "$LABEL"
    echo "Started: $(date)"
    echo "============================================================"

    if [[ -s "$SORTED" ]]        && [[ -s "$SORTED.bai" ]]        && samtools quickcheck -v "$SORTED"        && [[ "$(samtools view -c "$SORTED")" -ge 10 ]]
    then
        echo "Existing valid alignment found; skipping."
        touch "$MARKER"
        return
    fi

    rm -f         "$FASTQ"         "$UNSORTED"         "$SORTED"         "$SORTED.bai"         "$MARKER"

    samtools fastq         -0 "$FASTQ"         -s /dev/null         -n         "$INPUT_BAM"         2> "$FASTQ_LOG"

    minimap2         -ax map-ont         --MD         -t 12         "$REFERENCE_MMI"         "$FASTQ"         2> "$ALIGN_LOG"     | samtools view -b -o "$UNSORTED" -

    samtools sort         -@ 8         -o "$SORTED"         "$UNSORTED"

    samtools index "$SORTED"
    samtools quickcheck -v "$SORTED"

    TOTAL=$(samtools view -c "$SORTED")
    PRIMARY=$(samtools view -c -F 2304 "$SORTED")
    MAPPED=$(samtools view -c -F 4 "$SORTED")
    TARGET_OVERLAP=$(
        samtools view -c             "$SORTED"             "${EXPECTED_CHROM}:${TARGET_POS}-${TARGET_POS}"
    )

    echo "Total records: $TOTAL"
    echo "Primary records: $PRIMARY"
    echo "Mapped records: $MAPPED"
    echo "Target-overlapping records: $TARGET_OVERLAP"

    [[ "$PRIMARY" -eq 10 ]] || {
        echo "ERROR: Expected 10 primary records."
        exit 1
    }

    [[ "$MAPPED" -ge 10 ]] || {
        echo "ERROR: Expected all 10 reads to remain mapped."
        exit 1
    }

    touch "$MARKER"

    rm -f "$FASTQ" "$UNSORTED"

    echo "$LABEL: PASS"
}

align_condition     "L2 W0 ALIGNMENT"     "$INPUT_DIR/L2_chr1_20061156_A_T.W0.bam"     "L2_chr1_20061156_A_T.W0"     "chr1"     "20061156"

align_condition     "L3 W0 ALIGNMENT"     "$INPUT_DIR/L3_chr4_40028853_A_G.W0.bam"     "L3_chr4_40028853_A_G.W0"     "chr4"     "40028853"

echo
echo "============================================================"
echo "FINAL ALIGNMENT VALIDATION"
echo "============================================================"

for BAM in     "$OUTPUT_DIR/L2_chr1_20061156_A_T.W0.aligned.sorted.bam"     "$OUTPUT_DIR/L3_chr4_40028853_A_G.W0.aligned.sorted.bam"
do
    samtools quickcheck -v "$BAM"

    echo
    echo "$BAM"
    echo "  total: $(samtools view -c "$BAM")"
    echo "  primary: $(samtools view -c -F 2304 "$BAM")"
    echo "  mapped: $(samtools view -c -F 4 "$BAM")"
    echo "  MAPQ60 primary: $(samtools view -c -F 2304 -q 60 "$BAM")"
done

rm -f "$FAILED"
touch "$COMPLETE"

echo
echo "CROSS-LOCUS W0 ALIGNMENT: COMPLETE"
echo "Finished: $(date)"
