#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Project-GenoPhylax"

SOURCE="$HOME/datasets/hg002/pod5/PAO89685_pass__2264ba8c_afee3a87_0.pod5"
MODEL="$HOME/tools/dorado/models/dna_r10.4.1_e8.2_400bps_hac@v6.0.0"

POD5_DIR="$HOME/datasets/GenoPhylax/A2_signal_perturbations/gaussian_noise/pod5"
BAM_DIR="$HOME/datasets/GenoPhylax/A2_signal_perturbations/gaussian_noise/basecalls"

ROOT="experiments/A2_adversarial_dna/basecalling/perturbations"
PERTURB="$ROOT/scripts/perturb_pod5_gaussian.py"
COMPARE="$ROOT/scripts/compare_clean_vs_perturbed_bam.py"
METRICS="$ROOT/metrics"
LOGS="$ROOT/logs"

CLEAN_BAM="$BAM_DIR/hg002_100reads_clean_hac.bam"

mkdir -p "$POD5_DIR" "$BAM_DIR" "$METRICS" "$LOGS"

for seed in 1 2 3 4 5; do
  for spec in GN01:0.01 GN05:0.05 GN10:0.10; do
    level="${spec%%:*}"
    sigma="${spec##*:}"
    prefix="hg002_100reads_${level}_seed${seed}"

    pod5_file="$POD5_DIR/${prefix}.pod5"
    bam_file="$BAM_DIR/${prefix}_hac.bam"

    perturb_metrics="$METRICS/${prefix}_metrics.tsv"
    basecall_metrics="$METRICS/${prefix}_basecalling_metrics.tsv"

    per_read="$METRICS/hg002_100reads_clean_vs_${level}_seed${seed}_per_read.tsv"
    summary="$METRICS/hg002_100reads_clean_vs_${level}_seed${seed}_summary.tsv"

    perturb_log="$LOGS/${prefix}_perturbation.log"
    dorado_log="$LOGS/${prefix}_dorado.log"

    echo
    echo "========================================"
    echo "Running $level seed $seed"
    echo "========================================"

    rm -f \
      "$pod5_file" \
      "$bam_file" \
      "$perturb_metrics" \
      "$basecall_metrics" \
      "$per_read" \
      "$summary"

    python "$PERTURB" \
      --input "$SOURCE" \
      --output "$pod5_file" \
      --sigma-fraction "$sigma" \
      --seed "$seed" \
      --max-reads 100 \
      --metrics "$perturb_metrics" \
      > "$perturb_log" 2>&1

    /usr/bin/time -v \
      dorado basecaller \
      "$MODEL" \
      "$pod5_file" \
      --device cuda:all \
      > "$bam_file" \
      2> "$dorado_log"

    samtools quickcheck -u "$bam_file"

    records="$(samtools view -c "$bam_file")"

    if [[ "$records" != "100" ]]; then
      echo "ERROR: $level seed $seed produced $records records"
      exit 1
    fi

    {
      echo -e "metric\tvalue"
      echo -e "experiment_id\t${level}_100read_seed${seed}"
      echo -e "sigma_fraction\t${sigma}"
      echo -e "seed\t${seed}"
      echo -e "output_bam_records\t${records}"
      echo -e "unaligned_bam_quickcheck\tPASS"
      echo -e "dorado_exit_status\t0"
    } > "$basecall_metrics"

    python "$COMPARE" \
      --clean-bam "$CLEAN_BAM" \
      --perturbed-bam "$bam_file" \
      --per-read-output "$per_read" \
      --summary-output "$summary"

    echo "Completed $level seed $seed"
  done
done

echo
echo "========================================"
echo "EXPERIMENT B RUNS COMPLETE"
echo "All 15 runs succeeded"
echo "========================================"
