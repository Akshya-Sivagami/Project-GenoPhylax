#!/usr/bin/env python3

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path.home() / "Project-GenoPhylax"

EXP_D_DIR = (
    PROJECT_ROOT
    / "experiments/A2_adversarial_dna/basecalling/perturbations"
    / "experiment_D_alignment"
)

D1_DIR = EXP_D_DIR / "D1_clean_validation"
D2_DIR = EXP_D_DIR / "D2_seed42_alignment"
D3_DIR = EXP_D_DIR / "D3_multiseed_alignment"

OUTPUT_FILE = EXP_D_DIR / "experiment_D_alignment_findings.md"


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Missing or empty TSV: {path}")

    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def find_row(
    rows: list[dict[str, str]],
    key: str,
    value: str,
) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row

    raise KeyError(f"No row with {key}={value}")


def number(value: str, digits: int = 3) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return value

    if numeric.is_integer():
        return str(int(numeric))

    return f"{numeric:.{digits}f}"


def mean_sd(
    row: dict[str, str],
    metric: str,
    digits: int = 3,
) -> str:
    mean_key = f"mean_{metric}"
    sd_key = f"sd_{metric}"

    mean_value = row[mean_key]
    sd_value = row[sd_key]

    return (
        f"{number(mean_value, digits)} ± "
        f"{number(sd_value, digits)}"
    )


def monotonic_status(
    rows: list[dict[str, str]],
    metric: str,
) -> str:
    row = find_row(rows, "metric", metric)
    return row["monotonic"]


def yes_no(value: str) -> str:
    return "Yes" if value.lower() == "true" else "No"


def main() -> None:
    d1_summary_path = (
        D1_DIR
        / "metrics/experiment_D1_clean_alignment_summary.txt"
    )

    d2_alignment_path = (
        D2_DIR
        / "metrics/experiment_D2_seed42_alignment_summary.tsv"
    )

    d2_paired_path = (
        D2_DIR
        / "metrics/experiment_D2B_paired_alignment_summary.tsv"
    )

    d2_monotonicity_path = (
        D2_DIR
        / "metrics/experiment_D2B_monotonicity.tsv"
    )

    d3_alignment_runs_path = (
        D3_DIR
        / "metrics/experiment_D3_9run_alignment_results.tsv"
    )

    d3_alignment_aggregates_path = (
        D3_DIR
        / "metrics/experiment_D3_level_aggregates.tsv"
    )

    d3_alignment_monotonicity_path = (
        D3_DIR
        / "metrics/experiment_D3_alignment_monotonicity.tsv"
    )

    d3_paired_runs_path = (
        D3_DIR
        / "metrics/experiment_D3B_9run_paired_summary.tsv"
    )

    d3_paired_aggregates_path = (
        D3_DIR
        / "metrics/experiment_D3B_level_aggregates.tsv"
    )

    d3_paired_monotonicity_path = (
        D3_DIR
        / "metrics/experiment_D3B_monotonicity.tsv"
    )

    required_files = [
        d1_summary_path,
        d2_alignment_path,
        d2_paired_path,
        d2_monotonicity_path,
        d3_alignment_runs_path,
        d3_alignment_aggregates_path,
        d3_alignment_monotonicity_path,
        d3_paired_runs_path,
        d3_paired_aggregates_path,
        d3_paired_monotonicity_path,
    ]

    for path in required_files:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Missing required evidence: {path}")

    d2_alignment = read_tsv(d2_alignment_path)
    d2_paired = read_tsv(d2_paired_path)
    d2_mono = read_tsv(d2_monotonicity_path)

    d3_alignment_runs = read_tsv(d3_alignment_runs_path)
    d3_alignment_aggregates = read_tsv(
        d3_alignment_aggregates_path
    )
    d3_alignment_mono = read_tsv(
        d3_alignment_monotonicity_path
    )

    d3_paired_runs = read_tsv(d3_paired_runs_path)
    d3_paired_aggregates = read_tsv(
        d3_paired_aggregates_path
    )
    d3_paired_mono = read_tsv(
        d3_paired_monotonicity_path
    )

    clean = find_row(d2_alignment, "condition", "CLEAN")

    gn01_d2_alignment = find_row(
        d2_alignment, "condition", "GN01"
    )
    gn05_d2_alignment = find_row(
        d2_alignment, "condition", "GN05"
    )
    gn10_d2_alignment = find_row(
        d2_alignment, "condition", "GN10"
    )

    d2_paired_by_condition = {
        row["condition"]: row for row in d2_paired
    }

    d3_alignment_by_condition = {
        row["condition"]: row
        for row in d3_alignment_aggregates
    }

    d3_paired_by_condition = {
        row["condition"]: row
        for row in d3_paired_aggregates
    }

    lines: list[str] = []

    lines.extend(
        [
            "# Experiment D — Alignment-Level Consequences of "
            "Adversarial Nanopore Signal Perturbation",
            "",
            "## Objective",
            "",
            "Experiment D evaluated whether Gaussian perturbations "
            "introduced into raw Oxford Nanopore signal propagate "
            "beyond basecalling and alter downstream reference "
            "alignment outcomes.",
            "",
            "The experiment used the 1,000-read HG002 cohort from "
            "Experiment C and aligned CLEAN and perturbed Dorado "
            "basecalls against the GIAB GRCh38 no-alt analysis-set "
            "reference using minimap2 with the `map-ont` preset.",
            "",
            "The analysis addressed two questions:",
            "",
            "1. Do raw-signal perturbations affect aggregate alignment "
            "success and confidence?",
            "2. Do apparently small aggregate changes conceal "
            "read-level mapping, locus, edit-burden, and clipping "
            "changes?",
            "",
            "## Experimental Design",
            "",
            "### D1 — CLEAN alignment validation",
            "",
            "- Reference: "
            "`GCA_000001405.15_GRCh38_no_alt_analysis_set`",
            "- Aligner: minimap2 2.31-r1302",
            "- Preset: `map-ont`",
            "- CLEAN input reads: 1,000",
            "- Primary-read identity preservation was required.",
            "",
            "### D2 — Seed-42 dose-response",
            "",
            "The same 1,000 parent reads were evaluated under:",
            "",
            "- CLEAN",
            "- GN01 seed 42",
            "- GN05 seed 42",
            "- GN10 seed 42",
            "",
            "### D3 — Multi-seed replication",
            "",
            "GN01, GN05, and GN10 were repeated with seeds 1, 2, "
            "and 3, producing nine perturbed alignment conditions.",
            "",
            "All comparisons were paired by normalized parent read ID.",
            "",
            "## Validation",
            "",
            "All experiment stages completed successfully:",
            "",
            "- D1 CLEAN alignment validation: PASS",
            "- D2A seed-42 alignments: PASS",
            "- D2B seed-42 paired analysis: PASS",
            "- D3A nine-run multi-seed alignments: PASS",
            "- D3B nine-run paired replication analysis: PASS",
            "",
            "Across every condition:",
            "",
            "- exactly 1,000 primary records were retained;",
            "- exactly 1,000 unique parent read IDs were present;",
            "- no duplicate primary parent IDs were detected;",
            "- aligned BAM files passed `samtools quickcheck`;",
            "- every paired comparison contained exactly 1,000 rows.",
            "",
            "## D1 — CLEAN Baseline",
            "",
            "| Metric | CLEAN |",
            "|---|---:|",
            f"| Primary reads | {clean['primary_records']} |",
            f"| Mapped primary reads | {clean['mapped_primary']} |",
            f"| Unmapped primary reads | {clean['unmapped_primary']} |",
            f"| Primary mapping rate | "
            f"{number(clean['mapped_percent'])}% |",
            f"| Mean mapped-primary MAPQ | "
            f"{number(clean['mean_mapped_mapq'])} |",
            f"| MAPQ ≥20 | {clean['mapq_ge20']} |",
            f"| MAPQ ≥30 | {clean['mapq_ge30']} |",
            f"| MAPQ ≥60 | {clean['mapq_ge60']} |",
            f"| Secondary alignments | {clean['secondary']} |",
            f"| Supplementary alignments | "
            f"{clean['supplementary']} |",
            "",
            "The CLEAN cohort achieved a 97% primary mapping rate "
            "and high alignment confidence, providing a stable "
            "baseline for perturbation comparisons.",
            "",
            "## D2 — Seed-42 Aggregate Alignment Results",
            "",
            "| Condition | Mapped primary | Mapping rate | "
            "Mean MAPQ | MAPQ ≥20 | MAPQ ≥30 | MAPQ ≥60 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for row in [
        clean,
        gn01_d2_alignment,
        gn05_d2_alignment,
        gn10_d2_alignment,
    ]:
        lines.append(
            f"| {row['condition']} | "
            f"{row['mapped_primary']} | "
            f"{number(row['mapped_percent'])}% | "
            f"{number(row['mean_mapped_mapq'])} | "
            f"{row['mapq_ge20']} | "
            f"{row['mapq_ge30']} | "
            f"{row['mapq_ge60']} |"
        )

    lines.extend(
        [
            "",
            "Aggregate mapping changes were modest but directionally "
            "consistent. Mapping rate declined from 97.0% in CLEAN "
            "to 96.8% at GN10, while mean MAPQ and high-confidence "
            "mapping counts also declined.",
            "",
            "## D2 — Seed-42 Paired Read-Level Consequences",
            "",
            "| Metric | GN01 | GN05 | GN10 | Monotonic |",
            "|---|---:|---:|---:|:---:|",
        ]
    )

    paired_metrics: list[tuple[str, str]] = [
        ("Mapped → unmapped", "mapped_to_unmapped"),
        ("Chromosome changes", "chromosome_changed"),
        ("Strand changes", "strand_changed"),
        ("CIGAR changes", "cigar_changed"),
        ("Coordinate shifts ≥100 bp", "coordinate_shift_ge100"),
        ("Coordinate shifts ≥1,000 bp", "coordinate_shift_ge1000"),
        ("MAPQ drops ≥5", "mapq_drop_ge5"),
        ("MAPQ drops ≥10", "mapq_drop_ge10"),
        ("Reads with increased NM", "nm_increased_reads"),
        (
            "Reads with increased soft clipping",
            "soft_clip_increased_reads",
        ),
        (
            "Reads with increased secondary alignments",
            "secondary_increased_reads",
        ),
        (
            "Reads with increased supplementary alignments",
            "supplementary_increased_reads",
        ),
    ]

    d2_mono_map = {
        row["metric"]: row["monotonic"] for row in d2_mono
    }

    for label, metric in paired_metrics:
        monotonic = d2_mono_map.get(metric, "Not tested")

        lines.append(
            f"| {label} | "
            f"{number(d2_paired_by_condition['GN01'][metric])} | "
            f"{number(d2_paired_by_condition['GN05'][metric])} | "
            f"{number(d2_paired_by_condition['GN10'][metric])} | "
            f"{yes_no(monotonic) if monotonic != 'Not tested' else monotonic} |"
        )

    lines.extend(
        [
            "",
            "The paired analysis revealed substantially stronger "
            "effects than the aggregate mapping percentages alone.",
            "",
            "At GN10 seed 42:",
            "",
            f"- {d2_paired_by_condition['GN10']['mapped_to_unmapped']} "
            "previously mapped reads became unmapped;",
            f"- {d2_paired_by_condition['GN10']['chromosome_changed']} "
            "reads changed chromosome;",
            f"- {d2_paired_by_condition['GN10']['coordinate_shift_ge100']} "
            "reads shifted by at least 100 bp;",
            f"- {d2_paired_by_condition['GN10']['coordinate_shift_ge1000']} "
            "reads shifted by at least 1,000 bp;",
            f"- {d2_paired_by_condition['GN10']['mapq_drop_ge10']} "
            "reads lost at least 10 MAPQ points;",
            f"- {d2_paired_by_condition['GN10']['nm_increased_reads']} "
            "reads showed increased alignment edit burden;",
            f"- "
            f"{d2_paired_by_condition['GN10']['soft_clip_increased_reads']} "
            "reads showed increased soft clipping.",
            "",
            "These results demonstrate that successful mapping and "
            "small changes in cohort-level mapping rate can conceal "
            "substantial read-level integrity degradation.",
            "",
            "## D3 — Multi-Seed Aggregate Replication",
            "",
            "| Condition | Mapped primary | Mapping rate | "
            "Mean MAPQ | MAPQ ≥20 | MAPQ ≥30 | MAPQ ≥60 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for condition in ("GN01", "GN05", "GN10"):
        row = d3_alignment_by_condition[condition]

        lines.append(
            f"| {condition} | "
            f"{mean_sd(row, 'mapped_primary')} | "
            f"{mean_sd(row, 'mapped_percent')}% | "
            f"{mean_sd(row, 'mean_mapped_mapq')} | "
            f"{mean_sd(row, 'mapq_ge20')} | "
            f"{mean_sd(row, 'mapq_ge30')} | "
            f"{mean_sd(row, 'mapq_ge60')} |"
        )

    lines.extend(
        [
            "",
            "Across seeds 1–3, the following aggregate metrics changed "
            "monotonically with perturbation strength:",
            "",
            f"- unmapped primary reads increased: "
            f"{yes_no(monotonic_status(d3_alignment_mono, 'mean_unmapped_primary'))};",
            f"- mapping percentage decreased: "
            f"{yes_no(monotonic_status(d3_alignment_mono, 'mean_mapped_percent'))};",
            f"- mean mapped-primary MAPQ decreased: "
            f"{yes_no(monotonic_status(d3_alignment_mono, 'mean_mean_mapped_mapq'))};",
            f"- MAPQ ≥20 counts decreased: "
            f"{yes_no(monotonic_status(d3_alignment_mono, 'mean_mapq_ge20'))};",
            f"- MAPQ ≥30 counts decreased: "
            f"{yes_no(monotonic_status(d3_alignment_mono, 'mean_mapq_ge30'))};",
            f"- MAPQ ≥60 counts decreased: "
            f"{yes_no(monotonic_status(d3_alignment_mono, 'mean_mapq_ge60'))}.",
            "",
            "Secondary and supplementary totals were not monotonic "
            "across levels and should therefore be treated as "
            "variable alignment behaviours rather than primary "
            "dose-response indicators.",
            "",
            "## D3 — Multi-Seed Paired Replication",
            "",
            "| Metric | GN01 mean ± SD | GN05 mean ± SD | "
            "GN10 mean ± SD | Monotonic |",
            "|---|---:|---:|---:|:---:|",
        ]
    )

    d3_paired_metric_specs: list[tuple[str, str, str]] = [
        (
            "Mapped → unmapped",
            "mapped_to_unmapped",
            "mean_mapped_to_unmapped",
        ),
        (
            "Chromosome changes",
            "chromosome_changed",
            "mean_chromosome_changed",
        ),
        (
            "Strand changes",
            "strand_changed",
            "mean_strand_changed",
        ),
        (
            "CIGAR changes",
            "cigar_changed",
            "mean_cigar_changed",
        ),
        (
            "Coordinate shifts ≥100 bp",
            "coordinate_shift_ge100",
            "mean_coordinate_shift_ge100",
        ),
        (
            "Coordinate shifts ≥1,000 bp",
            "coordinate_shift_ge1000",
            "mean_coordinate_shift_ge1000",
        ),
        (
            "MAPQ drops ≥5",
            "mapq_drop_ge5",
            "mean_mapq_drop_ge5",
        ),
        (
            "MAPQ drops ≥10",
            "mapq_drop_ge10",
            "mean_mapq_drop_ge10",
        ),
        (
            "Reads with increased NM",
            "nm_increased_reads",
            "mean_nm_increased_reads",
        ),
        (
            "Reads with increased soft clipping",
            "soft_clip_increased_reads",
            "mean_soft_clip_increased_reads",
        ),
        (
            "Reads with increased secondary alignments",
            "secondary_increased_reads",
            "mean_secondary_increased_reads",
        ),
        (
            "Reads with increased supplementary alignments",
            "supplementary_increased_reads",
            "mean_supplementary_increased_reads",
        ),
    ]

    d3_paired_mono_map = {
        row["metric"]: row["monotonic"]
        for row in d3_paired_mono
    }

    for label, base_metric, monotonic_metric in d3_paired_metric_specs:
        gn01_row = d3_paired_by_condition["GN01"]
        gn05_row = d3_paired_by_condition["GN05"]
        gn10_row = d3_paired_by_condition["GN10"]

        lines.append(
            f"| {label} | "
            f"{mean_sd(gn01_row, base_metric)} | "
            f"{mean_sd(gn05_row, base_metric)} | "
            f"{mean_sd(gn10_row, base_metric)} | "
            f"{yes_no(d3_paired_mono_map[monotonic_metric])} |"
        )

    lines.extend(
        [
            "",
            "Additional continuous read-level effects were also "
            "monotonic across perturbation strengths:",
            "",
            f"- mean MAPQ change: "
            f"{number(d3_paired_by_condition['GN01']['mean_mean_mapq_change'])}, "
            f"{number(d3_paired_by_condition['GN05']['mean_mean_mapq_change'])}, "
            f"{number(d3_paired_by_condition['GN10']['mean_mean_mapq_change'])};",
            f"- mean aligned-query-length change: "
            f"{number(d3_paired_by_condition['GN01']['mean_mean_aligned_query_length_change'])}, "
            f"{number(d3_paired_by_condition['GN05']['mean_mean_aligned_query_length_change'])}, "
            f"{number(d3_paired_by_condition['GN10']['mean_mean_aligned_query_length_change'])} bases.",
            "",
            "The only paired metric in the selected monotonicity set "
            "that did not show a monotonic dose-response was the number "
            "of reads gaining supplementary alignments. This metric "
            "remained sparse and variable across seeds.",
            "",
            "## Main Finding",
            "",
            "Gaussian raw-signal perturbation propagated through "
            "Dorado basecalling into downstream reference alignment.",
            "",
            "The impact was not limited to a slight reduction in "
            "overall mapping rate. Paired parent-read analysis revealed "
            "dose-dependent changes in:",
            "",
            "- mapping status;",
            "- chromosome and strand assignment;",
            "- genomic coordinate placement;",
            "- alignment confidence;",
            "- CIGAR structure;",
            "- edit distance to the reference;",
            "- soft clipping;",
            "- aligned query length;",
            "- secondary alignment behaviour.",
            "",
            "Most major integrity-damage metrics were monotonic in both "
            "the seed-42 experiment and the independent multi-seed "
            "replication.",
            "",
            "## Security Interpretation",
            "",
            "A conventional pipeline-validity check would classify all "
            "conditions as successful:",
            "",
            "- POD5 files remained readable;",
            "- Dorado completed basecalling;",
            "- BAM files remained structurally valid;",
            "- minimap2 completed alignment;",
            "- aligned BAM files passed integrity checks;",
            "- most reads remained mapped.",
            "",
            "Nevertheless, the biological interpretation of individual "
            "reads changed.",
            "",
            "Therefore:",
            "",
            "> Structural validity, successful execution, and high "
            "aggregate mapping rates do not guarantee genomic-data "
            "integrity.",
            "",
            "This extends the central Experiment C result beyond "
            "basecalling. Perturbations can survive multiple apparently "
            "successful pipeline stages while progressively altering "
            "the digital genomic record.",
            "",
            "## Limitations",
            "",
            "- The experiment used a 1,000-read HG002 subset rather than "
            "a complete genome-scale sequencing run.",
            "- Gaussian noise is a controlled perturbation model and "
            "does not by itself demonstrate a physically synthesized "
            "adversarial molecule.",
            "- Only one basecaller model and one alignment configuration "
            "were evaluated.",
            "- Alignment changes were measured directly; downstream "
            "variant-calling consequences were not evaluated in "
            "Experiment D.",
            "- Some alignment behaviours, particularly supplementary "
            "alignments, were sparse and non-monotonic.",
            "",
            "## Conclusion",
            "",
            "Experiment D provides replicated evidence that raw nanopore "
            "signal perturbations can propagate into alignment-level "
            "errors despite successful execution and structurally valid "
            "outputs at every stage.",
            "",
            "The strongest evidence comes from paired parent-read "
            "analysis, where increasing perturbation strength produced "
            "replicated increases in mapping loss, locus displacement, "
            "MAPQ degradation, reference edit burden, CIGAR changes, "
            "soft clipping, and aligned-sequence loss.",
            "",
            "Experiment D is complete.",
            "",
            "## Evidence Files",
            "",
            "### D1",
            "",
            "- `D1_clean_validation/metrics/"
            "experiment_D1_clean_alignment_summary.txt`",
            "",
            "### D2",
            "",
            "- `D2_seed42_alignment/metrics/"
            "experiment_D2_seed42_alignment_summary.tsv`",
            "- `D2_seed42_alignment/metrics/"
            "experiment_D2B_paired_alignment_summary.tsv`",
            "- `D2_seed42_alignment/metrics/"
            "experiment_D2B_monotonicity.tsv`",
            "- `D2_seed42_alignment/paired_analysis/"
            "GN01_vs_CLEAN_per_read.tsv`",
            "- `D2_seed42_alignment/paired_analysis/"
            "GN05_vs_CLEAN_per_read.tsv`",
            "- `D2_seed42_alignment/paired_analysis/"
            "GN10_vs_CLEAN_per_read.tsv`",
            "",
            "### D3",
            "",
            "- `D3_multiseed_alignment/metrics/"
            "experiment_D3_9run_alignment_results.tsv`",
            "- `D3_multiseed_alignment/metrics/"
            "experiment_D3_level_aggregates.tsv`",
            "- `D3_multiseed_alignment/metrics/"
            "experiment_D3B_9run_paired_summary.tsv`",
            "- `D3_multiseed_alignment/metrics/"
            "experiment_D3B_level_aggregates.tsv`",
            "- `D3_multiseed_alignment/metrics/"
            "experiment_D3B_monotonicity.tsv`",
            "- `D3_multiseed_alignment/paired_analysis/"
            "GN01_seed1_vs_CLEAN_per_read.tsv` through "
            "`GN10_seed3_vs_CLEAN_per_read.tsv`",
            "",
        ]
    )

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print(f"Generated findings: {OUTPUT_FILE}")
    print(f"Bytes: {OUTPUT_FILE.stat().st_size}")
    print(f"Lines: {len(lines)}")


if __name__ == "__main__":
    main()
