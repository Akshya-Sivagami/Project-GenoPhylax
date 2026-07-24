# Experiment E — Cross-Locus Replication of a Targeted Nanopore Signal Attack

## Objective

This experiment tested whether the localized raw-signal attack demonstrated at the original HG002 chromosome 20 locus generalized to independent genomic loci with different chromosomes, substitutions, sequence contexts, read orientations, and signal-event durations.

The attack was evaluated at three truth-backed heterozygous HG002 loci:

| Locus | Variant |
|---|---|
| L1 | chr20:10003468 C>G |
| L2 | chr1:20061156 A>T |
| L3 | chr4:40028853 A>G |

L1 was the original targeted-locus experiment. L2 and L3 were selected as independent cross-locus replication targets.

## Final Result Summary

| Locus | Variant | Clean ALT | PM5 ALT | ALT Loss | Clean QUAL | PM5 QUAL | QUAL Loss | Genotype |
|---|---|---|---|---|---|---|---|---|
| L1 | chr20:10003468 C>G | 16 | 11 | 31.25% | 138.247 | 41.419 | 70.04% | 0/1 → 0/1 |
| L2 | chr1:20061156 A>T | 19 | 11 | 42.11% | 222.401 | 130.733 | 41.22% | 0/1 → 0/1 |
| L3 | chr4:40028853 A>G | 20 | 12 | 40.00% | 222.374 | 150.466 | 32.34% | 0/1 → 0/1 |

At the isolated targeted-read level, PM5 destroyed all intended ALT calls:
- **L2:** 10 ALT → 0 ALT
- **L3:** 10 ALT → 0 ALT

## Experimental Design

For L2 and L3:

1. Ten ALT-supporting nanopore reads were identified at each locus.
2. The corresponding raw POD5 reads were downloaded and extracted.
3. Reads were independently basecalled with Dorado HAC v6.
4. Clean basecalls were aligned to GRCh38.
5. The target nucleotide was mapped through the alignment and Dorado move table to its raw-signal interval.
6. A PM5 attack was applied, covering the target event and five neighboring base events on each side.
7. Signal inside the local window was replaced using linear interpolation.
8. Every sample outside the attack window was required to remain identical.
9. Attacked reads were independently basecalled and aligned.
10. Clean and attacked reads were inserted into matched regional background BAMs.
11. Variant calls were produced using `bcftools mpileup` followed by `bcftools call -mv`.

## Cohort Validation

The L2 and L3 attack cohorts were independent:

- L2 attack reads: 10
- L3 attack reads: 10
- L2/L3 read-ID overlap: 0
- L1/L2 overlap: 0
- L1/L3 overlap: 0

Twenty requested reads were extracted from sixteen downloaded POD5 source shards.

Extraction validation:
- Requested reads: 20
- Extracted reads: 20
- Missing reads: 0
- Unexpected reads: 0
- Duplicate or cross-locus reads: 0

## Clean Baseline

Dorado version: `2.1.0+48ab35d`  
Model: `dna_r10.4.1_e8.2_400bps_hac@v6.0.0`

All twenty clean reads were successfully basecalled.

Clean target-support results:

| Locus | Unique parents | ALT parents | REF | Deletion | Other |
|---|---|---|---|---|---|
| L2 | 10 | 10 | 0 | 0 | 0 |
| L3 | 10 | 10 | 0 | 0 | 0 |

All primary target alignments had MAPQ 60. L3 contained one supplementary target-overlapping alignment belonging to an already counted parent read. Parent-level counting therefore remained ten.

## Raw-Signal Window Mapping

All target bases were successfully mapped through the aligned query position, original Dorado sequence orientation, move table, and POD5 signal coordinates.

| Locus | Valid windows | Forward reads | Reverse reads | Mean target-event samples |
|---|---|---|---|---|
| L2 | 10/10 | 6 | 4 | 10.8 |
| L3 | 10/10 | 5 | 5 | 22.8 |

Target-event lengths ranged from:
- **L2:** 6–18 samples
- **L3:** 6–66 samples

All calculated signal intervals were inside the corresponding POD5 signals.

## PM5 Attack Generation

The PM5 attack modified the target base event and five neighboring base events on each side.

| Locus | Changed samples | Total signal samples | Changed percent | Attack-window range |
|---|---|---|---|---|
| L2 | 1,438 | 2,934,299 | 0.049007% | 114–168 samples |
| L3 | 1,592 | 2,988,077 | 0.053278% | 90–300 samples |

Independent signal comparison confirmed:
- Validated reads: 20
- Passed reads: 20
- Changed samples outside the intended windows: 0
- Read IDs preserved: Yes
- Raw-signal lengths preserved: Yes

## Attacked-Read Consequence

All attacked reads remained basecallable and globally alignable.

| Locus | Basecalled parents | Primary mapped | Unmapped | Mapping quality |
|---|---|---|---|---|
| L2 | 10 | 10 | 0 | MAPQ 60 |
| L3 | 10 | 10 | 0 | MAPQ 60 |

Despite preserved mapping, the targeted ALT evidence was completely removed from the attacked cohorts.

### L2 — chr1:20061156 A>T
- **Clean:** ALT: 10 | REF: 0 | Deletion: 0 | Other: 0
- **Attacked:** ALT: 0 | REF: 1 | Deletion: 7 | Other: 2
- **Result:** 100% loss of ALT-supporting attacked parents

### L3 — chr4:40028853 A>G
- **Clean:** ALT: 10 | REF: 0 | Deletion: 0 | Other: 0
- **Attacked:** ALT: 0 | REF: 3 | Deletion: 5 | Other: 2
- **Result:** 100% loss of ALT-supporting attacked parents

The dominant error mode was deletion formation, followed by REF conversion and alternative incorrect bases.

## Hybrid Genomic Consequence

The selected parents were removed from their regional background BAMs and replaced with either clean or PM5 attacked alignments.

All four hybrid BAMs passed:
- Selected-parent removal
- Selected-parent replacement
- Sorting
- Indexing
- BAM quickcheck
- Matched clean-versus-PM5 construction

### Hybrid Pileup Results

| Locus | Condition | ALT | REF | Deletion | Other |
|---|---|---|---|---|---|
| L2 | Clean | 19 | 19 | 0 | 0 |
| L2 | PM5 | 11 | 20 | 7 | 2 |
| L3 | Clean | 18 | 21 | 0 | 0 |
| L3 | PM5 | 12 | 24 | 5 | 2 |

The ten attacked ALT-supporting parents were removed from the usable ALT evidence at both loci while the untargeted genomic background remained present.

## Variant-Caller Consequence

Variant calling used:
- `bcftools mpileup`
- `bcftools call -mv`

*(Note: DeepVariant was used in earlier BAM-manipulation experiments, but `bcftools` was used exclusively for Experiment E.)*

### L2 — chr1:20061156 A>T
- **QUAL:** Clean = 222.401 | PM5 = 130.733 (-91.668 / 41.217% loss)
- **ALT DP4:** Clean = 19 | PM5 = 11 (-8 / 42.105% loss)
- **REF DP4:** Clean = 22 | PM5 = 23 (+1)
- **Genotype:** `0/1` → `0/1`

### L3 — chr4:40028853 A>G
- **QUAL:** Clean = 222.374 | PM5 = 150.466 (-71.908 / 32.337% loss)
- **ALT DP4:** Clean = 20 | PM5 = 12 (-8 / 40.000% loss)
- **REF DP4:** Clean = 23 | PM5 = 26 (+3)
- **Genotype:** `0/1` → `0/1`

## Main Finding & Interpretation

A localized raw-signal interpolation attack affecting approximately **0.05% of signal samples** eliminated the target allele from every attacked read at two independent loci while preserving mapping. In matched regional variant calls, this caused approximately **40–42% loss of ALT support** and **32–41% loss of variant quality** without changing the reported heterozygous genotype.

This is **targeted evidence suppression and caller-confidence degradation**, not a genotype flip. The genotype remained heterozygous because untargeted ALT-supporting reads were still present in the genomic background.

## Conclusion

Experiment E provides cross-locus evidence that highly localized nanopore raw-signal manipulation can selectively destroy support for genuine genomic variants while preserving the apparent integrity and global alignability of the affected sequencing reads.

This creates a cyber-biosecurity risk in which upstream signal manipulation propagates through basecalling and alignment into downstream variant evidence and caller confidence without producing an obvious pipeline failure.
