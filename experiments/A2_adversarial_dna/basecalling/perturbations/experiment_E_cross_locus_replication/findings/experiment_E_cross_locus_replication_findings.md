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

## Experimental design

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

## Cohort validation

The L2 and L3 attack cohorts were independent:

- L2 attack reads: 10
- L3 attack reads: 10
- L2/L3 read-ID overlap: 0
- L1/L2 overlap: 0
- L1/L3 overlap: 0

Twenty requested reads were extracted from sixteen downloaded POD5 source shards.

Extraction validation:

- requested reads: 20
- extracted reads: 20
- missing reads: 0
- unexpected reads: 0
- duplicate or cross-locus reads: 0

## Clean baseline

Dorado version:

```text
2.1.0+48ab35d
```

Model:

```text
dna_r10.4.1_e8.2_400bps_hac@v6.0.0
```

All twenty clean reads were successfully basecalled.

Clean target-support results:

| Locus | Unique parents | ALT parents | REF | Deletion | Other |
| ----- | -------------: | ----------: | --: | -------: | ----: |
| L2    |             10 |          10 |   0 |        0 |     0 |
| L3    |             10 |          10 |   0 |        0 |     0 |

All primary target alignments had MAPQ 60.

L3 contained one supplementary target-overlapping alignment belonging to an already counted parent read. Parent-level counting therefore remained ten.

## Raw-signal window mapping

All target bases were successfully mapped through the aligned query position, original Dorado sequence orientation, move table, and POD5 signal coordinates.

| Locus | Valid windows | Forward reads | Reverse reads | Mean target-event samples |
| ----- | ------------: | ------------: | ------------: | ------------------------: |
| L2    |         10/10 |             6 |             4 |                      10.8 |
| L3    |         10/10 |             5 |             5 |                      22.8 |

Target-event lengths ranged from:

* L2: 6–18 samples
* L3: 6–66 samples

All calculated signal intervals were inside the corresponding POD5 signals.

## PM5 attack generation

The PM5 attack modified the target base event and five neighboring base events on each side.

| Locus | Changed samples | Total signal samples | Changed percent | Attack-window range |
| ----- | --------------: | -------------------: | --------------: | ------------------: |
| L2    |           1,438 |            2,934,299 |       0.049007% |     114–168 samples |
| L3    |           1,592 |            2,988,077 |       0.053278% |      90–300 samples |

Independent signal comparison confirmed:

* validated reads: 20
* passed reads: 20
* changed samples outside the intended windows: 0
* read IDs preserved: yes
* raw-signal lengths preserved: yes

## Attacked-read consequence

All attacked reads remained basecallable and globally alignable.

| Locus | Basecalled parents | Primary mapped | Unmapped | Mapping quality |
| ----- | ------------------: | --------------: | -------: | ---------------- |
| L2    |                  10 |               10 |        0 | MAPQ 60           |
| L3    |                  10 |               10 |        0 | MAPQ 60           |

Despite preserved mapping, the targeted ALT evidence was completely removed from the attacked cohorts.

### L2 — chr1:20061156 A>T

Clean:

* ALT: 10
* REF: 0
* deletion: 0
* other: 0

Attacked:

* ALT: 0
* REF: 1
* deletion: 7
* other: 2

Result:

```text
100% loss of ALT-supporting attacked parents
```

### L3 — chr4:40028853 A>G

Clean:

* ALT: 10
* REF: 0
* deletion: 0
* other: 0

Attacked:

* ALT: 0
* REF: 3
* deletion: 5
* other: 2

Result:

```text
100% loss of ALT-supporting attacked parents
```

The dominant error mode was deletion formation, followed by REF conversion and alternative incorrect bases.

## Hybrid genomic consequence

The selected parents were removed from their regional background BAMs and replaced with either clean or PM5 attacked alignments.

All four hybrid BAMs passed:

* selected-parent removal;
* selected-parent replacement;
* sorting;
* indexing;
* BAM quickcheck;
* matched clean-versus-PM5 construction.

### Hybrid pileup results

| Locus | Condition | ALT | REF | Deletion | Other |
| ----- | --------- | --: | --: | -------: | ----: |
| L2    | Clean     |  19 |  19 |        0 |     0 |
| L2    | PM5       |   9 |  20 |        7 |     2 |
| L3    | Clean     |  18 |  21 |        0 |     0 |
| L3    | PM5       |   8 |  24 |        5 |     2 |

The ten attacked ALT-supporting parents were removed from the usable ALT evidence at both loci while the untargeted genomic background remained present.

## Variant-caller consequence

Variant calling used:

```text
bcftools mpileup
bcftools call -mv
```

The same caller and settings were used for clean and attacked conditions.

### L2 — chr1:20061156 A>T

| Metric   |   Clean |     PM5 |
| -------- | ------: | ------: |
| Genotype |     0/1 |     0/1 |
| QUAL     | 222.401 | 130.733 |
| REF DP4  |      22 |      23 |
| ALT DP4  |      19 |      11 |

Effects:

* QUAL change: -91.668
* QUAL loss: 41.217%
* ALT-support change: -8
* ALT-support loss: 42.105%
* REF-support change: +1

### L3 — chr4:40028853 A>G

| Metric   |   Clean |     PM5 |
| -------- | ------: | ------: |
| Genotype |     0/1 |     0/1 |
| QUAL     | 222.374 | 150.466 |
| REF DP4  |      23 |      26 |
| ALT DP4  |      20 |      12 |

Effects:

* QUAL change: -71.908
* QUAL loss: 32.337%
* ALT-support change: -8
* ALT-support loss: 40.000%
* REF-support change: +3

## Cross-locus comparison

| Locus                 | Signal changed | ALT-support loss | QUAL loss | Genotype  |
| ---------------------- | -------------: | ----------------: | --------: | --------- |
| L1 chr20:10003468 C>G  |        0.0378% |            31.25% |    70.04% | 0/1 → 0/1 |
| L2 chr1:20061156 A>T   |        0.0490% |            42.11% |    41.22% | 0/1 → 0/1 |
| L3 chr4:40028853 A>G   |        0.0533% |            40.00% |    32.34% | 0/1 → 0/1 |

## Main finding

A localized interpolation attack affecting approximately 0.04–0.05% of nanopore raw-signal samples reproducibly suppressed variant evidence across three independent genomic loci.

At the two replication loci, the attack eliminated the target ALT call from every attacked parent read while retaining full primary mapping at MAPQ 60.

When attacked reads were reintroduced into matched regional genomic backgrounds, the attack caused:

* 40–42% loss of variant ALT support;
* 32–41% loss of variant-call quality;
* minimal change in REF support;
* no loss of global read mapping.

The attack therefore acts as targeted genomic evidence suppression rather than indiscriminate sequencing corruption.

## Interpretation

The genotype remained heterozygous because untargeted ALT-supporting reads were still present in the regional background.

This does not constitute a genotype flip.

The demonstrated consequence is:

```text
targeted evidence destruction and variant-confidence degradation
```

The cross-locus replication shows that the effect is not limited to:

* the original chromosome 20 locus;
* one substitution type;
* one read orientation;
* one signal-event length;
* one local sequence context.

## Important methodological clarification

The ONT Experiment E consequence series used `bcftools` for controlled variant calling.

DeepVariant was used in earlier A2 BAM-manipulation experiments, but it was not the caller used for the Experiment E targeted raw-signal consequence results.

## Conclusion

Experiment E provides cross-locus evidence that highly localized nanopore raw-signal manipulation can selectively destroy support for genuine genomic variants while preserving the apparent integrity and global alignability of the affected sequencing reads.

This creates a cyber-biosecurity risk in which upstream signal manipulation propagates through basecalling and alignment into downstream variant evidence and caller confidence without producing an obvious pipeline failure.
