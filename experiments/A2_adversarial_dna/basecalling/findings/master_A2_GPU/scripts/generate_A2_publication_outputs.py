#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import csv
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path.cwd()

MASTER_DIR = Path(
    "experiments/A2_adversarial_dna/basecalling/"
    "findings/master_A2_GPU"
)

FIGURE_DIR = MASTER_DIR / "publication_figures"
TABLE_DIR = MASTER_DIR / "publication_tables"
MARKER_DIR = MASTER_DIR / "markers"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)
MARKER_DIR.mkdir(parents=True, exist_ok=True)

COMPLETE_MARKER = MARKER_DIR / "A2_PUBLICATION_OUTPUTS.COMPLETE"
FAILED_MARKER = MARKER_DIR / "A2_PUBLICATION_OUTPUTS.FAILED"

COMPLETE_MARKER.unlink(missing_ok=True)
FAILED_MARKER.unlink(missing_ok=True)


TABLE_PATHS = {
    "C1": Path(
        "experiments/A2_adversarial_dna/basecalling/perturbations/"
        "experiment_C_1000reads/metrics/experiment_C1_results.tsv"
    ),
    "C2": Path(
        "experiments/A2_adversarial_dna/basecalling/perturbations/"
        "experiment_C2_multiseed/metrics/"
        "experiment_C2_level_aggregates.tsv"
    ),
    "D3": Path(
        "experiments/A2_adversarial_dna/basecalling/perturbations/"
        "experiment_D_alignment/D3_multiseed_alignment/metrics/"
        "experiment_D3B_level_aggregates.tsv"
    ),
    "E_CONDITION": Path(
        "experiments/A2_adversarial_dna/basecalling/perturbations/"
        "experiment_E_cross_locus_replication/results/"
        "final_comparison/experiment_E_final_condition_comparison.tsv"
    ),
    "E_PM5": Path(
        "experiments/A2_adversarial_dna/basecalling/perturbations/"
        "experiment_E_cross_locus_replication/results/"
        "PM5_target_effect/PM5_clean_vs_attacked_summary.tsv"
    ),
    "E_HYBRID": Path(
        "experiments/A2_adversarial_dna/basecalling/perturbations/"
        "experiment_E_cross_locus_replication/results/"
        "PM5_hybrid_effect/PM5_hybrid_target_summary.tsv"
    ),
    "E_VARIANT": Path(
        "experiments/A2_adversarial_dna/basecalling/perturbations/"
        "experiment_E_cross_locus_replication/results/"
        "PM5_variant_consequence/"
        "PM5_cross_locus_variant_summary.tsv"
    ),
}


def read_table(name: str) -> pd.DataFrame:
    path = TABLE_PATHS[name]

    if not path.exists():
        raise FileNotFoundError(f"Missing source table: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Empty source table: {path}")

    frame = pd.read_csv(path, sep="\t")

    if frame.empty:
        raise ValueError(f"No rows parsed from source table: {path}")

    return frame


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    png_path = FIGURE_DIR / f"{stem}.png"
    pdf_path = FIGURE_DIR / f"{stem}.pdf"

    fig.tight_layout()
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    for path in (png_path, pdf_path):
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Figure was not created correctly: {path}")

    return [png_path, pdf_path]


def annotate_bars(ax: plt.Axes, decimals: int = 1) -> None:
    for container in ax.containers:
        try:
            ax.bar_label(
                container,
                fmt=f"%.{decimals}f",
                padding=3,
                fontsize=8,
            )
        except Exception:
            continue


def write_tsv(frame: pd.DataFrame, filename: str) -> Path:
    path = TABLE_DIR / filename
    frame.to_csv(path, sep="\t", index=False)

    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"Table was not created correctly: {path}")

    return path


def build_outputs() -> tuple[list[Path], list[Path]]:
    c1 = read_table("C1")
    c2 = read_table("C2")
    d3 = read_table("D3")
    e_condition = read_table("E_CONDITION")
    e_pm5 = read_table("E_PM5")
    e_hybrid = read_table("E_HYBRID")
    e_variant = read_table("E_VARIANT")

    generated_figures: list[Path] = []
    generated_tables: list[Path] = []

    condition_order = ["GN01", "GN05", "GN10"]

    c1 = c1.set_index("condition").loc[condition_order].reset_index()
    c2 = c2.set_index("condition").loc[condition_order].reset_index()
    d3 = d3.set_index("condition").loc[condition_order].reset_index()

    sigma_percent = c2["sigma_fraction"].to_numpy(dtype=float) * 100
    condition_labels = c2["condition"].tolist()

    # Figure 1 — sequence identity dose response
    fig, ax = plt.subplots(figsize=(7.2, 4.8))

    ax.errorbar(
        sigma_percent,
        c2["mean_sequence_identity_percent_mean"],
        yerr=c2["mean_sequence_identity_percent_sd"],
        marker="o",
        capsize=5,
        linewidth=2,
        label="Multi-seed mean ± SD",
    )

    ax.scatter(
        sigma_percent,
        c1["mean_sequence_identity_percent"],
        marker="s",
        s=70,
        label="Seed 42",
    )

    ax.set_xlabel("Gaussian noise level (% of per-read signal SD)")
    ax.set_ylabel("Mean sequence identity (%)")
    ax.set_title("Dorado sequence identity decreases with signal noise")
    ax.set_xticks(sigma_percent, condition_labels)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    generated_figures.extend(
        save_figure(fig, "Figure_01_gaussian_identity_dose_response")
    )

    # Figure 2 — edit-distance dose response
    fig, ax = plt.subplots(figsize=(7.2, 4.8))

    ax.errorbar(
        sigma_percent,
        c2["mean_edit_distance_mean"],
        yerr=c2["mean_edit_distance_sd"],
        marker="o",
        capsize=5,
        linewidth=2,
        label="Multi-seed mean ± SD",
    )

    ax.scatter(
        sigma_percent,
        c1["mean_edit_distance"],
        marker="s",
        s=70,
        label="Seed 42",
    )

    ax.set_xlabel("Gaussian noise level (% of per-read signal SD)")
    ax.set_ylabel("Mean edit distance")
    ax.set_title("Basecall edit distance increases with signal noise")
    ax.set_xticks(sigma_percent, condition_labels)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    generated_figures.extend(
        save_figure(fig, "Figure_02_gaussian_edit_distance")
    )

    # Figure 3 — Q-score change
    fig, ax = plt.subplots(figsize=(7.2, 4.8))

    ax.errorbar(
        sigma_percent,
        c2["mean_qscore_change_mean"],
        yerr=c2["mean_qscore_change_sd"],
        marker="o",
        capsize=5,
        linewidth=2,
        label="Multi-seed mean ± SD",
    )

    ax.scatter(
        sigma_percent,
        c1["mean_qscore_change"],
        marker="s",
        s=70,
        label="Seed 42",
    )

    ax.axhline(0, linewidth=1)
    ax.set_xlabel("Gaussian noise level (% of per-read signal SD)")
    ax.set_ylabel("Mean Q-score change")
    ax.set_title("Basecall confidence decreases with signal noise")
    ax.set_xticks(sigma_percent, condition_labels)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    generated_figures.extend(
        save_figure(fig, "Figure_03_gaussian_qscore_change")
    )

    # Figure 4 — alignment instability
    fig, ax = plt.subplots(figsize=(7.2, 4.8))

    bars = ax.bar(
        d3["condition"],
        d3["mean_mapq_drop_ge10"],
        yerr=d3["sd_mapq_drop_ge10"],
        capsize=5,
    )

    ax.set_xlabel("Perturbation condition")
    ax.set_ylabel("Reads with MAPQ drop ≥10\n(mean across seeds)")
    ax.set_title("Strong signal perturbation increases alignment instability")
    ax.grid(axis="y", alpha=0.3)
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)

    generated_figures.extend(
        save_figure(fig, "Figure_04_alignment_mapq_instability")
    )

    # Figure 5 — Experiment E condition comparison
    e_order = ["W0", "SHAM20", "SHAM100", "PM5"]
    e_condition = (
        e_condition.set_index("condition")
        .loc[e_order]
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(8.2, 5.0))

    bars = ax.bar(
        e_condition["condition_label"],
        e_condition["alt_changed_percent"],
    )

    ax.set_xlabel("Signal perturbation condition")
    ax.set_ylabel("Attacked ALT parents changed (%)")
    ax.set_title("Target-centred PM5 is context-dependent and spatially specific")
    ax.set_ylim(0, 112)
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.3)
    ax.bar_label(bars, fmt="%.0f%%", padding=3, fontsize=9)

    generated_figures.extend(
        save_figure(fig, "Figure_05_PM5_control_comparison")
    )

    # Figure 6 — PM5 transition composition
    transitions = e_pm5.copy()

    transitions["locus"] = transitions["candidate"].str.extract(r"^(L\d)")
    transitions = transitions.set_index("locus").loc[["L2", "L3"]].reset_index()

    categories = [
        "ALT_to_REF",
        "ALT_to_DELETION",
        "ALT_to_OTHER",
        "ALT_to_ALT",
    ]

    category_labels = [
        "ALT → REF",
        "ALT → deletion",
        "ALT → other",
        "ALT retained",
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))

    bottom = np.zeros(len(transitions), dtype=float)

    for column, label in zip(categories, category_labels, strict=True):
        values = transitions[column].to_numpy(dtype=float)

        ax.bar(
            transitions["locus"],
            values,
            bottom=bottom,
            label=label,
        )

        bottom += values

    ax.set_xlabel("Replication locus")
    ax.set_ylabel("Attacked ALT-supporting parent reads")
    ax.set_title("PM5 target-state transitions across replication loci")
    ax.set_ylim(0, 11)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    generated_figures.extend(
        save_figure(fig, "Figure_06_PM5_transition_composition")
    )

    # Figure 7 — hybrid ALT support
    hybrid_alt = e_hybrid.pivot(
        index="candidate",
        columns="condition",
        values="parent_ALT",
    ).loc[["L2", "L3"], ["CLEAN", "PM5"]]

    x = np.arange(len(hybrid_alt.index))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7.2, 4.8))

    bars_clean = ax.bar(
        x - width / 2,
        hybrid_alt["CLEAN"],
        width,
        label="Clean hybrid",
    )

    bars_pm5 = ax.bar(
        x + width / 2,
        hybrid_alt["PM5"],
        width,
        label="PM5 hybrid",
    )

    ax.set_xlabel("Replication locus")
    ax.set_ylabel("ALT-supporting parent reads")
    ax.set_title("PM5 suppresses ALT support in controlled hybrid cohorts")
    ax.set_xticks(x, hybrid_alt.index)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    ax.bar_label(bars_clean, fmt="%.0f", padding=3, fontsize=9)
    ax.bar_label(bars_pm5, fmt="%.0f", padding=3, fontsize=9)

    generated_figures.extend(
        save_figure(fig, "Figure_07_hybrid_ALT_support")
    )

    # Figure 8 — variant QUAL
    variant_qual = e_variant.pivot(
        index="candidate",
        columns="condition",
        values="QUAL",
    ).loc[["L2", "L3"], ["CLEAN", "PM5"]]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))

    bars_clean = ax.bar(
        x - width / 2,
        variant_qual["CLEAN"],
        width,
        label="Clean hybrid",
    )

    bars_pm5 = ax.bar(
        x + width / 2,
        variant_qual["PM5"],
        width,
        label="PM5 hybrid",
    )

    ax.set_xlabel("Replication locus")
    ax.set_ylabel("Variant QUAL")
    ax.set_title("PM5 reduces variant-call confidence without changing genotype")
    ax.set_xticks(x, variant_qual.index)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    ax.bar_label(bars_clean, fmt="%.1f", padding=3, fontsize=9)
    ax.bar_label(bars_pm5, fmt="%.1f", padding=3, fontsize=9)

    generated_figures.extend(
        save_figure(fig, "Figure_08_variant_QUAL")
    )

    # Publication table 1 — Gaussian results
    gaussian_table = c2[
        [
            "condition",
            "sigma_fraction",
            "seeds",
            "mean_sequence_identity_percent_mean",
            "mean_sequence_identity_percent_sd",
            "mean_edit_distance_mean",
            "mean_edit_distance_sd",
            "mean_qscore_change_mean",
            "mean_qscore_change_sd",
            "changed_sequence_fraction_mean",
        ]
    ].copy()

    gaussian_table = gaussian_table.merge(
        c1[
            [
                "condition",
                "mean_sequence_identity_percent",
                "mean_edit_distance",
                "mean_qscore_change",
            ]
        ],
        on="condition",
        how="left",
        validate="one_to_one",
    )

    gaussian_table = gaussian_table.rename(
        columns={
            "mean_sequence_identity_percent_mean": "multiseed_identity_mean",
            "mean_sequence_identity_percent_sd": "multiseed_identity_sd",
            "mean_edit_distance_mean": "multiseed_edit_distance_mean",
            "mean_edit_distance_sd": "multiseed_edit_distance_sd",
            "mean_qscore_change_mean": "multiseed_qscore_change_mean",
            "mean_qscore_change_sd": "multiseed_qscore_change_sd",
            "changed_sequence_fraction_mean": "multiseed_changed_fraction_mean",
            "mean_sequence_identity_percent": "seed42_identity",
            "mean_edit_distance": "seed42_edit_distance",
            "mean_qscore_change": "seed42_qscore_change",
        }
    )

    generated_tables.append(
        write_tsv(
            gaussian_table,
            "Table_01_gaussian_dose_response.tsv",
        )
    )

    # Publication table 2 — alignment consequences
    alignment_table = d3[
        [
            "condition",
            "seeds",
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
        ]
    ].copy()

    generated_tables.append(
        write_tsv(
            alignment_table,
            "Table_02_alignment_consequences.tsv",
        )
    )

    # Publication table 3 — control comparison
    condition_table = e_condition[
        [
            "condition",
            "condition_label",
            "placement",
            "base_events_per_read",
            "combined_changed_percent",
            "alt_changed_parents",
            "alt_changed_percent",
            "L2_alt_changed",
            "L3_alt_changed",
            "interpretation",
        ]
    ].copy()

    generated_tables.append(
        write_tsv(
            condition_table,
            "Table_03_PM5_control_comparison.tsv",
        )
    )

    # Publication table 4 — transitions
    transition_table = transitions[
        [
            "locus",
            "candidate",
            "clean_ALT",
            "attacked_ALT",
            "ALT_to_REF",
            "ALT_to_DELETION",
            "ALT_to_OTHER",
            "ALT_to_ALT",
            "ALT_support_loss",
            "ALT_support_loss_percent",
        ]
    ].copy()

    generated_tables.append(
        write_tsv(
            transition_table,
            "Table_04_PM5_target_transitions.tsv",
        )
    )

    # Publication table 5 — downstream consequences
    hybrid_clean = e_hybrid[e_hybrid["condition"] == "CLEAN"][
        ["candidate", "parent_ALT"]
    ].rename(columns={"parent_ALT": "clean_parent_ALT"})

    hybrid_pm5 = e_hybrid[e_hybrid["condition"] == "PM5"][
        [
            "candidate",
            "parent_ALT",
            "parent_REF",
            "parent_DELETION",
            "parent_OTHER",
        ]
    ].rename(
        columns={
            "parent_ALT": "PM5_parent_ALT",
            "parent_REF": "PM5_parent_REF",
            "parent_DELETION": "PM5_parent_DELETION",
            "parent_OTHER": "PM5_parent_OTHER",
        }
    )

    variant_clean = e_variant[e_variant["condition"] == "CLEAN"][
        ["candidate", "GT", "QUAL", "ALT_DP4"]
    ].rename(
        columns={
            "GT": "clean_GT",
            "QUAL": "clean_QUAL",
            "ALT_DP4": "clean_ALT_DP4",
        }
    )

    variant_pm5 = e_variant[e_variant["condition"] == "PM5"][
        ["candidate", "GT", "QUAL", "ALT_DP4"]
    ].rename(
        columns={
            "GT": "PM5_GT",
            "QUAL": "PM5_QUAL",
            "ALT_DP4": "PM5_ALT_DP4",
        }
    )

    downstream_table = (
        hybrid_clean
        .merge(hybrid_pm5, on="candidate", validate="one_to_one")
        .merge(variant_clean, on="candidate", validate="one_to_one")
        .merge(variant_pm5, on="candidate", validate="one_to_one")
    )

    downstream_table["ALT_parent_reduction"] = (
        downstream_table["clean_parent_ALT"]
        - downstream_table["PM5_parent_ALT"]
    )

    downstream_table["QUAL_reduction_percent"] = (
        (
            downstream_table["clean_QUAL"]
            - downstream_table["PM5_QUAL"]
        )
        / downstream_table["clean_QUAL"]
        * 100
    )

    generated_tables.append(
        write_tsv(
            downstream_table,
            "Table_05_hybrid_variant_consequences.tsv",
        )
    )

    # Figure captions
    captions_path = TABLE_DIR / "A2_publication_figure_captions.md"

    captions_path.write_text(
        """# A2 Publication Figure Captions

## Figure 1 — Gaussian identity dose response

Mean sequence identity decreased monotonically with increasing Gaussian
raw-signal perturbation. Squares show the 1,000-read seed-42 experiment.
Circles and error bars show the mean and standard deviation across three
independent 1,000-read seeds.

## Figure 2 — Gaussian edit-distance dose response

Mean clean-to-perturbed edit distance increased sharply with Gaussian
perturbation strength. Seed-42 results followed the same ordering observed
across the multi-seed replication.

## Figure 3 — Gaussian Q-score change

Mean read Q-score declined with perturbation strength. GN10 produced an
approximately 10.7-point mean reduction across the multi-seed experiment.

## Figure 4 — Alignment MAPQ instability

The number of reads losing at least 10 MAPQ points increased with
perturbation strength, despite most reads remaining genomically mapped.

## Figure 5 — PM5 control comparison

Target-centred PM5 changed all 20 attacked ALT-supporting parent reads.
The target-only W0 and distant +100-base sham produced no target changes.
The +20-base near sham produced one short-range spillover event.

## Figure 6 — PM5 transition composition

All attacked ALT-supporting reads lost ALT classification. The resulting
target states were REF, deletion, or other, with deletion being the most
common transition at both replication loci.

## Figure 7 — Hybrid ALT support

Replacing clean target reads with PM5-attacked reads reduced parent-level
ALT support from 19 to 9 at L2 and from 18 to 8 at L3.

## Figure 8 — Variant QUAL

PM5 reduced variant QUAL from 222.401 to 130.733 at L2 and from 222.374
to 150.466 at L3. Both controlled hybrid genotypes remained heterozygous.
""",
        encoding="utf-8",
    )

    generated_tables.append(captions_path)

    return generated_figures, generated_tables


def write_manifest(
    figures: list[Path],
    tables: list[Path],
) -> Path:
    manifest_path = MASTER_DIR / "A2_publication_output_manifest.tsv"

    rows: list[tuple[str, str, int]] = []

    for path in figures:
        rows.append(("figure", str(path), path.stat().st_size))

    for path in tables:
        rows.append(("table_or_caption", str(path), path.stat().st_size))

    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["artifact_type", "path", "size_bytes"])
        writer.writerows(rows)

    return manifest_path


def main() -> int:
    try:
        figures, tables = build_outputs()
        manifest = write_manifest(figures, tables)

        COMPLETE_MARKER.touch()

        print("=" * 80)
        print("A2 PUBLICATION OUTPUT GENERATION: COMPLETE")
        print("=" * 80)
        print(f"Figures created: {len(figures)}")
        print(f"Tables/captions created: {len(tables)}")
        print(f"Manifest: {manifest}")

        print()
        print("FIGURES")
        for path in figures:
            print(path, path.stat().st_size)

        print()
        print("TABLES AND CAPTIONS")
        for path in tables:
            print(path, path.stat().st_size)

        return 0

    except Exception as exc:
        FAILED_MARKER.touch()
        print(
            f"A2 PUBLICATION OUTPUT GENERATION FAILED: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
