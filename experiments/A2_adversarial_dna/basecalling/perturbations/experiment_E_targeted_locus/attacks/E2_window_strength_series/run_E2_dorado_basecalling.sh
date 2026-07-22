#!/usr/bin/env bash

set -Eeuo pipefail

cd ~/Project-GenoPhylax

EXP_E_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_targeted_locus"
E2_DIR="$EXP_E_DIR/attacks/E2_window_strength_series"

DORADO="$HOME/tools/dorado/dorado-2.1.0-linux-arm64-cuda-13.0/bin/dorado"
MODEL="$HOME/tools/dorado/models/dna_r10.4.1_e8.2_400bps_hac@v6.0.0"

MASTER_SUMMARY="$E2_DIR/E2_dorado_basecalling_summary.tsv"
DONE_MARKER="$E2_DIR/E2_DORADO_BASECALLING.COMPLETE"

rm -f "$DONE_MARKER"

echo "============================================================"
echo "EXPERIMENT E2 — DORADO BASECALLING"
echo "Started: $(date -Is)"
echo "============================================================"

[[ -x "$DORADO" ]] || {
  echo "ERROR: Dorado executable missing:"
  echo "$DORADO"
  exit 1
}

[[ -d "$MODEL" ]] || {
  echo "ERROR: Dorado model missing:"
  echo "$MODEL"
  exit 1
}

printf \
"condition\tinput_reads\toutput_records\toutput_size_bytes\tstatus\n" \
> "$MASTER_SUMMARY"

run_condition() {
  CONDITION="$1"

  CONDITION_DIR="$E2_DIR/$CONDITION"
  POD5="$CONDITION_DIR/${CONDITION}_local_interpolation.pod5"

  RESULT_DIR="$CONDITION_DIR/dorado_results"
  OUTPUT_BAM="$RESULT_DIR/${CONDITION}.unaligned.bam"
  CONDITION_LOG="$RESULT_DIR/${CONDITION}_dorado.log"
  COMPLETE_MARKER="$RESULT_DIR/${CONDITION}_DORADO.COMPLETE"

  mkdir -p "$RESULT_DIR"

  echo
  echo "------------------------------------------------------------"
  echo "Condition: $CONDITION"
  echo "Started:   $(date -Is)"
  echo "------------------------------------------------------------"

  [[ -s "$POD5" ]] || {
    echo "ERROR: Missing attacked POD5:"
    echo "$POD5"
    exit 1
  }

  if [[ -f "$COMPLETE_MARKER" ]] \
    && [[ -s "$OUTPUT_BAM" ]] \
    && samtools view -H "$OUTPUT_BAM" >/dev/null 2>&1
  then
    echo "$CONDITION already complete; reusing output."
  else
    rm -f \
      "$COMPLETE_MARKER" \
      "$OUTPUT_BAM" \
      "$CONDITION_LOG"

    /usr/bin/time -v \
      "$DORADO" basecaller \
      "$MODEL" \
      "$POD5" \
      --device cuda:all \
      --emit-moves \
      --no-trim \
      > "$OUTPUT_BAM" \
      2> "$CONDITION_LOG"

    if ! samtools view -H "$OUTPUT_BAM" >/dev/null 2>&1; then
      echo "ERROR: BAM header could not be read for $CONDITION."
      exit 1
    fi

    OUTPUT_RECORDS=$(samtools view -c "$OUTPUT_BAM")

    if [[ "$OUTPUT_RECORDS" -lt 11 ]]; then
      echo "ERROR: Expected at least 11 BAM records for $CONDITION; got $OUTPUT_RECORDS."
      exit 1
    fi

    INPUT_READS=$(
      pod5 inspect reads "$POD5" 2>/dev/null \
      | awk 'NR>1 {count++} END {print count+0}'
    )

    OUTPUT_RECORDS=$(samtools view -c "$OUTPUT_BAM")

    [[ "$INPUT_READS" -eq 11 ]] || {
      echo "ERROR: Expected 11 raw reads for $CONDITION; got $INPUT_READS."
      exit 1
    }

    [[ "$OUTPUT_RECORDS" -ge 11 ]] || {
      echo "ERROR: Expected at least 11 BAM records for $CONDITION."
      exit 1
    }

    touch "$COMPLETE_MARKER"
    echo "$CONDITION Dorado basecalling: PASS"
  fi

  INPUT_READS=$(
    pod5 inspect reads "$POD5" 2>/dev/null \
    | awk 'NR>1 {count++} END {print count+0}'
  )

  OUTPUT_RECORDS=$(samtools view -c "$OUTPUT_BAM")
  OUTPUT_SIZE=$(stat -c '%s' "$OUTPUT_BAM")

  printf \
    "%s\t%s\t%s\t%s\tPASS\n" \
    "$CONDITION" \
    "$INPUT_READS" \
    "$OUTPUT_RECORDS" \
    "$OUTPUT_SIZE" \
    >> "$MASTER_SUMMARY"

  echo "Input reads:    $INPUT_READS"
  echo "Output records: $OUTPUT_RECORDS"

  grep -E \
    'Simplex reads basecalled|Samples/s|Finished in|Elapsed|Maximum resident|Exit status' \
    "$CONDITION_LOG" \
    | tail -12 \
    || true

  echo "Finished: $(date -Is)"
}

run_condition "E2_W0"
run_condition "E2_PM2"
run_condition "E2_PM10"
run_condition "E2_PM20"

echo
echo "============================================================"
echo "E2 DORADO BASECALLING SUMMARY"
echo "============================================================"

column -t -s $'\t' "$MASTER_SUMMARY"

touch "$DONE_MARKER"

echo
echo "Finished: $(date -Is)"
echo "E2 Dorado basecalling: COMPLETE"
