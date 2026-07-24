#!/usr/bin/env bash

set -Eeuo pipefail

cd "/home/admin/Project-GenoPhylax"

source experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

CROSS_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication"
PYTHON="/home/admin/Project-GenoPhylax/experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/python"

DORADO="/home/admin/tools/dorado/dorado-2.1.0-linux-arm64-cuda-13.0/bin/dorado"
MODEL="/home/admin/tools/dorado/models/dna_r10.4.1_e8.2_400bps_hac@v6.0.0"
REFERENCE_MMI="/home/admin/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.map-ont.mmi"

SHAM_SCRIPT="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/scripts/generate_cross_locus_off_target_sham.py"
ANALYSIS_SCRIPT="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/scripts/analyze_cross_locus_W0_target_effect.py"

POD5_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_pod5/OFF_TARGET_SHAM"
BASECALL_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_basecalls/OFF_TARGET_SHAM"
ALIGN_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_alignments/OFF_TARGET_SHAM"
VALIDATION_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/discovery/validation/OFF_TARGET_SHAM"
RESULT_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/results/OFF_TARGET_SHAM_target_effect"
LOG_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/logs"
MARKER_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers"

COMPLETE="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_OFF_TARGET_SHAM.COMPLETE"
FAILED="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_OFF_TARGET_SHAM.FAILED"

trap '
    STATUS=$?
    echo
    echo "OFF-TARGET SHAM FAILED: $STATUS"
    echo "Time: $(date)"
    touch "$FAILED"
    exit $STATUS
' ERR

rm -f "$FAILED"

echo "============================================================"
echo "CROSS-LOCUS OFF-TARGET SHAM CONTROL"
echo "Started: $(date)"
echo "============================================================"

###############################################################################
# Stage 1 — Generate sham POD5
###############################################################################

STAGE1="$MARKER_DIR/OFF_TARGET_SHAM_GENERATION.COMPLETE"

if [[ -e "$STAGE1" ]]    && [[ -s "$POD5_DIR/L2_chr1_20061156_A_T.SHAM.pod5" ]]    && [[ -s "$POD5_DIR/L3_chr4_40028853_A_G.SHAM.pod5" ]]    && [[ -s "$VALIDATION_DIR/OFF_TARGET_SHAM_summary.tsv" ]]
then
    echo
    echo "STAGE 1 already complete."
else
    echo
    echo "============================================================"
    echo "STAGE 1 — SHAM SIGNAL GENERATION"
    echo "============================================================"

    rm -f       "$POD5_DIR/L2_chr1_20061156_A_T.SHAM.pod5"       "$POD5_DIR/L3_chr4_40028853_A_G.SHAM.pod5"       "$VALIDATION_DIR/OFF_TARGET_SHAM_audit.tsv"       "$VALIDATION_DIR/OFF_TARGET_SHAM_summary.tsv"       "$STAGE1"

    "$PYTHON" "$SHAM_SCRIPT"       --windows-tsv         "$CROSS_DIR/signal_windows/clean_target_signal_windows.tsv"       --l2-pod5         "$CROSS_DIR/target_pod5/L2_chr1_20061156_A_T.pod5"       --l2-bam         "$CROSS_DIR/clean_basecalls/L2_chr1_20061156_A_T.clean.bam"       --l2-output         "$POD5_DIR/L2_chr1_20061156_A_T.SHAM.pod5"       --l3-pod5         "$CROSS_DIR/target_pod5/L3_chr4_40028853_A_G.pod5"       --l3-bam         "$CROSS_DIR/clean_basecalls/L3_chr4_40028853_A_G.clean.bam"       --l3-output         "$POD5_DIR/L3_chr4_40028853_A_G.SHAM.pod5"       --audit-tsv         "$VALIDATION_DIR/OFF_TARGET_SHAM_audit.tsv"       --summary-tsv         "$VALIDATION_DIR/OFF_TARGET_SHAM_summary.tsv"       --context-bases 5       --offset-bases 20

    touch "$STAGE1"
fi

###############################################################################
# Stage 2 — Dorado
###############################################################################

STAGE2="$MARKER_DIR/OFF_TARGET_SHAM_DORADO.COMPLETE"

if [[ -e "$STAGE2" ]]    && [[ "$(samtools view -c "$BASECALL_DIR/L2_chr1_20061156_A_T.SHAM.bam" 2>/dev/null)" -eq 10 ]]    && [[ "$(samtools view -c "$BASECALL_DIR/L3_chr4_40028853_A_G.SHAM.bam" 2>/dev/null)" -eq 10 ]]
then
    echo
    echo "STAGE 2 already complete."
else
    echo
    echo "============================================================"
    echo "STAGE 2 — DORADO BASECALLING"
    echo "============================================================"

    rm -f       "$BASECALL_DIR/L2_chr1_20061156_A_T.SHAM.bam"       "$BASECALL_DIR/L3_chr4_40028853_A_G.SHAM.bam"       "$STAGE2"

    "$DORADO" basecaller       "$MODEL"       "$POD5_DIR/L2_chr1_20061156_A_T.SHAM.pod5"       --device cuda:all       --emit-moves       > "$BASECALL_DIR/L2_chr1_20061156_A_T.SHAM.bam"       2> "$LOG_DIR/L2_OFF_TARGET_SHAM_dorado.log"

    "$DORADO" basecaller       "$MODEL"       "$POD5_DIR/L3_chr4_40028853_A_G.SHAM.pod5"       --device cuda:all       --emit-moves       > "$BASECALL_DIR/L3_chr4_40028853_A_G.SHAM.bam"       2> "$LOG_DIR/L3_OFF_TARGET_SHAM_dorado.log"

    [[ "$(samtools view -c "$BASECALL_DIR/L2_chr1_20061156_A_T.SHAM.bam")" -eq 10 ]]
    [[ "$(samtools view -c "$BASECALL_DIR/L3_chr4_40028853_A_G.SHAM.bam")" -eq 10 ]]

    touch "$STAGE2"
fi

###############################################################################
# Stage 3 — Alignment
###############################################################################

STAGE3="$MARKER_DIR/OFF_TARGET_SHAM_ALIGNMENT.COMPLETE"

align_one() {
    local LOCUS="$1"
    local INPUT_BAM="$2"
    local OUTPUT_BAM="$3"
    local ALIGN_LOG="$4"

    local FASTQ="$ALIGN_DIR/${LOCUS}.SHAM.fastq"
    local UNSORTED="$ALIGN_DIR/${LOCUS}.SHAM.unsorted.bam"

    if [[ -s "$OUTPUT_BAM" ]]        && [[ -s "$OUTPUT_BAM.bai" ]]        && samtools quickcheck -v "$OUTPUT_BAM"        && [[ "$(samtools view -c -F 2304 "$OUTPUT_BAM")" -eq 10 ]]
    then
        echo "$LOCUS alignment already valid."
        return
    fi

    rm -f       "$FASTQ"       "$UNSORTED"       "$OUTPUT_BAM"       "$OUTPUT_BAM.bai"

    samtools fastq       -0 "$FASTQ"       -s /dev/null       -n       "$INPUT_BAM"       2> "$LOG_DIR/${LOCUS}_OFF_TARGET_SHAM_fastq.log"

    minimap2       -ax map-ont       --MD       -t 12       "$REFERENCE_MMI"       "$FASTQ"       2> "$ALIGN_LOG"     | samtools view -b -o "$UNSORTED" -

    samtools sort       -@ 8       -o "$OUTPUT_BAM"       "$UNSORTED"

    samtools index "$OUTPUT_BAM"
    samtools quickcheck -v "$OUTPUT_BAM"

    [[ "$(samtools view -c -F 2304 "$OUTPUT_BAM")" -eq 10 ]]
    [[ "$(samtools view -c -F 4 "$OUTPUT_BAM")" -ge 10 ]]

    rm -f "$FASTQ" "$UNSORTED"
}

if [[ -e "$STAGE3" ]]    && [[ -s "$ALIGN_DIR/L2_chr1_20061156_A_T.SHAM.aligned.sorted.bam" ]]    && [[ -s "$ALIGN_DIR/L3_chr4_40028853_A_G.SHAM.aligned.sorted.bam" ]]
then
    echo
    echo "STAGE 3 already complete."
else
    echo
    echo "============================================================"
    echo "STAGE 3 — ALIGNMENT"
    echo "============================================================"

    rm -f "$STAGE3"

    align_one       "L2_chr1_20061156_A_T"       "$BASECALL_DIR/L2_chr1_20061156_A_T.SHAM.bam"       "$ALIGN_DIR/L2_chr1_20061156_A_T.SHAM.aligned.sorted.bam"       "$LOG_DIR/L2_OFF_TARGET_SHAM_alignment.log"

    align_one       "L3_chr4_40028853_A_G"       "$BASECALL_DIR/L3_chr4_40028853_A_G.SHAM.bam"       "$ALIGN_DIR/L3_chr4_40028853_A_G.SHAM.aligned.sorted.bam"       "$LOG_DIR/L3_OFF_TARGET_SHAM_alignment.log"

    touch "$STAGE3"
fi

###############################################################################
# Stage 4 — True-target state analysis
###############################################################################

STAGE4="$MARKER_DIR/OFF_TARGET_SHAM_TARGET_EFFECT.COMPLETE"

if [[ -e "$STAGE4" ]]    && [[ -s "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_summary.tsv" ]]    && [[ -s "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_per_read.tsv" ]]
then
    echo
    echo "STAGE 4 already complete."
else
    echo
    echo "============================================================"
    echo "STAGE 4 — TRUE-TARGET STATE ANALYSIS"
    echo "============================================================"

    rm -f       "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_summary.tsv"       "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_per_read.tsv"       "$STAGE4"

    "$PYTHON" "$ANALYSIS_SCRIPT"       --l2-clean         "$CROSS_DIR/clean_alignments/L2_chr1_20061156_A_T.clean.aligned.sorted.bam"       --l2-w0         "$ALIGN_DIR/L2_chr1_20061156_A_T.SHAM.aligned.sorted.bam"       --l3-clean         "$CROSS_DIR/clean_alignments/L3_chr4_40028853_A_G.clean.aligned.sorted.bam"       --l3-w0         "$ALIGN_DIR/L3_chr4_40028853_A_G.SHAM.aligned.sorted.bam"       --per-read         "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_per_read.tsv"       --summary         "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_summary.tsv"

    test -s       "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_summary.tsv"

    test -s       "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_per_read.tsv"

    touch "$STAGE4"
fi

###############################################################################
# Final validation
###############################################################################

echo
echo "============================================================"
echo "FINAL OFF-TARGET SHAM VALIDATION"
echo "============================================================"

"$PYTHON" - <<PY
import csv
from pathlib import Path

generation = Path(
    "$VALIDATION_DIR/OFF_TARGET_SHAM_summary.tsv"
)

target_effect = Path(
    "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_summary.tsv"
)

with generation.open(
    newline="",
    encoding="utf-8",
) as handle:
    generation_rows = list(
        csv.DictReader(
            handle,
            delimiter="\t",
        )
    )

assert len(generation_rows) == 2

for row in generation_rows:
    assert row["context_bases"] == "5", row
    assert row["offset_bases"] == "20", row
    assert row["reads_processed"] == "10", row
    assert row["reads_passed"] == "10", row
    assert row["sham_base_events_per_read"] == "11", row
    assert row["target_overlap_reads"] == "0", row
    assert row["outside_changed_samples"] == "0", row
    assert row["status"] == "PASS", row

with target_effect.open(
    newline="",
    encoding="utf-8",
) as handle:
    effect_rows = list(
        csv.DictReader(
            handle,
            delimiter="\t",
        )
    )

assert len(effect_rows) == 2

for row in effect_rows:
    assert row["clean_parent_count"] == "10", row
    assert row["attacked_parent_count"] == "10", row
    assert row["clean_alt_parent_count"] == "10", row

print("Off-target sham validation: PASS")
PY

echo
echo "===== SIGNAL GENERATION ====="
column -t -s $'\t'   "$VALIDATION_DIR/OFF_TARGET_SHAM_summary.tsv"

echo
echo "===== TRUE-TARGET EFFECT ====="
column -t -s $'\t'   "$RESULT_DIR/OFF_TARGET_SHAM_clean_vs_attacked_summary.tsv"

echo
echo "===== ALIGNMENT ====="

for BAM in   "$ALIGN_DIR/L2_chr1_20061156_A_T.SHAM.aligned.sorted.bam"   "$ALIGN_DIR/L3_chr4_40028853_A_G.SHAM.aligned.sorted.bam"
do
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
echo "============================================================"
echo "OFF-TARGET SHAM CONTROL: COMPLETE"
echo "Finished: $(date)"
echo "============================================================"
