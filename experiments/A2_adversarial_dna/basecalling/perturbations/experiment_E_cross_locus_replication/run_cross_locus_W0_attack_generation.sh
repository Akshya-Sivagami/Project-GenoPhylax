#!/usr/bin/env bash

set -Eeuo pipefail

cd "/home/admin/Project-GenoPhylax"

CROSS_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication"
PYTHON="/home/admin/Project-GenoPhylax/experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/python"

W0_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/discovery/validation/W0_attack_generation"
W0_POD5_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_pod5/W0"

WINDOWS_TSV="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/signal_windows/clean_target_signal_windows.tsv"

L2_INPUT_POD5="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/target_pod5/L2_chr1_20061156_A_T.pod5"
L3_INPUT_POD5="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/target_pod5/L3_chr4_40028853_A_G.pod5"

L2_CLEAN_BAM="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/clean_alignments/L2_chr1_20061156_A_T.clean.aligned.sorted.bam"
L3_CLEAN_BAM="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/clean_alignments/L3_chr4_40028853_A_G.clean.aligned.sorted.bam"

L2_W0_POD5="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_pod5/W0/L2_chr1_20061156_A_T.W0.pod5"
L3_W0_POD5="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/attacked_pod5/W0/L3_chr4_40028853_A_G.W0.pod5"

AUDIT_TSV="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/discovery/validation/W0_attack_generation/W0_attack_audit.tsv"
SUMMARY_TSV="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/discovery/validation/W0_attack_generation/W0_attack_summary.tsv"

COMPLETE="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_W0_ATTACK_GENERATION.COMPLETE"
FAILED="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/markers/CROSS_LOCUS_W0_ATTACK_GENERATION.FAILED"

trap '
  STATUS=$?
  echo
  echo "W0 attack generation failed with exit status $STATUS"
  date
  touch "$FAILED"
  exit $STATUS
' ERR

echo "============================================================"
echo "CROSS-LOCUS W0 ATTACK GENERATION"
echo "Started: $(date)"
echo "============================================================"

rm -f "$FAILED"

if [[ -s "$L2_W0_POD5"    && -s "$L3_W0_POD5"    && -s "$AUDIT_TSV"    && -s "$SUMMARY_TSV" ]]    && awk -F '\t' '
        NR > 1 && $NF != "PASS" { bad = 1 }
        END { exit bad }
      ' "$SUMMARY_TSV"
then
  echo "Existing W0 outputs already complete; skipping regeneration."
else
  rm -f     "$L2_W0_POD5"     "$L3_W0_POD5"     "$AUDIT_TSV"     "$SUMMARY_TSV"

  "$PYTHON"     "$CROSS_DIR/scripts/generate_cross_locus_pm5_attack.py"     --windows-tsv "$WINDOWS_TSV"     --l2-pod5 "$L2_INPUT_POD5"     --l2-bam "$L2_CLEAN_BAM"     --l2-output "$L2_W0_POD5"     --l3-pod5 "$L3_INPUT_POD5"     --l3-bam "$L3_CLEAN_BAM"     --l3-output "$L3_W0_POD5"     --audit-tsv "$AUDIT_TSV"     --summary-tsv "$SUMMARY_TSV"     --context-bases 0
fi

echo
echo "============================================================"
echo "VALIDATION"
echo "============================================================"

test -s "$L2_W0_POD5"
test -s "$L3_W0_POD5"
test -s "$AUDIT_TSV"
test -s "$SUMMARY_TSV"

"$PYTHON" - <<PY
import csv
from pathlib import Path

summary = Path("$SUMMARY_TSV")

with summary.open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))

assert len(rows) == 2, f"Expected 2 summary rows, found {len(rows)}"

for row in rows:
    assert row["context_bases"] == "0", row
    assert row["reads_processed"] == "10", row
    assert row["reads_passed"] == "10", row
    assert row["outside_changed_samples"] == "0", row
    assert int(row["total_changed_samples"]) > 0, row
    assert row["status"] == "PASS", row

print("W0 summary validation: PASS")
PY

rm -f "$FAILED"
touch "$COMPLETE"

echo
echo "W0 ATTACK GENERATION: COMPLETE"
echo "Finished: $(date)"
echo
cat "$SUMMARY_TSV"
