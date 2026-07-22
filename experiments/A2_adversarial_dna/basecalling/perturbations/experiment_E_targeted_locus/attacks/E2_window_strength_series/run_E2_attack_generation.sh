#!/usr/bin/env bash

set -Eeuo pipefail

cd ~/Project-GenoPhylax

source \
  experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

EXP_E_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_targeted_locus"
E2_DIR="$EXP_E_DIR/attacks/E2_window_strength_series"

MAP_SCRIPT="$EXP_E_DIR/scripts/map_target_base_to_signal.py"
ATTACK_SCRIPT="$EXP_E_DIR/scripts/create_local_interpolation_attack.py"

CLEAN_BAM="$EXP_E_DIR/clean_dorado/hg002_chr20_10003468_alt_clean.aligned.sorted.bam"
CLEAN_POD5="$EXP_E_DIR/target_pod5/hg002_chr20_10003468_alt_11reads.pod5"

TARGET_CHROM="chr20"
TARGET_POS="10003468"
TARGET_ALT="G"

SUMMARY="$E2_DIR/E2_attack_generation_summary.tsv"
DONE_MARKER="$E2_DIR/E2_ATTACK_GENERATION.COMPLETE"

mkdir -p "$E2_DIR"

rm -f "$DONE_MARKER"

echo "============================================================"
echo "EXPERIMENT E2 — RESTART-SAFE ATTACK GENERATION"
echo "Started: $(date -Is)"
echo "============================================================"

for FILE in \
  "$MAP_SCRIPT" \
  "$ATTACK_SCRIPT" \
  "$CLEAN_BAM" \
  "$CLEAN_POD5"
do
  [[ -f "$FILE" ]] || {
    echo "ERROR: Missing required file: $FILE"
    exit 1
  }
done

samtools quickcheck -v "$CLEAN_BAM"
echo "Clean BAM validation: PASS"

printf \
"condition\tcontext_bases\tinterval_rows\tmapped_samples\tchanged_samples\tchanged_fraction\tstatus\n" \
> "$SUMMARY"

run_condition() {
  CONDITION="$1"
  CONTEXT="$2"

  CONDITION_DIR="$E2_DIR/$CONDITION"
  COMPLETE_MARKER="$CONDITION_DIR/${CONDITION}.COMPLETE"

  INTERVALS="$CONDITION_DIR/${CONDITION}_signal_intervals.tsv"
  EXCLUDED="$CONDITION_DIR/${CONDITION}_excluded.tsv"
  MAP_SUMMARY="$CONDITION_DIR/${CONDITION}_mapping_summary.txt"

  ATTACKED_POD5="$CONDITION_DIR/${CONDITION}_local_interpolation.pod5"
  METRICS="$CONDITION_DIR/${CONDITION}_attack_metrics.tsv"
  ATTACK_SUMMARY="$CONDITION_DIR/${CONDITION}_attack_summary.txt"
  VALIDATION="$CONDITION_DIR/${CONDITION}_attack_validation.txt"

  mkdir -p "$CONDITION_DIR"

  echo
  echo "------------------------------------------------------------"
  echo "Condition: $CONDITION"
  echo "Context: +/-$CONTEXT bases"
  echo "------------------------------------------------------------"

  if [[ -f "$COMPLETE_MARKER" ]] \
    && [[ -s "$INTERVALS" ]] \
    && [[ -s "$ATTACKED_POD5" ]] \
    && [[ -s "$METRICS" ]] \
    && [[ -s "$VALIDATION" ]]
  then
    echo "$CONDITION already complete; reusing existing outputs."
  else
    rm -f "$COMPLETE_MARKER"

    python "$MAP_SCRIPT" \
      "$CLEAN_BAM" \
      "$CLEAN_POD5" \
      "$TARGET_CHROM" \
      "$TARGET_POS" \
      "$TARGET_ALT" \
      "$CONTEXT" \
      "$INTERVALS" \
      "$EXCLUDED" \
      "$MAP_SUMMARY"

    INTERVAL_ROWS=$(( $(wc -l < "$INTERVALS") - 1 ))

    [[ "$INTERVAL_ROWS" -eq 10 ]] || {
      echo "ERROR: $CONDITION produced $INTERVAL_ROWS intervals; expected 10."
      exit 1
    }

    python "$ATTACK_SCRIPT" \
      "$CLEAN_POD5" \
      "$INTERVALS" \
      "$ATTACKED_POD5" \
      "$METRICS" \
      "$ATTACK_SUMMARY" \
      "$VALIDATION"

    sed -i \
      "s|Attack: linear interpolation across mapped +/-5-base windows|Attack: linear interpolation across mapped +/-${CONTEXT}-base windows|" \
      "$ATTACK_SUMMARY"

    grep -q \
      "Outside attack windows identical: True" \
      "$VALIDATION" \
      || {
        echo "ERROR: Outside-window validation failed for $CONDITION."
        cat "$VALIDATION"
        exit 1
      }

    grep -q \
      "Untouched reads identical: True" \
      "$VALIDATION" \
      || {
        echo "ERROR: Untouched-read validation failed for $CONDITION."
        cat "$VALIDATION"
        exit 1
      }

    touch "$COMPLETE_MARKER"
    echo "$CONDITION generation: PASS"
  fi

  INTERVAL_ROWS=$(( $(wc -l < "$INTERVALS") - 1 ))

  MAPPED_SAMPLES=$(
    awk -F'\t' '
      NR == 1 {
        for (i=1; i<=NF; i++) {
          if ($i=="window_samples") window_col=i
        }
        next
      }
      {sum += $window_col}
      END {print sum+0}
    ' "$METRICS"
  )

  CHANGED_SAMPLES=$(
    awk -F'\t' '
      NR == 1 {
        for (i=1; i<=NF; i++) {
          if ($i=="changed_samples") changed_col=i
        }
        next
      }
      {sum += $changed_col}
      END {print sum+0}
    ' "$METRICS"
  )

  CHANGED_FRACTION=$(
    awk -F': ' \
      '/Changed fraction of all POD5 signal:/ {print $2}' \
      "$ATTACK_SUMMARY" \
    | tail -1
  )

  printf \
    "%s\t%s\t%s\t%s\t%s\t%s\tPASS\n" \
    "$CONDITION" \
    "$CONTEXT" \
    "$INTERVAL_ROWS" \
    "$MAPPED_SAMPLES" \
    "$CHANGED_SAMPLES" \
    "$CHANGED_FRACTION" \
    >> "$SUMMARY"
}

run_condition "E2_W0" 0
run_condition "E2_PM2" 2
run_condition "E2_PM10" 10
run_condition "E2_PM20" 20

echo
echo "============================================================"
echo "E2 ATTACK GENERATION SUMMARY"
echo "============================================================"

column -t -s $'\t' "$SUMMARY"

echo
echo "Existing E1 PM5 reference:"
grep -E \
  'Total mapped window samples|Actually changed samples|Changed fraction of all POD5 signal' \
  "$EXP_E_DIR/attacks/local_interpolation_pm5/local_interpolation_pm5_summary.txt"

echo
echo "Generated POD5 files:"
find "$E2_DIR" \
  -type f \
  -name "*.pod5" \
  -printf '%p\t%k KB\n' \
| sort

touch "$DONE_MARKER"

echo
echo "Finished: $(date -Is)"
echo "E2 attack generation: COMPLETE"
