#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

source \
    experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate"
ATTACK_DIR="$RESULTS_DIR/controlled_signal_attacks"
OUTPUT_DIR="$RESULTS_DIR/attacked_rebasecalling"
SIGNAL_DIR="$RESULTS_DIR/signal_target_mapping"
CLEAN_DIR="$RESULTS_DIR/clean_rebasecalling"
MARKER_DIR="$A3_DIR/markers"

ATTACK_IDS="$SIGNAL_DIR/F11_clean_ALT_attack_parent_ids.txt"
CLEAN_PARENT_AUDIT="$CLEAN_DIR/F11_clean_target_parent_audit.tsv"

REFERENCE="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"

MASTER_SUMMARY="$OUTPUT_DIR/F11_attacked_rebasecalling_summary.tsv"
MASTER_TRANSITIONS="$OUTPUT_DIR/F11_clean_to_attacked_parent_transitions.tsv"
MASTER_REPORT="$OUTPUT_DIR/F11_attacked_rebasecalling_report.txt"

COMPLETE="$MARKER_DIR/A3_F11_ATTACKED_REBASECALLING.COMPLETE"
FAILED="$MARKER_DIR/A3_F11_ATTACKED_REBASECALLING.FAILED"

CONDITIONS=(W0 PM2 PM5 PM10 PM20)

mkdir -p "$OUTPUT_DIR" "$MARKER_DIR"

rm -f "$FAILED"

trap 'status=$?;
      {
          echo "Failed: $(date -Is)"
          echo "Exit status: $status"
      } > "$FAILED";
      echo "ERROR: Attacked rebasecalling failed with status $status";
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — ATTACKED REBASECALLING AND CONSEQUENCE ANALYSIS"
echo "============================================================"
echo "Started: $(date -Is)"
echo

echo "[1/8] Resolving tools and model"

DORADO="$(command -v dorado 2>/dev/null || true)"

if [[ -z "$DORADO" ]]; then
    DORADO="$(
        find "$HOME" \
            -type f \
            -path '*/bin/dorado' \
            -perm -111 \
            2>/dev/null \
            | head -1
    )"
fi

if [[ -z "$DORADO" || ! -x "$DORADO" ]]; then
    echo "ERROR: Dorado could not be located."
    exit 1
fi

for tool in samtools minimap2 python; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "ERROR: Missing required tool: $tool"
        exit 1
    }
done

MODEL_NAME="dna_r10.4.1_e8.2_400bps_hac@v6.0.0"

MODEL_PATH="$(
    find "$HOME" \
        -type d \
        -name "$MODEL_NAME" \
        2>/dev/null \
        | head -1
)"

if [[ -z "$MODEL_PATH" ]]; then
    echo "ERROR: Dorado model not found:"
    echo "$MODEL_NAME"
    exit 1
fi

if [[ ! -s "$REFERENCE" ]]; then
    echo "ERROR: GRCh38 reference missing:"
    echo "$REFERENCE"
    exit 1
fi

if [[ ! -s "$REFERENCE.fai" ]]; then
    samtools faidx "$REFERENCE"
fi

echo "Dorado: $DORADO"
"$DORADO" --version
echo "Model: $MODEL_PATH"
echo "Reference: $REFERENCE"

echo
echo "[2/8] Clearing previous aggregate outputs"

rm -f \
    "$MASTER_SUMMARY" \
    "$MASTER_TRANSITIONS" \
    "$MASTER_REPORT"

for condition in "${CONDITIONS[@]}"; do
    echo
    echo "============================================================"
    echo "PROCESSING CONDITION: $condition"
    echo "============================================================"

    CONDITION_INPUT="$ATTACK_DIR/$condition/F11_${condition}_local_interpolation.pod5"
    CONDITION_DIR="$OUTPUT_DIR/$condition"

    RAW_BAM="$CONDITION_DIR/F11_${condition}_dorado_raw.bam"
    FASTQ="$CONDITION_DIR/F11_${condition}.fastq"
    ALIGNED_BAM="$CONDITION_DIR/F11_${condition}_GRCh38.sorted.bam"

    BASECALL_LOG="$CONDITION_DIR/F11_${condition}_dorado.stderr.log"
    ALIGN_LOG="$CONDITION_DIR/F11_${condition}_alignment.stderr.log"

    RECORD_PARENT_MAP="$CONDITION_DIR/F11_${condition}_record_parent_map.tsv"
    RECORD_AUDIT="$CONDITION_DIR/F11_${condition}_target_record_audit.tsv"
    PARENT_AUDIT="$CONDITION_DIR/F11_${condition}_target_parent_audit.tsv"
    TRANSITIONS="$CONDITION_DIR/F11_${condition}_clean_to_attacked_transitions.tsv"
    CONDITION_SUMMARY="$CONDITION_DIR/F11_${condition}_summary.tsv"

    mkdir -p "$CONDITION_DIR"

    echo
    echo "[3/8][$condition] Dorado basecalling"

    rm -f \
        "$RAW_BAM" \
        "$FASTQ" \
        "$ALIGNED_BAM" \
        "$ALIGNED_BAM.bai" \
        "$BASECALL_LOG" \
        "$ALIGN_LOG"

    "$DORADO" basecaller \
        "$MODEL_PATH" \
        "$CONDITION_INPUT" \
        --device cuda:all \
        --emit-moves \
        > "$RAW_BAM" \
        2> "$BASECALL_LOG"

    if [[ ! -s "$RAW_BAM" ]]; then
        echo "ERROR: $condition Dorado BAM is missing or empty."
        exit 1
    fi

    # Dorado BAM is unaligned and intentionally lacks @SQ lines.
    samtools view -H "$RAW_BAM" >/dev/null
    samtools view "$RAW_BAM" >/dev/null

    RAW_RECORDS="$(samtools view -c "$RAW_BAM")"

    echo "$condition Dorado records: $RAW_RECORDS"
    tail -20 "$BASECALL_LOG"

    echo
    echo "[4/8][$condition] Recording split-child to raw-parent relationships"

    export RAW_BAM
    export RECORD_PARENT_MAP

    python <<'PY_EOF'
import csv
import os
from pathlib import Path

import pysam

bam_path = Path(os.environ["RAW_BAM"])
output_path = Path(os.environ["RECORD_PARENT_MAP"])

rows = []

with pysam.AlignmentFile(
    str(bam_path),
    "rb",
    check_sq=False,
) as bam:
    for record in bam.fetch(until_eof=True):
        query_name = record.query_name
        parent_id = (
            str(record.get_tag("pi"))
            if record.has_tag("pi")
            else query_name
        )

        rows.append(
            {
                "query_name": query_name,
                "parent_read_id": parent_id,
                "has_parent_tag": int(record.has_tag("pi")),
                "sequence_length": len(record.query_sequence or ""),
            }
        )

with output_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "query_name",
            "parent_read_id",
            "has_parent_tag",
            "sequence_length",
        ],
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Mapped Dorado records: {len(rows)}")
print(
    "Split-child records: "
    f"{sum(row['has_parent_tag'] for row in rows)}"
)
PY_EOF

    echo
    echo "[5/8][$condition] FASTQ conversion and GRCh38 alignment"

    samtools fastq \
        -n \
        "$RAW_BAM" \
        > "$FASTQ"

    FASTQ_RECORDS="$(
        awk 'END {print NR/4}' "$FASTQ"
    )"

    echo "$condition FASTQ records: $FASTQ_RECORDS"

    minimap2 \
        -ax map-ont \
        -t 16 \
        "$REFERENCE" \
        "$FASTQ" \
        2> "$ALIGN_LOG" \
        | samtools sort \
            -@ 8 \
            -o "$ALIGNED_BAM" \
            -

    samtools index "$ALIGNED_BAM"
    samtools quickcheck -v "$ALIGNED_BAM"

    TOTAL_ALIGNMENTS="$(samtools view -c "$ALIGNED_BAM")"
    MAPPED_ALIGNMENTS="$(samtools view -c -F 4 "$ALIGNED_BAM")"
    PRIMARY_MAPPED="$(samtools view -c -F 2308 "$ALIGNED_BAM")"

    echo "$condition total alignments: $TOTAL_ALIGNMENTS"
    echo "$condition mapped alignments: $MAPPED_ALIGNMENTS"
    echo "$condition primary mapped: $PRIMARY_MAPPED"

    echo
    echo "[6/8][$condition] F11 target and parent-transition audit"

    export CONDITION="$condition"
    export ALIGNED_BAM
    export RECORD_PARENT_MAP
    export ATTACK_IDS
    export CLEAN_PARENT_AUDIT
    export RECORD_AUDIT
    export PARENT_AUDIT
    export TRANSITIONS
    export CONDITION_SUMMARY
    export RAW_RECORDS
    export FASTQ_RECORDS
    export TOTAL_ALIGNMENTS
    export MAPPED_ALIGNMENTS
    export PRIMARY_MAPPED

    python <<'PY_EOF'
import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

import pysam

condition = os.environ["CONDITION"]

aligned_path = Path(os.environ["ALIGNED_BAM"])
map_path = Path(os.environ["RECORD_PARENT_MAP"])
attack_ids_path = Path(os.environ["ATTACK_IDS"])
clean_audit_path = Path(os.environ["CLEAN_PARENT_AUDIT"])

record_audit_path = Path(os.environ["RECORD_AUDIT"])
parent_audit_path = Path(os.environ["PARENT_AUDIT"])
transitions_path = Path(os.environ["TRANSITIONS"])
summary_path = Path(os.environ["CONDITION_SUMMARY"])

target_contig = "chr4"
target_position = 186274193
target_zero = target_position - 1
ref_base = "G"
alt_base = "T"

attack_ids = {
    line.strip()
    for line in attack_ids_path.read_text().splitlines()
    if line.strip()
}

if len(attack_ids) != 14:
    raise SystemExit(
        f"ERROR: Expected 14 attack parents, found {len(attack_ids)}."
    )

query_to_parent = {}

with map_path.open(newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")

    for row in reader:
        query_name = row["query_name"].strip()
        parent_id = row["parent_read_id"].strip()

        if query_name in query_to_parent:
            raise SystemExit(
                f"ERROR: Duplicate Dorado query name: {query_name}"
            )

        query_to_parent[query_name] = parent_id

clean_status = {}

with clean_audit_path.open(newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")

    for row in reader:
        parent_id = (row.get("parent_read_id") or "").strip()
        status = (row.get("parent_status") or "").strip()

        if parent_id in attack_ids:
            clean_status[parent_id] = status

if set(clean_status) != attack_ids:
    missing = sorted(attack_ids - set(clean_status))

    raise SystemExit(
        "ERROR: Missing clean statuses for: "
        + ",".join(missing)
    )

non_alt_clean = {
    parent_id: status
    for parent_id, status in clean_status.items()
    if status != "ALT"
}

if non_alt_clean:
    raise SystemExit(
        f"ERROR: Attack cohort contains non-ALT clean parents: "
        f"{non_alt_clean}"
    )

record_rows = []
parent_statuses = defaultdict(list)

with pysam.AlignmentFile(str(aligned_path), "rb") as bam:
    record_number = 0

    for record in bam.fetch(until_eof=True):
        query_name = record.query_name
        parent_id = query_to_parent.get(query_name, query_name)

        if parent_id not in attack_ids:
            continue

        record_number += 1

        status = "NO_COVERAGE"
        target_base = ""
        query_position = ""

        if record.is_unmapped:
            status = "UNMAPPED"
        elif record.reference_name == target_contig:
            found_target = False

            for query_pos, reference_pos in record.get_aligned_pairs(
                matches_only=False
            ):
                if reference_pos != target_zero:
                    continue

                found_target = True

                if query_pos is None:
                    status = "DEL"
                    target_base = "-"
                else:
                    sequence = record.query_sequence or ""

                    if query_pos >= len(sequence):
                        status = "OTHER"
                    else:
                        target_base = sequence[query_pos].upper()

                        if target_base == alt_base:
                            status = "ALT"
                        elif target_base == ref_base:
                            status = "REF"
                        else:
                            status = "OTHER"

                    query_position = query_pos

                break

            if not found_target:
                status = "NO_COVERAGE"

        parent_statuses[parent_id].append(status)

        record_rows.append(
            {
                "condition": condition,
                "parent_read_id": parent_id,
                "query_name": query_name,
                "record_number": record_number,
                "flag": record.flag,
                "is_primary": int(
                    not record.is_secondary
                    and not record.is_supplementary
                ),
                "is_secondary": int(record.is_secondary),
                "is_supplementary": int(record.is_supplementary),
                "is_reverse": int(record.is_reverse),
                "is_unmapped": int(record.is_unmapped),
                "reference_name": record.reference_name or "",
                "reference_start_1based": (
                    record.reference_start + 1
                    if record.reference_start is not None
                    and record.reference_start >= 0
                    else ""
                ),
                "reference_end_1based": (
                    record.reference_end
                    if record.reference_end is not None
                    else ""
                ),
                "mapq": record.mapping_quality,
                "target_status": status,
                "target_base": target_base,
                "query_position_0based": query_position,
                "cigar": record.cigarstring or "",
            }
        )

record_fields = [
    "condition",
    "parent_read_id",
    "query_name",
    "record_number",
    "flag",
    "is_primary",
    "is_secondary",
    "is_supplementary",
    "is_reverse",
    "is_unmapped",
    "reference_name",
    "reference_start_1based",
    "reference_end_1based",
    "mapq",
    "target_status",
    "target_base",
    "query_position_0based",
    "cigar",
]

with record_audit_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=record_fields,
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(record_rows)

# Conservative parent aggregation:
# retain ALT if any attacked child/record still supports ALT.
priority = [
    "ALT",
    "REF",
    "DEL",
    "OTHER",
    "NO_COVERAGE",
    "UNMAPPED",
]

parent_rows = []

for parent_id in sorted(attack_ids):
    statuses = parent_statuses.get(parent_id, [])

    if not statuses:
        attacked_status = "NO_DORADO_RECORD"
    else:
        attacked_status = next(
            (
                candidate
                for candidate in priority
                if candidate in statuses
            ),
            "OTHER",
        )

    parent_rows.append(
        {
            "condition": condition,
            "parent_read_id": parent_id,
            "record_count": len(statuses),
            "record_statuses": ",".join(statuses),
            "attacked_parent_status": attacked_status,
        }
    )

with parent_audit_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "condition",
            "parent_read_id",
            "record_count",
            "record_statuses",
            "attacked_parent_status",
        ],
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(parent_rows)

transition_rows = []

for row in parent_rows:
    parent_id = row["parent_read_id"]
    attacked_status = row["attacked_parent_status"]

    transition_rows.append(
        {
            "condition": condition,
            "parent_read_id": parent_id,
            "clean_parent_status": clean_status[parent_id],
            "attacked_parent_status": attacked_status,
            "transition": (
                f"{clean_status[parent_id]}->{attacked_status}"
            ),
            "alt_changed": int(attacked_status != "ALT"),
            "alt_retained": int(attacked_status == "ALT"),
            "record_count": row["record_count"],
            "record_statuses": row["record_statuses"],
        }
    )

with transitions_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "condition",
            "parent_read_id",
            "clean_parent_status",
            "attacked_parent_status",
            "transition",
            "alt_changed",
            "alt_retained",
            "record_count",
            "record_statuses",
        ],
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(transition_rows)

counts = Counter(
    row["attacked_parent_status"]
    for row in parent_rows
)

transition_counts = Counter(
    row["transition"]
    for row in transition_rows
)

alt_changed = sum(
    row["alt_changed"]
    for row in transition_rows
)

alt_retained = sum(
    row["alt_retained"]
    for row in transition_rows
)

summary_row = {
    "condition": condition,
    "attack_parents": len(attack_ids),
    "raw_dorado_records": int(os.environ["RAW_RECORDS"]),
    "fastq_records": int(float(os.environ["FASTQ_RECORDS"])),
    "total_alignment_records": int(os.environ["TOTAL_ALIGNMENTS"]),
    "mapped_alignment_records": int(os.environ["MAPPED_ALIGNMENTS"]),
    "primary_mapped_records": int(os.environ["PRIMARY_MAPPED"]),
    "parent_ALT": counts["ALT"],
    "parent_REF": counts["REF"],
    "parent_DEL": counts["DEL"],
    "parent_OTHER": counts["OTHER"],
    "parent_NO_COVERAGE": counts["NO_COVERAGE"],
    "parent_UNMAPPED": counts["UNMAPPED"],
    "parent_NO_DORADO_RECORD": counts["NO_DORADO_RECORD"],
    "alt_retained": alt_retained,
    "alt_changed": alt_changed,
    "alt_retention_percent": round(
        alt_retained * 100 / len(attack_ids),
        4,
    ),
    "alt_change_percent": round(
        alt_changed * 100 / len(attack_ids),
        4,
    ),
    "transition_counts": ",".join(
        f"{key}:{transition_counts[key]}"
        for key in sorted(transition_counts)
    ),
    "status": (
        "PASS"
        if len(parent_rows) == 14
        else "FAIL"
    ),
}

with summary_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(summary_row.keys()),
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerow(summary_row)

print(f"Condition: {condition}")
print(f"ALT retained: {alt_retained}/14")
print(f"ALT changed: {alt_changed}/14")
print(
    "Parent states: "
    + ", ".join(
        f"{state}={counts[state]}"
        for state in [
            "ALT",
            "REF",
            "DEL",
            "OTHER",
            "NO_COVERAGE",
            "UNMAPPED",
            "NO_DORADO_RECORD",
        ]
    )
)
print(f"Transitions: {summary_row['transition_counts']}")

if summary_row["status"] != "PASS":
    raise SystemExit(1)
PY_EOF

    echo
    echo "$condition parent audit:"
    column -t -s $'\t' "$PARENT_AUDIT" 2>/dev/null ||
        cat "$PARENT_AUDIT"

    echo
    echo "$condition summary:"
    column -t -s $'\t' "$CONDITION_SUMMARY" 2>/dev/null ||
        cat "$CONDITION_SUMMARY"
done

echo
echo "[7/8] Building cross-condition master tables"

export OUTPUT_DIR
export MASTER_SUMMARY
export MASTER_TRANSITIONS
export MASTER_REPORT

python <<'PY_EOF'
import csv
import os
from pathlib import Path

output_dir = Path(os.environ["OUTPUT_DIR"])
master_summary = Path(os.environ["MASTER_SUMMARY"])
master_transitions = Path(os.environ["MASTER_TRANSITIONS"])
master_report = Path(os.environ["MASTER_REPORT"])

conditions = ["W0", "PM2", "PM5", "PM10", "PM20"]

summary_rows = []
transition_rows = []

for condition in conditions:
    condition_dir = output_dir / condition

    summary_path = condition_dir / f"F11_{condition}_summary.tsv"
    transition_path = (
        condition_dir
        / f"F11_{condition}_clean_to_attacked_transitions.tsv"
    )

    with summary_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    if len(rows) != 1:
        raise SystemExit(
            f"ERROR: Expected one summary row for {condition}."
        )

    summary_rows.extend(rows)

    with transition_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    if len(rows) != 14:
        raise SystemExit(
            f"ERROR: Expected 14 transitions for {condition}, "
            f"found {len(rows)}."
        )

    transition_rows.extend(rows)

with master_summary.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(summary_rows[0].keys()),
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(summary_rows)

with master_transitions.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(transition_rows[0].keys()),
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(transition_rows)

lines = [
    "A3 F11 Attacked Rebasecalling and Clinical-Locus Consequence",
    "============================================================",
    "",
    "Clinical target: chr4:186274193 G>T",
    "Clean attack cohort: 14 ALT-confirmed parents",
    "Attack conditions: W0, PM2, PM5, PM10, PM20",
    "Parent aggregation: conservative ALT retention",
    "",
]

for row in summary_rows:
    lines.extend(
        [
            f"{row['condition']}:",
            f"  ALT retained: "
            f"{row['alt_retained']}/14 "
            f"({row['alt_retention_percent']}%)",
            f"  ALT changed: "
            f"{row['alt_changed']}/14 "
            f"({row['alt_change_percent']}%)",
            f"  Parent ALT: {row['parent_ALT']}",
            f"  Parent REF: {row['parent_REF']}",
            f"  Parent DEL: {row['parent_DEL']}",
            f"  Parent OTHER: {row['parent_OTHER']}",
            f"  Parent NO_COVERAGE: "
            f"{row['parent_NO_COVERAGE']}",
            f"  Parent UNMAPPED: {row['parent_UNMAPPED']}",
            f"  Parent NO_DORADO_RECORD: "
            f"{row['parent_NO_DORADO_RECORD']}",
            f"  Transitions: {row['transition_counts']}",
            "",
        ]
    )

total_changed = sum(
    int(row["alt_changed"])
    for row in summary_rows
)

lines.extend(
    [
        f"Total changed parent-condition observations: "
        f"{total_changed}/70",
        "",
        "Overall status: ATTACKED_REBASECALLING_COMPLETE",
    ]
)

master_report.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print(master_report.read_text(encoding="utf-8"))
PY_EOF

echo
echo "Master summary:"
column -t -s $'\t' "$MASTER_SUMMARY" 2>/dev/null ||
    cat "$MASTER_SUMMARY"

echo
echo "[8/8] Creating completion marker"

{
    echo "Completed: $(date -Is)"
    echo "Conditions: W0 PM2 PM5 PM10 PM20"
    echo "Attack parents per condition: 14"
    echo "Parent-condition observations: 70"
    echo "Master summary: $MASTER_SUMMARY"
    echo "Master transitions: $MASTER_TRANSITIONS"
    echo "Master report: $MASTER_REPORT"
    echo "Overall status: ATTACKED_REBASECALLING_COMPLETE"
} > "$COMPLETE"

rm -f "$FAILED"

echo
echo "============================================================"
echo "A3 F11 ATTACKED REBASECALLING COMPLETE"
echo "============================================================"
