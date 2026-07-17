# Experiment D — Alignment-Level Consequences of Adversarial Nanopore Signal Perturbation

## Objective

Experiment D evaluated whether Gaussian perturbations introduced into raw Oxford Nanopore signal propagate beyond basecalling and alter downstream reference alignment outcomes.

The experiment used the 1,000-read HG002 cohort from Experiment C and aligned CLEAN and perturbed Dorado basecalls against the GIAB GRCh38 no-alt analysis-set reference using minimap2 with the `map-ont` preset.

The analysis addressed two questions:

1. Do raw-signal perturbations affect aggregate alignment success and confidence?
2. Do apparently small aggregate changes conceal read-level mapping, locus, edit-burden, and clipping changes?

## Experimental Design

### D1 — CLEAN alignment validation

- Reference: `GCA_000001405.15_GRCh38_no_alt_analysis_set`
- Aligner: minimap2 2.31-r1302
- Preset: `map-ont`
- CLEAN input reads: 1,000
- Primary-read identity preservation was required.

### D2 — Seed-42 dose-response

The same 1,000 parent reads were evaluated under:

- CLEAN
- GN01 seed 42
- GN05 seed 42
- GN10 seed 42

### D3 — Multi-seed replication

GN01, GN05, and GN10 were repeated with seeds 1, 2, and 3, producing nine perturbed alignment conditions.

All comparisons were paired by normalized parent read ID.

## Validation

All experiment stages completed successfully:

- D1 CLEAN alignment validation: PASS
- D2A seed-42 alignments: PASS
- D2B seed-42 paired analysis: PASS
- D3A nine-run multi-seed alignments: PASS
- D3B nine-run paired replication analysis: PASS

Across every condition:

- exactly 1,000 primary records were retained;
- exactly 1,000 unique parent read IDs were present;
- no duplicate primary parent IDs were detected;
- aligned BAM files passed `samtools quickcheck`;
- every paired comparison contained exactly 1,000 rows.

## D1 — CLEAN Baseline

| Metric | CLEAN |
|---|---:|
| Primary reads | 1000 |
| Mapped primary reads | 970 |
| Unmapped primary reads | 30 |
| Primary mapping rate | 97% |
| Mean mapped-primary MAPQ | 55.336 |
| MAPQ ≥20 | 902 |
| MAPQ ≥30 | 892 |
| MAPQ ≥60 | 866 |
| Secondary alignments | 366 |
| Supplementary alignments | 31 |

The CLEAN cohort achieved a 97% primary mapping rate and high alignment confidence, providing a stable baseline for perturbation comparisons.

## D2 — Seed-42 Aggregate Alignment Results

| Condition | Mapped primary | Mapping rate | Mean MAPQ | MAPQ ≥20 | MAPQ ≥30 | MAPQ ≥60 |
|---|---:|---:|---:|---:|---:|---:|
| CLEAN | 970 | 97% | 55.336 | 902 | 892 | 866 |
| GN01 | 970 | 97% | 55.296 | 900 | 890 | 869 |
| GN05 | 969 | 96.900% | 55.288 | 897 | 891 | 863 |
| GN10 | 968 | 96.800% | 54.914 | 896 | 888 | 856 |

Aggregate mapping changes were modest but directionally consistent. Mapping rate declined from 97.0% in CLEAN to 96.8% at GN10, while mean MAPQ and high-confidence mapping counts also declined.

## D2 — Seed-42 Paired Read-Level Consequences

| Metric | GN01 | GN05 | GN10 | Monotonic |
|---|---:|---:|---:|:---:|
| Mapped → unmapped | 0 | 1 | 3 | Yes |
| Chromosome changes | 3 | 3 | 7 | Yes |
| Strand changes | 4 | 5 | 7 | Not tested |
| CIGAR changes | 889 | 954 | 966 | Not tested |
| Coordinate shifts ≥100 bp | 10 | 20 | 39 | Yes |
| Coordinate shifts ≥1,000 bp | 7 | 13 | 29 | Yes |
| MAPQ drops ≥5 | 5 | 12 | 34 | Yes |
| MAPQ drops ≥10 | 3 | 5 | 27 | Yes |
| Reads with increased NM | 469 | 842 | 938 | Yes |
| Reads with increased soft clipping | 264 | 414 | 607 | Yes |
| Reads with increased secondary alignments | 2 | 9 | 15 | Yes |
| Reads with increased supplementary alignments | 0 | 1 | 3 | Yes |

The paired analysis revealed substantially stronger effects than the aggregate mapping percentages alone.

At GN10 seed 42:

- 3 previously mapped reads became unmapped;
- 7 reads changed chromosome;
- 39 reads shifted by at least 100 bp;
- 29 reads shifted by at least 1,000 bp;
- 27 reads lost at least 10 MAPQ points;
- 938 reads showed increased alignment edit burden;
- 607 reads showed increased soft clipping.

These results demonstrate that successful mapping and small changes in cohort-level mapping rate can conceal substantial read-level integrity degradation.

## D3 — Multi-Seed Aggregate Replication

| Condition | Mapped primary | Mapping rate | Mean MAPQ | MAPQ ≥20 | MAPQ ≥30 | MAPQ ≥60 |
|---|---:|---:|---:|---:|---:|---:|
| GN01 | 970 ± 0 | 97 ± 0% | 55.337 ± 0.032 | 902.333 ± 0.577 | 892 ± 1 | 866.667 ± 0.577 |
| GN05 | 969.333 ± 1.155 | 96.933 ± 0.115% | 55.236 ± 0.056 | 898.667 ± 2.082 | 891 ± 0 | 864.333 ± 1.155 |
| GN10 | 967.667 ± 1.155 | 96.767 ± 0.115% | 54.725 ± 0.069 | 892.333 ± 2.887 | 881.667 ± 1.155 | 853.333 ± 2.517 |

Across seeds 1–3, the following aggregate metrics changed monotonically with perturbation strength:

- unmapped primary reads increased: Yes;
- mapping percentage decreased: Yes;
- mean mapped-primary MAPQ decreased: Yes;
- MAPQ ≥20 counts decreased: Yes;
- MAPQ ≥30 counts decreased: Yes;
- MAPQ ≥60 counts decreased: Yes.

Secondary and supplementary totals were not monotonic across levels and should therefore be treated as variable alignment behaviours rather than primary dose-response indicators.

## D3 — Multi-Seed Paired Replication

| Metric | GN01 mean ± SD | GN05 mean ± SD | GN10 mean ± SD | Monotonic |
|---|---:|---:|---:|:---:|
| Mapped → unmapped | 0 ± 0 | 0.667 ± 1.155 | 3 ± 1 | Yes |
| Chromosome changes | 3.667 ± 0.577 | 4.333 ± 0.577 | 5.333 ± 0.577 | Yes |
| Strand changes | 4.333 ± 1.528 | 5 ± 1.732 | 8.667 ± 1.155 | Yes |
| CIGAR changes | 882.667 ± 15.567 | 957 ± 0 | 966.333 ± 1.528 | Yes |
| Coordinate shifts ≥100 bp | 9 ± 2 | 21 ± 2 | 37.667 ± 2.082 | Yes |
| Coordinate shifts ≥1,000 bp | 6.667 ± 2.082 | 17.667 ± 2.082 | 28 ± 1.732 | Yes |
| MAPQ drops ≥5 | 2.667 ± 0.577 | 12.667 ± 1.155 | 37.333 ± 2.082 | Yes |
| MAPQ drops ≥10 | 1.667 ± 0.577 | 7.333 ± 1.155 | 27.333 ± 4.726 | Yes |
| Reads with increased NM | 456.667 ± 7.638 | 848.667 ± 6.658 | 940 ± 1.732 | Yes |
| Reads with increased soft clipping | 253.667 ± 5.508 | 380 ± 9.539 | 600.667 ± 4.163 | Yes |
| Reads with increased secondary alignments | 2 ± 1 | 7 ± 1 | 15 ± 2.646 | Yes |
| Reads with increased supplementary alignments | 1 ± 1 | 0 ± 0 | 1.333 ± 0.577 | No |

Additional continuous read-level effects were also monotonic across perturbation strengths:

- mean MAPQ change: 0.001, -0.110, -0.586;
- mean aligned-query-length change: -0.220, -8.305, -41.688 bases.

The only paired metric in the selected monotonicity set that did not show a monotonic dose-response was the number of reads gaining supplementary alignments. This metric remained sparse and variable across seeds.

## Main Finding

Gaussian raw-signal perturbation propagated through Dorado basecalling into downstream reference alignment.

The impact was not limited to a slight reduction in overall mapping rate. Paired parent-read analysis revealed dose-dependent changes in:

- mapping status;
- chromosome and strand assignment;
- genomic coordinate placement;
- alignment confidence;
- CIGAR structure;
- edit distance to the reference;
- soft clipping;
- aligned query length;
- secondary alignment behaviour.

Most major integrity-damage metrics were monotonic in both the seed-42 experiment and the independent multi-seed replication.

## Security Interpretation

A conventional pipeline-validity check would classify all conditions as successful:

- POD5 files remained readable;
- Dorado completed basecalling;
- BAM files remained structurally valid;
- minimap2 completed alignment;
- aligned BAM files passed integrity checks;
- most reads remained mapped.

Nevertheless, the biological interpretation of individual reads changed.

Therefore:

> Structural validity, successful execution, and high aggregate mapping rates do not guarantee genomic-data integrity.

This extends the central Experiment C result beyond basecalling. Perturbations can survive multiple apparently successful pipeline stages while progressively altering the digital genomic record.

## Limitations

- The experiment used a 1,000-read HG002 subset rather than a complete genome-scale sequencing run.
- Gaussian noise is a controlled perturbation model and does not by itself demonstrate a physically synthesized adversarial molecule.
- Only one basecaller model and one alignment configuration were evaluated.
- Alignment changes were measured directly; downstream variant-calling consequences were not evaluated in Experiment D.
- Some alignment behaviours, particularly supplementary alignments, were sparse and non-monotonic.

## Conclusion

Experiment D provides replicated evidence that raw nanopore signal perturbations can propagate into alignment-level errors despite successful execution and structurally valid outputs at every stage.

The strongest evidence comes from paired parent-read analysis, where increasing perturbation strength produced replicated increases in mapping loss, locus displacement, MAPQ degradation, reference edit burden, CIGAR changes, soft clipping, and aligned-sequence loss.

Experiment D is complete.

## Evidence Files

### D1

- `D1_clean_validation/metrics/experiment_D1_clean_alignment_summary.txt`

### D2

- `D2_seed42_alignment/metrics/experiment_D2_seed42_alignment_summary.tsv`
- `D2_seed42_alignment/metrics/experiment_D2B_paired_alignment_summary.tsv`
- `D2_seed42_alignment/metrics/experiment_D2B_monotonicity.tsv`
- `D2_seed42_alignment/paired_analysis/GN01_vs_CLEAN_per_read.tsv`
- `D2_seed42_alignment/paired_analysis/GN05_vs_CLEAN_per_read.tsv`
- `D2_seed42_alignment/paired_analysis/GN10_vs_CLEAN_per_read.tsv`

### D3

- `D3_multiseed_alignment/metrics/experiment_D3_9run_alignment_results.tsv`
- `D3_multiseed_alignment/metrics/experiment_D3_level_aggregates.tsv`
- `D3_multiseed_alignment/metrics/experiment_D3B_9run_paired_summary.tsv`
- `D3_multiseed_alignment/metrics/experiment_D3B_level_aggregates.tsv`
- `D3_multiseed_alignment/metrics/experiment_D3B_monotonicity.tsv`
- `D3_multiseed_alignment/paired_analysis/GN01_seed1_vs_CLEAN_per_read.tsv` through `GN10_seed3_vs_CLEAN_per_read.tsv`
