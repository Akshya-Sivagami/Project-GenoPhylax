# Experiment E — Final Cross-Locus Targeted Signal Attack Findings

## Objective

Experiment E tested whether localized nanopore raw-signal manipulation could alter variant evidence while preserving the reads' gross genomic alignment.

The final study used two independent heterozygous loci:

| Locus | Variant | ALT-supporting reads |
|---|---|---:|
| L2 | chr1:20061156 A>T | 10 |
| L3 | chr4:40028853 A>G | 10 |

Four conditions were compared:

1. **W0:** target event only;
2. **Near sham:** PM5-sized window shifted 20 bases from the target;
3. **Distant sham:** PM5-sized window shifted 100 bases from the target;
4. **PM5:** PM5-sized window centred on the target.

## Final condition comparison

| Condition | Window | Placement | Combined signal changed | L2 target changes | L3 target changes | Total target changes |
|---|---:|---|---:|---:|---:|---:|
| W0 target-only | 1 base-events | Centred on target | 0.005640% | 0/10 | 0/10 | 0/20 |
| Near sham +20 | 11 base-events | 20 bases downstream | 0.042584% | 1/10 | 0/10 | 1/20 |
| Distant sham +100 | 11 base-events | 100 bases downstream | 0.044459% | 0/10 | 0/10 | 0/20 |
| PM5 target-centred | 11 base-events | Centred on target | 0.051162% | 10/10 | 10/10 | 20/20 |

## Main result

The target-centred PM5 perturbation changed **20/20 ALT-supporting parent reads**, with 10/10 target-state changes at each independent locus.

In contrast:

- W0 changed 0/20 target states;
- the +20-base near sham changed 1/20;
- the +100-base distant sham changed 0/20.

All evaluated conditions retained ten high-confidence primary parent alignments per locus, and no signal samples outside the designated perturbation windows were modified.

## Context dependence

W0 altered only the signal event associated with the target nucleotide. Despite being positioned directly at the target, it produced no target-state changes at either locus.

This demonstrates that the successful attack cannot be explained by modifying an isolated target event. Dorado's prediction depends on a wider local signal context.

## Spatial specificity

The distant +100-base sham used the same 11-base-event interpolation mechanism and a signal-edit magnitude comparable to PM5, but produced no changes at the intended target.

This provides a clean negative control for nonspecific signal corruption.

The +20-base sham produced one L2 ALT-to-deletion transition. Audit showed that its window did not overlap PM5's target window, but the nearest window edges were only nine base-events apart. The read remained mapped at MAPQ 60 while its local CIGAR changed.

The near-sham result therefore indicates limited short-range contextual spillover rather than global loss of mapping.

## Cross-locus reproducibility

The target-centred PM5 attack produced the same qualitative result at both loci: all ten attacked ALT-supporting parent reads lost their intended ALT classification.

The replicated result across chromosomes 1 and 4 reduces the likelihood that the original observation was caused by one unusual locus, read cohort, or sequence context.

## Security interpretation

The results demonstrate a localized generation-stage integrity attack against nanopore basecalling:

- only a small fraction of raw signal was modified;
- changes were confined to explicitly selected windows;
- primary genomic mapping remained intact;
- target allele evidence was selectively disrupted;
- the effect transferred across independent loci;
- target-only and distant off-target controls were negative.

The attack is therefore not merely general signal degradation. Its effect depends on both local context width and spatial placement.

## Final conclusion

Experiment E establishes that a localized, target-centred raw-signal perturbation can systematically alter downstream nucleotide evidence without destroying the affected reads' high-confidence genomic alignment.

The full control series supports three central conclusions:

1. **Context is necessary:** one target event alone is insufficient.
2. **Placement is necessary:** an equally sized perturbation 100 bases away has no target effect.
3. **The effect generalizes:** PM5 disrupted all attacked ALT-supporting reads at both independent loci.

**Final status: COMPLETE**

## Machine-readable outputs

- `results/final_comparison/experiment_E_final_condition_comparison.tsv`
- `results/final_comparison/experiment_E_final_locus_comparison.tsv`

## PM5 source artifacts used

- Signal summary: `experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/discovery/validation/PM5_attack_generation/PM5_attack_summary.tsv`
- Target-effect summary: `experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/results/PM5_target_effect/PM5_clean_vs_attacked_summary.tsv`
