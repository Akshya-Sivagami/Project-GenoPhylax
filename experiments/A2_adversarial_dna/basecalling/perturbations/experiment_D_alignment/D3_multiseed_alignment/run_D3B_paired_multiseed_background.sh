#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$HOME/Project-GenoPhylax"

EXP_D_DIR="$PROJECT_ROOT/experiments/A2_adversarial_dna/basecalling/perturbations/experiment_D_alignment"
D1_DIR="$EXP_D_DIR/D1_clean_validation"
D3_DIR="$EXP_D_DIR/D3_multiseed_alignment"

ALIGN_DIR="$D3_DIR/alignments"
ANALYSIS_DIR="$D3_DIR/paired_analysis"
METRICS_DIR="$D3_DIR/metrics"
SCRIPT_DIR="$D3_DIR/scripts"

PYTHON_SCRIPT="$SCRIPT_DIR/analyze_D3B_paired_multiseed.py"

CLEAN_BAM="$D1_DIR/alignments/hg002_1000reads_clean_GRCh38.sorted.bam"

RUN_SUMMARY="$METRICS_DIR/experiment_D3B_9run_paired_summary.tsv"
LEVEL_SUMMARY="$METRICS_DIR/experiment_D3B_level_aggregates.tsv"
MONOTONICITY_TSV="$METRICS_DIR/experiment_D3B_monotonicity.tsv"
TOP_EVENTS_TSV="$METRICS_DIR/experiment_D3B_top_alignment_changes.tsv"
FINDINGS_TXT="$METRICS_DIR/experiment_D3B_paired_multiseed_findings.txt"

COMPLETE_FILE="$D3_DIR/D3B_PAIRED_MULTISEED_COMPLETE"
FAILED_FILE="$D3_DIR/D3B_PAIRED_MULTISEED_FAILED"

mkdir -p \
    "$ANALYSIS_DIR" \
    "$METRICS_DIR" \
    "$SCRIPT_DIR"

rm -f "$COMPLETE_FILE" "$FAILED_FILE"

trap '
    STATUS=$?
    echo
    echo "============================================================"
    echo "D3B paired multi-seed analysis failed with exit status: $STATUS"
    echo "Time: $(date --iso-8601=seconds)"
    echo "============================================================"
    touch "$FAILED_FILE"
    exit "$STATUS"
' ERR

echo "============================================================"
echo "Experiment D3B — Paired multi-seed alignment analysis"
echo "Started: $(date --iso-8601=seconds)"
echo "============================================================"
echo

echo "[1/5] Validating CLEAN and nine perturbed alignments"
echo "------------------------------------------------------------"

python - <<'PY'
import pysam
print("pysam version:", pysam.__version__)
PY

if [[ ! -s "$CLEAN_BAM" ]]; then
    echo "ERROR: CLEAN BAM not found:"
    echo "$CLEAN_BAM"
    exit 1
fi

if ! samtools quickcheck "$CLEAN_BAM"; then
    echo "ERROR: CLEAN BAM failed quickcheck."
    exit 1
fi

CLEAN_PRIMARY="$(samtools view -c -F 2304 "$CLEAN_BAM")"

if [[ "$CLEAN_PRIMARY" -ne 1000 ]]; then
    echo "ERROR: CLEAN BAM does not contain 1,000 primary records."
    exit 1
fi

echo "CLEAN:"
ls -lh "$CLEAN_BAM"
echo

for CONDITION in GN01 GN05 GN10; do
    CONDITION_LOWER="$(printf '%s' "$CONDITION" | tr '[:upper:]' '[:lower:]')"

    for SEED in 1 2 3; do
        BAM="$ALIGN_DIR/hg002_1000reads_${CONDITION_LOWER}_seed${SEED}_GRCh38.sorted.bam"

        if [[ ! -s "$BAM" ]]; then
            echo "ERROR: Missing aligned BAM:"
            echo "$BAM"
            exit 1
        fi

        if ! samtools quickcheck "$BAM"; then
            echo "ERROR: BAM failed quickcheck:"
            echo "$BAM"
            exit 1
        fi

        PRIMARY="$(samtools view -c -F 2304 "$BAM")"

        if [[ "$PRIMARY" -ne 1000 ]]; then
            echo "ERROR: Expected 1,000 primary records:"
            echo "$BAM"
            echo "Observed: $PRIMARY"
            exit 1
        fi

        echo "${CONDITION} seed ${SEED}: PASS"
        ls -lh "$BAM"
        echo
    done
done

echo "All ten BAM files: PASS"
echo

echo "[2/5] Writing paired multi-seed analysis script"
echo "------------------------------------------------------------"

cat > "$PYTHON_SCRIPT" <<'PY'
#!/usr/bin/env python3

from __future__ import annotations

import csv
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import pysam


@dataclass
class PrimaryRecord:
    read_id: str
    mapped: bool
    chrom: Optional[str]
    start: Optional[int]
    end: Optional[int]
    strand: Optional[str]
    mapq: int
    cigar: str
    nm: Optional[int]
    soft_clip: int
    hard_clip: int
    insertion_bases: int
    deletion_bases: int
    aligned_query_length: int
    reference_span: int


def cigar_metrics(
    cigartuples: Optional[list[tuple[int, int]]],
) -> tuple[int, int, int, int]:
    soft_clip = 0
    hard_clip = 0
    insertion_bases = 0
    deletion_bases = 0

    if not cigartuples:
        return soft_clip, hard_clip, insertion_bases, deletion_bases

    for operation, length in cigartuples:
        if operation == 4:
            soft_clip += length
        elif operation == 5:
            hard_clip += length
        elif operation == 1:
            insertion_bases += length
        elif operation == 2:
            deletion_bases += length

    return soft_clip, hard_clip, insertion_bases, deletion_bases


def load_bam(
    bam_path: Path,
) -> tuple[Dict[str, PrimaryRecord], Counter, Counter]:
    primary: Dict[str, PrimaryRecord] = {}
    secondary_counts: Counter = Counter()
    supplementary_counts: Counter = Counter()

    with pysam.AlignmentFile(str(bam_path), "rb") as bam:
        for record in bam.fetch(until_eof=True):
            read_id = record.query_name

            if record.is_secondary:
                secondary_counts[read_id] += 1
                continue

            if record.is_supplementary:
                supplementary_counts[read_id] += 1
                continue

            if read_id in primary:
                raise RuntimeError(
                    f"Duplicate primary record for {read_id} in {bam_path}"
                )

            mapped = not record.is_unmapped

            if mapped:
                chrom = record.reference_name
                start = int(record.reference_start)
                end = int(record.reference_end)
                strand = "-" if record.is_reverse else "+"
                mapq = int(record.mapping_quality)
                cigar = record.cigarstring or "*"
                nm = int(record.get_tag("NM")) if record.has_tag("NM") else None

                (
                    soft_clip,
                    hard_clip,
                    insertion_bases,
                    deletion_bases,
                ) = cigar_metrics(record.cigartuples)

                aligned_query_length = int(record.query_alignment_length or 0)
                reference_span = max(0, end - start)
            else:
                chrom = None
                start = None
                end = None
                strand = None
                mapq = 0
                cigar = "*"
                nm = None
                soft_clip = 0
                hard_clip = 0
                insertion_bases = 0
                deletion_bases = 0
                aligned_query_length = 0
                reference_span = 0

            primary[read_id] = PrimaryRecord(
                read_id=read_id,
                mapped=mapped,
                chrom=chrom,
                start=start,
                end=end,
                strand=strand,
                mapq=mapq,
                cigar=cigar,
                nm=nm,
                soft_clip=soft_clip,
                hard_clip=hard_clip,
                insertion_bases=insertion_bases,
                deletion_bases=deletion_bases,
                aligned_query_length=aligned_query_length,
                reference_span=reference_span,
            )

    return primary, secondary_counts, supplementary_counts


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.mean(values) if values else math.nan


def median(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.median(values) if values else math.nan


def sd(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.stdev(values) if len(values) > 1 else 0.0


def fmt(value: float) -> str:
    if math.isnan(value):
        return "NA"
    return f"{value:.6f}"


def numeric(value: str) -> float:
    return float(value)


def main() -> None:
    project_root = Path.home() / "Project-GenoPhylax"

    exp_d_dir = (
        project_root
        / "experiments/A2_adversarial_dna/basecalling/perturbations"
        / "experiment_D_alignment"
    )

    d1_dir = exp_d_dir / "D1_clean_validation"
    d3_dir = exp_d_dir / "D3_multiseed_alignment"

    align_dir = d3_dir / "alignments"
    analysis_dir = d3_dir / "paired_analysis"
    metrics_dir = d3_dir / "metrics"

    analysis_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    clean_path = (
        d1_dir
        / "alignments/hg002_1000reads_clean_GRCh38.sorted.bam"
    )

    clean_primary, clean_secondary, clean_supplementary = load_bam(
        clean_path
    )

    if len(clean_primary) != 1000:
        raise RuntimeError(
            f"CLEAN expected 1000 primary reads, found {len(clean_primary)}"
        )

    clean_ids = set(clean_primary)

    run_rows = []
    top_events = []

    for condition in ("GN01", "GN05", "GN10"):
        condition_lower = condition.lower()

        for seed in (1, 2, 3):
            bam_path = (
                align_dir
                / (
                    f"hg002_1000reads_{condition_lower}_seed{seed}"
                    "_GRCh38.sorted.bam"
                )
            )

            (
                perturbed_primary,
                perturbed_secondary,
                perturbed_supplementary,
            ) = load_bam(bam_path)

            if len(perturbed_primary) != 1000:
                raise RuntimeError(
                    f"{condition} seed {seed}: expected 1000 primary reads, "
                    f"found {len(perturbed_primary)}"
                )

            if set(perturbed_primary) != clean_ids:
                missing = clean_ids - set(perturbed_primary)
                extra = set(perturbed_primary) - clean_ids

                raise RuntimeError(
                    f"{condition} seed {seed}: read ID mismatch; "
                    f"missing={len(missing)}, extra={len(extra)}"
                )

            paired_path = (
                analysis_dir
                / f"{condition}_seed{seed}_vs_CLEAN_per_read.tsv"
            )

            counts = Counter()
            values = defaultdict(list)

            fieldnames = [
                "condition",
                "seed",
                "read_id",
                "mapping_transition",
                "clean_mapped",
                "perturbed_mapped",
                "clean_chrom",
                "perturbed_chrom",
                "chromosome_changed",
                "clean_start",
                "perturbed_start",
                "coordinate_shift_bp",
                "coordinate_shift_ge100",
                "coordinate_shift_ge1000",
                "clean_strand",
                "perturbed_strand",
                "strand_changed",
                "clean_mapq",
                "perturbed_mapq",
                "mapq_change",
                "mapq_drop_ge5",
                "mapq_drop_ge10",
                "clean_nm",
                "perturbed_nm",
                "nm_change",
                "nm_increased",
                "clean_cigar",
                "perturbed_cigar",
                "cigar_changed",
                "clean_soft_clip",
                "perturbed_soft_clip",
                "soft_clip_change",
                "soft_clip_increased",
                "clean_hard_clip",
                "perturbed_hard_clip",
                "hard_clip_change",
                "clean_insertion_bases",
                "perturbed_insertion_bases",
                "insertion_change",
                "clean_deletion_bases",
                "perturbed_deletion_bases",
                "deletion_change",
                "clean_aligned_query_length",
                "perturbed_aligned_query_length",
                "aligned_query_length_change",
                "clean_reference_span",
                "perturbed_reference_span",
                "reference_span_change",
                "clean_secondary_count",
                "perturbed_secondary_count",
                "secondary_count_change",
                "clean_supplementary_count",
                "perturbed_supplementary_count",
                "supplementary_count_change",
            ]

            with paired_path.open("w", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=fieldnames,
                    delimiter="\t",
                )
                writer.writeheader()

                for read_id in sorted(clean_ids):
                    clean = clean_primary[read_id]
                    perturbed = perturbed_primary[read_id]

                    if clean.mapped and perturbed.mapped:
                        transition = "mapped_to_mapped"
                    elif clean.mapped and not perturbed.mapped:
                        transition = "mapped_to_unmapped"
                    elif not clean.mapped and perturbed.mapped:
                        transition = "unmapped_to_mapped"
                    else:
                        transition = "unmapped_to_unmapped"

                    counts[transition] += 1

                    both_mapped = clean.mapped and perturbed.mapped
                    same_chrom = (
                        both_mapped and clean.chrom == perturbed.chrom
                    )

                    chromosome_changed = (
                        both_mapped and clean.chrom != perturbed.chrom
                    )

                    strand_changed = (
                        both_mapped and clean.strand != perturbed.strand
                    )

                    coordinate_shift = (
                        abs(perturbed.start - clean.start)
                        if same_chrom
                        else None
                    )

                    mapq_change = (
                        perturbed.mapq - clean.mapq
                        if both_mapped
                        else None
                    )

                    nm_change = (
                        perturbed.nm - clean.nm
                        if (
                            both_mapped
                            and perturbed.nm is not None
                            and clean.nm is not None
                        )
                        else None
                    )

                    cigar_changed = (
                        both_mapped and clean.cigar != perturbed.cigar
                    )

                    soft_clip_change = (
                        perturbed.soft_clip - clean.soft_clip
                        if both_mapped
                        else None
                    )

                    hard_clip_change = (
                        perturbed.hard_clip - clean.hard_clip
                        if both_mapped
                        else None
                    )

                    insertion_change = (
                        perturbed.insertion_bases
                        - clean.insertion_bases
                        if both_mapped
                        else None
                    )

                    deletion_change = (
                        perturbed.deletion_bases
                        - clean.deletion_bases
                        if both_mapped
                        else None
                    )

                    aligned_query_length_change = (
                        perturbed.aligned_query_length
                        - clean.aligned_query_length
                        if both_mapped
                        else None
                    )

                    reference_span_change = (
                        perturbed.reference_span
                        - clean.reference_span
                        if both_mapped
                        else None
                    )

                    clean_secondary_count = clean_secondary[read_id]
                    perturbed_secondary_count = (
                        perturbed_secondary[read_id]
                    )
                    secondary_change = (
                        perturbed_secondary_count
                        - clean_secondary_count
                    )

                    clean_supplementary_count = (
                        clean_supplementary[read_id]
                    )
                    perturbed_supplementary_count = (
                        perturbed_supplementary[read_id]
                    )
                    supplementary_change = (
                        perturbed_supplementary_count
                        - clean_supplementary_count
                    )

                    if chromosome_changed:
                        counts["chromosome_changed"] += 1

                    if strand_changed:
                        counts["strand_changed"] += 1

                    if cigar_changed:
                        counts["cigar_changed"] += 1

                    if coordinate_shift is not None:
                        values["coordinate_shift"].append(
                            coordinate_shift
                        )

                        if coordinate_shift >= 100:
                            counts["coordinate_shift_ge100"] += 1

                        if coordinate_shift >= 1000:
                            counts["coordinate_shift_ge1000"] += 1

                    if mapq_change is not None:
                        values["mapq_change"].append(mapq_change)

                        if mapq_change <= -5:
                            counts["mapq_drop_ge5"] += 1

                        if mapq_change <= -10:
                            counts["mapq_drop_ge10"] += 1

                    if nm_change is not None:
                        values["nm_change"].append(nm_change)

                        if nm_change > 0:
                            counts["nm_increased_reads"] += 1

                    if soft_clip_change is not None:
                        values["soft_clip_change"].append(
                            soft_clip_change
                        )

                        if soft_clip_change > 0:
                            counts["soft_clip_increased_reads"] += 1

                    if hard_clip_change is not None:
                        values["hard_clip_change"].append(
                            hard_clip_change
                        )

                    if insertion_change is not None:
                        values["insertion_change"].append(
                            insertion_change
                        )

                    if deletion_change is not None:
                        values["deletion_change"].append(
                            deletion_change
                        )

                    if aligned_query_length_change is not None:
                        values["aligned_query_length_change"].append(
                            aligned_query_length_change
                        )

                    if reference_span_change is not None:
                        values["reference_span_change"].append(
                            reference_span_change
                        )

                    values["secondary_change"].append(
                        secondary_change
                    )
                    values["supplementary_change"].append(
                        supplementary_change
                    )

                    if secondary_change > 0:
                        counts["secondary_increased_reads"] += 1

                    if supplementary_change > 0:
                        counts[
                            "supplementary_increased_reads"
                        ] += 1

                    event_score = 0

                    if transition == "mapped_to_unmapped":
                        event_score += 100000

                    if chromosome_changed:
                        event_score += 50000

                    if strand_changed:
                        event_score += 10000

                    if coordinate_shift is not None:
                        event_score += min(coordinate_shift, 9999)

                    if mapq_change is not None and mapq_change < 0:
                        event_score += abs(mapq_change) * 100

                    if nm_change is not None and nm_change > 0:
                        event_score += nm_change * 10

                    if (
                        soft_clip_change is not None
                        and soft_clip_change > 0
                    ):
                        event_score += soft_clip_change

                    if event_score > 0:
                        top_events.append(
                            {
                                "condition": condition,
                                "seed": seed,
                                "read_id": read_id,
                                "event_score": event_score,
                                "mapping_transition": transition,
                                "clean_chrom": clean.chrom or "*",
                                "perturbed_chrom": (
                                    perturbed.chrom or "*"
                                ),
                                "coordinate_shift_bp": (
                                    coordinate_shift
                                    if coordinate_shift is not None
                                    else "NA"
                                ),
                                "clean_mapq": clean.mapq,
                                "perturbed_mapq": perturbed.mapq,
                                "mapq_change": (
                                    mapq_change
                                    if mapq_change is not None
                                    else "NA"
                                ),
                                "clean_nm": (
                                    clean.nm
                                    if clean.nm is not None
                                    else "NA"
                                ),
                                "perturbed_nm": (
                                    perturbed.nm
                                    if perturbed.nm is not None
                                    else "NA"
                                ),
                                "nm_change": (
                                    nm_change
                                    if nm_change is not None
                                    else "NA"
                                ),
                                "soft_clip_change": (
                                    soft_clip_change
                                    if soft_clip_change is not None
                                    else "NA"
                                ),
                            }
                        )

                    writer.writerow(
                        {
                            "condition": condition,
                            "seed": seed,
                            "read_id": read_id,
                            "mapping_transition": transition,
                            "clean_mapped": int(clean.mapped),
                            "perturbed_mapped": int(
                                perturbed.mapped
                            ),
                            "clean_chrom": clean.chrom or "*",
                            "perturbed_chrom": (
                                perturbed.chrom or "*"
                            ),
                            "chromosome_changed": int(
                                chromosome_changed
                            ),
                            "clean_start": (
                                clean.start
                                if clean.start is not None
                                else "NA"
                            ),
                            "perturbed_start": (
                                perturbed.start
                                if perturbed.start is not None
                                else "NA"
                            ),
                            "coordinate_shift_bp": (
                                coordinate_shift
                                if coordinate_shift is not None
                                else "NA"
                            ),
                            "coordinate_shift_ge100": int(
                                coordinate_shift is not None
                                and coordinate_shift >= 100
                            ),
                            "coordinate_shift_ge1000": int(
                                coordinate_shift is not None
                                and coordinate_shift >= 1000
                            ),
                            "clean_strand": clean.strand or "*",
                            "perturbed_strand": (
                                perturbed.strand or "*"
                            ),
                            "strand_changed": int(strand_changed),
                            "clean_mapq": clean.mapq,
                            "perturbed_mapq": perturbed.mapq,
                            "mapq_change": (
                                mapq_change
                                if mapq_change is not None
                                else "NA"
                            ),
                            "mapq_drop_ge5": int(
                                mapq_change is not None
                                and mapq_change <= -5
                            ),
                            "mapq_drop_ge10": int(
                                mapq_change is not None
                                and mapq_change <= -10
                            ),
                            "clean_nm": (
                                clean.nm
                                if clean.nm is not None
                                else "NA"
                            ),
                            "perturbed_nm": (
                                perturbed.nm
                                if perturbed.nm is not None
                                else "NA"
                            ),
                            "nm_change": (
                                nm_change
                                if nm_change is not None
                                else "NA"
                            ),
                            "nm_increased": int(
                                nm_change is not None
                                and nm_change > 0
                            ),
                            "clean_cigar": clean.cigar,
                            "perturbed_cigar": perturbed.cigar,
                            "cigar_changed": int(cigar_changed),
                            "clean_soft_clip": clean.soft_clip,
                            "perturbed_soft_clip": (
                                perturbed.soft_clip
                            ),
                            "soft_clip_change": (
                                soft_clip_change
                                if soft_clip_change is not None
                                else "NA"
                            ),
                            "soft_clip_increased": int(
                                soft_clip_change is not None
                                and soft_clip_change > 0
                            ),
                            "clean_hard_clip": clean.hard_clip,
                            "perturbed_hard_clip": (
                                perturbed.hard_clip
                            ),
                            "hard_clip_change": (
                                hard_clip_change
                                if hard_clip_change is not None
                                else "NA"
                            ),
                            "clean_insertion_bases": (
                                clean.insertion_bases
                            ),
                            "perturbed_insertion_bases": (
                                perturbed.insertion_bases
                            ),
                            "insertion_change": (
                                insertion_change
                                if insertion_change is not None
                                else "NA"
                            ),
                            "clean_deletion_bases": (
                                clean.deletion_bases
                            ),
                            "perturbed_deletion_bases": (
                                perturbed.deletion_bases
                            ),
                            "deletion_change": (
                                deletion_change
                                if deletion_change is not None
                                else "NA"
                            ),
                            "clean_aligned_query_length": (
                                clean.aligned_query_length
                            ),
                            "perturbed_aligned_query_length": (
                                perturbed.aligned_query_length
                            ),
                            "aligned_query_length_change": (
                                aligned_query_length_change
                                if aligned_query_length_change
                                is not None
                                else "NA"
                            ),
                            "clean_reference_span": (
                                clean.reference_span
                            ),
                            "perturbed_reference_span": (
                                perturbed.reference_span
                            ),
                            "reference_span_change": (
                                reference_span_change
                                if reference_span_change is not None
                                else "NA"
                            ),
                            "clean_secondary_count": (
                                clean_secondary_count
                            ),
                            "perturbed_secondary_count": (
                                perturbed_secondary_count
                            ),
                            "secondary_count_change": (
                                secondary_change
                            ),
                            "clean_supplementary_count": (
                                clean_supplementary_count
                            ),
                            "perturbed_supplementary_count": (
                                perturbed_supplementary_count
                            ),
                            "supplementary_count_change": (
                                supplementary_change
                            ),
                        }
                    )

            run_rows.append(
                {
                    "condition": condition,
                    "seed": seed,
                    "paired_reads": 1000,
                    "mapped_to_mapped": (
                        counts["mapped_to_mapped"]
                    ),
                    "mapped_to_unmapped": (
                        counts["mapped_to_unmapped"]
                    ),
                    "unmapped_to_mapped": (
                        counts["unmapped_to_mapped"]
                    ),
                    "unmapped_to_unmapped": (
                        counts["unmapped_to_unmapped"]
                    ),
                    "chromosome_changed": (
                        counts["chromosome_changed"]
                    ),
                    "strand_changed": counts["strand_changed"],
                    "cigar_changed": counts["cigar_changed"],
                    "coordinate_shift_ge100": (
                        counts["coordinate_shift_ge100"]
                    ),
                    "coordinate_shift_ge1000": (
                        counts["coordinate_shift_ge1000"]
                    ),
                    "mean_coordinate_shift_bp": fmt(
                        mean(values["coordinate_shift"])
                    ),
                    "median_coordinate_shift_bp": fmt(
                        median(values["coordinate_shift"])
                    ),
                    "mean_mapq_change": fmt(
                        mean(values["mapq_change"])
                    ),
                    "mapq_drop_ge5": counts["mapq_drop_ge5"],
                    "mapq_drop_ge10": counts["mapq_drop_ge10"],
                    "mean_nm_change": fmt(
                        mean(values["nm_change"])
                    ),
                    "nm_increased_reads": (
                        counts["nm_increased_reads"]
                    ),
                    "mean_soft_clip_change": fmt(
                        mean(values["soft_clip_change"])
                    ),
                    "soft_clip_increased_reads": (
                        counts["soft_clip_increased_reads"]
                    ),
                    "mean_hard_clip_change": fmt(
                        mean(values["hard_clip_change"])
                    ),
                    "mean_insertion_change": fmt(
                        mean(values["insertion_change"])
                    ),
                    "mean_deletion_change": fmt(
                        mean(values["deletion_change"])
                    ),
                    "mean_aligned_query_length_change": fmt(
                        mean(values["aligned_query_length_change"])
                    ),
                    "mean_reference_span_change": fmt(
                        mean(values["reference_span_change"])
                    ),
                    "mean_secondary_count_change": fmt(
                        mean(values["secondary_change"])
                    ),
                    "secondary_increased_reads": (
                        counts["secondary_increased_reads"]
                    ),
                    "mean_supplementary_count_change": fmt(
                        mean(values["supplementary_change"])
                    ),
                    "supplementary_increased_reads": (
                        counts["supplementary_increased_reads"]
                    ),
                }
            )

    run_summary_path = (
        metrics_dir / "experiment_D3B_9run_paired_summary.tsv"
    )

    with run_summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(run_rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(run_rows)

    grouped = defaultdict(list)

    for row in run_rows:
        grouped[row["condition"]].append(row)

    aggregate_metrics = [
        key
        for key in run_rows[0].keys()
        if key not in {"condition", "seed", "paired_reads"}
    ]

    level_rows = []

    for condition in ("GN01", "GN05", "GN10"):
        rows = grouped[condition]

        out = {
            "condition": condition,
            "seeds": len(rows),
        }

        for metric in aggregate_metrics:
            vals = [
                numeric(row[metric])
                for row in rows
                if row[metric] != "NA"
            ]

            out[f"mean_{metric}"] = fmt(mean(vals))
            out[f"sd_{metric}"] = fmt(sd(vals))

        level_rows.append(out)

    level_summary_path = (
        metrics_dir / "experiment_D3B_level_aggregates.tsv"
    )

    with level_summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(level_rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(level_rows)

    monotonic_specs = {
        "mean_mapped_to_unmapped": "increasing",
        "mean_chromosome_changed": "increasing",
        "mean_strand_changed": "increasing",
        "mean_cigar_changed": "increasing",
        "mean_coordinate_shift_ge100": "increasing",
        "mean_coordinate_shift_ge1000": "increasing",
        "mean_mapq_drop_ge5": "increasing",
        "mean_mapq_drop_ge10": "increasing",
        "mean_nm_increased_reads": "increasing",
        "mean_soft_clip_increased_reads": "increasing",
        "mean_secondary_increased_reads": "increasing",
        "mean_supplementary_increased_reads": "increasing",
        "mean_mean_mapq_change": "decreasing",
        "mean_mean_aligned_query_length_change": "decreasing",
    }

    monotonic_rows = []

    for metric, direction in monotonic_specs.items():
        vals = [
            float(row[metric])
            for row in level_rows
        ]

        if direction == "increasing":
            monotonic = vals[0] <= vals[1] <= vals[2]
        else:
            monotonic = vals[0] >= vals[1] >= vals[2]

        monotonic_rows.append(
            {
                "metric": metric,
                "GN01": f"{vals[0]:.6f}",
                "GN05": f"{vals[1]:.6f}",
                "GN10": f"{vals[2]:.6f}",
                "expected_direction": direction,
                "monotonic": str(monotonic),
            }
        )

    monotonicity_path = (
        metrics_dir / "experiment_D3B_monotonicity.tsv"
    )

    with monotonicity_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(monotonic_rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(monotonic_rows)

    top_events.sort(
        key=lambda row: (
            -int(row["event_score"]),
            row["condition"],
            int(row["seed"]),
            row["read_id"],
        )
    )

    top_events_path = (
        metrics_dir / "experiment_D3B_top_alignment_changes.tsv"
    )

    top_fields = [
        "condition",
        "seed",
        "read_id",
        "event_score",
        "mapping_transition",
        "clean_chrom",
        "perturbed_chrom",
        "coordinate_shift_bp",
        "clean_mapq",
        "perturbed_mapq",
        "mapq_change",
        "clean_nm",
        "perturbed_nm",
        "nm_change",
        "soft_clip_change",
    ]

    with top_events_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=top_fields,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(top_events[:150])

    findings_path = (
        metrics_dir
        / "experiment_D3B_paired_multiseed_findings.txt"
    )

    with findings_path.open("w") as handle:
        handle.write(
            "Experiment D3B — Paired multi-seed alignment findings\n\n"
        )

        for row in level_rows:
            handle.write(f"{row['condition']} aggregate\n")
            handle.write("-" * 60 + "\n")

            selected = [
                "mean_mapped_to_unmapped",
                "mean_chromosome_changed",
                "mean_strand_changed",
                "mean_cigar_changed",
                "mean_coordinate_shift_ge100",
                "mean_coordinate_shift_ge1000",
                "mean_mean_mapq_change",
                "mean_mapq_drop_ge5",
                "mean_mapq_drop_ge10",
                "mean_mean_nm_change",
                "mean_nm_increased_reads",
                "mean_mean_soft_clip_change",
                "mean_soft_clip_increased_reads",
                "mean_mean_aligned_query_length_change",
                "mean_secondary_increased_reads",
                "mean_supplementary_increased_reads",
            ]

            for metric in selected:
                sd_metric = f"sd_{metric.removeprefix('mean_')}"
                handle.write(
                    f"{metric}: {row[metric]}"
                )

                if sd_metric in row:
                    handle.write(
                        f" ± {row[sd_metric]}"
                    )

                handle.write("\n")

            handle.write("\n")

        handle.write("Monotonicity checks\n")
        handle.write("-" * 60 + "\n")

        for row in monotonic_rows:
            handle.write(
                f"{row['metric']}: "
                f"GN01={row['GN01']}, "
                f"GN05={row['GN05']}, "
                f"GN10={row['GN10']}, "
                f"monotonic={row['monotonic']}\n"
            )

    print("D3B paired multi-seed analysis complete.")
    print(f"Run summary: {run_summary_path}")
    print(f"Level summary: {level_summary_path}")
    print(f"Monotonicity: {monotonicity_path}")
    print(f"Top events: {top_events_path}")
    print(f"Findings: {findings_path}")


if __name__ == "__main__":
    main()
PY

chmod +x "$PYTHON_SCRIPT"

echo "Analysis script:"
ls -lh "$PYTHON_SCRIPT"
echo

echo "[3/5] Running paired analysis across nine conditions"
echo "------------------------------------------------------------"

python "$PYTHON_SCRIPT"

echo
echo "[4/5] Displaying results"
echo "------------------------------------------------------------"

echo "Nine-run paired summary:"
column -t -s $'\t' "$RUN_SUMMARY" 2>/dev/null || cat "$RUN_SUMMARY"

echo
echo "Level aggregates:"
column -t -s $'\t' "$LEVEL_SUMMARY" 2>/dev/null || cat "$LEVEL_SUMMARY"

echo
echo "Monotonicity:"
column -t -s $'\t' "$MONOTONICITY_TSV" 2>/dev/null || cat "$MONOTONICITY_TSV"

echo
echo "Top 20 alignment-change events:"
head -21 "$TOP_EVENTS_TSV" |
column -t -s $'\t' 2>/dev/null ||
head -21 "$TOP_EVENTS_TSV"

echo
echo "Readable findings:"
cat "$FINDINGS_TXT"
echo

echo "[5/5] Final validation"
echo "------------------------------------------------------------"

[[ -s "$RUN_SUMMARY" ]]
[[ -s "$LEVEL_SUMMARY" ]]
[[ -s "$MONOTONICITY_TSV" ]]
[[ -s "$TOP_EVENTS_TSV" ]]
[[ -s "$FINDINGS_TXT" ]]

EXPECTED_FILES=9
FOUND_FILES=0

for CONDITION in GN01 GN05 GN10; do
    for SEED in 1 2 3; do
        PAIRED_FILE="$ANALYSIS_DIR/${CONDITION}_seed${SEED}_vs_CLEAN_per_read.tsv"

        if [[ ! -s "$PAIRED_FILE" ]]; then
            echo "ERROR: Missing paired file:"
            echo "$PAIRED_FILE"
            exit 1
        fi

        DATA_ROWS="$(( $(wc -l < "$PAIRED_FILE") - 1 ))"

        echo "${CONDITION} seed ${SEED} paired rows: $DATA_ROWS"

        if [[ "$DATA_ROWS" -ne 1000 ]]; then
            echo "ERROR: Expected 1,000 paired rows."
            exit 1
        fi

        FOUND_FILES=$((FOUND_FILES + 1))
    done
done

RUN_ROWS="$(( $(wc -l < "$RUN_SUMMARY") - 1 ))"
LEVEL_ROWS="$(( $(wc -l < "$LEVEL_SUMMARY") - 1 ))"

echo
echo "Validated paired files: $FOUND_FILES / $EXPECTED_FILES"
echo "Run-summary rows:       $RUN_ROWS"
echo "Level-summary rows:     $LEVEL_ROWS"

if [[ "$FOUND_FILES" -ne 9 ]]; then
    echo "ERROR: Expected nine paired-analysis files."
    exit 1
fi

if [[ "$RUN_ROWS" -ne 9 ]]; then
    echo "ERROR: Expected nine run-summary rows."
    exit 1
fi

if [[ "$LEVEL_ROWS" -ne 3 ]]; then
    echo "ERROR: Expected three level-summary rows."
    exit 1
fi

touch "$COMPLETE_FILE"
rm -f "$FAILED_FILE"

echo
echo "Experiment D3B validation: PASS"

echo
echo "Completion marker:"
ls -l "$COMPLETE_FILE"

echo
echo "============================================================"
echo "Experiment D3B paired multi-seed analysis completed"
echo "Completed: $(date --iso-8601=seconds)"
echo "============================================================"
