# Experiment E — Cross-Locus W0 Target-Only Signal Attack

## Objective

The W0 experiment tested whether modifying only the raw-signal event mapped to the target nucleotide was sufficient to alter Dorado's basecall at two independent heterozygous variant loci.

Unlike the successful PM5 attack, W0 used:

- `context_bases = 0`;
- no neighbouring base context;
- only the signal samples assigned to the target-base event.

The experiment was performed at:

| Locus | Variant |
|---|---|
| L2 | chr1:20061156 A>T |
| L3 | chr4:40028853 A>G |

Each cohort contained ten clean ALT-supporting parent reads.

## Signal-level validation

Attack generation passed for all reads at both loci.

| Locus | Reads passed | Changed signal samples | Total signal samples | Changed percentage | Outside-window changes |
|---|---:|---:|---:|---:|---:|
| L2 | 10/10 | 107 | 2,934,299 | 0.0036465% | 0 |
| L3 | 10/10 | 227 | 2,988,077 | 0.0075969% | 0 |

The attack therefore modified an extremely small portion of each cohort's raw signal while preserving all samples outside the intended target windows.

## Dorado basecalling

Dorado HAC v6.0.0 successfully basecalled all attacked reads.

| Locus | Input reads | Basecalled reads |
|---|---:|---:|
| L2 | 10 | 10 |
| L3 | 10 | 10 |

## Alignment preservation

All ten primary reads from each locus remained mapped with MAPQ 60.

| Locus | Total alignment records | Primary records | Mapped records | MAPQ 60 primary records | Target-overlapping records |
|---|---:|---:|---:|---:|---:|
| L2 | 10 | 10 | 10 | 10 | 10 |
| L3 | 11 | 10 | 11 | 10 | 11 |

L3 generated one additional supplementary or split-alignment record, but all ten parent reads retained high-confidence primary alignments.

## Target-base effect

W0 produced no change in the intended ALT allele at either locus.

| Locus | Clean ALT parents | ALT retained after W0 | ALT changed | Effect |
|---|---:|---:|---:|---|
| L2 | 10 | 10 | 0/10 | No effect |
| L3 | 10 | 10 | 0/10 | No effect |

All twenty clean ALT-supporting parent reads remained classified as ALT after W0 basecalling and alignment.

No reads transitioned to:

- REF;
- deletion;
- another nucleotide;
- no coverage;
- unmapped status.

## Comparison with PM5

The earlier PM5 attack altered the target state of all ten ALT-supporting parent reads at each locus while maintaining high-confidence mapping.

W0, in contrast, altered zero of twenty ALT-supporting parents.

This comparison shows that the successful attack does not arise merely because any signal samples associated with the target base were modified. A wider local signal context is required to destabilize Dorado's nucleotide prediction.

## Interpretation

The W0 result establishes an important lower-bound control.

A target-only interpolation window was too narrow to overcome the contextual nature of nanopore basecalling. Dorado infers sequence from a local signal neighbourhood rather than from a single isolated event. Consequently, modifying only the samples assigned to the target base did not remove the ALT allele.

The successful PM5 result should therefore be interpreted as a localized contextual signal attack rather than a single-base signal overwrite.

## Conclusion

Cross-locus W0 replication produced a consistent negative result:

- 20/20 target reads remained mapped;
- 20/20 retained MAPQ 60 primary alignments;
- 20/20 retained the intended ALT base;
- zero target-state changes occurred.

The result supports the conclusion that limited neighbouring signal context is necessary for the demonstrated targeted basecalling attack.

**Final status: COMPLETE — CONSISTENT NO-EFFECT CONTROL**
