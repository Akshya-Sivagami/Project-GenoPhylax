#!/usr/bin/env bash

set -euo pipefail

cd "$HOME/Project-GenoPhylax"

source experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

# ============================================================
# Experiment C2 configuration
# ============================================================

DATA_ROOT="$HOME/datasets/GenoPhylax/A2_signal_perturbations/gaussian_noise_1000reads"

POD5_DIR="$DATA_ROOT/pod5"
BASECALL_DIR="$DATA_ROOT/basecalls"
LOG_DIR="$DATA_ROOT/logs/experiment_C2"

EXP_C2_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_C2_multiseed"
METRICS_DIR="$EXP_C2_DIR/metrics"
RUN_STATUS_DIR="$EXP_C2_DIR/run_status"

SCRIPT_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/scripts"

PERTURB_SCRIPT="$SCRIPT_DIR/perturb_pod5_gaussian.py"
COLLAPSE_SCRIPT="$SCRIPT_DIR/collapse_split_reads.py"
COMPARE_SCRIPT="$SCRIPT_DIR/compare_clean_vs_perturbed_bam.py"

CLEAN_POD5="$POD5_DIR/hg002_1000reads_clean.pod5"
CLEAN_BAM="$BASECALL_DIR/hg002_1000reads_clean_hac_parent_normalized.bam"

MODEL="dna_r10.4.1_e8.2_400bps_hac@v6.0.0"

mkdir -p \
  "$POD5_DIR" \
  "$BASECALL_DIR" \
  "$LOG_DIR" \
  "$METRICS_DIR" \
  "$RUN_STATUS_DIR"

# ============================================================
# Initial validation
# ============================================================

echo "============================================================"
echo "Experiment C2 — 1,000-Read Multi-Seed Replication"
echo "============================================================"

echo
echo "[1] Required clean files"

if [[ ! -f "$CLEAN_POD5" ]]; then
    echo "ERROR: Clean POD5 is missing:"
    echo "$CLEAN_POD5"
    exit 1
fi

if [[ ! -f "$CLEAN_BAM" ]]; then
    echo "ERROR: Parent-normalized clean BAM is missing:"
    echo "$CLEAN_BAM"
    exit 1
fi

echo "Clean POD5:"
ls -lh "$CLEAN_POD5"

echo
echo "Clean parent-normalized BAM:"
ls -lh "$CLEAN_BAM"

CLEAN_BAM_RECORDS=$(samtools view -c "$CLEAN_BAM")
CLEAN_BAM_UNIQUE=$(
    samtools view "$CLEAN_BAM" |
      cut -f1 |
      sort -u |
      wc -l
)

echo "Clean BAM records:    $CLEAN_BAM_RECORDS"
echo "Clean unique IDs:     $CLEAN_BAM_UNIQUE"

if [[ "$CLEAN_BAM_RECORDS" -ne 1000 || "$CLEAN_BAM_UNIQUE" -ne 1000 ]]; then
    echo "ERROR: Clean normalized BAM is not a valid 1,000-read control."
    exit 1
fi

if ! samtools quickcheck -u "$CLEAN_BAM"; then
    echo "ERROR: Clean normalized BAM failed quickcheck."
    exit 1
fi

echo "Clean control validation: PASS"

echo
echo "[2] Tools"

python --version
dorado --version
samtools --version | head -1

for script in \
  "$PERTURB_SCRIPT" \
  "$COLLAPSE_SCRIPT" \
  "$COMPARE_SCRIPT"
do
    if [[ ! -f "$script" ]]; then
        echo "ERROR: Required script missing:"
        echo "$script"
        exit 1
    fi
done

echo "Required scripts: PASS"

# ============================================================
# Main experiment
# ============================================================

for SEED in 1 2 3; do
    for ENTRY in \
      "GN01 0.01" \
      "GN05 0.05" \
      "GN10 0.10"
    do
        read -r LEVEL SIGMA <<< "$ENTRY"

        CONDITION="${LEVEL}_seed${SEED}"

        PERTURBED_POD5="$POD5_DIR/hg002_1000reads_${CONDITION}.pod5"
        SIGNAL_METRICS="$METRICS_DIR/hg002_1000reads_${CONDITION}_signal_metrics.tsv"

        OPERATIONAL_BAM="$BASECALL_DIR/hg002_1000reads_${CONDITION}_hac.bam"
        TEMP_BAM="$BASECALL_DIR/hg002_1000reads_${CONDITION}_hac.tmp.bam"
        NORMALIZED_BAM="$BASECALL_DIR/hg002_1000reads_${CONDITION}_hac_parent_normalized.bam"

        DORADO_LOG="$LOG_DIR/hg002_1000reads_${CONDITION}_hac.log"
        SPLIT_SUMMARY="$METRICS_DIR/hg002_1000reads_${CONDITION}_split_summary.tsv"

        PER_READ_OUTPUT="$METRICS_DIR/hg002_1000reads_clean_vs_${CONDITION}_per_read.tsv"
        SUMMARY_OUTPUT="$METRICS_DIR/hg002_1000reads_clean_vs_${CONDITION}_summary.tsv"

        STATUS_FILE="$RUN_STATUS_DIR/${CONDITION}.complete"

        echo
        echo "============================================================"
        echo "Condition: $CONDITION"
        echo "Sigma:     $SIGMA"
        echo "============================================================"

        # ----------------------------------------------------
        # Step A: Generate perturbed POD5
        # ----------------------------------------------------

        echo
        echo "[A] Perturbed POD5"

        POD5_VALID=0

        if [[ -f "$PERTURBED_POD5" ]]; then
            POD5_COUNT=$(
                python - "$PERTURBED_POD5" <<'PY'
import sys
import pod5

with pod5.Reader(sys.argv[1]) as reader:
    print(sum(1 for _ in reader.reads()))
PY
            )

            if [[ "$POD5_COUNT" -eq 1000 ]]; then
                POD5_VALID=1
                echo "Existing POD5 is valid; skipping perturbation."
            else
                echo "Existing POD5 has $POD5_COUNT reads; regenerating."
                rm -f "$PERTURBED_POD5" "$SIGNAL_METRICS"
            fi
        fi

        if [[ "$POD5_VALID" -eq 0 ]]; then
            python "$PERTURB_SCRIPT" \
              --input "$CLEAN_POD5" \
              --output "$PERTURBED_POD5" \
              --sigma-fraction "$SIGMA" \
              --seed "$SEED" \
              --max-reads 1000 \
              --metrics "$SIGNAL_METRICS"
        fi

        python - "$CLEAN_POD5" "$PERTURBED_POD5" <<'PY'
import sys
import numpy as np
import pod5

clean_path = sys.argv[1]
perturbed_path = sys.argv[2]

clean_ids = []
perturbed_ids = []

changed_reads = 0
changed_samples = 0
total_samples = 0
sample_count_mismatches = 0

with pod5.Reader(clean_path) as clean_reader, \
     pod5.Reader(perturbed_path) as perturbed_reader:

    clean_iterator = clean_reader.reads()
    perturbed_iterator = perturbed_reader.reads()

    clean_count = 0
    perturbed_count = 0

    while True:
        try:
            clean_record = next(clean_iterator)
            clean_finished = False
        except StopIteration:
            clean_record = None
            clean_finished = True

        try:
            perturbed_record = next(perturbed_iterator)
            perturbed_finished = False
        except StopIteration:
            perturbed_record = None
            perturbed_finished = True

        if clean_finished and perturbed_finished:
            break

        if clean_finished != perturbed_finished:
            raise RuntimeError(
                "Clean and perturbed POD5 record counts differ"
            )

        clean_count += 1
        perturbed_count += 1

        clean_ids.append(str(clean_record.read_id))
        perturbed_ids.append(str(perturbed_record.read_id))

        clean_signal = np.asarray(clean_record.signal)
        perturbed_signal = np.asarray(perturbed_record.signal)

        if len(clean_signal) != len(perturbed_signal):
            sample_count_mismatches += 1
            continue

        differences = clean_signal != perturbed_signal

        total_samples += len(clean_signal)
        changed_samples += int(np.count_nonzero(differences))

        if np.any(differences):
            changed_reads += 1

valid = (
    clean_count == 1000
    and perturbed_count == 1000
    and len(set(perturbed_ids)) == 1000
    and clean_ids == perturbed_ids
    and changed_reads == 1000
    and sample_count_mismatches == 0
)

print(f"Clean reads:              {clean_count}")
print(f"Perturbed reads:          {perturbed_count}")
print(f"Unique perturbed IDs:     {len(set(perturbed_ids))}")
print(f"Read-ID order identical:  {clean_ids == perturbed_ids}")
print(f"Changed reads:            {changed_reads}")
print(f"Changed samples:          {changed_samples}")
print(f"Total samples:            {total_samples}")
print(f"Sample-count mismatches:  {sample_count_mismatches}")

if total_samples:
    print(
        "Changed sample fraction: "
        f"{changed_samples / total_samples:.10f}"
    )

if not valid:
    raise RuntimeError("Perturbed POD5 validation failed")

print("POD5 VALIDATION: PASS")
PY

        # ----------------------------------------------------
        # Step B: Dorado basecalling
        # ----------------------------------------------------

        echo
        echo "[B] Dorado basecalling"

        BAM_VALID=0

        if [[ -f "$OPERATIONAL_BAM" ]]; then
            if samtools quickcheck -u "$OPERATIONAL_BAM"; then
                BAM_VALID=1
                echo "Existing operational BAM is valid; skipping Dorado."
            else
                echo "Existing operational BAM failed quickcheck; regenerating."
                rm -f "$OPERATIONAL_BAM"
            fi
        fi

        if [[ "$BAM_VALID" -eq 0 ]]; then
            rm -f "$TEMP_BAM"

            /usr/bin/time -v \
              dorado basecaller \
              "$MODEL" \
              "$PERTURBED_POD5" \
              --device cuda:0 \
              --emit-moves \
              > "$TEMP_BAM" \
              2> "$DORADO_LOG"

            DORADO_STATUS=$?

            if [[ "$DORADO_STATUS" -ne 0 ]]; then
                echo "ERROR: Dorado failed for $CONDITION"
                echo "See log: $DORADO_LOG"
                exit 1
            fi

            mv "$TEMP_BAM" "$OPERATIONAL_BAM"
        fi

        if ! samtools quickcheck -u "$OPERATIONAL_BAM"; then
            echo "ERROR: Operational BAM failed quickcheck."
            exit 1
        fi

        TOTAL_RECORDS=$(samtools view -c "$OPERATIONAL_BAM")
        UNMAPPED_RECORDS=$(samtools view -c -f 4 "$OPERATIONAL_BAM")
        MAPPED_RECORDS=$(samtools view -c -F 4 "$OPERATIONAL_BAM")
        UNIQUE_RECORD_IDS=$(
            samtools view "$OPERATIONAL_BAM" |
              cut -f1 |
              sort -u |
              wc -l
        )

        PI_RECORDS=$(
            samtools view "$OPERATIONAL_BAM" |
              awk '
                {
                  for (i = 12; i <= NF; i++) {
                    if ($i ~ /^pi:Z:/) {
                      count++
                      break
                    }
                  }
                }
                END { print count + 0 }
              '
        )

        SPLIT_PARENT_GROUPS=$(
            samtools view "$OPERATIONAL_BAM" |
              awk '
                {
                  for (i = 12; i <= NF; i++) {
                    if ($i ~ /^pi:Z:/) {
                      split($i, tag, ":")
                      print tag[3]
                      break
                    }
                  }
                }
              ' |
              sort -u |
              wc -l
        )

        EXTRA_RECORDS=$((TOTAL_RECORDS - 1000))

        {
            printf "metric\tvalue\n"
            printf "condition\t%s\n" "$LEVEL"
            printf "seed\t%s\n" "$SEED"
            printf "input_pod5\t%s\n" "$PERTURBED_POD5"
            printf "output_bam\t%s\n" "$OPERATIONAL_BAM"
            printf "dorado_exit_status\t0\n"
            printf "total_bam_records\t%s\n" "$TOTAL_RECORDS"
            printf "unmapped_records\t%s\n" "$UNMAPPED_RECORDS"
            printf "mapped_records\t%s\n" "$MAPPED_RECORDS"
            printf "unique_record_ids\t%s\n" "$UNIQUE_RECORD_IDS"
            printf "pi_tagged_records\t%s\n" "$PI_RECORDS"
            printf "split_parent_groups\t%s\n" "$SPLIT_PARENT_GROUPS"
            printf "extra_bam_records\t%s\n" "$EXTRA_RECORDS"
            printf "quickcheck\tPASS\n"
        } > "$SPLIT_SUMMARY"

        echo "Operational BAM records:  $TOTAL_RECORDS"
        echo "Split parent groups:       $SPLIT_PARENT_GROUPS"
        echo "Extra BAM records:         $EXTRA_RECORDS"
        echo "Operational quickcheck:    PASS"

        # ----------------------------------------------------
        # Step C: Parent normalization
        # ----------------------------------------------------

        echo
        echo "[C] Parent normalization"

        NORMALIZED_VALID=0

        if [[ -f "$NORMALIZED_BAM" ]]; then
            NORMALIZED_COUNT=$(samtools view -c "$NORMALIZED_BAM")
            NORMALIZED_UNIQUE=$(
                samtools view "$NORMALIZED_BAM" |
                  cut -f1 |
                  sort -u |
                  wc -l
            )

            if [[ "$NORMALIZED_COUNT" -eq 1000 ]] \
              && [[ "$NORMALIZED_UNIQUE" -eq 1000 ]] \
              && samtools quickcheck -u "$NORMALIZED_BAM"
            then
                NORMALIZED_VALID=1
                echo "Existing normalized BAM is valid; skipping collapse."
            else
                echo "Existing normalized BAM is invalid; regenerating."
                rm -f "$NORMALIZED_BAM"
            fi
        fi

        if [[ "$NORMALIZED_VALID" -eq 0 ]]; then
            python "$COLLAPSE_SCRIPT" \
              --input-bam "$OPERATIONAL_BAM" \
              --output-bam "$NORMALIZED_BAM"
        fi

        NORMALIZED_COUNT=$(samtools view -c "$NORMALIZED_BAM")
        NORMALIZED_UNIQUE=$(
            samtools view "$NORMALIZED_BAM" |
              cut -f1 |
              sort -u |
              wc -l
        )

        if [[ "$NORMALIZED_COUNT" -ne 1000 ]] \
          || [[ "$NORMALIZED_UNIQUE" -ne 1000 ]]
        then
            echo "ERROR: Normalized BAM does not contain 1,000 unique parents."
            exit 1
        fi

        if ! samtools quickcheck -u "$NORMALIZED_BAM"; then
            echo "ERROR: Normalized BAM failed quickcheck."
            exit 1
        fi

        python - "$PERTURBED_POD5" "$NORMALIZED_BAM" <<'PY'
import sys
import pod5
import pysam

pod5_path = sys.argv[1]
bam_path = sys.argv[2]

with pod5.Reader(pod5_path) as reader:
    pod5_ids = {str(record.read_id) for record in reader.reads()}

with pysam.AlignmentFile(bam_path, "rb", check_sq=False) as bam:
    bam_ids = {record.query_name for record in bam}

pod5_only = pod5_ids - bam_ids
bam_only = bam_ids - pod5_ids

print(f"POD5 parent IDs:       {len(pod5_ids)}")
print(f"Normalized BAM IDs:    {len(bam_ids)}")
print(f"POD5-only IDs:         {len(pod5_only)}")
print(f"BAM-only IDs:          {len(bam_only)}")

if len(pod5_ids) != 1000 or pod5_ids != bam_ids:
    raise RuntimeError("Parent-ID validation failed")

print("PARENT-ID VALIDATION: PASS")
PY

        # ----------------------------------------------------
        # Step D: Paired comparison
        # ----------------------------------------------------

        echo
        echo "[D] Clean-versus-perturbed comparison"

        SUMMARY_VALID=0

        if [[ -f "$SUMMARY_OUTPUT" && -f "$PER_READ_OUTPUT" ]]; then
            PER_READ_ROWS=$(awk 'END {print NR-1}' "$PER_READ_OUTPUT")

            if [[ "$PER_READ_ROWS" -eq 1000 ]]; then
                SUMMARY_VALID=1
                echo "Existing comparison is valid; skipping comparison."
            else
                echo "Existing comparison is incomplete; regenerating."
                rm -f "$SUMMARY_OUTPUT" "$PER_READ_OUTPUT"
            fi
        fi

        if [[ "$SUMMARY_VALID" -eq 0 ]]; then
            /usr/bin/time -v \
              python "$COMPARE_SCRIPT" \
              --clean-bam "$CLEAN_BAM" \
              --perturbed-bam "$NORMALIZED_BAM" \
              --per-read-output "$PER_READ_OUTPUT" \
              --summary-output "$SUMMARY_OUTPUT"
        fi

        PER_READ_ROWS=$(awk 'END {print NR-1}' "$PER_READ_OUTPUT")

        if [[ "$PER_READ_ROWS" -ne 1000 ]]; then
            echo "ERROR: Paired comparison does not contain 1,000 reads."
            exit 1
        fi

        PAIRED_READS=$(
            awk -F '\t' '$1=="paired_reads" {gsub(/\\r/, "", $2); print $2; exit}' "$SUMMARY_OUTPUT"
        )

        CLEAN_ONLY=$(
            awk -F '\t' '$1=="clean_only_reads" {gsub(/\\r/, "", $2); print $2; exit}' "$SUMMARY_OUTPUT"
        )

        PERTURBED_ONLY=$(
            awk -F '\t' '$1=="perturbed_only_reads" {gsub(/\\r/, "", $2); print $2; exit}' "$SUMMARY_OUTPUT"
        )

        if [[ "$PAIRED_READS" -ne 1000 ]] \
          || [[ "$CLEAN_ONLY" -ne 0 ]] \
          || [[ "$PERTURBED_ONLY" -ne 0 ]]
        then
            echo "ERROR: Paired read matching failed."
            exit 1
        fi

        echo
        echo "Condition summary:"

        awk -F '\t' '
          $1 == "paired_reads" ||
          $1 == "exact_sequence_matches" ||
          $1 == "changed_sequences" ||
          $1 == "mean_sequence_identity_percent" ||
          $1 == "mean_edit_distance" ||
          $1 == "mean_normalized_edit_distance" ||
          $1 == "mean_qscore_change" ||
          $1 == "mean_length_change"
          {
            printf "%-38s %s\n", $1 ":", $2
          }
        ' "$SUMMARY_OUTPUT"

        {
            echo "condition=$LEVEL"
            echo "seed=$SEED"
            echo "sigma_fraction=$SIGMA"
            echo "operational_bam_records=$TOTAL_RECORDS"
            echo "split_parent_groups=$SPLIT_PARENT_GROUPS"
            echo "normalized_bam_records=$NORMALIZED_COUNT"
            echo "paired_reads=$PAIRED_READS"
            echo "status=PASS"
        } > "$STATUS_FILE"

        echo
        echo "CONDITION COMPLETE: $CONDITION"
    done
done

# ============================================================
# Final completion check
# ============================================================

echo
echo "============================================================"
echo "Experiment C2 completion check"
echo "============================================================"

COMPLETED=0

for SEED in 1 2 3; do
    for LEVEL in GN01 GN05 GN10; do
        STATUS_FILE="$RUN_STATUS_DIR/${LEVEL}_seed${SEED}.complete"

        if [[ -f "$STATUS_FILE" ]]; then
            echo "PASS $LEVEL seed $SEED"
            COMPLETED=$((COMPLETED + 1))
        else
            echo "MISSING $LEVEL seed $SEED"
        fi
    done
done

echo
echo "Completed conditions: $COMPLETED / 9"

if [[ "$COMPLETED" -ne 9 ]]; then
    echo "ERROR: Experiment C2 is incomplete."
    exit 1
fi

echo
echo "EXPERIMENT C2 COMPUTATIONAL RUNS: COMPLETE"
