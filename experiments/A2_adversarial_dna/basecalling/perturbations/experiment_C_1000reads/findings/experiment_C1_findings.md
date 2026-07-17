# Experiment C1 — 1,000-Read Gaussian Perturbation Scale Validation

## Objective

Experiment C1 tested whether the Gaussian raw-signal dose-response observed in the original 100-read prototype remained detectable after increasing the experiment to 1,000 paired Oxford Nanopore reads.

The experiment evaluated the same 1,000 HG002 raw reads under four conditions:

- CLEAN: no signal modification
- GN01: Gaussian noise with sigma fraction 0.01
- GN05: Gaussian noise with sigma fraction 0.05
- GN10: Gaussian noise with sigma fraction 0.10

All perturbed conditions used random seed 42.

The primary objective was to determine whether increasing Gaussian raw-signal perturbation caused reproducible degradation in basecalled sequence identity and confidence while preserving structurally valid POD5 and BAM files and apparently successful Dorado execution.

---

## Experimental setup

### Dataset

```text
Sample:
HG002 / GM24385

Source POD5:
PAO89685_pass__2264ba8c_afee3a87_0.pod5

Source POD5 reads:
4,000

Experiment C1 subset:
First 1,000 reads
```

### Basecaller

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

### Conditions

```text
CLEAN:
sigma fraction = 0.00

GN01:
sigma fraction = 0.01
seed = 42

GN05:
sigma fraction = 0.05
seed = 42

GN10:
sigma fraction = 0.10
seed = 42
```

---

## Clean-control validation

A clean 1,000-read POD5 subset was created without modifying the raw signal.

Validation results:

```text
POD5 reads:              1,000
Unique read IDs:         1,000
Duplicate read IDs:      0
Read-ID validation:      PASS
```

Dorado successfully basecalled all 1,000 physical reads.

Operational clean BAM:

```text
Dorado simplex reads basecalled: 1,000
Operational BAM records:         1,010
Unmapped records:                1,010
Mapped records:                  0
samtools quickcheck:             PASS
Dorado exit status:              0
```

The operational BAM contained 10 split parent reads, each represented by two child records.

```text
Split parent groups:       10
Split child records:       20
Additional BAM records:    10
Clean split-parent rate:   1.0%
```

A separate parent-normalized analysis BAM was created by grouping child records using the Dorado `pi` tag, ordering children using `sp`, concatenating child sequences and quality values, and restoring the original parent read ID.

```text
Parent-normalized records: 1,000
Unique parent IDs:         1,000
POD5-only IDs:             0
BAM-only IDs:              0
Duplicate parent IDs:      0
samtools quickcheck:       PASS
```

The original 1,010-record BAM was preserved as the authoritative operational output.

---

## Signal-level perturbation results

All three perturbation conditions:

* processed exactly 1,000 reads;
* preserved all 1,000 read IDs;
* preserved read-ID order;
* changed the raw signal in all 1,000 reads;
* preserved each read's signal-sample count;
* caused zero clipping.

| Condition | Changed samples | Changed fraction | Mean noise sigma | Mean absolute change | Clipped samples |
| --------- | ---------------: | ---------------: | ---------------: | -------------------: | ---------------: |
| GN01      |       42,285,148 |     0.7095886325 |         1.401094 |             1.085785 |                0 |
| GN05      |       56,049,090 |     0.9405618523 |         7.005469 |             5.550279 |                0 |
| GN10      |       57,819,286 |     0.9702675768 |        14.010939 |            11.107970 |                0 |

The signal-level perturbation magnitude increased monotonically from GN01 to GN05 to GN10.

---

## Dorado execution results

Dorado successfully processed all 1,000 physical reads in every condition.

| Condition | Simplex reads basecalled | BAM records | Exit status | Quickcheck |
| --------- | ------------------------: | -----------: | -----------: | ---------- |
| CLEAN     |                     1,000 |        1,010 |            0 | PASS       |
| GN01      |                     1,000 |        1,009 |            0 | PASS       |
| GN05      |                     1,000 |        1,013 |            0 | PASS       |
| GN10      |                     1,000 |        1,004 |            0 | PASS       |

Therefore, successful Dorado execution and valid BAM structure did not imply that the genomic sequence content remained unchanged.

---

## Split-read behavior

Dorado split-read behavior differed across conditions.

| Condition | Split parents | Split-parent rate | Extra BAM records |
| --------- | -------------: | ------------------: | -------------------: |
| CLEAN     |             10 |                1.0% |                   10 |
| GN01      |              9 |                0.9% |                    9 |
| GN05      |             13 |                1.3% |                   13 |
| GN10      |              4 |                0.4% |                    4 |

The split-parent rate was not monotonic with Gaussian-noise magnitude.

This indicates that raw-signal perturbation can alter Dorado segmentation decisions, but the segmentation response appears nonlinear and read-dependent rather than following the same monotonic dose-response as sequence degradation.

All operational BAM files were preserved unchanged. Separate parent-normalized BAMs containing exactly 1,000 parent records were used for paired sequence analysis.

---

## Paired basecall comparison

All 1,000 clean parent reads were matched successfully against all 1,000 perturbed parent reads for each condition.

```text
Clean-only IDs:       0
Perturbed-only IDs:   0
Paired reads:         1,000 per condition
```

### Primary results

| Condition | Changed reads | Exact matches | Mean identity | Mean edit distance | Mean normalized edit distance | Mean Q-score change |
| --------- | --------------: | --------------: | --------------: | --------------------: | -------------------------------: | --------------------: |
| GN01      |             936 |               64 |       98.523429% |                 39.343 |                     0.0147657120 |              -0.117883 |
| GN05      |             989 |               11 |       96.091928% |                113.241 |                     0.0390807207 |              -2.546585 |
| GN10      |             999 |                1 |       92.771583% |                274.567 |                     0.0722841680 |             -10.673997 |

The three principal degradation metrics were monotonic:

```text
Mean sequence identity:
GN01 > GN05 > GN10

Mean edit distance:
GN01 < GN05 < GN10

Mean normalized edit distance:
GN01 < GN05 < GN10

Mean Q-score change:
GN01 > GN05 > GN10
```

At GN10, 999 of 1,000 reads changed relative to their clean basecalls.

---

## Sequence-edit composition

### GN01

```text
Total edit distance:      39,343
Substitutions:            13,226
Insertions:                11,349
Deletions:                 14,768
Median edit distance:      13
P95 edit distance:         133.15
```

### GN05

```text
Total edit distance:      113,241
Substitutions:             34,963
Insertions:                 30,115
Deletions:                  48,163
Median edit distance:       43
P95 edit distance:          424.30
```

### GN10

```text
Total edit distance:      274,567
Substitutions:              92,612
Insertions:                  73,854
Deletions:                  108,101
Median edit distance:        119
P95 edit distance:           1,116.25
```

Substitutions, insertions, and deletions all increased substantially as perturbation magnitude increased.

---

## Read-length effects

| Condition | Mean clean length | Mean perturbed length | Mean length change |
| --------- | -------------------: | ------------------------: | ---------------------: |
| GN01      |             4,939.174 |                4,935.755 |                 -3.419 |
| GN05      |             4,939.174 |                4,921.126 |                -18.048 |
| GN10      |             4,939.174 |                4,904.927 |                -34.247 |

Although mean read length decreased with increasing noise, the magnitude of read-length change remained small relative to the average read length.

The perturbations therefore did not simply destroy or truncate the reads. They generated reads of broadly plausible length while substantially altering their nucleotide content and confidence.

---

## Confidence degradation

| Condition | Mean clean Q-score | Mean perturbed Q-score | Mean Q-score change | Reads with Q-score decrease |
| --------- | --------------------: | --------------------------: | ---------------------: | -----------------------------: |
| GN01      |             34.204719 |                   34.086836 |               -0.117883 |                             719 |
| GN05      |             34.204719 |                   31.658133 |               -2.546585 |                             960 |
| GN10      |             34.204719 |                   23.530722 |              -10.673997 |                             981 |

At GN10:

```text
Reads with Q-score drop >= 5:   927
Reads with Q-score drop >= 10:  621
```

This demonstrates severe confidence degradation across most of the read population.

---

## Severe-outlier analysis

| Condition | Edit distance >=100 | Edit distance >=500 | Edit distance >=1000 | Identity below 95% |
| --------- | ---------------------: | ----------------------: | -----------------------: | ---------------------: |
| GN01      |                     72 |                      10 |                        4 |                     41 |
| GN05      |                    268 |                      39 |                       12 |                    151 |
| GN10      |                    557 |                     142 |                       57 |                    488 |

At GN10:

* more than half of reads had at least 100 edits;
* 142 reads had at least 500 edits;
* 57 reads had at least 1,000 edits;
* 488 reads fell below 95% sequence identity.

The degradation was therefore not limited to a small number of anomalous reads.

---

## Bootstrap confidence intervals

Mean sequence-identity bootstrap 95% confidence intervals:

```text
GN01:
98.159869% to 98.833774%

GN05:
95.501841% to 96.644921%

GN10:
92.248792% to 93.250175%
```

The confidence intervals did not overlap, supporting clear separation between the three perturbation levels.

Mean edit-distance bootstrap 95% confidence intervals:

```text
GN01:
32.802 to 46.770

GN05:
99.443 to 128.721

GN10:
247.355 to 303.829
```

Mean Q-score-change bootstrap 95% confidence intervals:

```text
GN01:
-0.147689 to -0.087433

GN05:
-2.652466 to -2.443728

GN10:
-10.920221 to -10.425193
```

---

## Paired statistical comparisons

The paired read-level comparisons were overwhelmingly directional.

### GN01 versus GN05

```text
Reads with higher edit distance at GN05: 964
Reads with lower edit distance at GN05:  18
Ties:                                     18

Mean edit-distance increase:
+73.898

Sign-test p-value:
4.80e-258
```

### GN05 versus GN10

```text
Reads with higher edit distance at GN10: 975
Reads with lower edit distance at GN10:  21
Ties:                                      4

Mean edit-distance increase:
+161.326

Sign-test p-value:
4.44e-257
```

### GN01 versus GN10

```text
Reads with higher edit distance at GN10: 988
Reads with lower edit distance at GN10:   8
Ties:                                      4

Mean edit-distance increase:
+235.224

Sign-test p-value:
7.03e-281
```

The result was therefore driven by consistent degradation across nearly the entire paired-read population rather than by only a few extreme observations.

---

## Software correction discovered during Experiment C1

The existing split-read collapse utility initially failed while copying Dorado's `mv` move-table tag from child records into a synthetic parent record.

The `mv` tag is represented as a BAM `B`-array and describes the signal-to-base movement of an individual Dorado child record. It is not valid after concatenating multiple child sequences.

The collapse utility was corrected to:

* omit `pi`, `sp`, `mv`, `ts`, and `ns` from synthetic parent records;
* omit BAM array tags from collapsed records;
* preserve valid scalar metadata where possible;
* leave all unsplit operational records unchanged;
* preserve the original operational BAM;
* produce a separate parent-normalized analysis BAM.

The corrected implementation successfully normalized all four conditions to exactly 1,000 parent records.

---

## Main finding

Increasing Gaussian raw-signal perturbation caused a monotonic and statistically decisive degradation in Oxford Nanopore basecalling accuracy and confidence across 1,000 paired HG002 reads.

The effect included:

* lower sequence identity;
* higher raw and normalized edit distance;
* more substitutions, insertions, and deletions;
* increased read shortening;
* lower basecall Q-scores;
* more severe outlier reads.

Despite this corruption:

* every POD5 remained structurally valid;
* every Dorado run exited successfully;
* every physical read was processed;
* every BAM passed structural validation;
* no signal clipping occurred.

Therefore:

> Structurally valid sequencing files and apparently successful basecalling do not guarantee genomic integrity.

---

## Experiment C1 conclusion

The 100-read Gaussian-noise dose-response from Experiment A remained present and became more statistically robust after scaling to 1,000 paired reads.

Experiment C1 confirms that the result is not explained by the small size of the original prototype subset.

The next replication stage should evaluate the 1,000-read workflow across independent Gaussian-noise seeds.

Recommended next experiment:

```text
Experiment C2:
1,000 reads
GN01, GN05, GN10
Seeds 1, 2, and 3
```

This will test whether the scaled dose-response remains stable across independent perturbation realizations.

---

## GenoPhylax relevance

Experiment C1 strengthens:

```text
GRI Dimension D7:
Pipeline Exposure Risk
```

The experiment demonstrates the following lifecycle path:

```text
Raw-signal manipulation
        ↓
Plausible but corrupted basecalls
        ↓
Potential alignment and variant errors
        ↓
Structurally valid genomic records
        ↓
Storage and downstream sharing
```

The result supports the core GenoPhylax claim that successful pipeline execution alone is not a sufficient genomic-integrity guarantee.
