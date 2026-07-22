# Experiment E2 — Local Signal-Window Strength Series

## Objective

Experiment E2 tested how the size of a localized nanopore raw-signal interpolation window affected basecalling and downstream variant evidence at the truth-backed HG002 heterozygous SNV:

```text
chr20:10003468 C>G
GIAB genotype: 0/1
```

The experiment retained the same:

* locus;
* 10-read clean ALT-supporting attack cohort;
* clean source POD5;
* deterministic linear-interpolation operator;
* Dorado version and HAC v6 model;
* reference and alignment workflow;
* locked 51-record background;
* 63-record hybrid structure;
* bcftools calling procedure.

Only the signal-window radius changed.

---

## Experimental Conditions

```text
CLEAN    no signal modification
E2_W0    target-base-only
E2_PM2   plus/minus 2 bases
E1_PM5   plus/minus 5 bases
E2_PM10  plus/minus 10 bases
E2_PM20  plus/minus 20 bases
```

The previously validated E1 plus/minus 5-base condition was reused as the PM5 reference.

---

## Signal Modification Scale

```text
Condition  Changed samples  Fraction of total POD5 signal
E2_W0      280              0.0000661730
E2_PM2     776              0.0001833939
E1_PM5     1599             0.0003778954
E2_PM10    2982             0.0007047430
E2_PM20    5862             0.0013853800
```

Equivalent percentages:

```text
E2_W0:   approximately 0.0066%
E2_PM2:  approximately 0.0183%
E1_PM5:  approximately 0.0378%
E2_PM10: approximately 0.0705%
E2_PM20: approximately 0.1385%
```

All attack-generation conditions passed:

* read-ID preservation;
* attack-cohort validation;
* outside-window identity;
* untouched-read identity;
* signal-boundary validation.

---

## Dorado Basecalling

All four new E2 POD5 conditions were basecalled using:

```text
Dorado 2.1.0+48ab35d
dna_r10.4.1_e8.2_400bps_hac@v6.0.0
cuda:all
--emit-moves
--no-trim
```

Results:

```text
Condition  Raw reads  BAM records  Status
E2_W0      11         13           PASS
E2_PM2     11         13           PASS
E2_PM10    11         13           PASS
E2_PM20    11         13           PASS
```

The 11 raw reads generated 13 basecall records because two raw parents produced split child records.

---

## Target-State Results

Parent-level target states:

```text
Condition  ALT  REF  Deletion  Other  No coverage  Unmapped
E2_W0      6    2    3         0      0            0
E2_PM2     5    2    1         3      0            0
E1_PM5     5    0    6         0      0            0
E2_PM10    5    1    4         1      0            0
E2_PM20    5    1    4         1      0            0
```

All 11 raw parents remained mapped.

The number of retained ALT-supporting parents decreased from the clean baseline of 10 to:

```text
W0:   6
PM2:  5
PM5:  5
PM10: 5
PM20: 5
```

Different windows produced different mixtures of:

* reference calls;
* deletions;
* non-reference/non-alternate substitutions.

---

## Matched Hybrid Construction

For every condition:

```text
51 identical locked background records
+ 12 condition-specific Dorado replacement records
= 63 hybrid records
```

Every hybrid contained:

```text
63 total records
39 records overlapping the target
```

All hybrid count equations and construction checks passed.

---

## Controlled Variant-Calling Results

```text
Condition  QUAL      INFO/DP  REF depth  ALT depth  GT
CLEAN      138.247   34       18         16         0/1
E2_W0      42.4700   32       20         12         0/1
E2_PM2     34.3677   34       20         14         0/1
E1_PM5     41.4192   29       18         11         0/1
E2_PM10    36.3735   31       19         12         0/1
E2_PM20    40.4288   31       19         12         0/1
```

QUAL reductions relative to the matched clean-Dorado control:

```text
E2_W0:   69.28%
E2_PM2:  75.14%
E1_PM5:  70.04%
E2_PM10: 73.69%
E2_PM20: 70.76%
```

ALT-depth reductions relative to the matched clean-Dorado control:

```text
E2_W0:   16 -> 12
E2_PM2:  16 -> 14
E1_PM5:  16 -> 11
E2_PM10: 16 -> 12
E2_PM20: 16 -> 12
```

The genotype remained:

```text
0/1
```

in every condition.

---

## Main Supported Finding

At this single truth-backed HG002 locus, all tested localized interpolation windows substantially weakened downstream variant confidence.

Even target-base-only interpolation modified only approximately 0.0066% of total POD5 signal but reduced variant QUAL from 138.247 to 42.4700, a 69.28% reduction.

Across the tested conditions, QUAL reductions ranged from approximately:

```text
69.28% to 75.14%
```

while the target remained heterozygous and all attacked reads remained mapped.

---

## Preliminary Window-Response Observation

The observed response across this deterministic single-locus sweep was not monotonic with increasing window size.

However, the current data do not establish that:

* PM2 is inherently stronger than PM5;
* the numerical ranking of window sizes is reproducible;
* the response generally follows a threshold or plateau;
* the differences among QUAL values are statistically meaningful;
* the same pattern will occur at other loci.

The condition ranking is therefore descriptive and preliminary.

A defensible interpretation is:

> At one HG002 heterozygous SNV, substantial variant-confidence loss occurred even for the smallest localized signal window, while increasing the window radius did not produce a monotonic increase in damage. Replication across additional loci and attack realizations is required before treating the apparent ranking or saturation pattern as established.

---

## Determinism and Replication

The current linear-interpolation operator is deterministic.

For fixed:

* signal boundaries;
* clean signal;
* attack cohort;
* interpolation endpoints;

rerunning the same condition produces the same attacked signal.

Therefore, repeating PM5 with a different random seed would not constitute an independent replicate because this operator has no random seed.

Useful replication dimensions are:

### Cross-locus replication

Repeat selected conditions at additional GIAB heterozygous SNVs.

This is the strongest test of whether the result generalizes beyond chr20:10003468.

### Boundary-jitter robustness

Shift mapped signal boundaries by carefully controlled sample or move-chunk offsets.

This tests sensitivity to localization uncertainty, but represents alternative attack realizations rather than random-seed replicates.

### Stochastic operators

Use a genuinely randomized local operator such as seeded Gaussian perturbation or randomized smoothing.

This would be a new operator experiment, not a direct replicate of deterministic interpolation.

### Read-cohort dose experiments

Attack subsets of ALT-supporting reads.

This tests compromise-cohort size rather than window-size reproducibility.

Any future result answering a different experimental question must be labelled as such in the same statement as the result.

---

## Scientific Completion Status

### Operationally complete

```text
E2 signal-window generation: COMPLETE
E2 Dorado basecalling: COMPLETE
E2 alignment: COMPLETE
E2 target-state analysis: COMPLETE
E2 matched hybrid construction: COMPLETE
E2 controlled variant calling: COMPLETE
E2 single-locus descriptive analysis: COMPLETE
```

### Scientifically pending

```text
Window-size ranking validation: PENDING
Cross-locus replication: PENDING
Boundary-jitter robustness: PENDING
Off-target sham control: PENDING
General threshold or plateau claim: NOT ESTABLISHED
```

---

## Recommended Replication Plan

Before running the full five-window grid at multiple new loci:

1. Script reusable locus selection.
2. Select 2–3 additional GIAB heterozygous SNVs with:

   * balanced REF/ALT support;
   * high mapping quality;
   * adequate depth;
   * GIAB high-confidence inclusion;
   * non-homopolymer or less repetitive context;
   * recoverable raw POD5 reads.
3. Run only:

   * W0;
   * PM5.
4. Evaluate whether substantial QUAL and ALT-evidence loss generalizes.
5. Expand to the full window series only if cross-locus evidence supports it.

This cheaper screening design tests generalization before paying the cost of a full condition grid at every locus.

---

## Next Steps

```text
1. Build reusable multi-locus selection script
2. Select 2–3 additional GIAB heterozygous SNVs
3. Run W0 and PM5 at those loci
4. Compare cross-locus effect sizes
5. Run equal-sized off-target sham control
6. Compare targeted PM5 against sham PM5
7. Expand full window sweep if justified
```

---

## Conclusion

> Experiment E2 showed that, at one truth-backed HG002 heterozygous locus, deterministic localized interpolation windows modifying approximately 0.0066% to 0.1385% of total nanopore signal reduced variant QUAL by approximately 69% to 75% while preserving a heterozygous call and full read mapping. The apparent window-size ranking is preliminary and requires cross-locus validation before it can be treated as a general response pattern.
