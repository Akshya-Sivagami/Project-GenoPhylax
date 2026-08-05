#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

VENV="experiments/A2_adversarial_dna/basecalling/environment/pod5_env"
source "$VENV/bin/activate"

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate"
AUDIT_DIR="$RESULTS_DIR/validation_audit"
LOG_DIR="$A3_DIR/logs"
MARKER_DIR="$A3_DIR/markers"

mkdir -p "$AUDIT_DIR" "$LOG_DIR" "$MARKER_DIR"

COMPLETE_MARKER="$MARKER_DIR/A3_F11_VALIDATION_AND_CHECKPOINT.COMPLETE"
FAILED_MARKER="$MARKER_DIR/A3_F11_VALIDATION_AND_CHECKPOINT.FAILED"

REFERENCE="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"

TRUTH_VCF="$HOME/datasets/GenoPhylax/truth/HG002_GRCh38_v4.2.1/HG002_GRCh38_1_22_v4.2.1_benchmark.vcf.gz"

CLINVAR_VCF="$A3_DIR/references/clinvar/clinvar_GRCh38.vcf.gz"

CLINVAR_RECORD="$RESULTS_DIR/ClinVar_F11_record.vcf"
TRUTH_RECORD="$RESULTS_DIR/HG002_F11_truth_record.vcf"

ONT_BAM="$RESULTS_DIR/ONT_target_retrieval/F11_PAO89685_region.sorted.bam"
PER_RECORD_TSV="$RESULTS_DIR/ONT_target_retrieval/F11_target_per_record_states.tsv"
PER_PARENT_TSV="$RESULTS_DIR/ONT_target_retrieval/F11_target_per_parent_states.tsv"

TARGET_CHROM="chr4"
TARGET_POS="186274193"
TARGET_REF="G"
TARGET_ALT="T"

TARGET_REGION="${TARGET_CHROM}:${TARGET_POS}-${TARGET_POS}"
CONTEXT_START=$((TARGET_POS - 100))
CONTEXT_END=$((TARGET_POS + 100))
CONTEXT_REGION="${TARGET_CHROM}:${CONTEXT_START}-${CONTEXT_END}"

COORD_AUDIT="$AUDIT_DIR/F11_GRCh38_coordinate_audit.txt"
CONTEXT_FASTA="$AUDIT_DIR/F11_local_context_201bp.fasta"
CONTEXT_REPORT="$AUDIT_DIR/F11_local_sequence_context_report.txt"
GIAB_BED_REPORT="$AUDIT_DIR/F11_GIAB_high_confidence_audit.txt"
ONT_QUALITY_TSV="$AUDIT_DIR/F11_ONT_alignment_quality.tsv"
ONT_QUALITY_SUMMARY="$AUDIT_DIR/F11_ONT_alignment_quality_summary.txt"
STAGED_FILES="$AUDIT_DIR/A3_checkpoint_staged_files.txt"
STAGED_SIZES="$AUDIT_DIR/A3_checkpoint_staged_file_sizes.tsv"
CHECKPOINT_SUMMARY="$AUDIT_DIR/A3_checkpoint_summary.txt"

rm -f "$FAILED_MARKER"

trap 'status=$?;
      echo;
      echo "ERROR: F11 validation/checkpoint workflow failed with status ${status}";
      date -Is > "$FAILED_MARKER";
      echo "Exit status: ${status}" >> "$FAILED_MARKER";
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — VALIDATION AND CHECKPOINT WORKFLOW"
echo "============================================================"
echo "Started: $(date -Is)"
echo

echo "[1/10] Checking required programs"

for tool in python samtools bcftools git awk sed grep find sort stat; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "ERROR: Missing required program: $tool"
        exit 1
    fi
done

samtools --version | head -2
bcftools --version | head -2
git --version
python --version

echo
echo "[2/10] Validating required inputs"

for file in \
    "$REFERENCE" \
    "$TRUTH_VCF" \
    "$CLINVAR_VCF" \
    "$CLINVAR_RECORD" \
    "$TRUTH_RECORD" \
    "$ONT_BAM" \
    "${ONT_BAM}.bai" \
    "$PER_RECORD_TSV" \
    "$PER_PARENT_TSV"; do

    if [[ ! -s "$file" ]]; then
        echo "ERROR: Required input is missing or empty:"
        echo "$file"
        exit 1
    fi
done

if [[ ! -s "${REFERENCE}.fai" ]]; then
    samtools faidx "$REFERENCE"
fi

samtools quickcheck -v "$ONT_BAM"

echo
echo "[3/10] Building explicit GRCh38 coordinate audit"

REFERENCE_BASE="$(
    samtools faidx "$REFERENCE" "$TARGET_REGION" \
        | awk 'NR > 1 {printf "%s", $0}' \
        | tr '[:lower:]' '[:upper:]'
)"

TRUTH_LINE="$(
    bcftools view \
        -H \
        -r "$TARGET_REGION" \
        "$TRUTH_VCF" \
        | awk -v ref="$TARGET_REF" -v alt="$TARGET_ALT" \
            '$4 == ref && index(","$5",", ","alt",") > 0 {print; exit}'
)"

CLINVAR_LINE="$(
    bcftools view \
        -H \
        -r "4:${TARGET_POS}-${TARGET_POS}" \
        "$CLINVAR_VCF" \
        | awk -v ref="$TARGET_REF" -v alt="$TARGET_ALT" \
            '$4 == ref && index(","$5",", ","alt",") > 0 {print; exit}'
)"

LOCAL_TRUTH_LINE="$(
    awk -v chrom="$TARGET_CHROM" \
        -v pos="$TARGET_POS" \
        -v ref="$TARGET_REF" \
        -v alt="$TARGET_ALT" \
        '$1 == chrom && $2 == pos && $4 == ref &&
         index(","$5",", ","alt",") > 0 {print; exit}' \
        "$TRUTH_RECORD"
)"

LOCAL_CLINVAR_LINE="$(
    awk -v pos="$TARGET_POS" \
        -v ref="$TARGET_REF" \
        -v alt="$TARGET_ALT" \
        '$2 == pos && $4 == ref &&
         index(","$5",", ","alt",") > 0 {print; exit}' \
        "$CLINVAR_RECORD"
)"

if [[ "$REFERENCE_BASE" != "$TARGET_REF" ]]; then
    echo "ERROR: Reference base mismatch."
    echo "Expected: $TARGET_REF"
    echo "Observed: $REFERENCE_BASE"
    exit 1
fi

if [[ -z "$TRUTH_LINE" ]]; then
    echo "ERROR: Exact F11 allele not found in HG002 truth VCF."
    exit 1
fi

if [[ -z "$CLINVAR_LINE" ]]; then
    echo "ERROR: Exact F11 allele not found in ClinVar GRCh38 VCF."
    exit 1
fi

if [[ -z "$LOCAL_TRUTH_LINE" ]]; then
    echo "ERROR: Local saved HG002 truth record does not match target."
    exit 1
fi

if [[ -z "$LOCAL_CLINVAR_LINE" ]]; then
    echo "ERROR: Local saved ClinVar record does not match target."
    exit 1
fi

TRUTH_GT="$(
    printf '%s\n' "$TRUTH_LINE" \
        | bcftools query -f '[%GT]\n' 2>/dev/null || true
)"

TRUTH_FILTER="$(
    printf '%s\n' "$TRUTH_LINE" \
        | awk -F '\t' '{print $7}'
)"

CLINVAR_INFO="$(
    printf '%s\n' "$CLINVAR_LINE" \
        | awk -F '\t' '{print $8}'
)"

CLINVAR_CLNSIG="$(
    printf '%s\n' "$CLINVAR_INFO" \
        | tr ';' '\n' \
        | awk -F '=' '$1 == "CLNSIG" {print $2; exit}'
)"

CLINVAR_REVIEW="$(
    printf '%s\n' "$CLINVAR_INFO" \
        | tr ';' '\n' \
        | awk -F '=' '$1 == "CLNREVSTAT" {print $2; exit}'
)"

CLINVAR_MC="$(
    printf '%s\n' "$CLINVAR_INFO" \
        | tr ';' '\n' \
        | awk -F '=' '$1 == "MC" {print $2; exit}'
)"

CLINVAR_RS="$(
    printf '%s\n' "$CLINVAR_INFO" \
        | tr ';' '\n' \
        | awk -F '=' '$1 == "RS" {print $2; exit}'
)"

CLINVAR_VARIATION_ID="$(
    printf '%s\n' "$CLINVAR_INFO" \
        | tr ';' '\n' \
        | awk -F '=' '$1 == "ALLELEID" || $1 == "CLNVC" {print $2; exit}'
)"

{
    echo "F11 GRCh38 Coordinate and Allele Audit"
    echo "======================================="
    echo
    echo "Completed: $(date -Is)"
    echo
    echo "Expected target:"
    echo "Chromosome: $TARGET_CHROM"
    echo "Position: $TARGET_POS"
    echo "REF: $TARGET_REF"
    echo "ALT: $TARGET_ALT"
    echo
    echo "Reference assembly:"
    echo "$REFERENCE"
    echo
    echo "Reference sequence name:"
    grep -m1 '^>' <(
        samtools faidx "$REFERENCE" "$TARGET_REGION"
    )
    echo
    echo "Reference-base validation:"
    echo "Observed base: $REFERENCE_BASE"
    echo "Expected base: $TARGET_REF"
    echo "Status: PASS"
    echo
    echo "HG002 GIAB truth source:"
    echo "$TRUTH_VCF"
    echo
    echo "Exact truth record:"
    echo "$TRUTH_LINE"
    echo
    echo "Truth FILTER: $TRUTH_FILTER"
    echo "Truth GT: ${TRUTH_GT:-NOT_PARSED}"
    echo
    echo "ClinVar GRCh38 source:"
    echo "$CLINVAR_VCF"
    echo
    echo "Exact ClinVar record:"
    echo "$CLINVAR_LINE"
    echo
    echo "ClinVar CLNSIG: ${CLINVAR_CLNSIG:-NOT_PRESENT}"
    echo "ClinVar review status: ${CLINVAR_REVIEW:-NOT_PRESENT}"
    echo "ClinVar molecular consequence: ${CLINVAR_MC:-NOT_PRESENT}"
    echo "ClinVar dbSNP RS: ${CLINVAR_RS:-NOT_PRESENT}"
    echo
    echo "Saved local truth-record validation: PASS"
    echo "Saved local ClinVar-record validation: PASS"
    echo
    echo "Assembly/coordinate conclusion:"
    echo "The reference, GIAB truth VCF, ClinVar GRCh38 VCF and ONT query"
    echo "all use the same GRCh38 coordinate chr4:186274193 G>T."
    echo
    echo "Overall status: PASS"
} > "$COORD_AUDIT"

cat "$COORD_AUDIT"

echo
echo "[4/10] Auditing local sequence context"

samtools faidx "$REFERENCE" "$CONTEXT_REGION" > "$CONTEXT_FASTA"

export CONTEXT_FASTA
export CONTEXT_REPORT
export TARGET_POS
export CONTEXT_START
export TARGET_REF
export TARGET_ALT

python <<'PY_EOF'
import os
import re
from collections import Counter
from pathlib import Path

fasta_path = Path(os.environ["CONTEXT_FASTA"])
report_path = Path(os.environ["CONTEXT_REPORT"])

target_pos = int(os.environ["TARGET_POS"])
context_start = int(os.environ["CONTEXT_START"])
expected_ref = os.environ["TARGET_REF"].upper()
alt = os.environ["TARGET_ALT"].upper()

lines = fasta_path.read_text().splitlines()
sequence = "".join(
    line.strip()
    for line in lines
    if line and not line.startswith(">")
).upper()

target_index = target_pos - context_start
observed_ref = sequence[target_index]

if observed_ref != expected_ref:
    raise SystemExit(
        f"Reference mismatch in extracted context: "
        f"expected {expected_ref}, observed {observed_ref}"
    )

length = len(sequence)
gc_count = sequence.count("G") + sequence.count("C")
gc_percent = 100.0 * gc_count / length if length else 0.0

max_homopolymer = 0
max_homopolymer_base = ""
current_base = ""
current_length = 0

for base in sequence:
    if base == current_base:
        current_length += 1
    else:
        current_base = base
        current_length = 1

    if current_length > max_homopolymer:
        max_homopolymer = current_length
        max_homopolymer_base = base

target_run_start = target_index
target_run_end = target_index

while (
    target_run_start > 0
    and sequence[target_run_start - 1] == observed_ref
):
    target_run_start -= 1

while (
    target_run_end + 1 < length
    and sequence[target_run_end + 1] == observed_ref
):
    target_run_end += 1

target_homopolymer_length = target_run_end - target_run_start + 1

repeat_hits = []

for motif_length in range(1, 7):
    for start in range(0, length - motif_length * 3 + 1):
        motif = sequence[start:start + motif_length]

        if "N" in motif:
            continue

        copies = 1
        cursor = start + motif_length

        while sequence[cursor:cursor + motif_length] == motif:
            copies += 1
            cursor += motif_length

        if copies >= 3:
            repeat_hits.append(
                (
                    start,
                    cursor,
                    motif,
                    copies,
                    motif_length * copies,
                )
            )

repeat_hits = sorted(
    set(repeat_hits),
    key=lambda item: (-item[4], item[0], item[2]),
)

target_repeat_hits = [
    item
    for item in repeat_hits
    if item[0] <= target_index < item[1]
]

low_complexity_window = sequence[
    max(0, target_index - 10):
    min(length, target_index + 11)
]

base_counts = Counter(low_complexity_window)
dominant_fraction = (
    max(base_counts.values()) / len(low_complexity_window)
    if low_complexity_window
    else 0.0
)

with report_path.open("w") as handle:
    handle.write("F11 Local Sequence Context Audit\n")
    handle.write("================================\n\n")
    handle.write(f"Context length: {length} bp\n")
    handle.write(f"Context region: chr4:{context_start}-{context_start + length - 1}\n")
    handle.write(f"Target genomic position: {target_pos}\n")
    handle.write(f"Target context index: {target_index}\n")
    handle.write(f"Observed REF base: {observed_ref}\n")
    handle.write(f"Expected REF base: {expected_ref}\n")
    handle.write(f"ALT base: {alt}\n\n")

    handle.write(f"GC percentage: {gc_percent:.2f}%\n")
    handle.write(
        f"Longest homopolymer in 201-bp context: "
        f"{max_homopolymer_base} x {max_homopolymer}\n"
    )
    handle.write(
        f"Target-base homopolymer length: "
        f"{target_homopolymer_length}\n"
    )
    handle.write(
        f"21-bp target-window dominant-base fraction: "
        f"{dominant_fraction:.3f}\n"
    )
    handle.write(
        f"Number of tandem-repeat candidates: "
        f"{len(repeat_hits)}\n"
    )
    handle.write(
        f"Number of tandem-repeat candidates overlapping target: "
        f"{len(target_repeat_hits)}\n\n"
    )

    handle.write("Target-centered 41-bp sequence:\n")
    handle.write(
        sequence[
            max(0, target_index - 20):
            min(length, target_index + 21)
        ]
        + "\n\n"
    )

    handle.write("Longest detected tandem-repeat candidates:\n")

    if repeat_hits:
        for start, end, motif, copies, span in repeat_hits[:20]:
            genomic_start = context_start + start
            genomic_end = context_start + end - 1
            overlaps = start <= target_index < end

            handle.write(
                f"{genomic_start}-{genomic_end}\t"
                f"motif={motif}\t"
                f"copies={copies}\t"
                f"span={span}\t"
                f"overlaps_target={int(overlaps)}\n"
            )
    else:
        handle.write("None detected by the simple repeat screen.\n")

    handle.write("\nInterpretation flags:\n")

    flags = []

    if target_homopolymer_length >= 4:
        flags.append("TARGET_IN_HOMOPOLYMER")

    if target_repeat_hits:
        flags.append("TARGET_IN_TANDEM_REPEAT")

    if dominant_fraction >= 0.75:
        flags.append("LOW_COMPLEXITY_TARGET_WINDOW")

    if not flags:
        flags.append("NO_SIMPLE_LOCAL_COMPLEXITY_FLAG")

    for flag in flags:
        handle.write(f"- {flag}\n")

    handle.write(
        "\nNote: This is a deterministic local-sequence screen, "
        "not a full genome-wide mappability model.\n"
    )

print(report_path.read_text())
PY_EOF

echo
echo "[5/10] Checking GIAB high-confidence BED inclusion"

{
    echo "F11 GIAB High-Confidence Region Audit"
    echo "======================================"
    echo
    echo "Completed: $(date -Is)"
    echo "Target: $TARGET_REGION"
    echo
} > "$GIAB_BED_REPORT"

mapfile -t GIAB_BEDS < <(
    find "$HOME/datasets/GenoPhylax" \
        -type f \
        \( \
            -iname '*HG002*GRCh38*.bed' \
            -o -iname '*HG002*GRCh38*.bed.gz' \
            -o -iname '*benchmark*.bed' \
            -o -iname '*benchmark*.bed.gz' \
        \) \
        2>/dev/null \
        | sort -u
)

if [[ "${#GIAB_BEDS[@]}" -eq 0 ]]; then
    {
        echo "No candidate GIAB high-confidence BED file was found locally."
        echo "Status: BED_NOT_AVAILABLE"
        echo
        echo "The truth VCF exact PASS record remains available, but explicit"
        echo "BED containment could not be independently checked."
    } >> "$GIAB_BED_REPORT"
else
    BED_CONTAINMENT_FOUND=0

    for bed in "${GIAB_BEDS[@]}"; do
        echo "Candidate BED: $bed" >> "$GIAB_BED_REPORT"

        if [[ "$bed" == *.gz ]]; then
            MATCH="$(
                gzip -cd "$bed" 2>/dev/null \
                    | awk \
                        -v chrom="$TARGET_CHROM" \
                        -v pos0="$((TARGET_POS - 1))" \
                        '$1 == chrom && $2 <= pos0 && $3 > pos0 {
                            print
                            exit
                        }'
            )"
        else
            MATCH="$(
                awk \
                    -v chrom="$TARGET_CHROM" \
                    -v pos0="$((TARGET_POS - 1))" \
                    '$1 == chrom && $2 <= pos0 && $3 > pos0 {
                        print
                        exit
                    }' "$bed"
            )"
        fi

        if [[ -n "$MATCH" ]]; then
            BED_CONTAINMENT_FOUND=1
            echo "Containment: PASS" >> "$GIAB_BED_REPORT"
            echo "Matching interval: $MATCH" >> "$GIAB_BED_REPORT"
        else
            echo "Containment: NOT_FOUND_IN_THIS_FILE" >> "$GIAB_BED_REPORT"
        fi

        echo >> "$GIAB_BED_REPORT"
    done

    if [[ "$BED_CONTAINMENT_FOUND" -eq 1 ]]; then
        echo "Overall status: PASS" >> "$GIAB_BED_REPORT"
    else
        echo "Overall status: NOT_CONFIRMED" >> "$GIAB_BED_REPORT"
    fi
fi

cat "$GIAB_BED_REPORT"

echo
echo "[6/10] Auditing ONT mapping quality and strand support"

export ONT_BAM
export TARGET_CHROM
export TARGET_POS
export TARGET_REF
export TARGET_ALT
export ONT_QUALITY_TSV
export ONT_QUALITY_SUMMARY

python <<'PY_EOF'
import csv
import os
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import pysam

bam_path = Path(os.environ["ONT_BAM"])
chrom = os.environ["TARGET_CHROM"]
target_pos_1 = int(os.environ["TARGET_POS"])
target_pos_0 = target_pos_1 - 1
ref = os.environ["TARGET_REF"].upper()
alt = os.environ["TARGET_ALT"].upper()

tsv_path = Path(os.environ["ONT_QUALITY_TSV"])
summary_path = Path(os.environ["ONT_QUALITY_SUMMARY"])

rows = []
parent_states = defaultdict(list)

with pysam.AlignmentFile(str(bam_path), "rb") as bam:
    for read in bam.fetch(chrom, target_pos_0, target_pos_1):
        state = "NO_COVERAGE"
        observed = ""
        query_pos = None

        for qpos, rpos in read.get_aligned_pairs(matches_only=False):
            if rpos != target_pos_0:
                continue

            query_pos = qpos

            if qpos is None:
                state = "DEL"
                observed = "-"
            elif read.query_sequence is None:
                state = "NO_SEQUENCE"
            else:
                observed = read.query_sequence[qpos].upper()

                if observed == ref:
                    state = "REF"
                elif observed == alt:
                    state = "ALT"
                else:
                    state = "OTHER"

            break

        read_length = (
            read.query_length
            if read.query_length is not None
            else 0
        )

        if query_pos is None or read_length == 0:
            relative_position = ""
        else:
            relative_position = query_pos / read_length

        row = {
            "read_id": read.query_name,
            "state": state,
            "observed_base": observed,
            "mapping_quality": read.mapping_quality,
            "strand": "-" if read.is_reverse else "+",
            "is_primary": int(
                not read.is_secondary
                and not read.is_supplementary
            ),
            "is_secondary": int(read.is_secondary),
            "is_supplementary": int(read.is_supplementary),
            "query_length": read_length,
            "target_query_position_0based": (
                "" if query_pos is None else query_pos
            ),
            "target_relative_read_position": (
                ""
                if relative_position == ""
                else f"{relative_position:.6f}"
            ),
        }

        rows.append(row)
        parent_states[read.query_name].append(state)

fields = [
    "read_id",
    "state",
    "observed_base",
    "mapping_quality",
    "strand",
    "is_primary",
    "is_secondary",
    "is_supplementary",
    "query_length",
    "target_query_position_0based",
    "target_relative_read_position",
]

with tsv_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=fields,
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(rows)

state_counts = Counter(row["state"] for row in rows)
strand_counts = Counter(
    (row["state"], row["strand"])
    for row in rows
)
mapqs = defaultdict(list)
relative_positions = defaultdict(list)

for row in rows:
    mapqs[row["state"]].append(row["mapping_quality"])

    value = row["target_relative_read_position"]

    if value != "":
        relative_positions[row["state"]].append(float(value))

supplementary_count = sum(
    row["is_supplementary"]
    for row in rows
)

secondary_count = sum(
    row["is_secondary"]
    for row in rows
)

primary_count = sum(
    row["is_primary"]
    for row in rows
)

with summary_path.open("w") as handle:
    handle.write("F11 ONT Alignment Quality Audit\n")
    handle.write("================================\n\n")
    handle.write(f"Target: {chrom}:{target_pos_1} {ref}>{alt}\n")
    handle.write(f"Alignment records: {len(rows)}\n")
    handle.write(f"Unique parent reads: {len(parent_states)}\n")
    handle.write(f"Primary records: {primary_count}\n")
    handle.write(f"Secondary records: {secondary_count}\n")
    handle.write(f"Supplementary records: {supplementary_count}\n\n")

    handle.write("Allele-state counts:\n")

    for state in sorted(state_counts):
        handle.write(f"{state}: {state_counts[state]}\n")

    handle.write("\nStrand support:\n")

    for state in sorted(state_counts):
        handle.write(
            f"{state}: "
            f"forward={strand_counts[(state, '+')]}, "
            f"reverse={strand_counts[(state, '-')]}\n"
        )

    handle.write("\nMapping-quality summary:\n")

    for state in sorted(mapqs):
        values = mapqs[state]

        handle.write(
            f"{state}: "
            f"n={len(values)}, "
            f"min={min(values)}, "
            f"median={statistics.median(values):.2f}, "
            f"mean={statistics.mean(values):.2f}, "
            f"max={max(values)}\n"
        )

    handle.write("\nTarget relative-position summary:\n")

    for state in sorted(relative_positions):
        values = relative_positions[state]

        handle.write(
            f"{state}: "
            f"n={len(values)}, "
            f"min={min(values):.4f}, "
            f"median={statistics.median(values):.4f}, "
            f"max={max(values):.4f}\n"
        )

    alt_forward = strand_counts[("ALT", "+")]
    alt_reverse = strand_counts[("ALT", "-")]
    ref_forward = strand_counts[("REF", "+")]
    ref_reverse = strand_counts[("REF", "-")]

    handle.write("\nInterpretation flags:\n")

    flags = []

    if alt_forward == 0 or alt_reverse == 0:
        flags.append("ALT_STRAND_IMBALANCE")

    if ref_forward == 0 or ref_reverse == 0:
        flags.append("REF_STRAND_IMBALANCE")

    if supplementary_count > 0:
        flags.append("SUPPLEMENTARY_RECORDS_PRESENT")

    if secondary_count > 0:
        flags.append("SECONDARY_RECORDS_PRESENT")

    if any(
        row["mapping_quality"] < 20
        for row in rows
        if row["state"] in {"ALT", "REF"}
    ):
        flags.append("LOW_MAPQ_TARGET_RECORD_PRESENT")

    if not flags:
        flags.append("NO_BASIC_ONT_ALIGNMENT_QUALITY_FLAG")

    for flag in flags:
        handle.write(f"- {flag}\n")

print(summary_path.read_text())
PY_EOF

echo
echo "[7/10] Updating .gitignore for A3 large data"

touch .gitignore

GITIGNORE_BLOCK_START="# BEGIN GENOPHYLAX A3 LARGE DATA"
GITIGNORE_BLOCK_END="# END GENOPHYLAX A3 LARGE DATA"

if grep -Fq "$GITIGNORE_BLOCK_START" .gitignore; then
    awk \
        -v start="$GITIGNORE_BLOCK_START" \
        -v end="$GITIGNORE_BLOCK_END" '
        $0 == start {skip=1; next}
        $0 == end {skip=0; next}
        !skip {print}
    ' .gitignore > .gitignore.A3.tmp

    mv .gitignore.A3.tmp .gitignore
fi

cat >> .gitignore <<'IGNORE_EOF'

# BEGIN GENOPHYLAX A3 LARGE DATA
experiments/A3_clinical_consequence_mapping/references/clinvar/*.vcf.gz
experiments/A3_clinical_consequence_mapping/references/clinvar/*.vcf.gz.tbi
experiments/A3_clinical_consequence_mapping/**/*.bam
experiments/A3_clinical_consequence_mapping/**/*.bam.bai
experiments/A3_clinical_consequence_mapping/**/*.cram
experiments/A3_clinical_consequence_mapping/**/*.crai
experiments/A3_clinical_consequence_mapping/**/*.pod5
experiments/A3_clinical_consequence_mapping/**/*normalized*.vcf.gz
experiments/A3_clinical_consequence_mapping/**/*normalized*.vcf.gz.tbi
experiments/A3_clinical_consequence_mapping/**/isec_exact/
experiments/A3_clinical_consequence_mapping/**/*.pid
# END GENOPHYLAX A3 LARGE DATA
IGNORE_EOF

echo "Updated .gitignore block:"
sed -n \
    "/$GITIGNORE_BLOCK_START/,/$GITIGNORE_BLOCK_END/p" \
    .gitignore

echo
echo "[8/10] Reviewing A3 files and staging safe checkpoint"

git reset

git add .gitignore

while IFS= read -r file; do
    [[ -f "$file" ]] || continue

    size="$(stat -c '%s' "$file")"

    case "$file" in
        *.bam|*.bam.bai|*.cram|*.crai|*.pod5|*.vcf.gz|*.vcf.gz.tbi)
            continue
            ;;
    esac

    if [[ "$size" -gt 52428800 ]]; then
        echo "Skipping file larger than 50 MiB:"
        echo "$file"
        continue
    fi

    git add -- "$file"

done < <(
    find "$A3_DIR" \
        -type f \
        ! -path '*/__pycache__/*' \
        ! -path '*/pod5_env/*' \
        ! -name '*.pyc' \
        ! -name '*.bak' \
        ! -name '*.tmp' \
        ! -name '*.pid' \
        | sort
)

git diff --cached --name-only > "$STAGED_FILES"

{
    printf 'size_bytes\tpath\n'

    while IFS= read -r file; do
        [[ -f "$file" ]] || continue
        printf '%s\t%s\n' "$(stat -c '%s' "$file")" "$file"
    done < "$STAGED_FILES"

} > "$STAGED_SIZES"

echo
echo "Staged files:"
cat "$STAGED_FILES"

echo
echo "Staged size summary:"
sort -nr "$STAGED_SIZES" | head -40

echo
echo "Git staged statistics:"
git diff --cached --stat

echo
echo "[9/10] Enforcing commit safety gates"

FORBIDDEN_STAGED="$(
    git diff --cached --name-only \
        | grep -E \
            '\.(bam|bai|cram|crai|pod5|vcf\.gz|tbi)$' \
        || true
)"

if [[ -n "$FORBIDDEN_STAGED" ]]; then
    echo "ERROR: Forbidden large genomic files are staged:"
    echo "$FORBIDDEN_STAGED"
    echo
    echo "Nothing will be committed."
    exit 1
fi

OVERSIZED_STAGED="$(
    while IFS= read -r file; do
        [[ -f "$file" ]] || continue

        size="$(stat -c '%s' "$file")"

        if [[ "$size" -gt 52428800 ]]; then
            printf '%s\t%s\n' "$size" "$file"
        fi
    done < <(git diff --cached --name-only)
)"

if [[ -n "$OVERSIZED_STAGED" ]]; then
    echo "ERROR: Files larger than 50 MiB are staged:"
    echo "$OVERSIZED_STAGED"
    echo
    echo "Nothing will be committed."
    exit 1
fi

if git diff --cached --quiet; then
    echo "No safe A3 changes are staged."
    echo "Nothing to commit."
    COMMIT_CREATED="NO"
else
    git commit -m \
        "Add A3 F11 clinical candidate validation and ONT retrieval audit"

    COMMIT_CREATED="YES"
fi

echo
echo "[10/10] Pushing and recording checkpoint"

git push origin main

LATEST_COMMIT="$(git rev-parse HEAD)"
LATEST_COMMIT_SHORT="$(git rev-parse --short HEAD)"

{
    echo "A3 F11 Validation and Checkpoint Summary"
    echo "========================================="
    echo
    echo "Completed: $(date -Is)"
    echo
    echo "Target: $TARGET_CHROM:$TARGET_POS $TARGET_REF>$TARGET_ALT"
    echo
    echo "Coordinate audit:"
    echo "$COORD_AUDIT"
    echo
    echo "Sequence-context audit:"
    echo "$CONTEXT_REPORT"
    echo
    echo "GIAB BED audit:"
    echo "$GIAB_BED_REPORT"
    echo
    echo "ONT alignment-quality audit:"
    echo "$ONT_QUALITY_SUMMARY"
    echo
    echo "Commit created: $COMMIT_CREATED"
    echo "Current commit: $LATEST_COMMIT"
    echo "Current short commit: $LATEST_COMMIT_SHORT"
    echo
    echo "Branch status:"
    git status --short --branch
} > "$CHECKPOINT_SUMMARY"

{
    echo "Completed: $(date -Is)"
    echo "Target: $TARGET_CHROM:$TARGET_POS $TARGET_REF>$TARGET_ALT"
    echo "Coordinate validation: PASS"
    echo "Commit created: $COMMIT_CREATED"
    echo "Commit: $LATEST_COMMIT"
    echo "Summary: $CHECKPOINT_SUMMARY"
} > "$COMPLETE_MARKER"

rm -f "$FAILED_MARKER"

echo
echo "============================================================"
echo "A3 F11 VALIDATION AND CHECKPOINT COMPLETE"
echo "============================================================"
cat "$CHECKPOINT_SUMMARY"
