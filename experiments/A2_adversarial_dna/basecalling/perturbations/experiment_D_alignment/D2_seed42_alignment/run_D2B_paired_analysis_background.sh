#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$HOME/Project-GenoPhylax"

EXP_D_DIR="$PROJECT_ROOT/experiments/A2_adversarial_dna/basecalling/perturbations/experiment_D_alignment"
D1_DIR="$EXP_D_DIR/D1_clean_validation"
D2_DIR="$EXP_D_DIR/D2_seed42_alignment"

ANALYSIS_DIR="$D2_DIR/paired_analysis"
METRICS_DIR="$D2_DIR/metrics"
SCRIPT_DIR="$D2_DIR/scripts"

PYTHON_SCRIPT="$SCRIPT_DIR/analyze_D2B_paired_alignments.py"

CLEAN_BAM="$D1_DIR/alignments/hg002_1000reads_clean_GRCh38.sorted.bam"
GN01_BAM="$D2_DIR/alignments/hg002_1000reads_gn01_seed42_GRCh38.sorted.bam"
GN05_BAM="$D2_DIR/alignments/hg002_1000reads_gn05_seed42_GRCh38.sorted.bam"
GN10_BAM="$D2_DIR/alignments/hg002_1000reads_gn10_seed42_GRCh38.sorted.bam"

SUMMARY_TSV="$METRICS_DIR/experiment_D2B_paired_alignment_summary.tsv"
MONOTONICITY_TSV="$METRICS_DIR/experiment_D2B_monotonicity.tsv"
TOP_EVENTS_TSV="$METRICS_DIR/experiment_D2B_top_alignment_changes.tsv"
FINDINGS_TXT="$METRICS_DIR/experiment_D2B_paired_findings.txt"

COMPLETE_FILE="$D2_DIR/D2B_PAIRED_ANALYSIS_COMPLETE"
FAILED_FILE="$D2_DIR/D2B_PAIRED_ANALYSIS_FAILED"

mkdir -p \
    "$ANALYSIS_DIR" \
    "$METRICS_DIR" \
    "$SCRIPT_DIR"

rm -f "$COMPLETE_FILE" "$FAILED_FILE"

trap '
    STATUS=$?
    echo
    echo "============================================================"
    echo "D2B paired analysis failed with exit status: $STATUS"
    echo "Time: $(date --iso-8601=seconds)"
    echo "============================================================"
    touch "$FAILED_FILE"
    exit "$STATUS"
' ERR

echo "============================================================"
echo "Experiment D2B — Paired alignment consequence analysis"
echo "Started: $(date --iso-8601=seconds)"
echo "============================================================"
echo

echo "[1/5] Validating inputs"
echo "------------------------------------------------------------"

python - <<'PY'
import pysam
print("pysam version:", pysam.__version__)
PY

for BAM in "$CLEAN_BAM" "$GN01_BAM" "$GN05_BAM" "$GN10_BAM"; do
    if [[ ! -s "$BAM" ]]; then
        echo "ERROR: Missing BAM:"
        echo "$BAM"
        exit 1
    fi

    if ! samtools quickcheck "$BAM"; then
        echo "ERROR: BAM failed quickcheck:"
        echo "$BAM"
        exit 1
    fi

    PRIMARY_COUNT="$(samtools view -c -F 2304 "$BAM")"

    if [[ "$PRIMARY_COUNT" -ne 1000 ]]; then
        echo "ERROR: Expected 1,000 primary records in:"
        echo "$BAM"
        echo "Observed: $PRIMARY_COUNT"
        exit 1
    fi

    ls -lh "$BAM"
done

echo
echo "All BAM inputs: PASS"
echo

echo "[2/5] Writing paired-analysis script"
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


def count_cigar_bases(
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


def read_alignment_data(
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
                ) = count_cigar_bases(record.cigartuples)

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


def safe_mean(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.mean(values) if values else math.nan


def safe_median(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.median(values) if values else math.nan


def format_number(value: float, digits: int = 6) -> str:
    if math.isnan(value):
        return "NA"
    return f"{value:.{digits}f}"


def main() -> None:
    project_root = Path.home() / "Project-GenoPhylax"

    exp_d_dir = (
        project_root
        / "experiments/A2_adversarial_dna/basecalling/perturbations"
        / "experiment_D_alignment"
    )
    d1_dir = exp_d_dir / "D1_clean_validation"
    d2_dir = exp_d_dir / "D2_seed42_alignment"

    analysis_dir = d2_dir / "paired_analysis"
    metrics_dir = d2_dir / "metrics"

    analysis_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    bam_paths = {
        "CLEAN": (
            d1_dir
            / "alignments/hg002_1000reads_clean_GRCh38.sorted.bam"
        ),
        "GN01": (
            d2_dir
            / "alignments/hg002_1000reads_gn01_seed42_GRCh38.sorted.bam"
        ),
        "GN05": (
            d2_dir
            / "alignments/hg002_1000reads_gn05_seed42_GRCh38.sorted.bam"
        ),
        "GN10": (
            d2_dir
            / "alignments/hg002_1000reads_gn10_seed42_GRCh38.sorted.bam"
        ),
    }

    all_primary = {}
    all_secondary = {}
    all_supplementary = {}

    for condition, bam_path in bam_paths.items():
        (
            all_primary[condition],
            all_secondary[condition],
            all_supplementary[condition],
        ) = read_alignment_data(bam_path)

        if len(all_primary[condition]) != 1000:
            raise RuntimeError(
                f"{condition}: expected 1000 primary records, "
                f"found {len(all_primary[condition])}"
            )

    clean_ids = set(all_primary["CLEAN"])

    for condition in ("GN01", "GN05", "GN10"):
        condition_ids = set(all_primary[condition])

        if condition_ids != clean_ids:
            missing = clean_ids - condition_ids
            extra = condition_ids - clean_ids
            raise RuntimeError(
                f"{condition}: parent ID mismatch; "
                f"missing={len(missing)}, extra={len(extra)}"
            )

    summary_rows = []
    top_events = []

    severity_scores = {
        "GN01": 1,
        "GN05": 2,
        "GN10": 3,
    }

    for condition in ("GN01", "GN05", "GN10"):
        paired_path = analysis_dir / f"{condition}_vs_CLEAN_per_read.tsv"

        counts = Counter()
        numeric = defaultdict(list)

        with paired_path.open("w", newline="") as handle:
            fieldnames = [
                "read_id",
                "clean_mapped",
                "perturbed_mapped",
                "mapping_transition",
                "clean_chrom",
                "perturbed_chrom",
                "chromosome_changed",
                "clean_start",
                "perturbed_start",
                "coordinate_shift_bp",
                "large_coordinate_shift_ge100",
                "large_coordinate_shift_ge1000",
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
                "clean_cigar",
                "perturbed_cigar",
                "cigar_changed",
                "clean_soft_clip",
                "perturbed_soft_clip",
                "soft_clip_change",
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

            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                delimiter="\t",
            )
            writer.writeheader()

            for read_id in sorted(clean_ids):
                clean = all_primary["CLEAN"][read_id]
                perturbed = all_primary[condition][read_id]

                if clean.mapped and perturbed.mapped:
                    mapping_transition = "mapped_to_mapped"
                elif clean.mapped and not perturbed.mapped:
                    mapping_transition = "mapped_to_unmapped"
                elif not clean.mapped and perturbed.mapped:
                    mapping_transition = "unmapped_to_mapped"
                else:
                    mapping_transition = "unmapped_to_unmapped"

                counts[mapping_transition] += 1

                both_mapped = clean.mapped and perturbed.mapped

                chromosome_changed = (
                    both_mapped and clean.chrom != perturbed.chrom
                )

                same_chromosome = (
                    both_mapped and clean.chrom == perturbed.chrom
                )

                coordinate_shift = (
                    abs(perturbed.start - clean.start)
                    if same_chromosome
                    else None
                )

                strand_changed = (
                    both_mapped and clean.strand != perturbed.strand
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
                        and clean.nm is not None
                        and perturbed.nm is not None
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
                    perturbed.insertion_bases - clean.insertion_bases
                    if both_mapped
                    else None
                )

                deletion_change = (
                    perturbed.deletion_bases - clean.deletion_bases
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
                    perturbed.reference_span - clean.reference_span
                    if both_mapped
                    else None
                )

                clean_secondary = all_secondary["CLEAN"][read_id]
                perturbed_secondary = all_secondary[condition][read_id]
                secondary_change = perturbed_secondary - clean_secondary

                clean_supplementary = all_supplementary["CLEAN"][read_id]
                perturbed_supplementary = (
                    all_supplementary[condition][read_id]
                )
                supplementary_change = (
                    perturbed_supplementary - clean_supplementary
                )

                if chromosome_changed:
                    counts["chromosome_changed"] += 1

                if strand_changed:
                    counts["strand_changed"] += 1

                if cigar_changed:
                    counts["cigar_changed"] += 1

                if coordinate_shift is not None:
                    numeric["coordinate_shift"].append(coordinate_shift)

                    if coordinate_shift >= 100:
                        counts["coordinate_shift_ge100"] += 1

                    if coordinate_shift >= 1000:
                        counts["coordinate_shift_ge1000"] += 1

                if mapq_change is not None:
                    numeric["mapq_change"].append(mapq_change)

                    if mapq_change <= -5:
                        counts["mapq_drop_ge5"] += 1

                    if mapq_change <= -10:
                        counts["mapq_drop_ge10"] += 1

                if nm_change is not None:
                    numeric["nm_change"].append(nm_change)

                    if nm_change > 0:
                        counts["nm_increased"] += 1

                if soft_clip_change is not None:
                    numeric["soft_clip_change"].append(soft_clip_change)

                    if soft_clip_change > 0:
                        counts["soft_clip_increased"] += 1

                if hard_clip_change is not None:
                    numeric["hard_clip_change"].append(hard_clip_change)

                    if hard_clip_change > 0:
                        counts["hard_clip_increased"] += 1

                if insertion_change is not None:
                    numeric["insertion_change"].append(insertion_change)

                if deletion_change is not None:
                    numeric["deletion_change"].append(deletion_change)

                if aligned_query_length_change is not None:
                    numeric["aligned_query_length_change"].append(
                        aligned_query_length_change
                    )

                if reference_span_change is not None:
                    numeric["reference_span_change"].append(
                        reference_span_change
                    )

                numeric["secondary_change"].append(secondary_change)
                numeric["supplementary_change"].append(
                    supplementary_change
                )

                if secondary_change > 0:
                    counts["secondary_increased"] += 1

                if supplementary_change > 0:
                    counts["supplementary_increased"] += 1

                event_score = 0

                if mapping_transition == "mapped_to_unmapped":
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

                if soft_clip_change is not None and soft_clip_change > 0:
                    event_score += soft_clip_change

                if event_score > 0:
                    top_events.append(
                        {
                            "condition": condition,
                            "condition_severity": severity_scores[condition],
                            "read_id": read_id,
                            "event_score": event_score,
                            "mapping_transition": mapping_transition,
                            "clean_chrom": clean.chrom or "*",
                            "perturbed_chrom": perturbed.chrom or "*",
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
                                clean.nm if clean.nm is not None else "NA"
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
                            "secondary_count_change": secondary_change,
                            "supplementary_count_change": (
                                supplementary_change
                            ),
                        }
                    )

                writer.writerow(
                    {
                        "read_id": read_id,
                        "clean_mapped": int(clean.mapped),
                        "perturbed_mapped": int(perturbed.mapped),
                        "mapping_transition": mapping_transition,
                        "clean_chrom": clean.chrom or "*",
                        "perturbed_chrom": perturbed.chrom or "*",
                        "chromosome_changed": int(chromosome_changed),
                        "clean_start": (
                            clean.start if clean.start is not None else "NA"
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
                        "large_coordinate_shift_ge100": int(
                            coordinate_shift is not None
                            and coordinate_shift >= 100
                        ),
                        "large_coordinate_shift_ge1000": int(
                            coordinate_shift is not None
                            and coordinate_shift >= 1000
                        ),
                        "clean_strand": clean.strand or "*",
                        "perturbed_strand": perturbed.strand or "*",
                        "strand_changed": int(strand_changed),
                        "clean_mapq": clean.mapq,
                        "perturbed_mapq": perturbed.mapq,
                        "mapq_change": (
                            mapq_change
                            if mapq_change is not None
                            else "NA"
                        ),
                        "mapq_drop_ge5": int(
                            mapq_change is not None and mapq_change <= -5
                        ),
                        "mapq_drop_ge10": int(
                            mapq_change is not None and mapq_change <= -10
                        ),
                        "clean_nm": (
                            clean.nm if clean.nm is not None else "NA"
                        ),
                        "perturbed_nm": (
                            perturbed.nm
                            if perturbed.nm is not None
                            else "NA"
                        ),
                        "nm_change": (
                            nm_change if nm_change is not None else "NA"
                        ),
                        "clean_cigar": clean.cigar,
                        "perturbed_cigar": perturbed.cigar,
                        "cigar_changed": int(cigar_changed),
                        "clean_soft_clip": clean.soft_clip,
                        "perturbed_soft_clip": perturbed.soft_clip,
                        "soft_clip_change": (
                            soft_clip_change
                            if soft_clip_change is not None
                            else "NA"
                        ),
                        "clean_hard_clip": clean.hard_clip,
                        "perturbed_hard_clip": perturbed.hard_clip,
                        "hard_clip_change": (
                            hard_clip_change
                            if hard_clip_change is not None
                            else "NA"
                        ),
                        "clean_insertion_bases": clean.insertion_bases,
                        "perturbed_insertion_bases": (
                            perturbed.insertion_bases
                        ),
                        "insertion_change": (
                            insertion_change
                            if insertion_change is not None
                            else "NA"
                        ),
                        "clean_deletion_bases": clean.deletion_bases,
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
                            if aligned_query_length_change is not None
                            else "NA"
                        ),
                        "clean_reference_span": clean.reference_span,
                        "perturbed_reference_span": (
                            perturbed.reference_span
                        ),
                        "reference_span_change": (
                            reference_span_change
                            if reference_span_change is not None
                            else "NA"
                        ),
                        "clean_secondary_count": clean_secondary,
                        "perturbed_secondary_count": perturbed_secondary,
                        "secondary_count_change": secondary_change,
                        "clean_supplementary_count": clean_supplementary,
                        "perturbed_supplementary_count": (
                            perturbed_supplementary
                        ),
                        "supplementary_count_change": (
                            supplementary_change
                        ),
                    }
                )

        summary_rows.append(
            {
                "condition": condition,
                "paired_reads": 1000,
                "mapped_to_mapped": counts["mapped_to_mapped"],
                "mapped_to_unmapped": counts["mapped_to_unmapped"],
                "unmapped_to_mapped": counts["unmapped_to_mapped"],
                "unmapped_to_unmapped": counts["unmapped_to_unmapped"],
                "chromosome_changed": counts["chromosome_changed"],
                "strand_changed": counts["strand_changed"],
                "cigar_changed": counts["cigar_changed"],
                "coordinate_shift_ge100": counts[
                    "coordinate_shift_ge100"
                ],
                "coordinate_shift_ge1000": counts[
                    "coordinate_shift_ge1000"
                ],
                "mean_coordinate_shift_bp": format_number(
                    safe_mean(numeric["coordinate_shift"])
                ),
                "median_coordinate_shift_bp": format_number(
                    safe_median(numeric["coordinate_shift"])
                ),
                "mean_mapq_change": format_number(
                    safe_mean(numeric["mapq_change"])
                ),
                "mapq_drop_ge5": counts["mapq_drop_ge5"],
                "mapq_drop_ge10": counts["mapq_drop_ge10"],
                "mean_nm_change": format_number(
                    safe_mean(numeric["nm_change"])
                ),
                "nm_increased_reads": counts["nm_increased"],
                "mean_soft_clip_change": format_number(
                    safe_mean(numeric["soft_clip_change"])
                ),
                "soft_clip_increased_reads": counts[
                    "soft_clip_increased"
                ],
                "mean_hard_clip_change": format_number(
                    safe_mean(numeric["hard_clip_change"])
                ),
                "hard_clip_increased_reads": counts[
                    "hard_clip_increased"
                ],
                "mean_insertion_change": format_number(
                    safe_mean(numeric["insertion_change"])
                ),
                "mean_deletion_change": format_number(
                    safe_mean(numeric["deletion_change"])
                ),
                "mean_aligned_query_length_change": format_number(
                    safe_mean(numeric["aligned_query_length_change"])
                ),
                "mean_reference_span_change": format_number(
                    safe_mean(numeric["reference_span_change"])
                ),
                "mean_secondary_count_change": format_number(
                    safe_mean(numeric["secondary_change"])
                ),
                "secondary_increased_reads": counts[
                    "secondary_increased"
                ],
                "mean_supplementary_count_change": format_number(
                    safe_mean(numeric["supplementary_change"])
                ),
                "supplementary_increased_reads": counts[
                    "supplementary_increased"
                ],
            }
        )

    summary_path = (
        metrics_dir / "experiment_D2B_paired_alignment_summary.tsv"
    )

    with summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(summary_rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    monotonic_metrics = {
        "mapped_to_unmapped": "increasing",
        "chromosome_changed": "increasing",
        "coordinate_shift_ge100": "increasing",
        "coordinate_shift_ge1000": "increasing",
        "mapq_drop_ge5": "increasing",
        "mapq_drop_ge10": "increasing",
        "nm_increased_reads": "increasing",
        "soft_clip_increased_reads": "increasing",
        "secondary_increased_reads": "increasing",
        "supplementary_increased_reads": "increasing",
    }

    monotonicity_rows = []

    for metric, direction in monotonic_metrics.items():
        values = [float(row[metric]) for row in summary_rows]

        if direction == "increasing":
            monotonic = values[0] <= values[1] <= values[2]
        else:
            monotonic = values[0] >= values[1] >= values[2]

        monotonicity_rows.append(
            {
                "metric": metric,
                "GN01": values[0],
                "GN05": values[1],
                "GN10": values[2],
                "expected_direction": direction,
                "monotonic": str(monotonic),
            }
        )

    monotonicity_path = metrics_dir / "experiment_D2B_monotonicity.tsv"

    with monotonicity_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(monotonicity_rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(monotonicity_rows)

    top_events.sort(
        key=lambda row: (
            -int(row["event_score"]),
            -int(row["condition_severity"]),
            row["read_id"],
        )
    )

    top_events_path = (
        metrics_dir / "experiment_D2B_top_alignment_changes.tsv"
    )

    top_event_fields = [
        "condition",
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
        "secondary_count_change",
        "supplementary_count_change",
    ]

    with top_events_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=top_event_fields,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(top_events[:100])

    findings_path = metrics_dir / "experiment_D2B_paired_findings.txt"

    with findings_path.open("w") as handle:
        handle.write(
            "Experiment D2B — Paired alignment consequence analysis\n\n"
        )

        for row in summary_rows:
            handle.write(f"{row['condition']} versus CLEAN\n")
            handle.write("-" * 60 + "\n")
            handle.write(
                f"Mapped to unmapped: "
                f"{row['mapped_to_unmapped']}\n"
            )
            handle.write(
                f"Unmapped to mapped: "
                f"{row['unmapped_to_mapped']}\n"
            )
            handle.write(
                f"Chromosome changes: "
                f"{row['chromosome_changed']}\n"
            )
            handle.write(
                f"Strand changes: {row['strand_changed']}\n"
            )
            handle.write(
                f"CIGAR changes: {row['cigar_changed']}\n"
            )
            handle.write(
                f"Coordinate shifts >=100 bp: "
                f"{row['coordinate_shift_ge100']}\n"
            )
            handle.write(
                f"Coordinate shifts >=1000 bp: "
                f"{row['coordinate_shift_ge1000']}\n"
            )
            handle.write(
                f"Mean MAPQ change: "
                f"{row['mean_mapq_change']}\n"
            )
            handle.write(
                f"MAPQ drops >=5: {row['mapq_drop_ge5']}\n"
            )
            handle.write(
                f"MAPQ drops >=10: {row['mapq_drop_ge10']}\n"
            )
            handle.write(
                f"Mean NM change: {row['mean_nm_change']}\n"
            )
            handle.write(
                f"Reads with increased NM: "
                f"{row['nm_increased_reads']}\n"
            )
            handle.write(
                f"Mean soft-clipping change: "
                f"{row['mean_soft_clip_change']}\n"
            )
            handle.write(
                f"Reads with increased soft clipping: "
                f"{row['soft_clip_increased_reads']}\n"
            )
            handle.write(
                f"Mean aligned-query-length change: "
                f"{row['mean_aligned_query_length_change']}\n"
            )
            handle.write(
                f"Mean reference-span change: "
                f"{row['mean_reference_span_change']}\n"
            )
            handle.write(
                f"Reads with increased secondary alignments: "
                f"{row['secondary_increased_reads']}\n"
            )
            handle.write(
                f"Reads with increased supplementary alignments: "
                f"{row['supplementary_increased_reads']}\n\n"
            )

        handle.write("Monotonicity checks\n")
        handle.write("-" * 60 + "\n")

        for row in monotonicity_rows:
            handle.write(
                f"{row['metric']}: "
                f"GN01={row['GN01']}, "
                f"GN05={row['GN05']}, "
                f"GN10={row['GN10']}, "
                f"monotonic={row['monotonic']}\n"
            )

    print("Paired analysis complete.")
    print(f"Summary: {summary_path}")
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

echo "[3/5] Running paired per-read analysis"
echo "------------------------------------------------------------"

python "$PYTHON_SCRIPT"

echo
echo "[4/5] Displaying paired summary"
echo "------------------------------------------------------------"

echo "Paired alignment summary:"
column -t -s $'\t' "$SUMMARY_TSV" 2>/dev/null || cat "$SUMMARY_TSV"

echo
echo "Monotonicity results:"
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

[[ -s "$SUMMARY_TSV" ]]
[[ -s "$MONOTONICITY_TSV" ]]
[[ -s "$TOP_EVENTS_TSV" ]]
[[ -s "$FINDINGS_TXT" ]]

for CONDITION in GN01 GN05 GN10; do
    PAIRED_FILE="$ANALYSIS_DIR/${CONDITION}_vs_CLEAN_per_read.tsv"

    if [[ ! -s "$PAIRED_FILE" ]]; then
        echo "ERROR: Missing paired file:"
        echo "$PAIRED_FILE"
        exit 1
    fi

    DATA_ROWS="$(( $(wc -l < "$PAIRED_FILE") - 1 ))"

    echo "$CONDITION paired rows: $DATA_ROWS"

    if [[ "$DATA_ROWS" -ne 1000 ]]; then
        echo "ERROR: Expected 1,000 paired rows for $CONDITION."
        exit 1
    fi
done

touch "$COMPLETE_FILE"
rm -f "$FAILED_FILE"

echo
echo "Experiment D2B validation: PASS"

echo
echo "Completion marker:"
ls -l "$COMPLETE_FILE"

echo
echo "============================================================"
echo "Experiment D2B paired analysis completed successfully"
echo "Completed: $(date --iso-8601=seconds)"
echo "============================================================"
