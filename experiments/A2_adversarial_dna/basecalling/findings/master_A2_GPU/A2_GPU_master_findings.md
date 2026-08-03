# Project GenoPhylax — A2 GPU Extension Master Findings

## Module

```text
Project GenoPhylax
└── A2 — Adversarial Genomic Data
    └── Nanopore raw-signal perturbation and downstream genomic consequences
```

## Status

```text
A2 GPU EXPERIMENTAL WORK: COMPLETE
BONITO TRANSFERABILITY: NOT EXECUTED — PLATFORM INCOMPATIBLE
MASTER CONSOLIDATION: COMPLETE
```

---

# 1. Executive Summary

The A2 GPU extension investigated whether controlled perturbations to Oxford Nanopore raw electrical signal could alter machine-learning basecaller output and downstream genomic evidence.

The experiments progressed from clean baseline validation through increasingly realistic adversarial tests:

1. clean Dorado basecalling;
2. whole-read Gaussian signal perturbation;
3. multi-seed replication;
4. 1,000-read scale validation;
5. alignment-level consequence analysis;
6. targeted locus-specific signal manipulation;
7. cross-locus replication;
8. negative and spatial specificity controls;
9. hybrid BAM and variant-level consequence analysis;
10. attempted Bonito cross-model feasibility evaluation.

The principal finding was that a highly localized target-centred signal perturbation could consistently suppress ALT-supporting evidence while preserving high-confidence genomic mapping.

Across two independent heterozygous loci:

```text
20/20 attacked ALT-supporting reads lost ALT classification
```

All primary reads remained mapped at MAPQ 60.

The effect was context-dependent and spatially specific:

```text
W0 target-only control:       0/20 target changes
Near sham at +20 bases:       1/20 target changes
Distant sham at +100 bases:   0/20 target changes
Target-centred PM5:          20/20 target changes
```

When attacked reads were inserted into controlled hybrid cohorts, ALT support and variant confidence decreased substantially, although the final cohort-level genotypes remained heterozygous.

Therefore, A2 demonstrated strong manipulation of local sequencing evidence and variant confidence, but did not demonstrate a complete genotype flip.

---

# 2. Research Objective

The A2 GPU extension addressed the following central question:

```text
Can small controlled changes to Nanopore raw electrical signal alter
basecalled genomic evidence while preserving apparently normal read mapping?
```

The work also examined:

* whether signal perturbation produces a measurable dose response;
* whether the effect is reproducible across random seeds;
* whether basecalling degradation propagates into alignment;
* whether a perturbation can be localized to one genomic locus;
* whether the effect reproduces across independent loci;
* whether target effects are distinguishable from generic signal corruption;
* whether altered read evidence changes downstream variant support;
* whether the attack transfers between basecalling models.

---

# 3. Experimental Platform

## Hardware

The experiments were conducted on:

* NVIDIA GB10 Grace Blackwell system;
* Linux AArch64;
* CUDA 13.0;
* approximately 122 GB system memory.

## Basecaller

The primary basecaller was:

```text
Dorado 2.1.0
```

Model:

```text
dna_r10.4.1_e8.2_400bps_hac@v6.0.0
```

## Dataset

The raw signal dataset used HG002 / GM24385 Nanopore reads generated using:

* R10.4.1 pore chemistry;
* E8.2 motor;
* 400 bases per second;
* GIAB-compatible HG002 material.

## Main supporting tools

* POD5 Python API;
* NumPy;
* pysam;
* edlib;
* minimap2;
* samtools;
* bcftools;
* DeepVariant where applicable.

---

# 4. Experimental Progression

| Experiment         | Scope                                             | Main purpose                                                   |
| ------------------ | ------------------------------------------------- | -------------------------------------------------------------- |
| A                  | Clean baseline and initial Gaussian dose response | Establish normal Dorado behaviour and perturbation sensitivity |
| B                  | Multi-seed 100-read replication                   | Test reproducibility across independent noise realizations     |
| C1                 | 1,000-read scale validation                       | Confirm that effects persist at larger sample size             |
| C2                 | 1,000-read multi-seed replication                 | Measure larger-scale between-seed stability                    |
| D                  | Alignment consequence analysis                    | Determine whether altered basecalls affect genomic mapping     |
| E1                 | Initial targeted-locus attack                     | Demonstrate local manipulation at one truth-backed locus       |
| E2                 | Target-window strength series                     | Compare W0, PM2, PM10 and PM20 attack windows                  |
| E cross-locus      | Replication at L2 and L3                          | Establish reproducibility beyond one locus                     |
| E controls         | W0 and shifted shams                              | Establish context dependence and spatial specificity           |
| E hybrid           | Downstream variant consequence                    | Measure ALT support and variant-confidence effects             |
| Bonito feasibility | Cross-model transferability attempt               | Determine whether the same test could be run with Bonito       |

---

# 5. Experiment A — Clean Baseline and Initial Dose Response

## Objective

Experiment A established a clean Dorado control and measured how increasing Gaussian signal noise affected the resulting basecalled sequences.

## Clean 100-read control

The clean control contained:

```text
100 physical reads
```

The BAM passed integrity validation.

Approximate clean-run metrics included:

* mean Q-score: 35.03;
* basecalling time: 27.62 seconds;
* throughput: approximately 1.70 million samples per second;
* peak memory use: approximately 800 MB.

## Perturbation levels

Gaussian noise was added using:

```text
sigma = fraction × per-read signal standard deviation
```

The tested levels were:

* GN01: 0.01;
* GN05: 0.05;
* GN10: 0.10.

Seed 42 was used for the initial dose-response experiment.

## Results

| Condition | Changed reads | Mean identity | Mean edit distance | Mean Q-score change |
| --------- | ------------: | ------------: | -----------------: | ------------------: |
| GN01      |        95/100 |      98.7903% |              14.19 |              -0.064 |
| GN05      |       100/100 |      96.9033% |              43.40 |              -2.250 |
| GN10      |       100/100 |      93.8863% |             112.67 |             -10.111 |

Additional median results:

| Condition | Median identity | Median edit distance | P95 edit distance |
| --------- | --------------: | -------------------: | ----------------: |
| GN01      |        99.5177% |                  9.0 |             45.05 |
| GN05      |        98.4688% |                 28.5 |            129.10 |
| GN10      |        95.3069% |                 82.0 |            319.15 |

## Finding

Increasing signal noise produced a clear monotonic degradation in:

* sequence identity;
* edit distance;
* confidence score;
* sequence stability.

Dorado still completed successfully for every condition.

## Interpretation

The basecaller was robust enough to continue producing valid output, but the nucleotide content of that output increasingly diverged from the clean control.

This demonstrated that apparently successful basecalling does not guarantee preservation of the underlying sequence evidence.

---

# 6. Experiment B — Multi-Seed Replication

## Objective

Experiment B tested whether the Gaussian dose-response pattern was reproducible across independent noise realizations.

## Design

The experiment used:

* 100 identical physical reads;
* GN01, GN05 and GN10;
* seeds 1, 2, 3, 4 and 5;
* 15 total perturbation conditions.

## Aggregate ranges

| Condition | Mean identity range | Mean edit-distance range | Mean Q-score-change range |
| --------- | ------------------: | -----------------------: | ------------------------: |
| GN01      |    98.2933–99.2379% |              12.48–17.36 |    -0.184145 to -0.083067 |
| GN05      |    97.1493–97.6866% |              40.71–44.12 |    -2.373500 to -2.154335 |
| GN10      |    93.5584–93.9454% |            112.38–115.20 |  -10.434556 to -10.270288 |

## Split-read observation

GN01 seed 5 produced 101 BAM records from 100 physical reads because one read was split into multiple output records.

The analysis was corrected to compare physical parent reads rather than assuming one BAM record per input read.

## Finding

The ordering remained stable across seeds:

```text
GN01 < GN05 < GN10
```

for degradation severity.

## Interpretation

The signal-to-basecall dose response was not an artifact of one random seed.

The split-read observation also established an important methodological requirement:

```text
Nanopore attack analysis must track parent read identity, not only BAM record counts.
```

---

# 7. Experiment C — 1,000-Read Scale Validation

## Objective

Experiment C tested whether the same perturbation behaviour persisted at a larger and more representative scale.

## Experiment C1

C1 used:

* 1,000 physical reads;
* clean control;
* GN01, GN05 and GN10;
* seed 42.

The experiment confirmed:

* monotonic sequence-identity degradation;
* increasing edit distance;
* increasing Q-score loss;
* more severe sequence outliers at stronger perturbation levels;
* successful Dorado completion across all conditions.

At GN10:

```text
488 reads fell below 95% sequence identity
```

## Experiment C2

C2 expanded the 1,000-read test to:

* seeds 1, 2 and 3;
* three Gaussian levels;
* nine total perturbed runs.

The dose-response ordering remained stable across all seeds.

## Finding

The degradation pattern remained reproducible after scaling from 100 to 1,000 reads.

## Interpretation

The observed effect was not limited to a small convenience sample.

The larger experiments supported the conclusion that controlled raw-signal changes can systematically alter basecalled nucleotide output while allowing the basecalling process itself to finish normally.

---

# 8. Experiment D — Alignment-Level Consequences

## Objective

Experiment D examined whether sequence changes caused by raw-signal perturbation propagated into genomic alignment.

## Design

The reads were aligned against the GIAB GRCh38 no-alt reference using minimap2.

The experiment included:

* D1 clean alignment validation;
* D2 seed-42 dose response;
* D3 multi-seed alignment replication.

## Aggregate result

Overall mapping remained high, at approximately:

```text
97% mapped reads
```

across the tested perturbed conditions.

However, stronger perturbation caused increasing read-level mapping instability, including:

* lower MAPQ for subsets of reads;
* reductions in MAPQ-threshold counts;
* altered genomic positions;
* changed alignment structure;
* changed CIGAR strings;
* occasional loss of primary mapping confidence.

Examples from the seed-42 paired analysis included:

```text
27 reads losing at least 10 MAPQ points
```

in one tested condition.

Across multi-seed analysis, mean MAPQ changes were small in aggregate but worsened with perturbation strength.

## Finding

Whole-read Gaussian signal corruption produced strong sequence degradation, but most reads still remained alignable.

## Interpretation

This created the key attack condition required by GenoPhylax:

```text
The pipeline can continue successfully and produce plausible mapped output,
even when the nucleotide sequence has been materially altered.
```

A simple pipeline-success check would therefore fail to detect many corrupted reads.

---

# 9. Experiment E — Targeted Locus Signal Attack

## Objective

Experiment E moved beyond generic whole-read degradation and tested whether an attacker could manipulate a small local signal region associated with one genomic locus.

The desired property was:

```text
Change local target evidence
while preserving the read’s gross genomic alignment.
```

## Original target

The initial target locus was:

```text
chr20:10003468
```

The analysis used HG002 truth-backed data and an approximately 13 kb call window around the target.

Eleven ALT-associated parent reads were identified and traced to their source POD5 files.

## Attack method

The attack used localized signal interpolation over a signal window derived from Dorado move-table information.

The attack strengths included:

* W0;
* PM2;
* PM10;
* PM20.

The later cross-locus experiment standardized the primary attack at:

```text
PM5 = target event ± 5 surrounding base-events
```

This produced an 11-base-event target-centred window.

---

# 10. Experiment E2 — Window Strength Series

## Conditions

| Condition | Context bases |
| --------- | ------------: |
| W0        |             0 |
| PM2       |             2 |
| PM10      |            10 |
| PM20      |            20 |

Each condition used the same 11 target-associated input parent reads.

Dorado produced 13 BAM records because of split-read output, while parent-level analysis remained based on the original 11 reads.

## Target-state results

### W0

* ALT: 6;
* REF: 2;
* deletion: 3;
* other: 0.

### PM2

* ALT: 5;
* REF: 2;
* deletion: 1;
* other: 3.

### PM10

* ALT: 5;
* REF: 1;
* deletion: 4;
* other: 1.

### PM20

* ALT: 5;
* REF: 1;
* deletion: 4;
* other: 1.

## Finding

Increasing the local context beyond the isolated target event altered target-state outcomes.

## Interpretation

The basecaller did not treat the target nucleotide as an independent signal event.

Instead, its prediction depended on a wider local signal neighbourhood.

---

# 11. Experiment E — Cross-Locus Replication

## Objective

The cross-locus experiment tested whether the PM5 effect reproduced beyond the original chromosome 20 locus.

## Replication loci

| Locus | Variant           |
| ----- | ----------------- |
| L2    | chr1:20061156 A>T |
| L3    | chr4:40028853 A>G |

For each locus:

* ten clean ALT-supporting parent reads were extracted;
* the clean target state was validated;
* signal windows were mapped;
* PM5 was applied;
* attacked reads were basecalled with Dorado;
* reads were realigned;
* target states were compared parent-by-parent.

## Signal modification

| Locus | Changed signal samples | Percentage of total signal |
| ----- | ---------------------: | -------------------------: |
| L2    |                  1,438 |                 0.0490066% |
| L3    |                  1,592 |                 0.0532784% |

No samples outside the designated attack windows changed.

## Target-state result

| Locus    | Clean ALT reads | ALT retained | ALT lost |
| -------- | --------------: | -----------: | -------: |
| L2       |              10 |            0 |       10 |
| L3       |              10 |            0 |       10 |
| Combined |              20 |            0 |       20 |

## Detailed transitions

### L2

* 1 ALT → REF;
* 7 ALT → deletion;
* 2 ALT → other;
* 0 ALT retained.

### L3

* 3 ALT → REF;
* 5 ALT → deletion;
* 2 ALT → other;
* 0 ALT retained.

## Mapping preservation

All ten primary reads at each locus remained mapped at:

```text
MAPQ 60
```

## Finding

```text
PM5 caused 20/20 attacked ALT-supporting reads to lose ALT classification.
```

## Interpretation

The attack modified local nucleotide evidence without destroying gross genomic alignment.

The result reproduced across independent loci on chromosomes 1 and 4.

---

# 12. Experiment E — Context and Specificity Controls

Three controls were used to distinguish a target-specific contextual effect from generic raw-signal corruption.

## Control 1 — W0 target-only perturbation

W0 modified only the isolated signal event assigned to the target nucleotide.

| Locus | Changed samples | Percentage | Target changes |
| ----- | --------------: | ---------: | -------------: |
| L2    |             107 | 0.0036465% |           0/10 |
| L3    |             227 | 0.0075969% |           0/10 |

Combined:

```text
0/20 target changes
```

### Interpretation

Changing only the isolated target event was insufficient.

The successful PM5 result therefore required surrounding local signal context.

---

## Control 2 — Near off-target sham at +20 bases

The same PM5-sized 11-base-event window was shifted 20 bases downstream.

| Locus | Changed samples | Percentage | Target changes |
| ----- | --------------: | ---------: | -------------: |
| L2    |           1,350 | 0.0460076% |           1/10 |
| L3    |           1,172 | 0.0392226% |           0/10 |

Combined:

```text
1/20 target changes
```

The changed L2 read transitioned:

```text
ALT → deletion
```

while remaining mapped at MAPQ 60.

### Interpretation

A perturbation 20 bases away was not a perfect negative control.

The isolated change suggested short-range contextual spillover in Dorado’s sequence prediction.

---

## Control 3 — Distant off-target sham at +100 bases

The same 11-base-event window was shifted 100 bases downstream.

| Locus | Changed samples | Percentage | Target changes |
| ----- | --------------: | ---------: | -------------: |
| L2    |           1,246 | 0.0424633% |           0/10 |
| L3    |           1,387 | 0.0464178% |           0/10 |

Combined:

```text
0/20 target changes
```

All primary reads remained mapped at MAPQ 60.

### Interpretation

A perturbation of comparable magnitude 100 bases from the target did not change target classification.

This provided the clean spatial negative control.

---

# 13. Final Experiment E Condition Comparison

| Condition    |         Window | Placement      | Combined signal changed | L2 changes | L3 changes | Total |
| ------------ | -------------: | -------------- | ----------------------: | ---------: | ---------: | ----: |
| W0           |   1 base-event | Target-centred |              0.0056396% |       0/10 |       0/10 |  0/20 |
| Near sham    | 11 base-events | +20 bases      |              0.0425843% |       1/10 |       0/10 |  1/20 |
| Distant sham | 11 base-events | +100 bases     |              0.0444585% |       0/10 |       0/10 |  0/20 |
| PM5          | 11 base-events | Target-centred |              0.0511619% |      10/10 |      10/10 | 20/20 |

## Consolidated interpretation

The comparison established four properties.

### Context dependence

The isolated W0 target event was insufficient.

### Spatial specificity

A comparably strong perturbation 100 bases away caused no target changes.

### Short-range contextual spillover

The +20-base sham produced one nearby target change.

### Cross-locus reproducibility

Target-centred PM5 altered all 20 attacked ALT-supporting reads across two independent loci.

---

# 14. Hybrid BAM and Variant-Level Consequences

## Objective

The attacked reads were inserted into controlled background cohorts to determine whether local read-level manipulation affected downstream variant evidence.

## ALT support

| Locus | Clean hybrid ALT support | PM5 hybrid ALT support | Reduction |
| ----- | -----------------------: | ---------------------: | --------: |
| L2    |                       19 |                      9 |        10 |
| L3    |                       18 |                      8 |        10 |

## Variant quality

Approximate QUAL reductions were:

* L2: 41.22%;
* L3: 32.34%.

## Genotype outcome

The variant caller continued to return heterozygous genotypes in the controlled hybrid cohorts.

## Finding

PM5 substantially reduced ALT evidence and variant confidence but did not completely flip the cohort-level genotype.

## Interpretation

The demonstrated consequence is:

```text
Variant-evidence suppression and confidence degradation
```

rather than:

```text
Complete genotype replacement
```

This distinction must be preserved in all publications and presentations.

---

# 15. Bonito Cross-Model Transferability

## Objective

The planned extension was to test:

```text
Clean and PM5 POD5
        ↓
Bonito basecalling
        ↓
Alignment
        ↓
Target-state comparison
```

## Platform outcome

The available machine used Linux AArch64.

PyTorch 2.10.0 with CUDA 13.0 installed and successfully completed a basic GPU tensor calculation.

However:

* the NVIDIA GB10 reported compute capability 12.1;
* the tested PyTorch build officially declared support only through capability 12.0;
* Bonito 1.1.0 required `ont-koi==0.6.5`;
* no compatible `ont-koi` distribution was available for Linux AArch64.

The installation therefore stopped with:

```text
No matching distribution found for ont-koi==0.6.5
```

## Interpretation

Bonito transferability was not experimentally evaluated.

This must not be interpreted as:

* attack failure against Bonito;
* Bonito resistance;
* evidence that PM5 is Dorado-specific.

The experiment was blocked by platform compatibility.

## Future requirement

A valid Bonito comparison requires an officially supported Linux x86-64 NVIDIA CUDA environment using the preserved L2 and L3 clean and PM5 POD5 inputs.

---

# 16. Main Scientific Findings

## Finding 1 — Raw-signal perturbation produces a reproducible dose response

Increasing Gaussian perturbation strength caused progressively greater sequence divergence and confidence loss.

This result reproduced across:

* multiple noise strengths;
* multiple seeds;
* 100-read experiments;
* 1,000-read experiments.

## Finding 2 — Basecalling success does not guarantee sequence integrity

Dorado completed successfully even when basecalled sequences were substantially altered.

Pipeline completion alone is therefore not a sufficient integrity check.

## Finding 3 — Most perturbed reads remain genomically alignable

Even after sequence degradation, most reads retained valid genomic mappings.

This allows corrupted sequence evidence to proceed into downstream analysis.

## Finding 4 — Local target evidence can be manipulated without destroying mapping

PM5 changed the target state of all 20 attacked ALT-supporting reads while all primary reads remained mapped at MAPQ 60.

## Finding 5 — Successful targeting requires local context

The isolated W0 event produced no target changes.

The attack depended on a wider signal neighbourhood.

## Finding 6 — The effect is spatially specific

The +100-base distant sham caused no target changes despite modifying a comparable fraction of the signal.

## Finding 7 — Very nearby perturbations may create contextual spillover

The +20-base sham caused one target change, suggesting that local basecalling influence extends beyond exact signal-event boundaries.

## Finding 8 — The targeted result reproduces across loci

The PM5 effect reproduced at two independent loci on chromosomes 1 and 4.

## Finding 9 — Read-level evidence manipulation affects variant confidence

Hybrid ALT support fell by ten reads at both loci, and variant QUAL decreased by approximately 32–41%.

## Finding 10 — Complete genotype flipping was not demonstrated

The controlled hybrid calls remained heterozygous.

The defensible claim is evidence suppression and confidence degradation, not complete genotype conversion.

---

# 17. Security Interpretation

The A2 GPU results demonstrate a generation-time integrity risk in machine-learning genomic pipelines.

The attack does not need to crash the basecaller or prevent alignment.

Instead, it can produce:

```text
Plausible, mapped and processable reads
with altered local genomic evidence
```

This is important because conventional operational monitoring often checks:

* whether basecalling completed;
* whether a BAM was generated;
* whether reads mapped;
* whether the file passed structural validation.

All of those conditions may remain true while the nucleotide evidence has changed.

Within GenoPhylax, A2 therefore informs the pipeline-exposure component of lifecycle risk.

The resulting corrupted or weakened variant evidence can then enter:

* variant databases;
* clinical interpretation systems;
* genomic storage;
* downstream sharing infrastructure;
* kinship-linked platforms.

---

# 18. Claims Supported by the Evidence

The following claims are supported.

1. Controlled Nanopore raw-signal perturbations can systematically alter Dorado basecalling output.

2. Gaussian perturbation produces a reproducible dose response across seeds and sample sizes.

3. Many altered reads remain successfully mapped.

4. A localized target-centred PM5 perturbation changed all 20 attacked ALT-supporting reads across two independent loci.

5. All primary PM5-attacked reads remained mapped at MAPQ 60.

6. The successful target effect required local signal context.

7. A comparable perturbation 100 bases away did not affect the target.

8. Targeted evidence suppression reduced hybrid ALT support and variant QUAL.

---

# 19. Claims Not Supported

The following claims must not be made.

1. The attack always flips a final genotype.

2. The attack has been shown to cause a clinical misdiagnosis.

3. The attack transfers to Bonito or other basecallers.

4. The attack is model-agnostic.

5. The attack works at arbitrary genomic loci.

6. The tested interpolation method represents a naturally occurring biological signal process.

7. The experiments demonstrate compromise of a deployed clinical sequencing system.

8. The two selected cross-locus variants are clinically pathogenic.

---

# 20. Limitations

The primary limitations are:

* Dorado was the only experimentally evaluated basecaller;
* Bonito could not be installed on the available AArch64 platform;
* only two independent cross-locus replication sites were used;
* the targeted cohorts contained ten parent reads per locus;
* the attack used controlled synthetic signal interpolation;
* the hybrid genotypes remained heterozygous;
* clinical significance was not established;
* physical wet-lab attack delivery was not evaluated;
* the experiments used one sequencing chemistry and one Dorado HAC model;
* the effective contextual influence radius was not fully mapped;
* attack success across additional models, chemistries and variant classes remains unknown.

---

# 21. Recommended Defensive Implications

The findings suggest that genomic pipeline integrity controls should include more than file-validity and mapping checks.

Potential defensive directions include:

* raw-signal provenance tracking;
* cryptographic linkage between POD5, basecalls, alignments and VCFs;
* signal-level anomaly detection;
* cross-basecaller consistency checks;
* local sequence-confidence auditing;
* unexpected CIGAR-transition detection;
* parent-read-aware split-output tracking;
* variant-evidence consistency checks;
* comparison against orthogonal sequencing or validation methods;
* lifecycle risk scoring through the GenoPhylax Risk Index.

---

# 22. Relationship to A3

A2 established experimentally observable sequence and variant-evidence changes.

A3 should now determine how such error classes could affect clinical interpretation.

The A3 mapping should follow:

```text
Observed A2 error type
        ↓
Variant representation change
        ↓
Gene and transcript annotation
        ↓
ClinVar or pharmacogenomic relevance
        ↓
Potential interpretation consequence
```

A3 must clearly separate:

* experimentally demonstrated errors;
* annotation-derived consequences;
* hypothetical clinical scenarios;
* clinically validated outcomes.

Most A3 work can be performed on CPU.

---

# 23. Final Conclusion

The A2 GPU extension demonstrated that controlled alterations to Nanopore raw electrical signal can change machine-learning-derived genomic evidence without necessarily causing obvious pipeline failure.

Whole-read Gaussian perturbation produced a reproducible dose response across seeds and sample sizes.

More importantly, the target-centred PM5 attack altered all 20 attacked ALT-supporting reads across two independent loci while preserving MAPQ 60 primary alignments.

The W0 and distant-sham controls showed that this effect required local context and was spatially specific.

When attacked reads were inserted into controlled hybrid cohorts, ALT support and variant confidence decreased substantially, although the genotype remained heterozygous.

The strongest defensible conclusion is therefore:

```text
Localized raw-signal manipulation can reproducibly suppress target variant
evidence and reduce downstream variant confidence while preserving apparently
normal high-confidence genomic mapping.
```

Cross-model transferability remains unresolved because Bonito’s required backend was unavailable for Linux AArch64.

A2 is now complete and ready to support:

* publication tables and figures;
* A3 clinical consequence mapping;
* Module C lifecycle synthesis;
* GenoPhylax Risk Index development.
