# A2 GPU — Numerical Results Summary

## Purpose

This document consolidates the primary numerical results from the Project GenoPhylax A2 Nanopore GPU experiments.

It is intended to support:

* publication tables;
* presentation slides;
* final report writing;
* figure generation;
* claims verification.

---

# 1. Experimental Platform

| Item                 | Value                                |
| -------------------- | ------------------------------------ |
| Dataset              | HG002 / GM24385                      |
| Sequencing chemistry | ONT R10.4.1 E8.2 400 bps             |
| Basecaller           | Dorado 2.1.0                         |
| Model                | `dna_r10.4.1_e8.2_400bps_hac@v6.0.0` |
| GPU system           | NVIDIA GB10                          |
| System architecture  | Linux AArch64                        |
| CUDA environment     | CUDA 13.0                            |
| Primary reference    | GIAB GRCh38 no-alt                   |

---

# 2. Clean Baseline

## 100-read clean control

| Metric                  |                        Result |
| ----------------------- | ----------------------------: |
| Physical reads          |                           100 |
| Mean Q-score            |                     35.026829 |
| Basecalling time        |                 27.62 seconds |
| Approximate throughput  | 1.7037 million samples/second |
| Approximate peak memory |                        800 MB |
| BAM integrity           |                          PASS |

## Full clean GPU run

| Metric                   |          Result |
| ------------------------ | --------------: |
| BAM records              |          12,703 |
| Simplex reads basecalled |          11,999 |
| Dorado pipeline time     | 106.779 seconds |

---

# 3. Experiment A — 100-Read Gaussian Dose Response

Seed:

```text
42
```

| Condition | Sigma fraction | Changed reads | Mean identity | Mean edit distance | Mean Q-score change | Mean length change |
| --------- | -------------: | ------------: | ------------: | -----------------: | ------------------: | -----------------: |
| GN01      |           0.01 |        95/100 |      98.7903% |              14.19 |              -0.064 |              +0.88 |
| GN05      |           0.05 |       100/100 |      96.9033% |              43.40 |              -2.250 |              -0.23 |
| GN10      |           0.10 |       100/100 |      93.8863% |             112.67 |             -10.111 |              -1.02 |

## Distribution summary

| Condition | Median identity | Median edit distance | P95 edit distance |
| --------- | --------------: | -------------------: | ----------------: |
| GN01      |        99.5177% |                  9.0 |             45.05 |
| GN05      |        98.4688% |                 28.5 |            129.10 |
| GN10      |        95.3069% |                 82.0 |            319.15 |

## Main numerical pattern

```text
Increasing perturbation strength
        ↓
Lower sequence identity
Higher edit distance
Greater Q-score loss
```

---

# 4. Experiment B — 100-Read Multi-Seed Replication

Seeds:

```text
1, 2, 3, 4, 5
```

Total perturbed runs:

```text
15
```

| Condition | Mean identity range | Mean edit-distance range | Mean Q-score-change range |
| --------- | ------------------: | -----------------------: | ------------------------: |
| GN01      |    98.2933–99.2379% |              12.48–17.36 |    -0.184145 to -0.083067 |
| GN05      |    97.1493–97.6866% |              40.71–44.12 |    -2.373500 to -2.154335 |
| GN10      |    93.5584–93.9454% |            112.38–115.20 |  -10.434556 to -10.270288 |

## Split-read observation

| Condition   | Physical reads | BAM records |
| ----------- | -------------: | ----------: |
| GN01 seed 5 |            100 |         101 |

This was resolved through parent-read-aware analysis.

---

# 5. Experiment C — 1,000-Read Scale Validation

## C1 design

| Item           | Value                   |
| -------------- | ----------------------- |
| Physical reads | 1,000                   |
| Conditions     | CLEAN, GN01, GN05, GN10 |
| Seed           | 42                      |

## Main observations

| Observation                      | Result |
| -------------------------------- | -----: |
| Dorado runs completed            |    4/4 |
| GN10 reads below 95% identity    |    488 |
| Dose-response ordering preserved |    Yes |
| Increasing Q-score degradation   |    Yes |
| Increasing edit distance         |    Yes |
| Increasing severe outliers       |    Yes |

## C2 design

| Item                         | Value            |
| ---------------------------- | ---------------- |
| Physical reads per condition | 1,000            |
| Noise levels                 | GN01, GN05, GN10 |
| Seeds                        | 1, 2, 3          |
| Total perturbed runs         | 9                |

## C2 conclusion

The dose-response pattern remained stable across all nine runs.

---

# 6. Experiment D — Alignment Consequences

## Overall mapping

| Metric                 |      Approximate result |
| ---------------------- | ----------------------: |
| Mapped-read percentage |               About 97% |
| Mean mapped MAPQ       | Approximately 55.3–55.4 |

## Paired alignment effects

Observed perturbation consequences included:

* reduced MAPQ;
* changed CIGAR structure;
* changed alignment position;
* altered primary alignment confidence;
* threshold-level losses at MAPQ 20, 30 and 60.

Example result:

| Metric                                                        | Result |
| ------------------------------------------------------------- | -----: |
| Reads losing at least 10 MAPQ points in one seed-42 condition |     27 |

## Multi-seed mean MAPQ changes

| Perturbation level | Approximate mean MAPQ change |
| ------------------ | ---------------------------: |
| GN01               |                       +0.001 |
| GN05               |                       -0.110 |
| GN10               |                       -0.586 |

The aggregate means were small because most reads remained stably mapped, while a smaller subset experienced stronger local effects.

---

# 7. Experiment E — Original Targeted Locus

## Original locus

```text
chr20:10003468
```

## Parent-read composition

| State    | Parent reads |
| -------- | -----------: |
| ALT      |            6 |
| REF      |            2 |
| Deletion |            3 |
| Total    |           11 |

Dorado produced 13 records from 11 physical parent reads because of split-read output.

---

# 8. Experiment E2 — Target-Window Strength Series

| Condition | Context bases | Changed signal samples | Changed fraction | ALT | REF | Deletion | Other |
| --------- | ------------: | ---------------------: | ---------------: | --: | --: | -------: | ----: |
| W0        |             0 |                    280 |       0.0066173% |   6 |   2 |        3 |     0 |
| PM2       |             2 |                    776 |      0.01833939% |   5 |   2 |        1 |     3 |
| PM10      |            10 |                  2,982 |       0.0704743% |   5 |   1 |        4 |     1 |
| PM20      |            20 |                  5,862 |        0.138538% |   5 |   1 |        4 |     1 |

All conditions completed successfully.

---

# 9. Experiment E — Cross-Locus PM5 Replication

## Loci

| Locus | Variant           |
| ----- | ----------------- |
| L2    | chr1:20061156 A>T |
| L3    | chr4:40028853 A>G |

## Signal modification

| Locus | Changed signal samples | Percentage of total signal |
| ----- | ---------------------: | -------------------------: |
| L2    |                  1,438 |                 0.0490066% |
| L3    |                  1,592 |                 0.0532784% |

## Target-state result

| Locus    | Clean ALT reads | ALT retained | ALT lost |
| -------- | --------------: | -----------: | -------: |
| L2       |              10 |            0 |       10 |
| L3       |              10 |            0 |       10 |
| Combined |              20 |            0 |       20 |

## Detailed transitions

| Locus    | ALT→REF | ALT→Deletion | ALT→Other | ALT retained |
| -------- | ------: | -----------: | --------: | -----------: |
| L2       |       1 |            7 |         2 |            0 |
| L3       |       3 |            5 |         2 |            0 |
| Combined |       4 |           12 |         4 |            0 |

## Mapping preservation

| Metric                         | Result |
| ------------------------------ | -----: |
| Primary reads remaining mapped |  20/20 |
| Primary-read MAPQ              |     60 |
| ALT-loss rate                  |   100% |

---

# 10. Experiment E — Specificity Controls

| Condition    |         Window | Placement      | Combined signal changed | L2 changes | L3 changes | Total target changes |
| ------------ | -------------: | -------------- | ----------------------: | ---------: | ---------: | -------------------: |
| W0           |   1 base-event | Target-centred |              0.0056396% |       0/10 |       0/10 |                 0/20 |
| Near sham    | 11 base-events | +20 bases      |              0.0425843% |       1/10 |       0/10 |                 1/20 |
| Distant sham | 11 base-events | +100 bases     |              0.0444585% |       0/10 |       0/10 |                 0/20 |
| PM5          | 11 base-events | Target-centred |              0.0511619% |      10/10 |      10/10 |                20/20 |

## Control interpretation

| Question                                                     | Result                    |
| ------------------------------------------------------------ | ------------------------- |
| Is one isolated target event sufficient?                     | No                        |
| Can a nearby perturbation influence the target?              | Rarely; 1/20 at +20 bases |
| Does comparable corruption 100 bases away affect the target? | No; 0/20                  |
| Does target-centred PM5 reproduce across loci?               | Yes; 20/20                |

---

# 11. Experiment E — Hybrid Variant Consequence

## ALT support

| Locus | Clean ALT support | PM5 ALT support | Absolute reduction | Relative reduction |
| ----- | ----------------: | --------------: | -----------------: | -----------------: |
| L2    |                19 |               9 |                 10 |             52.63% |
| L3    |                18 |               8 |                 10 |             55.56% |

## Variant-confidence change

| Locus | Approximate QUAL reduction |
| ----- | -------------------------: |
| L2    |                     41.22% |
| L3    |                     32.34% |

## Genotype result

| Locus | Clean genotype | PM5 genotype |
| ----- | -------------- | ------------ |
| L2    | Heterozygous   | Heterozygous |
| L3    | Heterozygous   | Heterozygous |

## Correct interpretation

```text
Demonstrated:
Variant-evidence suppression
Variant-confidence reduction

Not demonstrated:
Complete genotype flipping
```

---

# 12. Bonito Feasibility

| Item                       | Result           |
| -------------------------- | ---------------- |
| Machine architecture       | Linux AArch64    |
| PyTorch installation       | Successful       |
| PyTorch CUDA tensor test   | PASS             |
| GPU detected               | NVIDIA GB10      |
| GPU compute capability     | 12.1             |
| PyTorch declared support   | Up to 12.0       |
| Bonito release attempted   | 1.1.0            |
| Required backend           | `ont-koi==0.6.5` |
| ARM64 backend availability | Not available    |
| Bonito experiment          | Not executed     |

The result was a platform compatibility limitation, not an attack failure.

---

# 13. Final Numerical Conclusions

| Scientific question                           | Numerical answer                                           |
| --------------------------------------------- | ---------------------------------------------------------- |
| Did Gaussian noise produce a dose response?   | Yes, across GN01, GN05 and GN10                            |
| Did the dose response replicate across seeds? | Yes, across five 100-read seeds and three 1,000-read seeds |
| Did most reads remain alignable?              | Yes, approximately 97% mapping                             |
| Did PM5 suppress target ALT evidence?         | Yes, 20/20 attacked reads lost ALT classification          |
| Did mapping remain high confidence?           | Yes, 20/20 primary reads remained MAPQ 60                  |
| Did W0 cause target changes?                  | No, 0/20                                                   |
| Did the +100-base sham cause target changes?  | No, 0/20                                                   |
| Did the +20-base sham cause target changes?   | Yes, 1/20                                                  |
| Did hybrid ALT support decrease?              | Yes, by 10 reads at both loci                              |
| Did variant QUAL decrease?                    | Yes, approximately 32–41%                                  |
| Did the final genotype flip?                  | No                                                         |
| Was Bonito transfer tested?                   | No, platform incompatible                                  |

---

# 14. Strongest Quantitative Statement

```text
A target-centred PM5 perturbation modifying approximately 0.05% of the
raw signal caused 20/20 attacked ALT-supporting reads across two independent
loci to lose ALT classification, while all 20 primary reads retained MAPQ 60.
```
