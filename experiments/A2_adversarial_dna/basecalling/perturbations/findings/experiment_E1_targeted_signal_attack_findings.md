# Experiment E1 — Targeted Local Nanopore Signal Attack

## Objective

Experiment E1 tested whether a very small, localized perturbation to nanopore
raw signal could selectively suppress evidence for a real, truth-backed genomic
variant and weaken downstream variant-calling confidence without broadly
destroying reads or causing alignment failure.

## Target

```text
Sample: HG002 / GM24385
Flowcell: PAO89685
Reference: GRCh38 GIAB no-alt analysis set
Target: chr20:10003468 C>G
GIAB genotype: 0/1
GIAB truth set: v4.2.1
```

The target was selected because it had balanced reference and alternate
support, strong mapping quality, usable strand balance, and GIAB
high-confidence inclusion.

## Environment

```text
Host: promaxgb10-ca47
Architecture: ARM64
GPU: NVIDIA GB10
CUDA: 13.0
Dorado: 2.1.0+48ab35d
Model: dna_r10.4.1_e8.2_400bps_hac@v6.0.0
samtools: 1.19.2
bcftools: 1.19
Python: 3.12.3
```

Reference compatibility was explicitly validated.

```text
chr20 length: 64,444,167
chr20 MD5: b18e6c531b0bd70e949a7fc20859cb01
Compatibility: PASS
```

## Depth Reconciliation

The initial target-selection scan identified:

```text
24 C/G-supporting reads
13 REF-supporting
11 ALT-supporting
```

This was a filtered allele-support set used to identify the attack cohort. It
was not the total number of alignment records overlapping the position.

The complete regional BAM contained:

```text
39 target-overlapping records
34 primary records
5 supplementary records
```

The additional observations included supplementary alignments, deletions, and
a non-C/G observation.

The counting layers were therefore:

```text
24 = initial filtered C/G-support set
39 = all target-overlapping alignment records
35, 34, 29 = caller-filtered INFO/DP values
```

## Raw-Read Extraction

All 11 original ALT-supporting read IDs were mapped to their source POD5 files
and extracted.

```text
Requested IDs: 11
Found IDs: 11
Written reads: 11
Missing IDs: 0
Duplicate IDs: 0
Unexpected IDs: 0
Validation: PASS
```

## Clean Dorado Baseline

The 11-read POD5 was basecalled using Dorado HAC v6 with move tables retained.

```text
Raw reads: 11
BAM records: 13
Raw parents represented: 11
Move tables: 13/13
Mapped records: 13
Unmapped records: 0
```

At the target:

```text
G-supporting parents: 10
Deletion-supporting parents: 1
REF-supporting parents: 0
```

The clean deletion-producing parent was excluded from the active attack
cohort.

Final attack cohort:

```text
10 clean G-supporting raw reads
```

## Signal Mapping

Dorado move tables were used to map the aligned target base to the relevant
raw-signal interval.

The mapping incorporated:

* move-table stride;
* trim offset;
* split-child offset;
* aligned query position;
* raw parent identity.

For each attack read, both the exact target-base interval and a plus/minus
five-base context interval were calculated.

```text
Mapped attack candidates: 10
Excluded clean deletion record: 1
Coordinate validation: PASS
```

## Attack

The attack replaced each mapped plus/minus five-base signal context with a
linear interpolation between its neighbouring boundary values.

```text
Input raw reads: 11
Attacked raw reads: 10
Untouched raw reads: 1

Total signal samples: 4,231,330
Mapped window samples: 1,608
Actually changed samples: 1,599

Changed fraction:
approximately 0.0378%
```

Validation:

```text
Read-ID preservation: PASS
Outside-window identity: PASS
Untouched-read identity: PASS
Missing attack IDs: 0
Unexpected attack IDs: 0
```

## Direct Read-Level Effect

Clean target state:

```text
G: 10
Deletion: 1
```

Attacked target state:

```text
G: 5
Deletion: 6
```

Transitions:

```text
G -> deletion: 5
G -> G: 5
Deletion -> deletion: 1
```

Therefore, half of the clean G-supporting parents lost their alternate call.

All affected reads remained mapped at MAPQ 60.

## Controlled Hybrid Construction

The original regional BAM contained 63 records.

The 11 target ALT parent IDs corresponded to 12 regional records. Removing
those records produced a locked 51-record background.

Two matched hybrids were constructed:

```text
Clean hybrid:
51 identical background records
+ 12 clean Dorado replacement records
= 63 records

Attacked hybrid:
51 identical background records
+ 12 attacked Dorado replacement records
= 63 records
```

Validation:

```text
Clean replacement records: 12
Attacked replacement records: 12
Replacement parent cohorts: identical
Target parents remaining in background: 0
Hybrid count equations: PASS
```

Both hybrids contained:

```text
39 target-overlapping records
34 primary records
5 supplementary records
```

This removed the original basecaller-version confound. The final causal
comparison used the same Dorado version, model, background, cohort, reference,
alignment procedure, and variant-calling procedure.

## Controlled Variant-Calling Result

Identical bcftools parameters were used for all calls.

### Original public regional BAM

```text
GT: 0/1
QUAL: 124.233
INFO/DP: 35
DP4: 7,11,10,7
REF depth: 18
ALT depth: 17
```

### Controlled clean-Dorado hybrid

```text
GT: 0/1
QUAL: 138.247
INFO/DP: 34
DP4: 7,11,9,7
REF depth: 18
ALT depth: 16
```

### Controlled attacked-Dorado hybrid

```text
GT: 0/1
QUAL: 41.4192
INFO/DP: 29
DP4: 7,11,4,7
REF depth: 18
ALT depth: 11
```

### Controlled effect

```text
Genotype:
0/1 -> 0/1

QUAL:
138.247 -> 41.4192

QUAL reduction:
70.0397%

REF depth:
18 -> 18

ALT depth:
16 -> 11

ALT-depth reduction:
31.2500%

INFO/DP:
34 -> 29
```

The genotype remained heterozygous, but its support was substantially
weakened.

## Per-Record Audit

A reproducible audit table was generated for all records in both controlled
hybrids.

```text
Clean hybrid rows: 63
Attacked hybrid rows: 63
Total audit rows: 126
```

Each record was classified by source and target state.

Categories included:

```text
background-REF
background-ALT(B)
background-other
swap-cohort-clean
swap-cohort-attacked
```

Validation:

```text
Clean background records: 51
Attacked background records: 51
Clean replacement records: 12
Attacked replacement records: 12
Unknown or double membership: 0
Background records and target states identical: PASS
Target-overlapping records: 39 in both conditions
Overall audit: PASS
```

Raw replacement-cohort target states were:

```text
Clean:
ALT: 10
Deletion: 1
No target coverage: 1

Attacked:
ALT: 5
Deletion: 6
No target coverage: 1
```

## Preliminary Localization Evidence

The exact same 51 untouched background records were used in both hybrids.

The per-record audit found:

```text
Raw background ALT records in clean hybrid: 5
Raw background ALT records in attacked hybrid: 5
Background target states identical: PASS
```

The background-only BAM did not independently produce a bcftools variant
record at the target, so a standalone caller-filtered background ALT value is
not reported.

The unchanged raw background states provide preliminary evidence that the
observed difference originated in the replacement cohort rather than the
untouched regional background.

This does not replace the planned off-target sham control. An equal-sized
perturbation at a distant non-target signal interval is still required before
making a strong general claim of spatial specificity.

## Main Finding

Experiment E1 demonstrates:

> A localized linear-interpolation perturbation affecting approximately 0.038%
> of the nanopore raw signal reduced alternate-allele depth from 16 to 11 and
> variant QUAL from 138.247 to 41.4192, a 70.04% reduction, while reference
> support remained unchanged at 18 and the complete target-overlapping
> alignment-record structure was preserved.

At the raw-parent level:

```text
10 clean G-supporting parents
became
5 G-supporting parents and 5 deletion-producing parents
```

## Interpretation

The result supports the following claim:

> Correctly localized nanopore raw-signal manipulation can selectively suppress
> truth-backed alternate-allele evidence and substantially weaken downstream
> variant confidence without causing obvious mapping failure or broad read
> corruption.

Stealth indicators included:

* only approximately 0.038% of signal samples changed;
* all attacked reads remained aligned;
* target-cohort MAPQ remained 60;
* reference evidence remained exactly 18;
* record structure remained unchanged;
* untouched background records and target states remained identical;
* the variant call remained plausible and heterozygous.

## Limitations

1. The genotype did not flip from 0/1 to 0/0.
2. The result currently covers one GIAB heterozygous SNV.
3. The attack uses one deterministic interpolation operator.
4. Multi-locus replication remains pending.
5. A dedicated equal-size off-target sham control remains pending.
6. DeepVariant consequences remain untested.
7. Bonito transferability remains untested.
8. The target has repetitive local sequence context.

## Next Steps

### E2 — Attack-strength series

Planned window sizes:

```text
target-base-only
plus/minus 2 bases
plus/minus 5 bases — completed E1 condition
plus/minus 10 bases
plus/minus 20 bases
```

Metrics will include:

* changed samples;
* changed-signal fraction;
* G-supporting reads;
* deletions and substitutions;
* mapping and MAPQ;
* REF and ALT depth;
* INFO/DP;
* QUAL;
* genotype;
* variant presence or absence.

### Further controls

```text
Equal-sized off-target sham perturbation
Multi-locus replication across 3–5 GIAB SNVs
DeepVariant controlled comparison
Bonito cross-model transferability
```

## Status

```text
E1 targeted attack: COMPLETE
Basecaller-confound correction: COMPLETE
Depth reconciliation: COMPLETE
Matched-hybrid validation: COMPLETE
Per-record audit: COMPLETE
Controlled variant consequence: COMPLETE
Findings documentation: COMPLETE

E2 attack-strength series: NEXT
Off-target sham: PENDING
Multi-locus replication: PENDING
DeepVariant: PENDING
Bonito: PENDING
```

## Conclusion

> Modifying only approximately 0.038% of the nanopore raw signal at a
> truth-backed HG002 heterozygous locus selectively halved clean
> alternate-supporting basecalls and reduced controlled downstream variant QUAL
> by 70.04%, while reference evidence, mapping quality, untouched background
> states, and alignment-record structure remained unchanged.
