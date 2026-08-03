# A2 GPU — Claims, Evidence and Limitations Matrix

## Purpose

This matrix defines what may and may not be claimed from the Project GenoPhylax A2 GPU experiments.

It should be consulted when preparing:

* papers;
* abstracts;
* presentations;
* mentor reports;
* posters;
* future research proposals.

---

# 1. Supported Claims

| Claim                                                             | Supporting evidence                                                                                                 | Strength                      |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| Gaussian raw-signal perturbation alters Dorado output             | Increasing GN01, GN05 and GN10 produced progressively lower identity, higher edit distance and greater Q-score loss | Strong                        |
| The Gaussian dose response is reproducible                        | Repeated across five seeds at 100 reads and three seeds at 1,000 reads                                              | Strong                        |
| Basecalling can complete despite altered nucleotide output        | Dorado completed all tested perturbation conditions successfully                                                    | Strong                        |
| Many corrupted reads remain genomically alignable                 | Mapping remained approximately 97% across alignment experiments                                                     | Strong                        |
| Stronger signal corruption increases alignment instability        | Increasing MAPQ losses, threshold-count reductions, CIGAR changes and position changes were observed                | Moderate to strong            |
| Parent-read tracking is required                                  | Some physical reads produced multiple BAM records                                                                   | Strong methodological finding |
| Target-centred PM5 can suppress ALT evidence                      | 20/20 attacked ALT-supporting reads lost ALT classification                                                         | Strong                        |
| The PM5 target effect reproduced across loci                      | Replicated at independent loci on chromosomes 1 and 4                                                               | Strong within tested scope    |
| PM5 preserves gross genomic mapping                               | 20/20 primary attacked reads remained mapped at MAPQ 60                                                             | Strong                        |
| Successful targeting requires surrounding signal context          | W0 target-only perturbation produced 0/20 target changes                                                            | Strong                        |
| The target effect is spatially specific                           | A comparably strong perturbation 100 bases away produced 0/20 target changes                                        | Strong                        |
| Nearby perturbations can create short-range spillover             | The +20-base sham produced 1/20 target changes                                                                      | Preliminary                   |
| PM5 reduces hybrid ALT support                                    | ALT support fell from 19 to 9 at L2 and from 18 to 8 at L3                                                          | Strong                        |
| PM5 reduces variant-call confidence                               | QUAL fell by approximately 41.22% at L2 and 32.34% at L3                                                            | Strong                        |
| File validity and mapping alone are insufficient integrity checks | Altered reads remained processable and highly mapped                                                                | Strong security implication   |

---

# 2. Partially Supported Claims

| Claim                                                         | Evidence                                                           | Required qualification                                                        |
| ------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| Signal manipulation can affect downstream variant calling     | ALT support and QUAL decreased                                     | The final genotype remained heterozygous                                      |
| Targeted attacks can influence genomic interpretation         | Variant evidence changed                                           | Clinical interpretation was not directly evaluated                            |
| Local perturbations have a contextual influence radius        | W0 failed, +20 caused one change, +100 caused none                 | Exact radius was not mapped                                                   |
| The attack could evade simple operational monitoring          | Runs completed and reads remained mapped                           | No real clinical monitoring system was tested                                 |
| The method may generalize beyond one locus                    | It reproduced at L2 and L3                                         | Only two replication loci were tested                                         |
| Perturbation effects can propagate through a genomic pipeline | Signal changes affected basecalls, alignments and variant evidence | Full clinical and storage lifecycle propagation was not experimentally tested |

---

# 3. Unsupported Claims

| Claim                                                            | Why unsupported                                                                                                                    |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| The attack always flips a genotype                               | Both hybrid calls remained heterozygous                                                                                            |
| The attack caused a clinical misdiagnosis                        | No clinical interpretation or patient outcome was tested                                                                           |
| The attack works against Bonito                                  | Bonito could not be executed on the available system                                                                               |
| The attack is model-agnostic                                     | Only Dorado was experimentally evaluated                                                                                           |
| The attack works against every Dorado model                      | Only one HAC model was tested                                                                                                      |
| The attack works across all ONT chemistries                      | Only R10.4.1 E8.2 400-bps data was tested                                                                                          |
| The attack works at arbitrary loci                               | Only the original target and two replication loci were evaluated                                                                   |
| The method represents a naturally occurring biological attack    | The signal interpolation was synthetic and controlled                                                                              |
| A physical DNA sample was engineered to deliver the attack       | No wet-lab delivery was attempted                                                                                                  |
| A deployed clinical sequencing system was compromised            | Experiments were conducted in a controlled research pipeline                                                                       |
| The selected L2 and L3 loci were clinically pathogenic           | They were selected as truth-backed technical replication loci                                                                      |
| PM5 leaves all non-target sequence unaffected                    | Only signal samples outside the defined windows were unchanged; local basecalling effects may extend beyond exact event boundaries |
| A successful CUDA tensor test proves complete GB10 compatibility | PyTorch warned that capability 12.1 exceeded the declared supported maximum                                                        |
| Bonito failed because of the attack                              | Bonito failed before basecalling because its ARM64 backend dependency was unavailable                                              |

---

# 4. Required Publication Qualifications

Every A2 publication or presentation should state:

1. Dorado was the only basecaller experimentally evaluated.

2. Bonito transferability remained unresolved because the required KOI backend was unavailable for Linux AArch64.

3. PM5 produced complete ALT-loss classification among the 20 specifically attacked reads, not among all reads in the full genomic cohort.

4. All attacked primary reads remained mapped at MAPQ 60.

5. Hybrid ALT support and QUAL decreased, but the final genotypes remained heterozygous.

6. The attack was a controlled synthetic raw-signal interpolation method.

7. Only two cross-locus replication sites were used.

8. Ten targeted parent reads were evaluated at each replication locus.

9. Clinical significance and real-world delivery were not established.

10. The results show pipeline integrity risk, not demonstrated patient harm.

---

# 5. Preferred Terminology

## Use

* targeted raw-signal perturbation;
* local signal interpolation;
* ALT-evidence suppression;
* target-state change;
* variant-confidence degradation;
* high-confidence mapping preservation;
* cross-locus replication;
* context-dependent effect;
* spatial specificity;
* short-range contextual spillover;
* controlled hybrid cohort;
* platform-limited Bonito feasibility.

## Avoid

* genotype hijacking;
* guaranteed genotype flip;
* clinical attack;
* universal basecaller attack;
* invisible attack;
* undetectable manipulation;
* model-agnostic attack;
* patient misdiagnosis demonstration;
* biological malware;
* complete pipeline compromise.

---

# 6. Recommended Main Claim

```text
Localized raw-signal manipulation can reproducibly suppress target variant
evidence and reduce downstream variant confidence while preserving apparently
normal high-confidence genomic mapping.
```

---

# 7. Recommended Secondary Claims

```text
Whole-read Gaussian signal perturbation produced a reproducible,
strength-dependent degradation in Dorado basecalling quality across multiple
random seeds and sample sizes.
```

```text
A target-centred PM5 perturbation changed all 20 attacked ALT-supporting reads
across two independent loci, whereas a target-only W0 control and a comparably
strong perturbation 100 bases away produced no target changes.
```

```text
Targeted PM5 perturbation reduced hybrid ALT support by ten reads at both
replication loci and reduced variant QUAL by approximately 32–41%, although
the final genotype remained heterozygous.
```

---

# 8. Limitation Severity Matrix

| Limitation                               | Impact on conclusions                         | Priority for future work |
| ---------------------------------------- | --------------------------------------------- | ------------------------ |
| Only Dorado tested                       | Prevents model-transfer claims                | High                     |
| Bonito ARM64 incompatibility             | Leaves cross-model transfer unresolved        | High                     |
| Two replication loci                     | Limits genomic generalization                 | High                     |
| Ten attacked reads per locus             | Limits cohort-size inference                  | Medium to high           |
| Synthetic interpolation                  | Limits claims about natural physical delivery | High                     |
| One ONT chemistry                        | Limits chemistry generalization               | Medium                   |
| One Dorado HAC model                     | Limits model-version generalization           | Medium                   |
| No complete genotype flip                | Restricts downstream consequence claim        | Medium                   |
| No clinical annotation experiment        | Prevents direct clinical-harm claims          | High                     |
| No wet-lab implementation                | Prevents biological-delivery claims           | High                     |
| Context radius not systematically mapped | Limits mechanistic understanding              | Medium                   |
| No runtime detector evaluation           | Leaves detectability unresolved               | Medium                   |

---

# 9. Future Work Needed to Strengthen Claims

| Future experiment                   | Claim it would strengthen              |
| ----------------------------------- | -------------------------------------- |
| Bonito test on supported x86-64 GPU | Cross-model transferability            |
| Additional Dorado model versions    | Model-version generalization           |
| Additional genomic loci             | Cross-locus generalization             |
| Larger attacked parent-read cohorts | Cohort-level effect estimation         |
| Pathogenic or pharmacogenomic loci  | Clinical consequence relevance         |
| Systematic context-distance sweep   | Contextual influence-radius estimation |
| Alternative perturbation mechanisms | Attack-method generalization           |
| Signal anomaly detector evaluation  | Detectability and defence claims       |
| Orthogonal sequencing validation    | Real-world integrity verification      |
| Wet-lab signal manipulation study   | Physical delivery feasibility          |

---

# 10. Final Scientific Boundary

A2 establishes:

```text
Generation-time manipulation of Nanopore signal can alter local sequence
evidence while preserving plausible downstream processing.
```

A2 does not establish:

```text
Universal, clinical or physically delivered compromise of genomic sequencing.
```
