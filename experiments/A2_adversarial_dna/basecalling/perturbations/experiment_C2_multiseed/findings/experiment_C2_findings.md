# Experiment C2 — 1,000-Read Multi-Seed Gaussian Perturbation Replication

## Objective

Experiment C2 tested whether the 1,000-read Gaussian raw-signal perturbation dose-response observed in Experiment C1 remained reproducible across independent random-noise realizations.

The same 1,000 HG002 Oxford Nanopore reads were evaluated at three perturbation levels:

- GN01: Gaussian noise with sigma fraction 0.01
- GN05: Gaussian noise with sigma fraction 0.05
- GN10: Gaussian noise with sigma fraction 0.10

Three independent random seeds were evaluated:

- seed 1
- seed 2
- seed 3

This produced nine perturbed POD5, Dorado basecalling, parent-normalization, and paired-comparison conditions.

The clean 1,000-read control from Experiment C1 was reused unchanged.

---

## Experimental design

```text
Physical reads per condition:
1,000

Perturbation levels:
GN01
GN05
GN10

Seeds:
1
2
3

Total perturbed conditions:
9

Total paired clean-versus-perturbed comparisons:
9,000 reads
```

### Basecalling environment

```text
Dorado:
2.1.0+48ab35d

Model:
dna_r10.4.1_e8.2_400bps_hac@v6.0.0

Device:
NVIDIA GB10

CUDA device:
cuda:0
```

---

## Validation

All nine perturbed POD5 files:

* contained exactly 1,000 reads;
* contained 1,000 unique read IDs;
* preserved clean-read ordering;
* preserved signal-sample counts;
* changed all 1,000 raw signals;
* caused zero signal clipping.

All nine Dorado runs:

* successfully processed all 1,000 physical reads;
* exited successfully;
* produced structurally valid BAM files;
* passed `samtools quickcheck`.

All nine parent-normalized BAM files:

* contained exactly 1,000 records;
* contained 1,000 unique parent IDs;
* contained zero missing POD5 parent IDs;
* contained zero additional BAM parent IDs;
* passed `samtools quickcheck`.

All nine paired comparisons:

* matched exactly 1,000 clean and perturbed parent reads;
* had zero clean-only reads;
* had zero perturbed-only reads.

---

## Per-run results

| Condition | Seed | Changed reads | Mean identity | Mean edit distance | Mean normalized edit distance | Mean Q-score change |
| --------- | ---: | -------------: | ---------------: | --------------------: | --------------------------------: | ----------------------: |
| GN01      |    1 |            943 |       98.594994% |                 40.064 |                     0.0140500598 |               -0.109944 |
| GN01      |    2 |            942 |       98.403965% |                 41.277 |                     0.0159603452 |               -0.106692 |
| GN01      |    3 |            923 |       98.514927% |                 39.625 |                     0.0148507265 |               -0.124200 |
| GN05      |    1 |            993 |       96.169877% |                112.845 |                     0.0383012338 |               -2.500241 |
| GN05      |    2 |            991 |       96.218358% |                112.809 |                     0.0378164210 |               -2.525635 |
| GN05      |    3 |            993 |       96.230425% |                112.719 |                     0.0376957481 |               -2.573565 |
| GN10      |    1 |            999 |       92.743084% |                274.774 |                     0.0725691609 |              -10.714170 |
| GN10      |    2 |          1,000 |       92.828144% |                272.995 |                     0.0717185570 |              -10.738176 |
| GN10      |    3 |            999 |       92.671354% |                276.151 |                     0.0732864604 |              -10.732645 |

---

## Per-level aggregate results

### GN01

```text
Seeds:
3

Mean changed-read fraction:
0.936000

Mean sequence identity:
98.504629%

Sequence-identity SD:
0.095930

Mean edit distance:
40.322

Edit-distance SD:
0.855686

Mean normalized edit distance:
0.0149537105

Mean Q-score change:
-0.113612

Mean length change:
-3.990333 bases
```

### GN05

```text
Seeds:
3

Mean changed-read fraction:
0.992333

Mean sequence identity:
96.206220%

Sequence-identity SD:
0.032047

Mean edit distance:
112.791

Edit-distance SD:
0.064900

Mean normalized edit distance:
0.0379378010

Mean Q-score change:
-2.533147

Mean length change:
-19.251667 bases
```

### GN10

```text
Seeds:
3

Mean changed-read fraction:
0.999333

Mean sequence identity:
92.747527%

Sequence-identity SD:
0.078489

Mean edit distance:
274.640

Edit-distance SD:
1.582261

Mean normalized edit distance:
0.0725247261

Mean Q-score change:
-10.728330

Mean length change:
-37.268333 bases
```

---

## Cross-seed reproducibility

The primary degradation metrics were monotonic in all three seeds.

| Seed | Identity decreased | Edit distance increased | Normalized edit distance increased | Q-score degradation worsened | All primary metrics monotonic |
| ---: | ------------------- | ------------------------- | ------------------------------------- | -------------------------------- | -------------------------------- |
|    1 | True                 | True                       | True                                    | True                               | True                               |
|    2 | True                 | True                       | True                                    | True                               | True                               |
|    3 | True                 | True                       | True                                    | True                               | True                               |

For every seed:

```text
GN01 identity > GN05 identity > GN10 identity

GN01 edit distance < GN05 edit distance < GN10 edit distance

GN01 normalized edit distance

GN05 normalized edit distance

GN10 normalized edit distance

GN01 Q-score change
>
GN05 Q-score change
>
GN10 Q-score change
```

This demonstrates that the scaled dose-response was not dependent on one particular Gaussian-noise realization.

---

## Between-seed variability

Between-seed variability was small relative to the differences between perturbation levels.

### Mean sequence identity

```text
GN01:
98.403965% to 98.594994%

GN05:
96.169877% to 96.230425%

GN10:
92.671354% to 92.828144%
```

### Mean edit distance

```text
GN01:
39.625 to 41.277

GN05:
112.719 to 112.845

GN10:
272.995 to 276.151
```

### Mean Q-score change

```text
GN01:
-0.124200 to -0.106692

GN05:
-2.573565 to -2.500241

GN10:
-10.738176 to -10.714170
```

The narrow cross-seed ranges show that perturbation magnitude had a much stronger effect than random-noise seed.

---

## Signal-level reproducibility

The fraction of changed raw-signal samples was extremely stable across seeds.

### GN01

```text
Seed 1:
0.7095533756

Seed 2:
0.7095819537

Seed 3:
0.7095540804

Mean:
0.7095631366
```

### GN05

```text
Seed 1:
0.9405661650

Seed 2:
0.9405973610

Seed 3:
0.9405738172

Mean:
0.9405791144
```

### GN10

```text
Seed 1:
0.9702373038

Seed 2:
0.9702800451

Seed 3:
0.9702474564

Mean:
0.9702549351
```

No signal clipping occurred in any condition.

---

## Split-read behavior

Split-parent counts differed across conditions and seeds.

| Condition | Seed 1 | Seed 2 | Seed 3 | Mean |
| --------- | -----: | -----: | -----: | ---: |
| GN01      |      9 |     12 |     12 | 11.0 |
| GN05      |      8 |      9 |     12 | 9.67 |
| GN10      |      7 |      4 |      7 |  6.0 |

The clean control contained 10 split-parent groups.

The split-read result did not show a strict monotonic pattern in every individual seed, although the aggregate mean declined from GN01 to GN10.

Split-read behavior should therefore be treated as a nonlinear segmentation response rather than as a primary perturbation dose-response metric.

The primary conclusions are based on sequence identity, edit distance, normalized edit distance, Q-score change, and changed-read fraction.

---

## Main finding

Experiment C2 reproduced the 1,000-read Gaussian raw-signal perturbation dose-response across three independent random seeds.

Increasing perturbation magnitude consistently caused:

* lower basecalled sequence identity;
* higher edit distance;
* higher normalized edit distance;
* lower basecall confidence;
* increased read shortening;
* a higher fraction of changed reads.

The effect was monotonic for every seed and showed low between-seed variability.

Despite this degradation:

* all perturbed POD5 files remained structurally valid;
* no signal clipping occurred;
* Dorado successfully processed every physical read;
* all operational BAM files passed structural validation;
* all parent-normalized BAM files retained the complete read-ID set.

Therefore:

> The observed genomic degradation is reproducible across independent perturbation realizations and remains invisible to ordinary file-integrity and pipeline-success checks.

---

## Experiment C conclusion

Experiment C consisted of two stages.

### Experiment C1

```text
Purpose:
Scale validation

Reads:
1,000

Seed:
42

Status:
COMPLETE
```

### Experiment C2

```text
Purpose:
Multi-seed replication

Reads:
1,000

Seeds:
1, 2, 3

Conditions:
GN01, GN05, GN10

Status:
COMPLETE
```

Together, Experiments C1 and C2 demonstrate that the Gaussian raw-signal dose-response:

* persists after scaling from 100 to 1,000 reads;
* is statistically robust;
* reproduces across independent random seeds;
* affects nearly the entire read population at moderate and high perturbation levels;
* remains undetected by structural file validation and successful basecaller execution.

Experiment C is therefore complete.

---

## GenoPhylax relevance

Experiment C strengthens:

```text
GRI Dimension D7:
Pipeline Exposure Risk
```

The demonstrated lifecycle pathway is:

```text
Raw-signal perturbation
        ↓
Reproducible sequence degradation
        ↓
Successful basecaller execution
        ↓
Structurally valid BAM output
        ↓
Potential alignment and variant errors
        ↓
Storage and downstream sharing
```

The result supports the GenoPhylax principle that genomic-integrity controls must evaluate biological content and provenance rather than relying only on conventional file validity and process exit status.

---

## Next stage

The recommended next stage is alignment-level consequence analysis.

```text
Experiment D:
Align clean and perturbed basecalls to a reference genome

Primary questions:
- Does mapping rate decrease?
- Does mapping quality decrease?
- Do alignment coordinates shift?
- Do mismatch and indel burdens increase?
- Do secondary or supplementary alignments increase?
- Do reads become unmapped?
```
