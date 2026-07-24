#!/usr/bin/env bash

set -Eeuo pipefail

cd "/home/admin/Project-GenoPhylax"

PYTHON="/home/admin/Project-GenoPhylax/experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/python"
SCRIPT="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/scripts/analyze_cross_locus_W0_target_effect.py"

PER_READ="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/results/W0_target_effect/W0_clean_vs_attacked_per_read.tsv"
SUMMARY="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/results/W0_target_effect/W0_clean_vs_attacked_summary.tsv"

COMPLETE="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_W0_TARGET_EFFECT.COMPLETE"
FAILED="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_W0_TARGET_EFFECT.FAILED"

trap '
    STATUS=$?
    echo
    echo "W0 target-effect analysis failed: $STATUS"
    date
    touch "$FAILED"
    exit $STATUS
' ERR

rm -f "$COMPLETE" "$FAILED"

"$PYTHON" "$SCRIPT"   --l2-clean "experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/clean_alignments/L2_chr1_20061156_A_T.clean.aligned.sorted.bam"   --l2-w0 "experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_alignments/W0/L2_chr1_20061156_A_T.W0.aligned.sorted.bam"   --l3-clean "experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/clean_alignments/L3_chr4_40028853_A_G.clean.aligned.sorted.bam"   --l3-w0 "experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_alignments/W0/L3_chr4_40028853_A_G.W0.aligned.sorted.bam"   --per-read "$PER_READ"   --summary "$SUMMARY"

test -s "$PER_READ"
test -s "$SUMMARY"

"$PYTHON" - <<PY
import csv

with open(
    "$SUMMARY",
    newline="",
    encoding="utf-8",
) as handle:
    rows = list(
        csv.DictReader(
            handle,
            delimiter="\t",
        )
    )

assert len(rows) == 2, rows

for row in rows:
    assert int(row["clean_parent_count"]) == 10, row
    assert int(row["attacked_parent_count"]) == 10, row
    assert int(row["clean_alt_parent_count"]) == 10, row

print("W0 target-effect summary validation: PASS")
PY

rm -f "$FAILED"
touch "$COMPLETE"

echo
echo "CROSS-LOCUS W0 TARGET-EFFECT ANALYSIS: COMPLETE"
echo "Finished: $(date)"
