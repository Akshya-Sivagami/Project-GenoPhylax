#!/usr/bin/env bash

set -Eeuo pipefail

cd "/home/admin/Project-GenoPhylax"

DORADO="/home/admin/tools/dorado/dorado-2.1.0-linux-arm64-cuda-13.0/bin/dorado"
MODEL="/home/admin/tools/dorado/models/dna_r10.4.1_e8.2_400bps_hac@v6.0.0"

INPUT_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_pod5/W0"
OUTPUT_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_basecalls/W0"
LOG_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/logs"

COMPLETE="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_W0_DORADO.COMPLETE"
FAILED="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_W0_DORADO.FAILED"

trap '
    STATUS=$?
    echo
    echo "W0 Dorado failed with exit status $STATUS"
    date
    touch "$FAILED"
    exit $STATUS
' ERR

rm -f "$FAILED"

run_condition() {
    local LABEL="$1"
    local INPUT_POD5="$2"
    local OUTPUT_BAM="$3"
    local CONDITION_LOG="$4"
    local CONDITION_MARKER="$5"

    echo
    echo "============================================================"
    echo "$LABEL"
    echo "Started: $(date)"
    echo "============================================================"

    if [[ -s "$OUTPUT_BAM" ]]        && samtools view -H "$OUTPUT_BAM" >/dev/null 2>&1        && [[ "$(samtools view -c "$OUTPUT_BAM")" -ge 10 ]]
    then
        echo "Existing valid output found; skipping."
        touch "$CONDITION_MARKER"
        return
    fi

    rm -f "$OUTPUT_BAM" "$CONDITION_MARKER"

    "$DORADO" basecaller         "$MODEL"         "$INPUT_POD5"         --device cuda:all         --emit-moves         > "$OUTPUT_BAM"         2> "$CONDITION_LOG"

    samtools view -H "$OUTPUT_BAM" >/dev/null

    RECORDS=$(samtools view -c "$OUTPUT_BAM")

    echo "Output records: $RECORDS"

    [[ "$RECORDS" -ge 10 ]] || {
        echo "ERROR: Expected at least 10 records."
        exit 1
    }

    touch "$CONDITION_MARKER"

    echo "$LABEL: PASS"
}

run_condition     "L2 W0 DORADO"     "$INPUT_DIR/L2_chr1_20061156_A_T.W0.pod5"     "$OUTPUT_DIR/L2_chr1_20061156_A_T.W0.bam"     "$LOG_DIR/L2_W0_dorado.log"     "$OUTPUT_DIR/L2_W0_DORADO.COMPLETE"

run_condition     "L3 W0 DORADO"     "$INPUT_DIR/L3_chr4_40028853_A_G.W0.pod5"     "$OUTPUT_DIR/L3_chr4_40028853_A_G.W0.bam"     "$LOG_DIR/L3_W0_dorado.log"     "$OUTPUT_DIR/L3_W0_DORADO.COMPLETE"

echo
echo "============================================================"
echo "FINAL VALIDATION"
echo "============================================================"

for BAM in     "$OUTPUT_DIR/L2_chr1_20061156_A_T.W0.bam"     "$OUTPUT_DIR/L3_chr4_40028853_A_G.W0.bam"
do
    samtools view -H "$BAM" >/dev/null
    echo "$BAM"
    echo "  records: $(samtools view -c "$BAM")"
done

rm -f "$FAILED"
touch "$COMPLETE"

echo
echo "CROSS-LOCUS W0 DORADO: COMPLETE"
echo "Finished: $(date)"
