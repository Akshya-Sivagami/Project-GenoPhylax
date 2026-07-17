#!/usr/bin/env bash

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

THREADS="$(nproc)"

PROJECT_ROOT="$HOME/Project-GenoPhylax"

REFERENCE_DIR="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB"
REFERENCE_NAME="GCA_000001405.15_GRCh38_no_alt_analysis_set"
REFERENCE_MMI="$REFERENCE_DIR/${REFERENCE_NAME}.map-ont.mmi"

EXP_D_DIR="$PROJECT_ROOT/experiments/A2_adversarial_dna/basecalling/perturbations/experiment_D_alignment"
D1_DIR="$EXP_D_DIR/D1_clean_validation"
D2_DIR="$EXP_D_DIR/D2_seed42_alignment"

FASTQ_DIR="$D2_DIR/fastq"
ALIGN_DIR="$D2_DIR/alignments"
LOG_DIR="$D2_DIR/logs"
METRICS_DIR="$D2_DIR/metrics"
INPUT_DIR="$D2_DIR/input_paths"

COMPLETE_FILE="$D2_DIR/D2_SEED42_ALIGNMENT_COMPLETE"
FAILED_FILE="$D2_DIR/D2_SEED42_ALIGNMENT_FAILED"

CLEAN_ALIGN_BAM="$D1_DIR/alignments/hg002_1000reads_clean_GRCh38.sorted.bam"

SEARCH_ROOTS=(
    "$PROJECT_ROOT/experiments/A2_adversarial_dna/basecalling/perturbations"
    "$HOME/datasets/GenoPhylax/A2_signal_perturbations/gaussian_noise_1000reads"
)

mkdir -p \
    "$FASTQ_DIR" \
    "$ALIGN_DIR" \
    "$LOG_DIR" \
    "$METRICS_DIR" \
    "$INPUT_DIR"

rm -f "$COMPLETE_FILE" "$FAILED_FILE"

trap '
    STATUS=$?
    echo
    echo "============================================================"
    echo "D2 seed-42 pipeline failed with exit status: $STATUS"
    echo "Time: $(date --iso-8601=seconds)"
    echo "============================================================"
    touch "$FAILED_FILE"
    exit "$STATUS"
' ERR

echo "============================================================"
echo "Experiment D2A — Seed-42 alignment pipeline"
echo "Started: $(date --iso-8601=seconds)"
echo "Threads: $THREADS"
echo "============================================================"
echo

echo "[1/8] Validating tools, reference, and CLEAN alignment"
echo "------------------------------------------------------------"

for TOOL in minimap2 samtools python awk sort grep find cut; do
    if ! command -v "$TOOL" >/dev/null 2>&1; then
        echo "ERROR: Missing required tool: $TOOL"
        exit 1
    fi
done

if [[ ! -s "$REFERENCE_MMI" ]]; then
    echo "ERROR: minimap2 reference index not found:"
    echo "$REFERENCE_MMI"
    exit 1
fi

if [[ ! -s "$CLEAN_ALIGN_BAM" ]]; then
    echo "ERROR: D1 CLEAN alignment not found:"
    echo "$CLEAN_ALIGN_BAM"
    exit 1
fi

if ! samtools quickcheck "$CLEAN_ALIGN_BAM"; then
    echo "ERROR: D1 CLEAN alignment failed quickcheck."
    exit 1
fi

echo "Reference index:"
ls -lh "$REFERENCE_MMI"

echo
echo "CLEAN baseline alignment:"
ls -lh "$CLEAN_ALIGN_BAM"

echo
echo "Initial validation: PASS"
echo

echo "[2/8] Locating C1 seed-42 parent-normalized BAMs"
echo "------------------------------------------------------------"

resolve_condition_bam() {
    local CONDITION="$1"
    local CONDITION_LOWER
    local CANDIDATE_FILE
    local FILTERED_FILE
    local SEED42_FILE
    local COUNT
    local SELECTED

    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    CANDIDATE_FILE="$INPUT_DIR/${CONDITION}_all_candidates.txt"
    FILTERED_FILE="$INPUT_DIR/${CONDITION}_filtered_candidates.txt"
    SEED42_FILE="$INPUT_DIR/${CONDITION}_seed42_candidates.txt"

    : > "$CANDIDATE_FILE"

    for ROOT in "${SEARCH_ROOTS[@]}"; do
        if [[ -d "$ROOT" ]]; then
            find "$ROOT" \
                -type f \
                -iname "*${CONDITION_LOWER}*" \
                -iname "*parent*normalized*.bam" \
                2>/dev/null >> "$CANDIDATE_FILE"
        fi
    done

    sort -u "$CANDIDATE_FILE" -o "$CANDIDATE_FILE"

    grep -viE \
        'experiment_C2|multiseed|seed[_-]?(1|2|3)([^0-9]|$)' \
        "$CANDIDATE_FILE" \
        > "$FILTERED_FILE" || true

    grep -Ei \
        'seed[_-]?42|experiment_C_1000reads|experiment_C1|/C1/' \
        "$FILTERED_FILE" \
        > "$SEED42_FILE" || true

    COUNT="$(wc -l < "$SEED42_FILE")"

    if [[ "$COUNT" -eq 1 ]]; then
        SELECTED="$(cat "$SEED42_FILE")"
    else
        COUNT="$(wc -l < "$FILTERED_FILE")"

        if [[ "$COUNT" -eq 1 ]]; then
            SELECTED="$(cat "$FILTERED_FILE")"
        else
            echo "ERROR: Could not uniquely resolve $CONDITION seed-42 BAM."
            echo
            echo "All candidates:"
            cat "$CANDIDATE_FILE" || true
            echo
            echo "Filtered candidates:"
            cat "$FILTERED_FILE" || true
            echo
            echo "Preferred seed-42/C1 candidates:"
            cat "$SEED42_FILE" || true
            return 1
        fi
    fi

    if [[ ! -s "$SELECTED" ]]; then
        echo "ERROR: Selected $CONDITION BAM is missing or empty:"
        echo "$SELECTED"
        return 1
    fi

    printf '%s\n' "$SELECTED"
}

GN01_BAM="$(resolve_condition_bam GN01)"
GN05_BAM="$(resolve_condition_bam GN05)"
GN10_BAM="$(resolve_condition_bam GN10)"

printf '%s\n' "$GN01_BAM" > "$INPUT_DIR/GN01_selected_bam.txt"
printf '%s\n' "$GN05_BAM" > "$INPUT_DIR/GN05_selected_bam.txt"
printf '%s\n' "$GN10_BAM" > "$INPUT_DIR/GN10_selected_bam.txt"

echo "GN01:"
echo "$GN01_BAM"
ls -lh "$GN01_BAM"

echo
echo "GN05:"
echo "$GN05_BAM"
ls -lh "$GN05_BAM"

echo
echo "GN10:"
echo "$GN10_BAM"
ls -lh "$GN10_BAM"
echo

echo "[3/8] Validating selected normalized BAMs"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    case "$CONDITION" in
        GN01) INPUT_BAM="$GN01_BAM" ;;
        GN05) INPUT_BAM="$GN05_BAM" ;;
        GN10) INPUT_BAM="$GN10_BAM" ;;
    esac

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

    echo "$CONDITION records:       $RECORDS"
    echo "$CONDITION unique IDs:    $UNIQUE_IDS"
    echo "$CONDITION duplicate IDs: $DUPLICATE_IDS"

    if [[ "$RECORDS" -ne 1000 ]]; then
        echo "ERROR: $CONDITION does not contain exactly 1,000 records."
        exit 1
    fi

    if [[ "$UNIQUE_IDS" -ne 1000 ]]; then
        echo "ERROR: $CONDITION does not contain 1,000 unique IDs."
        exit 1
    fi

    if [[ "$DUPLICATE_IDS" -ne 0 ]]; then
        echo "ERROR: $CONDITION contains duplicate parent IDs."
        exit 1
    fi

    echo
done

echo "All normalized input BAMs: PASS"
echo

echo "[4/8] Converting perturbed BAMs to FASTQ"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    case "$CONDITION" in
        GN01) INPUT_BAM="$GN01_BAM" ;;
        GN05) INPUT_BAM="$GN05_BAM" ;;
        GN10) INPUT_BAM="$GN10_BAM" ;;
    esac

    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    FASTQ="$FASTQ_DIR/hg002_1000reads_${CONDITION_LOWER}_seed42.fastq"
    FASTQ_LOG="$LOG_DIR/${CONDITION}_fastq.log"

    if [[ -s "$FASTQ" ]] && [[ "$(wc -l < "$FASTQ")" -eq 4000 ]]; then
        echo "$CONDITION valid FASTQ already exists."
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

    echo "$CONDITION FASTQ lines:      $FASTQ_LINES"
    echo "$CONDITION FASTQ reads:      $FASTQ_READS"
    echo "$CONDITION FASTQ unique IDs: $FASTQ_UNIQUE_IDS"

    if [[ "$FASTQ_LINES" -ne 4000 ]] ||
       [[ "$FASTQ_READS" -ne 1000 ]] ||
       [[ "$FASTQ_UNIQUE_IDS" -ne 1000 ]]; then
        echo "ERROR: $CONDITION FASTQ validation failed."
        exit 1
    fi

    echo
done

echo "All FASTQ files: PASS"
echo

echo "[5/8] Aligning GN01, GN05, and GN10 seed 42"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    FASTQ="$FASTQ_DIR/hg002_1000reads_${CONDITION_LOWER}_seed42.fastq"
    ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed42_GRCh38.sorted.bam"
    ALIGN_LOG="$LOG_DIR/${CONDITION}_seed42_minimap2.log"

    echo "Aligning $CONDITION seed 42..."

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
            -R "@RG\tID:HG002_${CONDITION}_S42\tSM:HG002\tPL:ONT\tLB:HG002_1000reads" \
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

    echo "$CONDITION alignment:"
    ls -lh "$ALIGN_BAM" "${ALIGN_BAM}.bai"

    echo
    echo "$CONDITION minimap2 log tail:"
    tail -20 "$ALIGN_LOG" 2>/dev/null || true
    echo
done

echo "[6/8] Validating all perturbed alignments"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"
    ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed42_GRCh38.sorted.bam"

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

    echo "$CONDITION total records:         $TOTAL_RECORDS"
    echo "$CONDITION primary records:       $PRIMARY_RECORDS"
    echo "$CONDITION unique primary IDs:    $UNIQUE_PRIMARY_IDS"
    echo "$CONDITION duplicate primary IDs: $DUPLICATE_PRIMARY_IDS"

    if [[ "$PRIMARY_RECORDS" -ne 1000 ]] ||
       [[ "$UNIQUE_PRIMARY_IDS" -ne 1000 ]] ||
       [[ "$DUPLICATE_PRIMARY_IDS" -ne 0 ]]; then
        echo "ERROR: $CONDITION primary read accounting failed."
        exit 1
    fi

    echo
done

echo "All perturbed alignments: PASS"
echo

echo "[7/8] Generating aggregate alignment metrics"
echo "------------------------------------------------------------"

SUMMARY_TSV="$METRICS_DIR/experiment_D2_seed42_alignment_summary.tsv"

printf '%s\n' \
    $'condition\tinput_reads\ttotal_records\tprimary_records\tmapped_primary\tunmapped_primary\tmapped_percent\tsecondary\tsupplementary\tmean_mapped_mapq\tmapq_ge20\tmapq_ge30\tmapq_ge60' \
    > "$SUMMARY_TSV"

for CONDITION in CLEAN GN01 GN05 GN10; do
    if [[ "$CONDITION" == "CLEAN" ]]; then
        ALIGN_BAM="$CLEAN_ALIGN_BAM"
    else
        CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"
        ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed42_GRCh38.sorted.bam"
    fi

    FLAGSTAT="$METRICS_DIR/${CONDITION}_seed42_flagstat.txt"
    STATS="$METRICS_DIR/${CONDITION}_seed42_stats.txt"
    IDXSTATS="$METRICS_DIR/${CONDITION}_seed42_idxstats.txt"

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

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$CONDITION" \
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
        >> "$SUMMARY_TSV"
done

echo "Aggregate metrics:"
column -t -s $'\t' "$SUMMARY_TSV" 2>/dev/null || cat "$SUMMARY_TSV"
echo

echo "[8/8] Final D2A validation"
echo "------------------------------------------------------------"

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    FASTQ="$FASTQ_DIR/hg002_1000reads_${CONDITION_LOWER}_seed42.fastq"
    ALIGN_BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed42_GRCh38.sorted.bam"

    [[ -s "$FASTQ" ]]
    [[ -s "$ALIGN_BAM" ]]
    [[ -s "${ALIGN_BAM}.bai" ]]
    [[ "$(samtools view -c -F 2304 "$ALIGN_BAM")" -eq 1000 ]]
done

[[ -s "$SUMMARY_TSV" ]]

touch "$COMPLETE_FILE"
rm -f "$FAILED_FILE"

echo "Experiment D2A validation: PASS"

echo
echo "Completion marker:"
ls -l "$COMPLETE_FILE"

echo
echo "============================================================"
echo "Experiment D2A seed-42 alignments completed successfully"
echo "Completed: $(date --iso-8601=seconds)"
echo "============================================================"
