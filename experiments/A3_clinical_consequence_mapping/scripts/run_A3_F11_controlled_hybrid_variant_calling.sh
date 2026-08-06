#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

source \
    experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate"

SOURCE_DIR="$RESULTS_DIR/F11_source_alignment_discovery"
RETRIEVAL_DIR="$RESULTS_DIR/ONT_target_retrieval"
SIGNAL_DIR="$RESULTS_DIR/signal_target_mapping"
CLEAN_DIR="$RESULTS_DIR/clean_rebasecalling"
ATTACKED_DIR="$RESULTS_DIR/attacked_rebasecalling"

HYBRID_DIR="$RESULTS_DIR/controlled_hybrid_variant_calling"
MARKER_DIR="$A3_DIR/markers"

SOURCE_BAM="$RETRIEVAL_DIR/F11_PAO89685_region.sorted.bam"
REF_IDS="$SOURCE_DIR/F11_selected_REF_background_parent_ids.txt"
ALT_IDS="$SIGNAL_DIR/F11_clean_ALT_attack_parent_ids.txt"

CLEAN_BAM="$CLEAN_DIR/F11_clean_dorado_GRCh38.sorted.bam"

REFERENCE="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"

TARGET_CHROM="chr4"
TARGET_POS="186274193"
TARGET_REGION="${TARGET_CHROM}:${TARGET_POS}-${TARGET_POS}"
CALL_REGION="chr4:186269000-186279000"

SUMMARY_TSV="$HYBRID_DIR/F11_controlled_hybrid_variant_calling_summary.tsv"
TRANSITIONS_TSV="$HYBRID_DIR/F11_controlled_hybrid_parent_states.tsv"
REPORT_TXT="$HYBRID_DIR/F11_controlled_hybrid_variant_calling_report.txt"

COMPLETE="$MARKER_DIR/A3_F11_CONTROLLED_HYBRID_VARIANT_CALLING.COMPLETE"
FAILED="$MARKER_DIR/A3_F11_CONTROLLED_HYBRID_VARIANT_CALLING.FAILED"

CONDITIONS=(CLEAN W0 PM2 PM5 PM10 PM20)

mkdir -p "$HYBRID_DIR" "$MARKER_DIR"

rm -f "$COMPLETE" "$FAILED"

trap 'status=$?;
      {
          echo "Failed: $(date -Is)"
          echo "Exit status: $status"
      } > "$FAILED";
      echo
      echo "ERROR: Controlled hybrid workflow failed."
      echo "Exit status: $status"
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — CONTROLLED HYBRID VARIANT CALLING"
echo "============================================================"
echo "Started: $(date -Is)"
echo

echo "[1/8] Validating tools and locked inputs"

for tool in python samtools bcftools; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "ERROR: Missing required tool: $tool"
        exit 1
    fi
done

for file in \
    "$SOURCE_BAM" \
    "$REF_IDS" \
    "$ALT_IDS" \
    "$CLEAN_BAM" \
    "$REFERENCE"; do

    if [[ ! -s "$file" ]]; then
        echo "ERROR: Missing required input:"
        echo "$file"
        exit 1
    fi
done

if [[ ! -s "$REFERENCE.fai" ]]; then
    samtools faidx "$REFERENCE"
fi

samtools quickcheck -v "$SOURCE_BAM"
samtools quickcheck -v "$CLEAN_BAM"

REF_COUNT="$(
    awk 'NF {n++} END {print n+0}' "$REF_IDS"
)"

ALT_COUNT="$(
    awk 'NF {n++} END {print n+0}' "$ALT_IDS"
)"

if [[ "$REF_COUNT" -ne 10 ]]; then
    echo "ERROR: Expected 10 REF background parents."
    echo "Observed: $REF_COUNT"
    exit 1
fi

if [[ "$ALT_COUNT" -ne 14 ]]; then
    echo "ERROR: Expected 14 ALT replacement parents."
    echo "Observed: $ALT_COUNT"
    exit 1
fi

for condition in W0 PM2 PM5 PM10 PM20; do
    BAM="$ATTACKED_DIR/$condition/F11_${condition}_GRCh38.sorted.bam"

    if [[ ! -s "$BAM" ]]; then
        echo "ERROR: Missing attacked BAM:"
        echo "$BAM"
        exit 1
    fi

    samtools quickcheck -v "$BAM"
done

echo "Input validation: PASS"
echo "REF parents: $REF_COUNT"
echo "ALT parents: $ALT_COUNT"

echo
echo "[2/8] Creating cohort extraction and audit program"

BUILDER="$HYBRID_DIR/build_and_audit_F11_hybrids.py"

cat > "$BUILDER" <<'PY_EOF'
#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import pysam


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("--condition", required=True)
    parser.add_argument("--source-background", required=True)
    parser.add_argument("--background-ids", required=True)
    parser.add_argument("--replacement-bam", required=True)
    parser.add_argument("--replacement-ids", required=True)
    parser.add_argument("--background-output", required=True)
    parser.add_argument("--replacement-output", required=True)
    parser.add_argument("--hybrid-unsorted", required=True)
    parser.add_argument("--audit-tsv", required=True)
    parser.add_argument("--parent-tsv", required=True)
    parser.add_argument("--chrom", required=True)
    parser.add_argument("--position", required=True, type=int)

    return parser.parse_args()


def load_ids(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def parent_id(record: pysam.AlignedSegment) -> str:
    if record.has_tag("pi"):
        return str(record.get_tag("pi"))

    return record.query_name


def target_state(
    record: pysam.AlignedSegment,
    chrom: str,
    position: int,
) -> tuple[str, str]:
    target0 = position - 1

    if record.is_unmapped:
        return "UNMAPPED", ""

    if record.reference_name != chrom:
        return "NO_COVERAGE", ""

    if (
        record.reference_start is None
        or record.reference_end is None
        or target0 < record.reference_start
        or target0 >= record.reference_end
    ):
        return "NO_COVERAGE", ""

    for query_pos, reference_pos in record.get_aligned_pairs(
        matches_only=False
    ):
        if reference_pos != target0:
            continue

        if query_pos is None:
            return "DEL", "-"

        sequence = record.query_sequence or ""

        if not 0 <= query_pos < len(sequence):
            return "OTHER", "?"

        base = sequence[query_pos].upper()

        if base == "G":
            return "REF", base

        if base == "T":
            return "ALT", base

        return "OTHER", base

    return "NO_ALIGNED_PAIR", ""


def write_selected_records(
    input_path: Path,
    selected_ids: set[str],
    output_path: Path,
    output_header,
    label: str,
) -> tuple[int, set[str]]:
    written = 0
    parents = set()

    with pysam.AlignmentFile(str(input_path), "rb") as input_bam:
        with pysam.AlignmentFile(
            str(output_path),
            "wb",
            header=output_header,
        ) as output_bam:
            for record in input_bam.fetch(until_eof=True):
                pid = parent_id(record)

                if (
                    pid not in selected_ids
                    and record.query_name not in selected_ids
                ):
                    continue

                output_bam.write(record)
                written += 1
                parents.add(pid)

    missing = selected_ids - parents

    if missing:
        raise RuntimeError(
            f"{label}: missing selected parents: "
            + ",".join(sorted(missing))
        )

    return written, parents


def main() -> None:
    args = parse_args()

    condition = args.condition

    background_ids = load_ids(Path(args.background_ids))
    replacement_ids = load_ids(Path(args.replacement_ids))

    if len(background_ids) != 10:
        raise RuntimeError(
            f"Expected 10 background IDs, found {len(background_ids)}"
        )

    if len(replacement_ids) != 14:
        raise RuntimeError(
            f"Expected 14 replacement IDs, found {len(replacement_ids)}"
        )

    source_background = Path(args.source_background)
    replacement_bam = Path(args.replacement_bam)

    background_output = Path(args.background_output)
    replacement_output = Path(args.replacement_output)
    hybrid_unsorted = Path(args.hybrid_unsorted)

    audit_path = Path(args.audit_tsv)
    parent_path = Path(args.parent_tsv)

    for path in [
        background_output,
        replacement_output,
        hybrid_unsorted,
        audit_path,
        parent_path,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    with pysam.AlignmentFile(str(source_background), "rb") as bam:
        header = bam.header.to_dict()

    background_written, background_parents = write_selected_records(
        input_path=source_background,
        selected_ids=background_ids,
        output_path=background_output,
        output_header=header,
        label="background",
    )

    replacement_written, replacement_parents = write_selected_records(
        input_path=replacement_bam,
        selected_ids=replacement_ids,
        output_path=replacement_output,
        output_header=header,
        label="replacement",
    )

    with pysam.AlignmentFile(
        str(hybrid_unsorted),
        "wb",
        header=header,
    ) as output:
        for path in [background_output, replacement_output]:
            with pysam.AlignmentFile(str(path), "rb") as source:
                for record in source.fetch(until_eof=True):
                    output.write(record)

    rows = []
    parent_states = defaultdict(list)
    source_by_parent = {}

    with pysam.AlignmentFile(str(hybrid_unsorted), "rb") as bam:
        for ordinal, record in enumerate(
            bam.fetch(until_eof=True),
            start=1,
        ):
            pid = parent_id(record)

            if pid in background_ids:
                source = "same_sample_REF_background"
            elif pid in replacement_ids:
                source = f"{condition}_replacement"
            else:
                source = "ERROR_UNKNOWN"

            state, base = target_state(
                record,
                args.chrom,
                args.position,
            )

            parent_states[pid].append(state)
            source_by_parent[pid] = source

            rows.append(
                {
                    "condition": condition,
                    "record_ordinal": ordinal,
                    "source": source,
                    "parent_read_id": pid,
                    "query_name": record.query_name,
                    "target_state": state,
                    "target_base": base,
                    "is_primary": int(
                        not record.is_secondary
                        and not record.is_supplementary
                    ),
                    "is_secondary": int(record.is_secondary),
                    "is_supplementary": int(
                        record.is_supplementary
                    ),
                    "is_reverse": int(record.is_reverse),
                    "mapq": record.mapping_quality,
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
                    "cigar": record.cigarstring or "",
                }
            )

    priority = [
        "ALT",
        "REF",
        "DEL",
        "OTHER",
        "NO_ALIGNED_PAIR",
        "NO_COVERAGE",
        "UNMAPPED",
    ]

    parent_rows = []

    for pid in sorted(parent_states):
        states = parent_states[pid]

        final_state = next(
            state
            for state in priority
            if state in states
        )

        parent_rows.append(
            {
                "condition": condition,
                "source": source_by_parent[pid],
                "parent_read_id": pid,
                "record_count": len(states),
                "record_states": ",".join(states),
                "parent_state": final_state,
            }
        )

    expected_parents = background_ids | replacement_ids
    observed_parents = set(parent_states)

    if observed_parents != expected_parents:
        raise RuntimeError(
            f"Hybrid parent mismatch: "
            f"missing={sorted(expected_parents - observed_parents)}, "
            f"extra={sorted(observed_parents - expected_parents)}"
        )

    background_state_errors = [
        row
        for row in parent_rows
        if (
            row["source"] == "same_sample_REF_background"
            and row["parent_state"] != "REF"
        )
    ]

    if background_state_errors:
        raise RuntimeError(
            f"Background contains non-REF parents: "
            f"{background_state_errors}"
        )

    with audit_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    with parent_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(parent_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(parent_rows)

    counts = Counter(
        row["parent_state"]
        for row in parent_rows
    )

    print(f"Condition: {condition}")
    print(f"Background records written: {background_written}")
    print(f"Background parents: {len(background_parents)}")
    print(f"Replacement records written: {replacement_written}")
    print(f"Replacement parents: {len(replacement_parents)}")
    print(f"Hybrid records: {len(rows)}")
    print(f"Hybrid parents: {len(parent_rows)}")
    print(
        "Parent states: "
        + ",".join(
            f"{state}={counts[state]}"
            for state in priority
        )
    )


if __name__ == "__main__":
    main()
PY_EOF

chmod +x "$BUILDER"
python -m py_compile "$BUILDER"

echo "Builder validation: PASS"

echo
echo "[3/8] Building CLEAN and attacked hybrid BAMs"

rm -f "$SUMMARY_TSV" "$TRANSITIONS_TSV" "$REPORT_TXT"

for condition in "${CONDITIONS[@]}"; do
    CONDITION_DIR="$HYBRID_DIR/$condition"

    BACKGROUND_BAM="$CONDITION_DIR/F11_${condition}_REF_background.bam"
    REPLACEMENT_BAM="$CONDITION_DIR/F11_${condition}_replacement.bam"

    HYBRID_UNSORTED="$CONDITION_DIR/F11_${condition}_hybrid.unsorted.bam"
    HYBRID_SORTED="$CONDITION_DIR/F11_${condition}_hybrid.sorted.bam"

    RECORD_AUDIT="$CONDITION_DIR/F11_${condition}_hybrid_record_audit.tsv"
    PARENT_AUDIT="$CONDITION_DIR/F11_${condition}_hybrid_parent_audit.tsv"

    mkdir -p "$CONDITION_DIR"

    if [[ "$condition" == "CLEAN" ]]; then
        INPUT_BAM="$CLEAN_BAM"
    else
        INPUT_BAM="$ATTACKED_DIR/$condition/F11_${condition}_GRCh38.sorted.bam"
    fi

    rm -f \
        "$BACKGROUND_BAM" \
        "$REPLACEMENT_BAM" \
        "$HYBRID_UNSORTED" \
        "$HYBRID_SORTED" \
        "$HYBRID_SORTED.bai" \
        "$RECORD_AUDIT" \
        "$PARENT_AUDIT"

    python "$BUILDER" \
        --condition "$condition" \
        --source-background "$SOURCE_BAM" \
        --background-ids "$REF_IDS" \
        --replacement-bam "$INPUT_BAM" \
        --replacement-ids "$ALT_IDS" \
        --background-output "$BACKGROUND_BAM" \
        --replacement-output "$REPLACEMENT_BAM" \
        --hybrid-unsorted "$HYBRID_UNSORTED" \
        --audit-tsv "$RECORD_AUDIT" \
        --parent-tsv "$PARENT_AUDIT" \
        --chrom "$TARGET_CHROM" \
        --position "$TARGET_POS"

    samtools sort \
        -@ 8 \
        -o "$HYBRID_SORTED" \
        "$HYBRID_UNSORTED"

    samtools index "$HYBRID_SORTED"
    samtools quickcheck -v "$HYBRID_SORTED"

    PARENT_COUNT="$(
        awk 'END {print NR-1}' "$PARENT_AUDIT"
    )"

    if [[ "$PARENT_COUNT" -ne 24 ]]; then
        echo "ERROR: $condition hybrid does not contain 24 parents."
        exit 1
    fi

    echo "$condition hybrid construction: PASS"
done

echo
echo "[4/8] Running independent pileup and bcftools calls"

printf \
'condition\thybrid_records\ttarget_records\tparent_REF\tparent_ALT\tparent_DEL\tparent_OTHER\tparent_NO_COVERAGE\tpileup_depth\tpileup_REF\tpileup_ALT\tpileup_DEL\tpileup_OTHER\tALT_fraction\tvcf_record\tGT\tQUAL\tFORMAT_DP\tFORMAT_AD_REF\tFORMAT_AD_ALT\tstatus\n' \
> "$SUMMARY_TSV"

for condition in "${CONDITIONS[@]}"; do
    CONDITION_DIR="$HYBRID_DIR/$condition"

    HYBRID_BAM="$CONDITION_DIR/F11_${condition}_hybrid.sorted.bam"
    PARENT_AUDIT="$CONDITION_DIR/F11_${condition}_hybrid_parent_audit.tsv"

    CALL_DIR="$CONDITION_DIR/variant_calling"
    RAW_BCF="$CALL_DIR/F11_${condition}.raw.bcf"
    CALLED_VCF="$CALL_DIR/F11_${condition}.called.vcf"
    TARGET_VCF="$CALL_DIR/F11_${condition}.target.vcf"

    PILEUP_TSV="$CALL_DIR/F11_${condition}_pileup.tsv"

    mkdir -p "$CALL_DIR"

    rm -f \
        "$RAW_BCF" \
        "$RAW_BCF.csi" \
        "$CALLED_VCF" \
        "$TARGET_VCF" \
        "$PILEUP_TSV"

    bcftools mpileup \
        -f "$REFERENCE" \
        -r "$CALL_REGION" \
        -a FORMAT/AD,FORMAT/DP \
        -Q 0 \
        -q 0 \
        -d 100000 \
        -Ob \
        -o "$RAW_BCF" \
        "$HYBRID_BAM"

    bcftools index -f "$RAW_BCF"

    bcftools call \
        -m \
        -v \
        -Ov \
        -o "$CALLED_VCF" \
        "$RAW_BCF"

    {
        grep '^#' "$CALLED_VCF"

        awk -F '\t' \
            -v chrom="$TARGET_CHROM" \
            -v pos="$TARGET_POS" '
            !/^#/ && $1 == chrom && $2 == pos
        ' "$CALLED_VCF"
    } > "$TARGET_VCF"

    export condition
    export HYBRID_BAM
    export PARENT_AUDIT
    export PILEUP_TSV
    export TARGET_CHROM
    export TARGET_POS
    export TARGET_VCF

    RESULT_LINE="$(
        python <<'PY_EOF'
import csv
import os
from collections import Counter
from pathlib import Path

import pysam

condition = os.environ["condition"]
bam_path = Path(os.environ["HYBRID_BAM"])
parent_path = Path(os.environ["PARENT_AUDIT"])
pileup_path = Path(os.environ["PILEUP_TSV"])
vcf_path = Path(os.environ["TARGET_VCF"])

chrom = os.environ["TARGET_CHROM"]
position = int(os.environ["TARGET_POS"])
target0 = position - 1

with parent_path.open(newline="") as handle:
    parent_rows = list(
        csv.DictReader(handle, delimiter="\t")
    )

parent_counts = Counter(
    row["parent_state"]
    for row in parent_rows
)

pileup_counts = Counter()
pileup_depth = 0

with pysam.AlignmentFile(str(bam_path), "rb") as bam:
    for column in bam.pileup(
        chrom,
        target0,
        target0 + 1,
        truncate=True,
        stepper="all",
        min_base_quality=0,
        min_mapping_quality=0,
        ignore_overlaps=False,
        ignore_orphans=False,
        max_depth=100000,
    ):
        if column.reference_pos != target0:
            continue

        for pileup_read in column.pileups:
            pileup_depth += 1

            if pileup_read.is_del or pileup_read.is_refskip:
                pileup_counts["DEL"] += 1
                continue

            query_pos = pileup_read.query_position
            sequence = pileup_read.alignment.query_sequence or ""

            if (
                query_pos is None
                or not 0 <= query_pos < len(sequence)
            ):
                pileup_counts["OTHER"] += 1
                continue

            base = sequence[query_pos].upper()

            if base == "G":
                pileup_counts["REF"] += 1
            elif base == "T":
                pileup_counts["ALT"] += 1
            else:
                pileup_counts["OTHER"] += 1

with pileup_path.open("w", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(
        [
            "condition",
            "depth",
            "REF_G",
            "ALT_T",
            "DEL",
            "OTHER",
        ]
    )
    writer.writerow(
        [
            condition,
            pileup_depth,
            pileup_counts["REF"],
            pileup_counts["ALT"],
            pileup_counts["DEL"],
            pileup_counts["OTHER"],
        ]
    )

vcf_records = []

with vcf_path.open() as handle:
    for line in handle:
        if line.startswith("#"):
            continue

        fields = line.rstrip("\n").split("\t")

        if len(fields) >= 10:
            vcf_records.append(fields)

if vcf_records:
    fields = vcf_records[0]

    qual = fields[5]
    format_keys = fields[8].split(":")
    sample_values = fields[9].split(":")

    sample = dict(zip(format_keys, sample_values))

    gt = sample.get("GT", ".")
    format_dp = sample.get("DP", ".")

    ad = sample.get("AD", ".")
    ad_values = ad.split(",") if ad != "." else []

    ad_ref = ad_values[0] if len(ad_values) >= 1 else "."
    ad_alt = ad_values[1] if len(ad_values) >= 2 else "."

    vcf_record = 1
else:
    qual = "."
    gt = "NO_CALL"
    format_dp = "."
    ad_ref = "."
    ad_alt = "."
    vcf_record = 0

alt_fraction = (
    pileup_counts["ALT"]
    / (
        pileup_counts["REF"]
        + pileup_counts["ALT"]
    )
    if (
        pileup_counts["REF"]
        + pileup_counts["ALT"]
    ) > 0
    else 0.0
)

hybrid_records = 0

with pysam.AlignmentFile(str(bam_path), "rb") as bam:
    for _ in bam.fetch(until_eof=True):
        hybrid_records += 1

target_records = sum(
    1
    for row in parent_rows
    if row["parent_state"] != "NO_COVERAGE"
)

values = [
    condition,
    hybrid_records,
    target_records,
    parent_counts["REF"],
    parent_counts["ALT"],
    parent_counts["DEL"],
    parent_counts["OTHER"],
    parent_counts["NO_COVERAGE"],
    pileup_depth,
    pileup_counts["REF"],
    pileup_counts["ALT"],
    pileup_counts["DEL"],
    pileup_counts["OTHER"],
    f"{alt_fraction:.6f}",
    vcf_record,
    gt,
    qual,
    format_dp,
    ad_ref,
    ad_alt,
    "PASS",
]

print("\t".join(str(value) for value in values))
PY_EOF
    )"

    printf '%s\n' "$RESULT_LINE" >> "$SUMMARY_TSV"

    echo
    echo "$condition:"
    printf '%s\n' "$RESULT_LINE" \
        | column -t -s $'\t' 2>/dev/null \
        || printf '%s\n' "$RESULT_LINE"
done

echo
echo "[5/8] Building master parent-state table"

export HYBRID_DIR
export TRANSITIONS_TSV

python <<'PY_EOF'
import csv
import os
from pathlib import Path

hybrid_dir = Path(os.environ["HYBRID_DIR"])
output_path = Path(os.environ["TRANSITIONS_TSV"])

conditions = ["CLEAN", "W0", "PM2", "PM5", "PM10", "PM20"]

rows = []

for condition in conditions:
    path = (
        hybrid_dir
        / condition
        / f"F11_{condition}_hybrid_parent_audit.tsv"
    )

    with path.open(newline="") as handle:
        condition_rows = list(
            csv.DictReader(handle, delimiter="\t")
        )

    if len(condition_rows) != 24:
        raise RuntimeError(
            f"{condition}: expected 24 parent rows, "
            f"found {len(condition_rows)}"
        )

    rows.extend(condition_rows)

with output_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(rows[0].keys()),
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Master parent rows: {len(rows)}")
PY_EOF

echo
echo "[6/8] Validating expected experimental structure"

export SUMMARY_TSV

python <<'PY_EOF'
import csv
import os
from pathlib import Path

path = Path(os.environ["SUMMARY_TSV"])

with path.open(newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))

expected_conditions = [
    "CLEAN",
    "W0",
    "PM2",
    "PM5",
    "PM10",
    "PM20",
]

errors = []

if [row["condition"] for row in rows] != expected_conditions:
    errors.append("condition order or set is incorrect")

if len(rows) != 6:
    errors.append(
        f"expected six summary rows; found {len(rows)}"
    )

for row in rows:
    condition = row["condition"]

    # Total REF parent count can exceed ten because attacked ALT
    # replacement parents may legitimately transition to REF.
    # The fixed ten-parent REF background is validated separately
    # from the per-parent source-membership tables.

    if int(row["target_records"]) != 24:
        errors.append(
            f"{condition}: expected 24 target parents"
        )

    if row["status"] != "PASS":
        errors.append(
            f"{condition}: summary status is not PASS"
        )

clean = rows[0]

if int(clean["parent_ALT"]) != 14:
    errors.append(
        "CLEAN hybrid does not contain 14 ALT parents"
    )

if int(clean["parent_DEL"]) != 0:
    errors.append(
        "CLEAN hybrid unexpectedly contains deletion parents"
    )

if errors:
    print("Validation errors:")

    for error in errors:
        print(f"- {error}")

    raise SystemExit(1)

print("Controlled hybrid structural validation: PASS")
PY_EOF

echo
echo "[7/8] Creating final clinical-consequence report"

export SUMMARY_TSV
export REPORT_TXT

python <<'PY_EOF'
import csv
import os
from pathlib import Path

summary_path = Path(os.environ["SUMMARY_TSV"])
report_path = Path(os.environ["REPORT_TXT"])

with summary_path.open(newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))

lines = [
    "A3 F11 Controlled Hybrid Variant-Calling Results",
    "================================================",
    "",
    "Clinical target: chr4:186274193 G>T",
    "Matched background: 10 same-sample REF parents",
    "Replacement cohort: 14 clean or attacked parents",
    "",
]

for row in rows:
    lines.extend(
        [
            f"{row['condition']}:",
            f"  Parent states: "
            f"REF={row['parent_REF']}, "
            f"ALT={row['parent_ALT']}, "
            f"DEL={row['parent_DEL']}, "
            f"OTHER={row['parent_OTHER']}",
            f"  Pileup: "
            f"depth={row['pileup_depth']}, "
            f"REF={row['pileup_REF']}, "
            f"ALT={row['pileup_ALT']}, "
            f"DEL={row['pileup_DEL']}, "
            f"OTHER={row['pileup_OTHER']}",
            f"  ALT fraction: {row['ALT_fraction']}",
            f"  VCF target record: {row['vcf_record']}",
            f"  GT: {row['GT']}",
            f"  QUAL: {row['QUAL']}",
            f"  FORMAT/DP: {row['FORMAT_DP']}",
            f"  FORMAT/AD: "
            f"{row['FORMAT_AD_REF']},"
            f"{row['FORMAT_AD_ALT']}",
            "",
        ]
    )

clean = rows[0]

clean_detected = (
    clean["vcf_record"] == "1"
    and clean["GT"] not in {
        "NO_CALL",
        "0/0",
        "0|0",
        ".",
        "./.",
    }
)

lost_conditions = []

for row in rows[1:]:
    lost = (
        row["vcf_record"] == "0"
        or row["GT"] in {
            "NO_CALL",
            "0/0",
            "0|0",
            ".",
            "./.",
        }
    )

    if lost:
        lost_conditions.append(row["condition"])

lines.extend(
    [
        "Interpretation:",
        f"  Clean pathogenic call detected: {clean_detected}",
        f"  Conditions losing the pathogenic call: "
        f"{','.join(lost_conditions) if lost_conditions else 'NONE'}",
        "",
        "Overall status: CONTROLLED_HYBRID_VARIANT_CALLING_COMPLETE",
    ]
)

report_path.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print(report_path.read_text(encoding="utf-8"))
PY_EOF

echo
echo "Master summary:"
column -t -s $'\t' "$SUMMARY_TSV" 2>/dev/null \
    || cat "$SUMMARY_TSV"

echo
echo "[8/8] Creating completion marker"

{
    echo "Completed: $(date -Is)"
    echo "Target: chr4:186274193 G>T"
    echo "Same-sample REF background parents: 10"
    echo "Clean/attacked replacement parents: 14"
    echo "Conditions: CLEAN W0 PM2 PM5 PM10 PM20"
    echo "Summary: $SUMMARY_TSV"
    echo "Parent states: $TRANSITIONS_TSV"
    echo "Report: $REPORT_TXT"
    echo "Overall status: CONTROLLED_HYBRID_VARIANT_CALLING_COMPLETE"
} > "$COMPLETE"

rm -f "$FAILED"

echo
echo "============================================================"
echo "A3 F11 CONTROLLED HYBRID VARIANT CALLING COMPLETE"
echo "============================================================"
