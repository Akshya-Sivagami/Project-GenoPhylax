#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

source \
    experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

A3_DIR="experiments/A3_clinical_consequence_mapping"
RESULTS_DIR="$A3_DIR/results/F11_candidate"

SIGNAL_DIR="$RESULTS_DIR/signal_target_mapping"
SOURCE_DIR="$RESULTS_DIR/F11_source_alignment_discovery"
RETRIEVAL_DIR="$RESULTS_DIR/ONT_target_retrieval"
SHAM_DIR="$RESULTS_DIR/PM2_off_target_sham"
MARKER_DIR="$A3_DIR/markers"

SOURCE_POD5="$RESULTS_DIR/ONT_target_retrieval/F11_extracted_signal/F11_ALT_reads.pod5"
WINDOW_MAP="$SIGNAL_DIR/F11_target_signal_windows.tsv"
ATTACK_IDS="$SIGNAL_DIR/F11_clean_ALT_attack_parent_ids.txt"

REF_IDS="$SOURCE_DIR/F11_selected_REF_background_parent_ids.txt"
SOURCE_BACKGROUND="$RETRIEVAL_DIR/F11_PAO89685_region.sorted.bam"

REFERENCE="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"

SHAM_POD5="$SHAM_DIR/F11_PM2_off_target_sham.pod5"
SHAM_WINDOW_MAP="$SHAM_DIR/F11_PM2_off_target_sham_windows.tsv"
GENERATION_AUDIT="$SHAM_DIR/F11_PM2_off_target_sham_generation_audit.tsv"

RAW_BAM="$SHAM_DIR/F11_PM2_off_target_sham_dorado_raw.bam"
FASTQ="$SHAM_DIR/F11_PM2_off_target_sham.fastq"
ALIGNED_BAM="$SHAM_DIR/F11_PM2_off_target_sham_GRCh38.sorted.bam"

RECORD_PARENT_MAP="$SHAM_DIR/F11_PM2_off_target_sham_record_parent_map.tsv"
TARGET_PARENT_AUDIT="$SHAM_DIR/F11_PM2_off_target_sham_target_parent_audit.tsv"

REF_BACKGROUND_BAM="$SHAM_DIR/F11_PM2_off_target_REF_background.bam"
SHAM_REPLACEMENT_BAM="$SHAM_DIR/F11_PM2_off_target_replacement.bam"
HYBRID_UNSORTED="$SHAM_DIR/F11_PM2_off_target_hybrid.unsorted.bam"
HYBRID_SORTED="$SHAM_DIR/F11_PM2_off_target_hybrid.sorted.bam"

VCF="$SHAM_DIR/F11_PM2_off_target_hybrid.called.vcf"
TARGET_VCF="$SHAM_DIR/F11_PM2_off_target_hybrid.target.vcf"

SUMMARY="$SHAM_DIR/F11_PM2_off_target_sham_summary.tsv"
REPORT="$SHAM_DIR/F11_PM2_off_target_sham_report.txt"

COMPLETE="$MARKER_DIR/A3_F11_PM2_OFF_TARGET_SHAM.COMPLETE"
FAILED="$MARKER_DIR/A3_F11_PM2_OFF_TARGET_SHAM.FAILED"

TARGET_CHROM="chr4"
TARGET_POS="186274193"
TARGET_REGION="${TARGET_CHROM}:${TARGET_POS}-${TARGET_POS}"
CALL_REGION="chr4:186269000-186279000"

mkdir -p "$SHAM_DIR" "$MARKER_DIR"

rm -f "$COMPLETE" "$FAILED"

trap 'status=$?;
      {
          echo "Failed: $(date -Is)"
          echo "Exit status: $status"
      } > "$FAILED";
      echo
      echo "ERROR: PM2 off-target sham workflow failed."
      echo "Exit status: $status"
      exit "$status"' ERR

echo "============================================================"
echo "A3 F11 — PM2 OFF-TARGET SHAM CONTROL"
echo "============================================================"
echo "Started: $(date -Is)"
echo

echo "[1/9] Validating tools and locked inputs"

for tool in python samtools minimap2 bcftools; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "ERROR: Missing tool: $tool"
        exit 1
    }
done

for file in \
    "$SOURCE_POD5" \
    "$WINDOW_MAP" \
    "$ATTACK_IDS" \
    "$REF_IDS" \
    "$SOURCE_BACKGROUND" \
    "$REFERENCE"; do

    if [[ ! -s "$file" ]]; then
        echo "ERROR: Missing required input:"
        echo "$file"
        exit 1
    fi
done

ATTACK_COUNT="$(awk 'NF {n++} END {print n+0}' "$ATTACK_IDS")"
REF_COUNT="$(awk 'NF {n++} END {print n+0}' "$REF_IDS")"

[[ "$ATTACK_COUNT" -eq 14 ]] || {
    echo "ERROR: Expected 14 attack parents."
    exit 1
}

[[ "$REF_COUNT" -eq 10 ]] || {
    echo "ERROR: Expected 10 REF parents."
    exit 1
}

if [[ ! -s "$REFERENCE.fai" ]]; then
    samtools faidx "$REFERENCE"
fi

echo "Input validation: PASS"

echo
echo "[2/9] Generating PM2-sized off-target sham POD5"

export SOURCE_POD5
export WINDOW_MAP
export ATTACK_IDS
export SHAM_POD5
export SHAM_WINDOW_MAP
export GENERATION_AUDIT

python <<'PY_STAGE2'
from __future__ import annotations

import csv
import os
from dataclasses import replace
from pathlib import Path

import numpy as np
import pod5


source_path = Path(os.environ["SOURCE_POD5"])
window_path = Path(os.environ["WINDOW_MAP"])
attack_ids_path = Path(os.environ["ATTACK_IDS"])

output_path = Path(os.environ["SHAM_POD5"])
sham_map_path = Path(os.environ["SHAM_WINDOW_MAP"])
audit_path = Path(os.environ["GENERATION_AUDIT"])


def load_ids(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    }


attack_ids = load_ids(attack_ids_path)

if len(attack_ids) != 14:
    raise RuntimeError(
        f"Expected 14 attack IDs, found {len(attack_ids)}"
    )

with window_path.open(newline="") as handle:
    all_window_rows = list(
        csv.DictReader(handle, delimiter="\t")
    )

pm2_rows = []

for row in all_window_rows:
    parent_id = row.get("parent_read_id", "")

    context_value = row.get(
        "context_bases_each_side",
        row.get("context_bases", ""),
    )

    condition_value = row.get(
        "condition",
        row.get("window_condition", ""),
    )

    is_pm2 = (
        str(context_value).strip() == "2"
        or str(condition_value).strip().upper()
        in {"PM2", "E2_PM2"}
    )

    if is_pm2 and parent_id in attack_ids:
        pm2_rows.append(row)

if len(pm2_rows) != 14:
    available_columns = (
        sorted(all_window_rows[0])
        if all_window_rows
        else []
    )

    raise RuntimeError(
        f"Expected 14 PM2 window rows, found {len(pm2_rows)}. "
        f"Available columns: {available_columns}"
    )

row_by_parent = {
    row["parent_read_id"]: row
    for row in pm2_rows
}

start_candidates = [
    "window_signal_start_sample",
    "signal_start_sample",
    "window_start_sample",
]

end_candidates = [
    "window_signal_end_sample_exclusive",
    "signal_end_sample_exclusive",
    "window_end_sample_exclusive",
]


def resolve_integer(row: dict[str, str], names: list[str]) -> int:
    for name in names:
        value = row.get(name)

        if value not in {None, ""}:
            return int(value)

    raise RuntimeError(
        f"None of the expected columns were found: {names}"
    )


output_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

output_path.unlink(missing_ok=True)

audit_rows = []
sham_rows = []

source_ids = set()
sham_modified_ids = set()

with pod5.Reader(str(source_path)) as reader:
    with pod5.Writer(str(output_path)) as writer:
        for record in reader.reads():
            read_id = str(record.read_id)
            source_ids.add(read_id)

            # pod5.Reader.reads() yields ReadRecord, which cannot
            # be passed directly to dataclasses.replace().
            writable_read = record.to_read()

            original = np.asarray(
                writable_read.signal
            ).copy()

            modified = original.copy()

            if read_id not in attack_ids:
                writer.add_read(writable_read)
                continue

            row = row_by_parent[read_id]

            target_start = resolve_integer(
                row,
                start_candidates,
            )

            target_end = resolve_integer(
                row,
                end_candidates,
            )

            target_length = target_end - target_start
            signal_length = len(original)

            if target_length <= 0:
                raise RuntimeError(
                    f"{read_id}: invalid PM2 target window "
                    f"{target_start}:{target_end}"
                )

            if not (
                0 <= target_start
                < target_end
                <= signal_length
            ):
                raise RuntimeError(
                    f"{read_id}: target window outside signal; "
                    f"window={target_start}:{target_end}, "
                    f"signal_length={signal_length}"
                )

            downstream_start = target_end + 5000
            downstream_end = (
                downstream_start + target_length
            )

            upstream_end = target_start - 5000
            upstream_start = (
                upstream_end - target_length
            )

            if downstream_end < signal_length:
                sham_start = downstream_start
                sham_end = downstream_end
                direction = "downstream"

            elif upstream_start > 0:
                sham_start = upstream_start
                sham_end = upstream_end
                direction = "upstream"

            else:
                raise RuntimeError(
                    f"{read_id}: unable to place a PM2-sized "
                    f"sham window 5000 samples from target"
                )

            if not (
                0 < sham_start
                < sham_end
                < signal_length
            ):
                raise RuntimeError(
                    f"{read_id}: invalid sham interval "
                    f"{sham_start}:{sham_end}"
                )

            target_overlap = not (
                sham_end <= target_start
                or sham_start >= target_end
            )

            if target_overlap:
                raise RuntimeError(
                    f"{read_id}: sham interval overlaps target"
                )

            left_value = original[sham_start - 1]
            right_value = original[sham_end]

            interpolated = np.linspace(
                float(left_value),
                float(right_value),
                num=target_length + 2,
            )[1:-1]

            if np.issubdtype(
                original.dtype,
                np.integer,
            ):
                limits = np.iinfo(original.dtype)

                interpolated = np.clip(
                    np.rint(interpolated),
                    limits.min,
                    limits.max,
                ).astype(original.dtype)

            else:
                interpolated = interpolated.astype(
                    original.dtype
                )

            modified[sham_start:sham_end] = interpolated

            changed = original != modified

            target_changed = int(
                changed[target_start:target_end].sum()
            )

            sham_changed = int(
                changed[sham_start:sham_end].sum()
            )

            outside_changed = int(
                changed[:sham_start].sum()
                + changed[sham_end:].sum()
            )

            if target_changed != 0:
                raise RuntimeError(
                    f"{read_id}: F11 target signal changed"
                )

            if outside_changed != 0:
                raise RuntimeError(
                    f"{read_id}: signal changed outside sham window"
                )

            if sham_changed <= 0:
                raise RuntimeError(
                    f"{read_id}: interpolation made no signal changes"
                )

            modified_read = replace(
                writable_read,
                signal=modified,
            )

            writer.add_read(modified_read)
            sham_modified_ids.add(read_id)

            separation = min(
                abs(sham_start - target_end),
                abs(target_start - sham_end),
            )

            sham_rows.append(
                {
                    "parent_read_id": read_id,
                    "target_start": target_start,
                    "target_end_exclusive": target_end,
                    "target_window_samples": target_length,
                    "sham_start": sham_start,
                    "sham_end_exclusive": sham_end,
                    "sham_window_samples": target_length,
                    "direction": direction,
                    "minimum_signal_distance": separation,
                    "total_signal_samples": signal_length,
                }
            )

            audit_rows.append(
                {
                    "parent_read_id": read_id,
                    "target_changed_samples": target_changed,
                    "sham_changed_samples": sham_changed,
                    "outside_changed_samples": outside_changed,
                    "signal_length_unchanged": int(
                        len(modified) == len(original)
                    ),
                    "status": "PASS",
                }
            )

if len(source_ids) != 15:
    raise RuntimeError(
        f"Expected 15 source reads, found {len(source_ids)}"
    )

missing_attack_ids = attack_ids - source_ids

if missing_attack_ids:
    raise RuntimeError(
        "Attack IDs missing from source POD5: "
        + ",".join(sorted(missing_attack_ids))
    )

if sham_modified_ids != attack_ids:
    raise RuntimeError(
        "Sham-modified ID mismatch: "
        f"missing={sorted(attack_ids - sham_modified_ids)}, "
        f"unexpected={sorted(sham_modified_ids - attack_ids)}"
    )

if len(sham_rows) != 14 or len(audit_rows) != 14:
    raise RuntimeError(
        "Expected exactly 14 sham map and audit rows"
    )

with sham_map_path.open(
    "w",
    newline="",
    encoding="utf-8",
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(sham_rows[0].keys()),
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(sham_rows)

with audit_path.open(
    "w",
    newline="",
    encoding="utf-8",
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(audit_rows[0].keys()),
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(audit_rows)

print(f"Source reads: {len(source_ids)}")
print(
    f"Sham-attacked parents: "
    f"{len(sham_modified_ids)}"
)
print(
    "Total sham changed samples: "
    f"{sum(row['sham_changed_samples'] for row in audit_rows)}"
)
print(
    "F11 target changed samples: "
    f"{sum(row['target_changed_samples'] for row in audit_rows)}"
)
print(
    "Outside-window changed samples: "
    f"{sum(row['outside_changed_samples'] for row in audit_rows)}"
)
print("Sham POD5 generation: PASS")
PY_STAGE2

if [[ ! -s "$SHAM_POD5" ]]; then
    echo "ERROR: Sham POD5 was not created."
    exit 1
fi

export SHAM_POD5

python <<'PY_STAGE2_VALIDATE'
from pathlib import Path
import os

import pod5

path = Path(os.environ["SHAM_POD5"])

with pod5.Reader(str(path)) as reader:
    ids = [
        str(record.read_id)
        for record in reader.reads()
    ]

if len(ids) != 15:
    raise RuntimeError(
        f"Expected 15 sham POD5 reads, found {len(ids)}"
    )

if len(set(ids)) != 15:
    raise RuntimeError(
        "Duplicate read IDs found in sham POD5"
    )

print(f"Sham POD5 reads: {len(ids)}")
print("Sham POD5 structural validation: PASS")
PY_STAGE2_VALIDATE

echo
echo "[3/9] Resolving Dorado and model"

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

[[ -x "$DORADO" ]] || {
    echo "ERROR: Dorado not found."
    exit 1
}

MODEL_NAME="dna_r10.4.1_e8.2_400bps_hac@v6.0.0"

MODEL_PATH="$(
    find "$HOME" \
        -type d \
        -name "$MODEL_NAME" \
        2>/dev/null \
        | head -1
)"

[[ -d "$MODEL_PATH" ]] || {
    echo "ERROR: Dorado model not found."
    exit 1
}

echo "Dorado: $DORADO"
echo "Model: $MODEL_PATH"

echo
echo "[4/9] Re-basecalling sham POD5"

rm -f \
    "$RAW_BAM" \
    "$FASTQ" \
    "$ALIGNED_BAM" \
    "$ALIGNED_BAM.bai"

"$DORADO" basecaller \
    "$MODEL_PATH" \
    "$SHAM_POD5" \
    --device cuda:all \
    --emit-moves \
    > "$RAW_BAM" \
    2> "$SHAM_DIR/F11_PM2_off_target_dorado.log"

samtools view -H "$RAW_BAM" >/dev/null
samtools view "$RAW_BAM" >/dev/null

RAW_RECORDS="$(samtools view -c "$RAW_BAM")"

samtools fastq \
    -n \
    "$RAW_BAM" \
    > "$FASTQ"

minimap2 \
    -ax map-ont \
    -t 16 \
    "$REFERENCE" \
    "$FASTQ" \
    2> "$SHAM_DIR/F11_PM2_off_target_alignment.log" \
    | samtools sort \
        -@ 8 \
        -o "$ALIGNED_BAM" \
        -

samtools index "$ALIGNED_BAM"
samtools quickcheck -v "$ALIGNED_BAM"

MAPPED_RECORDS="$(samtools view -c -F 4 "$ALIGNED_BAM")"

echo "Dorado records: $RAW_RECORDS"
echo "Mapped records: $MAPPED_RECORDS"

echo
echo "[5/9] Auditing sham parent states at F11"

export RAW_BAM
export ALIGNED_BAM
export ATTACK_IDS
export RECORD_PARENT_MAP
export TARGET_PARENT_AUDIT
export TARGET_CHROM
export TARGET_POS

python <<'PY_EOF'
import csv
import os
from collections import defaultdict
from pathlib import Path

import pysam

raw_path = Path(os.environ["RAW_BAM"])
aligned_path = Path(os.environ["ALIGNED_BAM"])
ids_path = Path(os.environ["ATTACK_IDS"])

map_path = Path(os.environ["RECORD_PARENT_MAP"])
audit_path = Path(os.environ["TARGET_PARENT_AUDIT"])

chrom = os.environ["TARGET_CHROM"]
position = int(os.environ["TARGET_POS"])
target0 = position - 1

attack_ids = {
    line.strip()
    for line in ids_path.read_text().splitlines()
    if line.strip()
}

query_to_parent = {}

with pysam.AlignmentFile(
    str(raw_path),
    "rb",
    check_sq=False,
) as bam:
    for record in bam.fetch(until_eof=True):
        pid = (
            str(record.get_tag("pi"))
            if record.has_tag("pi")
            else record.query_name
        )

        query_to_parent[record.query_name] = pid

with map_path.open("w", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(["query_name", "parent_read_id"])

    for query_name in sorted(query_to_parent):
        writer.writerow(
            [query_name, query_to_parent[query_name]]
        )

states_by_parent = defaultdict(list)

with pysam.AlignmentFile(str(aligned_path), "rb") as bam:
    for record in bam.fetch(until_eof=True):
        pid = query_to_parent.get(
            record.query_name,
            record.query_name,
        )

        if pid not in attack_ids:
            continue

        state = "NO_COVERAGE"

        if record.is_unmapped:
            state = "UNMAPPED"
        elif record.reference_name == chrom:
            for query_pos, reference_pos in record.get_aligned_pairs(
                matches_only=False
            ):
                if reference_pos != target0:
                    continue

                if query_pos is None:
                    state = "DEL"
                else:
                    sequence = record.query_sequence or ""

                    if not 0 <= query_pos < len(sequence):
                        state = "OTHER"
                    else:
                        base = sequence[query_pos].upper()

                        if base == "T":
                            state = "ALT"
                        elif base == "G":
                            state = "REF"
                        else:
                            state = "OTHER"

                break

        states_by_parent[pid].append(state)

priority = [
    "ALT",
    "REF",
    "DEL",
    "OTHER",
    "NO_COVERAGE",
    "UNMAPPED",
]

rows = []

for pid in sorted(attack_ids):
    states = states_by_parent.get(pid, [])

    if states:
        parent_state = next(
            state
            for state in priority
            if state in states
        )
    else:
        parent_state = "NO_DORADO_RECORD"

    rows.append(
        {
            "parent_read_id": pid,
            "record_count": len(states),
            "record_states": ",".join(states),
            "parent_state": parent_state,
        }
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

alt_count = sum(
    row["parent_state"] == "ALT"
    for row in rows
)

print(f"Sham ALT parents: {alt_count}/14")

if alt_count != 14:
    print("NOTICE: Off-target sham altered one or more F11 parents.")
PY_EOF

echo
echo "Sham target-parent audit:"
column -t -s $'\t' "$TARGET_PARENT_AUDIT" 2>/dev/null \
    || cat "$TARGET_PARENT_AUDIT"

echo
echo "[6/9] Building controlled sham hybrid"

export SOURCE_BACKGROUND
export REF_IDS
export ALIGNED_BAM
export ATTACK_IDS
export RECORD_PARENT_MAP
export REF_BACKGROUND_BAM
export SHAM_REPLACEMENT_BAM
export HYBRID_UNSORTED

python <<'PY_STAGE6'
from __future__ import annotations

import csv
import os
from pathlib import Path

import pysam


def load_ids(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    }


def source_parent_id(
    record: pysam.AlignedSegment,
) -> str:
    if record.has_tag("pi"):
        return str(record.get_tag("pi"))

    return record.query_name


source_path = Path(os.environ["SOURCE_BACKGROUND"])
replacement_path = Path(os.environ["ALIGNED_BAM"])

ref_ids = load_ids(Path(os.environ["REF_IDS"]))
attack_ids = load_ids(Path(os.environ["ATTACK_IDS"]))

record_parent_map_path = Path(
    os.environ["RECORD_PARENT_MAP"]
)

background_output = Path(
    os.environ["REF_BACKGROUND_BAM"]
)

replacement_output = Path(
    os.environ["SHAM_REPLACEMENT_BAM"]
)

hybrid_output = Path(
    os.environ["HYBRID_UNSORTED"]
)

if len(ref_ids) != 10:
    raise RuntimeError(
        f"Expected 10 REF IDs, found {len(ref_ids)}"
    )

if len(attack_ids) != 14:
    raise RuntimeError(
        f"Expected 14 attack IDs, found {len(attack_ids)}"
    )

query_to_parent = {}

with record_parent_map_path.open(newline="") as handle:
    reader = csv.DictReader(
        handle,
        delimiter="\t",
    )

    for row in reader:
        query_to_parent[row["query_name"]] = (
            row["parent_read_id"]
        )

if not query_to_parent:
    raise RuntimeError(
        "Record-to-parent map is empty"
    )

with pysam.AlignmentFile(
    str(source_path),
    "rb",
) as source:
    output_header = source.header.to_dict()

background_parents = set()
background_records = 0

with pysam.AlignmentFile(
    str(source_path),
    "rb",
) as source:
    with pysam.AlignmentFile(
        str(background_output),
        "wb",
        header=output_header,
    ) as output:
        for record in source.fetch(until_eof=True):
            pid = source_parent_id(record)

            if pid not in ref_ids:
                continue

            output.write(record)
            background_parents.add(pid)
            background_records += 1

missing_background = ref_ids - background_parents

if missing_background:
    raise RuntimeError(
        "Missing REF background parents: "
        + ",".join(sorted(missing_background))
    )

replacement_parents = set()
replacement_records = 0
unknown_query_names = set()

with pysam.AlignmentFile(
    str(replacement_path),
    "rb",
) as source:
    with pysam.AlignmentFile(
        str(replacement_output),
        "wb",
        header=output_header,
    ) as output:
        for record in source.fetch(until_eof=True):
            pid = query_to_parent.get(
                record.query_name
            )

            if pid is None:
                unknown_query_names.add(
                    record.query_name
                )
                continue

            if pid not in attack_ids:
                continue

            output.write(record)
            replacement_parents.add(pid)
            replacement_records += 1

missing_replacements = (
    attack_ids - replacement_parents
)

if missing_replacements:
    raise RuntimeError(
        "Missing sham replacement parents: "
        + ",".join(sorted(missing_replacements))
        + f"; unmapped query names={sorted(unknown_query_names)}"
    )

with pysam.AlignmentFile(
    str(hybrid_output),
    "wb",
    header=output_header,
) as output:
    for input_path in [
        background_output,
        replacement_output,
    ]:
        with pysam.AlignmentFile(
            str(input_path),
            "rb",
        ) as source:
            for record in source.fetch(until_eof=True):
                output.write(record)

print(
    f"REF background records: {background_records}"
)
print(
    f"REF background parents: {len(background_parents)}"
)
print(
    f"Sham replacement records: {replacement_records}"
)
print(
    f"Sham replacement parents: {len(replacement_parents)}"
)
print(
    f"Unmatched aligned query names: "
    f"{len(unknown_query_names)}"
)
print("Controlled sham hybrid assembly: PASS")
PY_STAGE6

samtools sort \
    -@ 8 \
    -o "$HYBRID_SORTED" \
    "$HYBRID_UNSORTED"

samtools index "$HYBRID_SORTED"
samtools quickcheck -v "$HYBRID_SORTED"

HYBRID_RECORDS="$(
    samtools view -c "$HYBRID_SORTED"
)"

HYBRID_MAPPED="$(
    samtools view -c -F 4 "$HYBRID_SORTED"
)"

echo "Hybrid records: $HYBRID_RECORDS"
echo "Hybrid mapped records: $HYBRID_MAPPED"

if [[ "$HYBRID_MAPPED" -lt 24 ]]; then
    echo "ERROR: Sham hybrid contains fewer than 24 mapped records."
    exit 1
fi

echo
echo "[7/9] Calling the F11 variant in the sham hybrid"

bcftools mpileup \
    -f "$REFERENCE" \
    -r "$CALL_REGION" \
    -a FORMAT/AD,FORMAT/DP \
    -Q 0 \
    -q 0 \
    -d 100000 \
    -Ou \
    "$HYBRID_SORTED" \
    | bcftools call \
        -m \
        -v \
        -Ov \
        -o "$VCF"

{
    grep '^#' "$VCF"

    awk -F '\t' \
        -v chrom="$TARGET_CHROM" \
        -v pos="$TARGET_POS" '
        !/^#/ && $1 == chrom && $2 == pos
    ' "$VCF"
} > "$TARGET_VCF"

echo
echo "[8/9] Building and validating the sham result"

export HYBRID_SORTED
export TARGET_PARENT_AUDIT
export TARGET_VCF
export SUMMARY
export REPORT

python <<'PY_EOF'
import csv
import os
from collections import Counter
from pathlib import Path

import pysam

bam_path = Path(os.environ["HYBRID_SORTED"])
parent_path = Path(os.environ["TARGET_PARENT_AUDIT"])
vcf_path = Path(os.environ["TARGET_VCF"])

summary_path = Path(os.environ["SUMMARY"])
report_path = Path(os.environ["REPORT"])

chrom = "chr4"
position = 186274193
target0 = position - 1

with parent_path.open(newline="") as handle:
    parent_rows = list(csv.DictReader(handle, delimiter="\t"))

parent_counts = Counter(
    row["parent_state"]
    for row in parent_rows
)

pileup_counts = Counter()
depth = 0

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
        for item in column.pileups:
            depth += 1

            if item.is_del or item.is_refskip:
                pileup_counts["DEL"] += 1
                continue

            query_pos = item.query_position
            sequence = item.alignment.query_sequence or ""

            if query_pos is None or query_pos >= len(sequence):
                pileup_counts["OTHER"] += 1
                continue

            base = sequence[query_pos].upper()

            if base == "G":
                pileup_counts["REF"] += 1
            elif base == "T":
                pileup_counts["ALT"] += 1
            else:
                pileup_counts["OTHER"] += 1

records = []

with vcf_path.open() as handle:
    for line in handle:
        if not line.startswith("#"):
            records.append(line.rstrip("\n").split("\t"))

if records:
    fields = records[0]
    format_keys = fields[8].split(":")
    sample_values = fields[9].split(":")
    sample = dict(zip(format_keys, sample_values))

    vcf_record = 1
    gt = sample.get("GT", ".")
    qual = fields[5]
    dp = sample.get("DP", ".")
    ad = sample.get("AD", ".")
else:
    vcf_record = 0
    gt = "NO_CALL"
    qual = "."
    dp = "."
    ad = "."

alt_fraction = (
    pileup_counts["ALT"]
    / (
        pileup_counts["REF"]
        + pileup_counts["ALT"]
    )
    if (
        pileup_counts["REF"]
        + pileup_counts["ALT"]
    )
    else 0.0
)

errors = []

if parent_counts["ALT"] != 14:
    errors.append(
        f"Expected 14 sham ALT parents; "
        f"observed {parent_counts['ALT']}"
    )

if vcf_record != 1:
    errors.append("F11 target VCF record was lost in sham control")

if gt != "0/1":
    errors.append(
        f"Expected sham genotype 0/1; observed {gt}"
    )

status = "PASS" if not errors else "FAIL"

row = {
    "condition": "PM2_OFF_TARGET_SHAM",
    "sham_ALT_parents": parent_counts["ALT"],
    "sham_REF_parents": parent_counts["REF"],
    "sham_DEL_parents": parent_counts["DEL"],
    "sham_OTHER_parents": parent_counts["OTHER"],
    "pileup_depth": depth,
    "pileup_REF": pileup_counts["REF"],
    "pileup_ALT": pileup_counts["ALT"],
    "pileup_DEL": pileup_counts["DEL"],
    "pileup_OTHER": pileup_counts["OTHER"],
    "ALT_fraction": f"{alt_fraction:.6f}",
    "vcf_record": vcf_record,
    "GT": gt,
    "QUAL": qual,
    "FORMAT_DP": dp,
    "FORMAT_AD": ad,
    "validation_errors": len(errors),
    "status": status,
}

with summary_path.open("w", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(row.keys()),
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerow(row)

lines = [
    "A3 F11 PM2 Off-Target Sham Control",
    "==================================",
    "",
    "Control design:",
    "  Same 14 F11 ALT-confirmed parents",
    "  Same PM2 signal-window length per parent",
    "  Interpolation shifted at least 5,000 signal samples away",
    "  F11 target signal samples unchanged",
    "",
    f"Sham ALT parents: {parent_counts['ALT']}/14",
    f"Pileup REF: {pileup_counts['REF']}",
    f"Pileup ALT: {pileup_counts['ALT']}",
    f"ALT fraction: {alt_fraction:.6f}",
    f"VCF target record: {vcf_record}",
    f"Genotype: {gt}",
    f"QUAL: {qual}",
    f"Validation errors: {len(errors)}",
    "",
    f"Overall status: "
    f"{'OFF_TARGET_SHAM_RETAINED_PATHOGENIC_CALL' if not errors else 'OFF_TARGET_SHAM_REQUIRES_REVIEW'}",
]

if errors:
    lines.extend(["", "Errors:"])
    lines.extend(f"- {error}" for error in errors)

report_path.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print(report_path.read_text())

if errors:
    raise SystemExit(1)
PY_EOF

echo
echo "Sham summary:"
column -t -s $'\t' "$SUMMARY" 2>/dev/null \
    || cat "$SUMMARY"

echo
echo "[9/9] Creating completion marker"

{
    echo "Completed: $(date -Is)"
    echo "Control: PM2-sized off-target interpolation"
    echo "Signal offset: at least 5,000 samples from F11 target"
    echo "Attack parents: 14"
    echo "Summary: $SUMMARY"
    echo "Report: $REPORT"
    echo "Overall status: OFF_TARGET_SHAM_RETAINED_PATHOGENIC_CALL"
} > "$COMPLETE"

rm -f "$FAILED"

echo
echo "============================================================"
echo "A3 F11 PM2 OFF-TARGET SHAM COMPLETE"
echo "============================================================"
