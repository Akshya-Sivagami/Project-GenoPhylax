# A3 — F11 Targeted Raw-Signal Attack and Clinical Variant-Call Consequence

## Objective

Module A3 tested whether a localized nanopore raw-signal perturbation could propagate through basecalling, alignment and variant calling to alter the digital interpretation of a clinically relevant pathogenic variant.

The selected target was:

```text
chr4:186274193 G>T
```

This is a pathogenic nonsense variant in **F11**, associated in ClinVar with Factor XI deficiency.

The study does not claim that HG002 has clinically diagnosed Factor XI deficiency. The experiment evaluates suppression of a pathogenic variant record in a controlled computational workflow.

---

## Why the target was selected

The original A2 loci did not have exact pathogenic ClinVar matches and therefore could not support a direct clinical-consequence claim.

The F11 target was selected through an exact intersection between:

- the HG002 GIAB GRCh38 truth VCF;
- pathogenic ClinVar GRCh38 records.

The target was independently verified as:

- GRCh38 coordinate: `chr4:186274193`;
- reference allele: `G`;
- alternate allele: `T`;
- GIAB truth genotype: `0/1`;
- GIAB high-confidence locus;
- ClinVar classification: Pathogenic;
- molecular consequence: nonsense;
- review status: multiple submitters, no conflicts.

---

## Source ONT evidence

The public HG002 PAO89685 HAC alignment contained:

- 29 target-overlapping records;
- 27 unique target parents;
- 17 ALT parents;
- 10 REF parents;
- no deletion or OTHER parents.

All selected target reads had MAPQ 60.

Of the 17 ALT-supporting parents:

- 15 raw reads were recoverable in POD5;
- 14 were independently confirmed as ALT following clean Dorado re-basecalling;
- one recovered raw read was excluded because it did not produce a usable clean Dorado parent record.

The final attack cohort therefore contained 14 clean ALT-confirmed parents.

---

## Signal mapping

Dorado move-table information was used to map the target base to raw-signal sample intervals.

Validation results:

- attack parents: 14;
- mapped parents: 14;
- reverse-strand parents: 8;
- attack conditions: W0, PM2, PM5, PM10 and PM20;
- total mapped windows: 70;
- mapping validation errors: 0.

The conditions represented:

- W0: target base only;
- PM2: target plus two bases on each side;
- PM5: target plus five bases on each side;
- PM10: target plus ten bases on each side;
- PM20: target plus twenty bases on each side.

---

## Controlled signal perturbation

Each selected signal interval was replaced using local linear interpolation between the signal values directly outside the chosen window.

Every generated POD5 retained all 15 source reads.

Exactly 14 target parents were modified in each condition. The excluded fifteenth read remained unchanged.

Attack-generation results:

| Condition | Changed samples | Off-window changed samples |
|---|---:|---:|
| W0 | 221 | 0 |
| PM2 | 1,006 | 0 |
| PM5 | 2,178 | 0 |
| PM10 | 4,018 | 0 |
| PM20 | 7,528 | 0 |

All generation audits passed.

---

## Re-basecalling and alignment

All attacked conditions were processed with the same Dorado HAC model and the same minimap2 GRCh38 alignment workflow.

For every condition:

- Dorado records: 16;
- aligned records: 16;
- primary mapped records: 16;
- unmapped attack parents: 0;
- missing target-coverage parents: 0;
- missing Dorado parents: 0.

The signal attack therefore did not simply destroy the reads or prevent genome alignment.

---

## Read-level target effects

Parent-level target outcomes were:

| Condition | ALT | REF | DEL | OTHER | ALT changed |
|---|---:|---:|---:|---:|---:|
| W0 | 11 | 0 | 0 | 3 | 3/14 |
| PM2 | 0 | 5 | 5 | 4 | 14/14 |
| PM5 | 0 | 1 | 10 | 3 | 14/14 |
| PM10 | 0 | 1 | 13 | 0 | 14/14 |
| PM20 | 0 | 0 | 14 | 0 | 14/14 |

Across all conditions:

- parent-condition observations: 70;
- changed observations: 59;
- overall target-state change rate: 84.2857%.

A thresholded dose response was observed:

- W0 weakened target evidence;
- PM2 eliminated all ALT support;
- larger windows increasingly shifted the target error mode toward deletion.

---

## Controlled hybrid design

A matched hybrid experiment was constructed using:

- 10 fixed same-sample REF parents;
- 14 clean or attacked replacement parents.

Each condition contained:

- 24 unique parents;
- 25 target-covering records due to one split-read record;
- constant target depth across controlled comparisons.

Variant calling was performed using:

```text
bcftools mpileup
bcftools call -m -v
```

---

## Controlled hybrid results

| Condition | REF pileup | ALT pileup | DEL | OTHER | ALT fraction | GT | QUAL | Outcome |
|---|---:|---:|---:|---:|---:|---|---:|---|
| CLEAN | 11 | 14 | 0 | 0 | 0.560000 | 0/1 | 222.201 | Pathogenic call retained |
| W0 | 11 | 11 | 0 | 3 | 0.500000 | 0/1 | 141.391 | Pathogenic call retained |
| PM2 | 16 | 0 | 5 | 4 | 0.000000 | NO_CALL | — | Pathogenic call lost |
| PM5 | 12 | 0 | 10 | 3 | 0.000000 | NO_CALL | — | Pathogenic call lost |
| PM10 | 12 | 0 | 13 | 0 | 0.000000 | NO_CALL | — | Pathogenic call lost |
| PM20 | 11 | 0 | 14 | 0 | 0.000000 | NO_CALL | — | Pathogenic call lost |

The clean hybrid produced:

```text
GT: 0/1
ALT fraction: 0.560000
QUAL: 222.201
```

W0 retained the call but reduced its quality:

```text
GT: 0/1
ALT fraction: 0.500000
QUAL: 141.391
```

PM2 and every larger on-target attack eliminated all ALT-supporting evidence and removed the F11 target record from the called VCF.

---

## PM2 off-target sham control

A matched sham control tested whether interpolation alone could explain the result.

For each of the same 14 ALT parents:

- the sham used the same signal-window length as PM2;
- interpolation was shifted at least 5,000 signal samples from the mapped F11 target;
- F11 target samples were unchanged;
- no samples outside the sham window changed.

Generation validation:

- source reads: 15;
- sham-modified parents: 14;
- changed sham samples: 1,005;
- changed F11 target samples: 0;
- changed samples outside sham windows: 0.

The sham produced:

```text
ALT parents: 14/14
Pileup REF: 11
Pileup ALT: 14
ALT fraction: 0.560000
VCF target record: present
GT: 0/1
QUAL: 222.202
Validation errors: 0
```

This was effectively identical to the clean baseline.

Therefore, PM2-sized interpolation alone was not sufficient to suppress the variant. Suppression required overlap with the raw-signal interval mapped to the pathogenic F11 target.

---

## Principal finding

A localized raw-signal interpolation attack overlapping the pathogenic F11 locus altered downstream Dorado basecalling while preserving read production and genome alignment.

In the controlled matched hybrid:

- clean data produced a heterozygous `0/1` pathogenic F11 call;
- target-base-only perturbation weakened but retained the call;
- target ±2-base perturbation eliminated all ALT evidence and removed the pathogenic target record;
- larger windows reproduced suppression and increasingly produced deletion errors;
- an identically sized off-target sham retained all ALT evidence and reproduced the clean `0/1` call.

Final experimental status:

```text
PATHOGENIC_VARIANT_CALL_SUPPRESSION_CONFIRMED
OFF_TARGET_SHAM_RETAINED_PATHOGENIC_CALL
```

---

## Defensible claim

A localized nanopore raw-signal interpolation attack spanning the pathogenic F11 target and two flanking bases on each side eliminated all ALT-supporting evidence and suppressed a previously detected heterozygous pathogenic variant call in a controlled bcftools-based variant-calling workflow.

An identically sized off-target interpolation placed at least 5,000 signal samples away preserved all 14 ALT parents, the heterozygous genotype and the clean call quality, supporting target-specific causality.

---

## Limitations

This is a controlled single-locus case study.

Current units of generalization are:

- individuals: 1;
- pathogenic loci: 1;
- sequencing runs: 1;
- basecallers: 1;
- basecaller models: 1;
- variant callers: 1.

The study does not prove:

- an actual clinical misdiagnosis;
- clinical disease in HG002;
- generalization across pathogenic loci;
- transferability to Bonito;
- transferability across variant callers;
- transferability across sequencing runs or individuals;
- feasibility without raw-signal access and accurate target localization.

The controlled hybrid was intentionally constructed to isolate causal allele-evidence changes. It is not equivalent to an untouched whole-genome clinical workflow.

---

## Final status

```text
A3 core objective: COMPLETE
A3 pathogenic case study: COMPLETE
A3 controlled hybrid validation: PASS
A3 off-target sham validation: PASS
A3 required GPU work remaining: NONE
```
