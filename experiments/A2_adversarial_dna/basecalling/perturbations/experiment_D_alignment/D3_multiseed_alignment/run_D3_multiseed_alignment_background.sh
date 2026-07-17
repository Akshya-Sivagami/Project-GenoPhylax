#!/usr/bin/env bash

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

THREADS="$(nproc)"

PROJECT_ROOT="$HOME/Project-GenoPhylax"

REFERENCE_DIR="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB"
REFERENCE_NAME="GCA_000001405.15_GRCh38_no_alt_analysis_set"
REFERENCE_MMI="$REFERENCE_DIR/${REFERENCE_NAME}.map-ont.mmi"

PERTURB_ROOT="$PROJECT_ROOT/experiments/A2_adversarial_dna/basecalling/perturbations"
C2_ROOT="$PERTURB_ROOT/experiment_C2_multiseed"

EXP_D_DIR="$PERTURB_ROOT/experiment_D_alignment"
D1_DIR="$EXP_D_DIR/D1_clean_validation"
D3_DIR="$EXP_D_DIR/D3_multiseed_alignment"

INPUT_DIR="$D3_DIR/input_paths"
FASTQ_DIR="$D3_DIR/fastq"
ALIGN_DIR="$D3_DIR/alignments"
LOG_DIR="$D3_DIR/logs"
METRICS_DIR="$D3_DIR/metrics"

COMPLETE_FILE="$D3_DIR/D3_MULTISEED_ALIGNMENT_COMPLETE"
FAILED_FILE="$D3_DIR/D3_MULTISEED_ALIGNMENT_FAILED"

CLEAN_ALIGN_BAM="$D1_DIR/alignments/hg002_1000reads_clean_GRCh38.sorted.bam"

mkdir -p \
    "$INPUT_DIR" \
    "$FASTQ_DIR" \
    "$ALIGN_DIR" \
    "$LOG_DIR" \
    "$METRICS_DIR"

rm -f "$COMPLETE_FILE" "$FAILED_FILE"

trap '
    STATUS=$?
    echo
    echo "============================================================"
    echo "D3 multi-seed alignment failed with exit status: $STATUS"
    echo "Time: $(date --iso-8601=seconds)"
    echo "============================================================"
    touch "$FAILED_FILE"
    exit "$STATUS"
' ERR

echo "============================================================"
echo "Experiment D3A — Multi-seed alignment replication"
echo "Started: $(date --iso-8601=seconds)"
echo "Threads: $THREADS"
echo "============================================================"
echo

echo "[1/8] Validating tools, reference, and CLEAN baseline"
echo "------------------------------------------------------------"

for TOOL in minimap2 samtools awk sort grep find cut python; do
    if ! command -v "$TOOL" >/dev/null 2>&1; then
        echo "ERROR: Missing required tool: $TOOL"
        exit 1
    fi
done

if [[ ! -s "$REFERENCE_MMI" ]]; then
    echo "ERROR: minimap2 index not found:"
    echo "$REFERENCE_MMI"
    exit 1
fi

if [[ ! -s "$CLEAN_ALIGN_BAM" ]]; then
    echo "ERROR: CLEAN alignment not found:"
    echo "$CLEAN_ALIGN_BAM"
    exit 1
fi

if ! samtools quickcheck "$CLEAN_ALIGN_BAM"; then
    echo "ERROR: CLEAN alignment failed quickcheck."
    exit 1
fi

if [[ ! -d "$C2_ROOT" ]]; then
    echo "ERROR: Experiment C2 directory not found:"
    echo "$C2_ROOT"
    exit 1
fi

echo "Reference index:"
ls -lh "$REFERENCE_MMI"

echo
echo "CLEAN alignment:"
ls -lh "$CLEAN_ALIGN_BAM"

echo
echo "C2 source directory:"
echo "$C2_ROOT"

echo
echo "Initial validation: PASS"
echo

echo "[2/8] Resolving all nine C2 parent-normalized BAMs"
echo "------------------------------------------------------------"

resolve_bam() {
    local CONDITION="$1"
    local SEED="$2"
    local CONDITION_LOWER
    local CANDIDATES
    local COUNT
    local SELECTED

    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"
    CANDIDATES="$INPUT_DIR/${CONDITION}_seed${SEED}_candidates.txt"

    find \
        "$C2_ROOT" \
        "$HOME/datasets/GenoPhylax/A2_signal_perturbations" \
        -type f \
        -iname "*${CONDITION_LOWER}*" \
        -iname "*seed${SEED}*" \
        -iname "*parent*normalized*.bam" \
        2>/dev/null |
    sort -u > "$CANDIDATES"

    COUNT="$(wc -l < "$CANDIDATES")"

    if [[ "$COUNT" -ne 1 ]]; then
        echo "ERROR: Could not uniquely resolve ${CONDITION} seed ${SEED}."
        echo
        echo "Candidates:"
        cat "$CANDIDATES" || true
        return 1
    fi

    SELECTED="$(cat "$CANDIDATES")"

    if [[ ! -s "$SELECTED" ]]; then
        echo "ERROR: Selected BAM is missing or empty:"
        echo "$SELECTED"
        return 1
    fi

    printf '%s\n' "$SELECTED"
}

for CONDITION in GN01 GN05 GN10; do
    for SEED in 1 2 3; do
        BAM_PATH="$(resolve_bam "$CONDITION" "$SEED")"

        printf '%s\n' "$BAM_PATH" \
            > "$INPUT_DIR/${CONDITION}_seed${SEED}_selected_bam.txt"

        echo "${CONDITION} seed ${SEED}:"
        echo "$BAM_PATH"
        ls -lh "$BAM_PATH"
        echo
    done
done

echo "All nine BAM paths resolved."
echo

echo "[3/8] Validating all nine normalized BAMs"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    for SEED in 1 2 3; do
        INPUT_BAM="$(
            cat "$INPUT_DIR/${CONDITION}_seed${SEED}_selected_bam.txt"
        )"

        RECORDS="$(samtools view -c "$INPUT_BAM")"

        UNIQUE_IDS="$(
            samtools view "$INPUT_BAM" |
            cut -f1 |
            sort -u |
            wc -l
        )"

        DUPLICATE_IDS="$(
            samtools view "$INPUT_BAM" |
            cut -f1 |
            sort |
            uniq -d |
            wc -l
        )"

        echo "${CONDITION} seed ${SEED} records:       $RECORDS"
        echo "${CONDITION} seed ${SEED} unique IDs:    $UNIQUE_IDS"
        echo "${CONDITION} seed ${SEED} duplicate IDs: $DUPLICATE_IDS"

        if [[ "$RECORDS" -ne 1000 ]]; then
            echo "ERROR: Expected 1,000 records."
            exit 1
        fi

        if [[ "$UNIQUE_IDS" -ne 1000 ]]; then
            echo "ERROR: Expected 1,000 unique IDs."
            exit 1
        fi

        if [[ "$DUPLICATE_IDS" -ne 0 ]]; then
            echo "ERROR: Duplicate IDs detected."
            exit 1
        fi

        echo
    done
done

echo "All nine normalized BAMs: PASS"
echo

echo "[4/8] Converting all nine BAMs to FASTQ"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    for SEED in 1 2 3; do
        INPUT_BAM="$(
            cat "$INPUT_DIR/${CONDITION}_seed${SEED}_selected_bam.txt"
        )"

        FASTQ="$FASTQ_DIR/hg002_1000reads_${CONDITION_LOWER}_seed${SEED}.fastq"
        FASTQ_LOG="$LOG_DIR/${CONDITION}_seed${SEED}_fastq.log"

        if [[ -s "$FASTQ" ]] &&
           [[ "$(wc -l < "$FASTQ")" -eq 4000 ]]; then
            echo "${CONDITION} seed ${SEED}: valid FASTQ already exists."
        else
            rm -f "$FASTQ" "${FASTQ}.tmp"

            samtools fastq \
                -@ "$THREADS" \
                -n \
                "$INPUT_BAM" \
                > "${FASTQ}.tmp" \
                2> "$FASTQ_LOG"

            mv "${FASTQ}.tmp" "$FASTQ"
        fi

        FASTQ_LINES="$(wc -l < "$FASTQ")"
        FASTQ_READS=$((FASTQ_LINES / 4))

        FASTQ_UNIQUE_IDS="$(
            awk 'NR % 4 == 1 {
                sub(/^@/, "", $1)
                print $1
            }' "$FASTQ" |
            sort -u |
            wc -l
        )"

        echo "${CONDITION} seed ${SEED} FASTQ lines:      $FASTQ_LINES"
        echo "${CONDITION} seed ${SEED} FASTQ reads:      $FASTQ_READS"
        echo "${CONDITION} seed ${SEED} FASTQ unique IDs: $FASTQ_UNIQUE_IDS"

        if [[ "$FASTQ_LINES" -ne 4000 ]] ||
           [[ "$FASTQ_READS" -ne 1000 ]] ||
           [[ "$FASTQ_UNIQUE_IDS" -ne 1000 ]]; then
            echo "ERROR: FASTQ validation failed."
            exit 1
        fi

        echo
    done
done

echo "All nine FASTQ files: PASS"
echo

echo "[5/8] Aligning all nine multi-seed conditions"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    for SEED in 1 2 3; do
        FASTQ="$FASTQ_DIR/hg002_1000reads_${CONDITION_LOWER}_seed${SEED}.fastq"

        ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed${SEED}_GRCh38.sorted.bam"

        ALIGN_LOG="$LOG_DIR/${CONDITION}_seed${SEED}_minimap2.log"

        echo "Aligning ${CONDITION} seed ${SEED}..."

        if [[ -s "$ALIGN_BAM" ]] &&
           [[ -s "${ALIGN_BAM}.bai" ]] &&
           samtools quickcheck "$ALIGN_BAM" 2>/dev/null; then

            echo "Existing valid alignment found; reusing it."
        else
            rm -f \
                "$ALIGN_BAM" \
                "${ALIGN_BAM}.bai" \
                "${ALIGN_BAM}.tmp"

            minimap2 \
                -a \
                -x map-ont \
                --MD \
                -t "$THREADS" \
                -R "@RG\tID:HG002_${CONDITION}_S${SEED}\tSM:HG002\tPL:ONT\tLB:HG002_1000reads" \
                "$REFERENCE_MMI" \
                "$FASTQ" \
                2> "$ALIGN_LOG" |
            samtools sort \
                -@ "$THREADS" \
                -o "${ALIGN_BAM}.tmp" \
                -

            mv "${ALIGN_BAM}.tmp" "$ALIGN_BAM"

            samtools index \
                -@ "$THREADS" \
                "$ALIGN_BAM"
        fi

        echo "${CONDITION} seed ${SEED} alignment:"
        ls -lh "$ALIGN_BAM" "${ALIGN_BAM}.bai"

        echo
        echo "Alignment log tail:"
        tail -15 "$ALIGN_LOG" 2>/dev/null || true
        echo
    done
done

echo "[6/8] Validating all nine aligned BAMs"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    for SEED in 1 2 3; do
        ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed${SEED}_GRCh38.sorted.bam"

        samtools quickcheck -v "$ALIGN_BAM"

        TOTAL_RECORDS="$(samtools view -c "$ALIGN_BAM")"
        PRIMARY_RECORDS="$(samtools view -c -F 2304 "$ALIGN_BAM")"

        UNIQUE_PRIMARY_IDS="$(
            samtools view -F 2304 "$ALIGN_BAM" |
            cut -f1 |
            sort -u |
            wc -l
        )"

        DUPLICATE_PRIMARY_IDS="$(
            samtools view -F 2304 "$ALIGN_BAM" |
            cut -f1 |
            sort |
            uniq -d |
            wc -l
        )"

        echo "${CONDITION} seed ${SEED} total records:         $TOTAL_RECORDS"
        echo "${CONDITION} seed ${SEED} primary records:       $PRIMARY_RECORDS"
        echo "${CONDITION} seed ${SEED} unique primary IDs:    $UNIQUE_PRIMARY_IDS"
        echo "${CONDITION} seed ${SEED} duplicate primary IDs: $DUPLICATE_PRIMARY_IDS"

        if [[ "$PRIMARY_RECORDS" -ne 1000 ]] ||
           [[ "$UNIQUE_PRIMARY_IDS" -ne 1000 ]] ||
           [[ "$DUPLICATE_PRIMARY_IDS" -ne 0 ]]; then
            echo "ERROR: Primary read accounting failed."
            exit 1
        fi

        echo
    done
done

echo "All nine aligned BAMs: PASS"
echo

echo "[7/8] Generating per-run and aggregate alignment metrics"
echo "------------------------------------------------------------"

RUN_TSV="$METRICS_DIR/experiment_D3_9run_alignment_results.tsv"
AGG_TSV="$METRICS_DIR/experiment_D3_level_aggregates.tsv"
MONO_TSV="$METRICS_DIR/experiment_D3_alignment_monotonicity.tsv"

printf '%s\n' \
    $'condition\tseed\tinput_reads\ttotal_records\tprimary_records\tmapped_primary\tunmapped_primary\tmapped_percent\tsecondary\tsupplementary\tmean_mapped_mapq\tmapq_ge20\tmapq_ge30\tmapq_ge60' \
    > "$RUN_TSV"

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    for SEED in 1 2 3; do
        ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed${SEED}_GRCh38.sorted.bam"

        FLAGSTAT="$METRICS_DIR/${CONDITION}_seed${SEED}_flagstat.txt"
        STATS="$METRICS_DIR/${CONDITION}_seed${SEED}_stats.txt"
        IDXSTATS="$METRICS_DIR/${CONDITION}_seed${SEED}_idxstats.txt"

        samtools flagstat -@ "$THREADS" "$ALIGN_BAM" > "$FLAGSTAT"
        samtools stats -@ "$THREADS" "$ALIGN_BAM" > "$STATS"
        samtools idxstats "$ALIGN_BAM" > "$IDXSTATS"

        TOTAL_RECORDS="$(samtools view -c "$ALIGN_BAM")"
        PRIMARY_RECORDS="$(samtools view -c -F 2304 "$ALIGN_BAM")"
        MAPPED_PRIMARY="$(samtools view -c -F 2308 "$ALIGN_BAM")"
        UNMAPPED_PRIMARY="$(samtools view -c -f 4 -F 2304 "$ALIGN_BAM")"
        SECONDARY="$(samtools view -c -f 256 "$ALIGN_BAM")"
        SUPPLEMENTARY="$(samtools view -c -f 2048 "$ALIGN_BAM")"

        MAPQ_GE20="$(samtools view -c -F 2308 -q 20 "$ALIGN_BAM")"
        MAPQ_GE30="$(samtools view -c -F 2308 -q 30 "$ALIGN_BAM")"
        MAPQ_GE60="$(samtools view -c -F 2308 -q 60 "$ALIGN_BAM")"

        MAPPED_PERCENT="$(
            awk \
                -v mapped="$MAPPED_PRIMARY" \
                -v total="$PRIMARY_RECORDS" \
                'BEGIN {
                    if (total == 0) print "0.000000"
                    else printf "%.6f", 100 * mapped / total
                }'
        )"

        MEAN_MAPQ="$(
            samtools view -F 2308 "$ALIGN_BAM" |
            awk '
                {
                    sum += $5
                    count++
                }
                END {
                    if (count == 0) print "NA"
                    else printf "%.6f", sum / count
                }
            '
        )"

        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$CONDITION" \
            "$SEED" \
            "1000" \
            "$TOTAL_RECORDS" \
            "$PRIMARY_RECORDS" \
            "$MAPPED_PRIMARY" \
            "$UNMAPPED_PRIMARY" \
            "$MAPPED_PERCENT" \
            "$SECONDARY" \
            "$SUPPLEMENTARY" \
            "$MEAN_MAPQ" \
            "$MAPQ_GE20" \
            "$MAPQ_GE30" \
            "$MAPQ_GE60" \
            >> "$RUN_TSV"
    done
done

python - "$RUN_TSV" "$AGG_TSV" "$MONO_TSV" <<'PY'
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

run_path = Path(sys.argv[1])
agg_path = Path(sys.argv[2])
mono_path = Path(sys.argv[3])

numeric_fields = [
    "total_records",
    "mapped_primary",
    "unmapped_primary",
    "mapped_percent",
    "secondary",
    "supplementary",
    "mean_mapped_mapq",
    "mapq_ge20",
    "mapq_ge30",
    "mapq_ge60",
]

rows = []

with run_path.open() as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    rows = list(reader)

grouped = defaultdict(list)

for row in rows:
    grouped[row["condition"]].append(row)

aggregate_rows = []

for condition in ("GN01", "GN05", "GN10"):
    condition_rows = grouped[condition]

    out = {
        "condition": condition,
        "seeds": len(condition_rows),
    }

    for field in numeric_fields:
        values = [float(row[field]) for row in condition_rows]
        out[f"mean_{field}"] = f"{statistics.mean(values):.6f}"
        out[f"sd_{field}"] = (
            f"{statistics.stdev(values):.6f}"
            if len(values) > 1
            else "0.000000"
        )

    aggregate_rows.append(out)

with agg_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(aggregate_rows[0].keys()),
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(aggregate_rows)

monotonic_specs = {
    "mean_unmapped_primary": "increasing",
    "mean_secondary": "increasing",
    "mean_supplementary": "increasing",
    "mean_mapped_percent": "decreasing",
    "mean_mean_mapped_mapq": "decreasing",
    "mean_mapq_ge20": "decreasing",
    "mean_mapq_ge30": "decreasing",
    "mean_mapq_ge60": "decreasing",
}

monotonic_rows = []

for metric, direction in monotonic_specs.items():
    values = [
        float(row[metric])
        for row in aggregate_rows
    ]

    if direction == "increasing":
        monotonic = values[0] <= values[1] <= values[2]
    else:
        monotonic = values[0] >= values[1] >= values[2]

    monotonic_rows.append(
        {
            "metric": metric,
            "GN01": f"{values[0]:.6f}",
            "GN05": f"{values[1]:.6f}",
            "GN10": f"{values[2]:.6f}",
            "expected_direction": direction,
            "monotonic": str(monotonic),
        }
    )

with mono_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(monotonic_rows[0].keys()),
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(monotonic_rows)
PY

echo "Nine-run alignment results:"
column -t -s $'\t' "$RUN_TSV" 2>/dev/null || cat "$RUN_TSV"

echo
echo "Level aggregates:"
column -t -s $'\t' "$AGG_TSV" 2>/dev/null || cat "$AGG_TSV"

echo
echo "Alignment monotonicity:"
column -t -s $'\t' "$MONO_TSV" 2>/dev/null || cat "$MONO_TSV"

echo

echo "[8/8] Final validation"
echo "------------------------------------------------------------"

EXPECTED_ALIGNMENTS=9
FOUND_ALIGNMENTS=0

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    for SEED in 1 2 3; do
        FASTQ="$FASTQ_DIR/hg002_1000reads_${CONDITION_LOWER}_seed${SEED}.fastq"

        ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed${SEED}_GRCh38.sorted.bam"

        [[ -s "$FASTQ" ]]
        [[ -s "$ALIGN_BAM" ]]
        [[ -s "${ALIGN_BAM}.bai" ]]
        [[ "$(samtools view -c -F 2304 "$ALIGN_BAM")" -eq 1000 ]]

        FOUND_ALIGNMENTS=$((FOUND_ALIGNMENTS + 1))
    done
done

if [[ "$FOUND_ALIGNMENTS" -ne "$EXPECTED_ALIGNMENTS" ]]; then
    echo "ERROR: Expected 9 validated alignments."
    exit 1
fi

RUN_ROWS="$(( $(wc -l < "$RUN_TSV") - 1 ))"
AGG_ROWS="$(( $(wc -l < "$AGG_TSV") - 1 ))"

echo "Validated alignments: $FOUND_ALIGNMENTS / $EXPECTED_ALIGNMENTS"
echo "Nine-run metric rows: $RUN_ROWS"
echo "Aggregate rows:       $AGG_ROWS"

if [[ "$RUN_ROWS" -ne 9 ]]; then
    echo "ERROR: Expected nine per-run metric rows."
    exit 1
fi

if [[ "$AGG_ROWS" -ne 3 ]]; then
    echo "ERROR: Expected three aggregate rows."
    exit 1
fi

touch "$COMPLETE_FILE"
rm -f "$FAILED_FILE"

echo
echo "Experiment D3A validation: PASS"

echo
echo "Completion marker:"
ls -l "$COMPLETE_FILE"

echo
echo "============================================================"
echo "Experiment D3A multi-seed alignments completed successfully"
echo "Completed: $(date --iso-8601=seconds)"
echo "============================================================"
