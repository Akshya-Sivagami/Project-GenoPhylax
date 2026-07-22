#!/usr/bin/env bash

set -Eeuo pipefail

cd ~/Project-GenoPhylax

source \
  experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

EXP_E_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_targeted_locus"
E2_DIR="$EXP_E_DIR/attacks/E2_window_strength_series"
SCRIPT_DIR="$EXP_E_DIR/scripts"

ANALYSIS_SCRIPT="$SCRIPT_DIR/analyze_E2_target_states.py"

REF="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"

TARGET_CHROM="chr20"
TARGET_POS="10003468"
TARGET_REF="C"
TARGET_ALT="G"

SUMMARY="$E2_DIR/E2_alignment_target_summary.tsv"
DONE_MARKER="$E2_DIR/E2_ALIGNMENT_TARGET_ANALYSIS.COMPLETE"

rm -f "$DONE_MARKER"

echo "============================================================"
echo "EXPERIMENT E2 — ALIGNMENT AND TARGET ANALYSIS"
echo "Started: $(date -Is)"
echo "============================================================"

command -v minimap2 >/dev/null || {
  echo "ERROR: minimap2 not found."
  exit 1
}

command -v samtools >/dev/null || {
  echo "ERROR: samtools not found."
  exit 1
}

[[ -f "$REF" ]] || {
  echo "ERROR: Reference missing:"
  echo "$REF"
  exit 1
}

[[ -f "$ANALYSIS_SCRIPT" ]] || {
  echo "ERROR: Analysis script missing:"
  echo "$ANALYSIS_SCRIPT"
  exit 1
}

printf \
"condition\tcontext_bases\tchanged_samples\tchanged_fraction\ttotal_records\tprimary_records\tmapped_records\ttarget_overlapping_records\traw_parent_count\tparent_ALT\tparent_REF\tparent_DELETION\tparent_OTHER\tparent_NO_COVERAGE\tparent_UNMAPPED\trecord_ALT\trecord_REF\trecord_DELETION\trecord_OTHER\trecord_NO_COVERAGE\trecord_UNMAPPED\tstatus\n" \
> "$SUMMARY"

run_condition() {
  CONDITION="$1"
  CONTEXT="$2"
  CHANGED_SAMPLES="$3"
  CHANGED_FRACTION="$4"

  CONDITION_DIR="$E2_DIR/$CONDITION"
  RESULT_DIR="$CONDITION_DIR/dorado_results"
  ANALYSIS_DIR="$CONDITION_DIR/target_analysis"

  UNALIGNED_BAM="$RESULT_DIR/${CONDITION}.unaligned.bam"
  FASTQ="$RESULT_DIR/${CONDITION}.fastq"
  UNSORTED_BAM="$RESULT_DIR/${CONDITION}.aligned.unsorted.bam"
  SORTED_BAM="$RESULT_DIR/${CONDITION}.aligned.sorted.bam"

  RECORDS_TSV="$ANALYSIS_DIR/${CONDITION}_target_records.tsv"
  PARENTS_TSV="$ANALYSIS_DIR/${CONDITION}_target_parents.tsv"
  CONDITION_SUMMARY="$ANALYSIS_DIR/${CONDITION}_target_summary.tsv"
  PARENT_MAP="$ANALYSIS_DIR/${CONDITION}_query_to_parent.tsv"

  COMPLETE_MARKER="$ANALYSIS_DIR/${CONDITION}_ALIGNMENT_ANALYSIS.COMPLETE"

  mkdir -p "$ANALYSIS_DIR"

  echo
  echo "------------------------------------------------------------"
  echo "Condition: $CONDITION"
  echo "------------------------------------------------------------"

  [[ -s "$UNALIGNED_BAM" ]] || {
    echo "ERROR: Missing unaligned BAM:"
    echo "$UNALIGNED_BAM"
    exit 1
  }

  if [[ -f "$COMPLETE_MARKER" ]] \
    && [[ -s "$SORTED_BAM" ]] \
    && [[ -s "$CONDITION_SUMMARY" ]]
  then
    echo "$CONDITION already complete; reusing outputs."
  else
    rm -f "$COMPLETE_MARKER"

    samtools fastq \
      -0 "$FASTQ" \
      -s /dev/null \
      -n \
      "$UNALIGNED_BAM" \
      2> "$RESULT_DIR/${CONDITION}_samtools_fastq.log"

    FASTQ_RECORDS=$(
      awk 'END {print NR/4}' "$FASTQ"
    )

    [[ "$FASTQ_RECORDS" -ge 11 ]] || {
      echo "ERROR: Too few FASTQ records for $CONDITION:"
      echo "$FASTQ_RECORDS"
      exit 1
    }

    minimap2 \
      -ax map-ont \
      -t 8 \
      "$REF" \
      "$FASTQ" \
      2> "$RESULT_DIR/${CONDITION}_minimap2.log" \
    | samtools view -b -o "$UNSORTED_BAM" -

    samtools sort \
      -@ 4 \
      -o "$SORTED_BAM" \
      "$UNSORTED_BAM"

    samtools index "$SORTED_BAM"

    samtools quickcheck -v "$SORTED_BAM" || {
      echo "ERROR: Aligned BAM validation failed for $CONDITION."
      exit 1
    }

    python "$ANALYSIS_SCRIPT" \
      --bam "$SORTED_BAM" \
      --condition "$CONDITION" \
      --chrom "$TARGET_CHROM" \
      --position "$TARGET_POS" \
      --ref "$TARGET_REF" \
      --alt "$TARGET_ALT" \
      --records-tsv "$RECORDS_TSV" \
      --parents-tsv "$PARENTS_TSV" \
      --summary-tsv "$CONDITION_SUMMARY"       --parent-map "$PARENT_MAP"

    RAW_PARENTS=$(
      awk -F'\t' 'NR==2 {print $6}' "$CONDITION_SUMMARY"
    )

    [[ "$RAW_PARENTS" -eq 11 ]] || {
      echo "ERROR: Expected 11 raw parents for $CONDITION; got $RAW_PARENTS."
      exit 1
    }

    touch "$COMPLETE_MARKER"
    echo "$CONDITION alignment and target analysis: PASS"
  fi

  awk -F'\t' \
    -v OFS='\t' \
    -v context="$CONTEXT" \
    -v changed="$CHANGED_SAMPLES" \
    -v fraction="$CHANGED_FRACTION" '
      NR==2 {
        print $1, context, changed, fraction,
              $2, $3, $4, $5, $6, $7, $8, $9,
              $10, $11, $12, $13, $14, $15, $16,
              $17, $18, "PASS"
      }
    ' "$CONDITION_SUMMARY" \
    >> "$SUMMARY"
}

run_condition "E2_W0"   0  280  0.0000661730
run_condition "E2_PM2"  2  776  0.0001833939
run_condition "E2_PM10" 10 2982 0.0007047430
run_condition "E2_PM20" 20 5862 0.0013853800

echo
echo "============================================================"
echo "ADD EXISTING E1 PM5 REFERENCE"
echo "============================================================"

PM5_BAM="$EXP_E_DIR/attacks/local_interpolation_pm5/dorado_results/attacked.aligned.sorted.bam"
PM5_ANALYSIS_DIR="$E2_DIR/E1_PM5_reference"
PM5_RECORDS="$PM5_ANALYSIS_DIR/E1_PM5_target_records.tsv"
PM5_PARENTS="$PM5_ANALYSIS_DIR/E1_PM5_target_parents.tsv"
PM5_SUMMARY="$PM5_ANALYSIS_DIR/E1_PM5_target_summary.tsv"

mkdir -p "$PM5_ANALYSIS_DIR"

[[ -s "$PM5_BAM" ]] || {
  echo "ERROR: Existing PM5 BAM missing:"
  echo "$PM5_BAM"
  exit 1
}

python "$ANALYSIS_SCRIPT" \
  --bam "$PM5_BAM" \
  --condition "E1_PM5" \
  --chrom "$TARGET_CHROM" \
  --position "$TARGET_POS" \
  --ref "$TARGET_REF" \
  --alt "$TARGET_ALT" \
  --records-tsv "$PM5_RECORDS" \
  --parents-tsv "$PM5_PARENTS" \
  --summary-tsv "$PM5_SUMMARY"

awk -F'\t' \
  -v OFS='\t' '
    NR==2 {
      print $1, 5, 1599, 0.0003778954,
            $2, $3, $4, $5, $6, $7, $8, $9,
            $10, $11, $12, $13, $14, $15, $16,
            $17, $18, "PASS"
    }
  ' "$PM5_SUMMARY" \
  >> "$SUMMARY"

echo
echo "============================================================"
echo "E2 ALIGNMENT AND TARGET-STATE SUMMARY"
echo "============================================================"

column -t -s $'\t' "$SUMMARY"

touch "$DONE_MARKER"

echo
echo "Finished: $(date -Is)"
echo "E2 alignment and target analysis: COMPLETE"
