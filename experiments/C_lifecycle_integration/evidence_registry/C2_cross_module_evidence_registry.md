# Module C2 — Cross-Module Evidence Registry

## Status

`DRAFT_SOURCE_REVIEW_REQUIRED`

## Purpose

This registry links measured GenoPhylax results to the canonical lifecycle stages defined in C1. It separates experimental evidence from simulation, calibration, model-derived values and project design decisions.

## Important source qualification

The source paths in this first pass are automatically resolved candidates. Strong candidates may still require human inspection before they are locked as authoritative paper sources. No GenoPhylax Risk Index weights or composite scores are assigned in C2.

## Module coverage

- **A1:** 4 evidence records
- **A2:** 4 evidence records
- **A3:** 4 evidence records
- **B1:** 2 evidence records
- **B2:** 3 evidence records
- **B3:** 3 evidence records

## Evidence records

### A1_E01 — A1

**Lifecycle stages:** S3, S10

**Evidence type:** experimental

**Asset:** BWA alignment software

**Threat:** Malformed genomic input triggering memory corruption

**Mechanism:** Coverage-guided fuzzing of AddressSanitizer-instrumented BWA 0.7.19

**Measured result:** Approximately 2.5 million fuzz executions

**Evidence confidence:** high

**Claim scope:** software-test campaign

**Limitations:** Single principal target version and incomplete program coverage

**Candidate source:** `experiments/A3_clinical_consequence_mapping/findings/A3_F11_final_numerical_summary.tsv`

**Source resolution:** WEAK_CANDIDATE (score 45)

### A1_E02 — A1

**Lifecycle stages:** S3, S10

**Evidence type:** experimental

**Asset:** BWA alignment software

**Threat:** Memory-safety vulnerability

**Mechanism:** ASAN-confirmed crash triage

**Measured result:** 54 total crashes, 33 unique crashes and two root causes

**Evidence confidence:** high

**Claim scope:** software-test campaign

**Limitations:** Root causes were established within the project audit; external CVE assignment was not claimed

**Candidate source:** `experiments/A2_adversarial_dna/basecalling/findings/master_A2_GPU/A2_GPU_master_findings.md`

**Source resolution:** WEAK_CANDIDATE (score 58)

### A1_E03 — A1

**Lifecycle stages:** S3

**Evidence type:** experimental

**Asset:** BWA ksw alignment routine

**Threat:** Heap buffer overflow

**Mechanism:** Malformed-input execution reaching ksw_extend2

**Measured result:** Heap buffer overflow in ksw_extend2 at ksw.c:428

**Evidence confidence:** high

**Claim scope:** function-level finding

**Limitations:** Exploitability beyond the demonstrated crash was not established

**Candidate source:** `experiments/A2_adversarial_dna/basecalling/dorado/findings.md`

**Source resolution:** WEAK_CANDIDATE (score 30)

### A1_E04 — A1

**Lifecycle stages:** S3

**Evidence type:** experimental

**Asset:** BWA SAM-output routine

**Threat:** Global buffer overflow

**Mechanism:** Malformed-input execution reaching mem_aln2sam

**Measured result:** Global overflow in mem_aln2sam at bwamem.c:906

**Evidence confidence:** high

**Claim scope:** function-level finding

**Limitations:** Exploitability beyond the demonstrated crash was not established

**Candidate source:** `experiments/A2_adversarial_dna/basecalling/dorado/findings.md`

**Source resolution:** WEAK_CANDIDATE (score 30)

### A2_E01 — A2

**Lifecycle stages:** S1, S2

**Evidence type:** experimental

**Asset:** Nanopore raw signal and basecalled reads

**Threat:** Whole-read Gaussian raw-signal perturbation

**Mechanism:** Controlled Gaussian-noise dose series

**Measured result:** Seed-42 mean identity declined from 98.79% at GN01 to 93.89% at GN10

**Evidence confidence:** high

**Claim scope:** 100-read controlled experiment

**Limitations:** One sequencing dataset, one production basecaller and a limited perturbation family

**Candidate source:** `experiments/A2_adversarial_dna/basecalling/perturbations/metrics/hg002_100reads_gaussian_dose_response_summary.tsv`

**Source resolution:** STRONG_CANDIDATE (score 141)

### A2_E02 — A2

**Lifecycle stages:** S1, S2

**Evidence type:** experimental

**Asset:** Nanopore raw signal and basecalled reads

**Threat:** Stochastic raw-signal perturbation

**Mechanism:** Five-seed replication across GN01, GN05 and GN10

**Measured result:** GN10 mean identity replicated within approximately 93.56% to 93.95%

**Evidence confidence:** high

**Claim scope:** multi-seed technical replication

**Limitations:** Replication varied noise realization, not biological sample

**Candidate source:** `experiments/A2_adversarial_dna/basecalling/perturbations/findings/experiment_B_multiseed_findings.md`

**Source resolution:** STRONG_CANDIDATE (score 258)

### A2_E03 — A2

**Lifecycle stages:** S2, S3

**Evidence type:** experimental

**Asset:** Perturbed nanopore reads

**Threat:** Basecall degradation while preserving downstream usability

**Mechanism:** Minimap2 map-ont alignment of the 1,000-read series

**Measured result:** Approximately 97% remained mapped with mean MAPQ approximately 55.3 to 55.4

**Evidence confidence:** high

**Claim scope:** 1,000-read alignment series

**Limitations:** Mapping retention does not establish preservation of all downstream biological information

**Candidate source:** `experiments/A2_adversarial_dna/basecalling/perturbations/experiment_D_alignment/D2_seed42_alignment/metrics/experiment_D2_seed42_alignment_summary.tsv`

**Source resolution:** STRONG_CANDIDATE (score 263)

### A2_E04 — A2

**Lifecycle stages:** S1, S2, S3

**Evidence type:** experimental

**Asset:** Truth-backed nanopore locus evidence

**Threat:** Target-local signal perturbation

**Mechanism:** W0 targeted-locus perturbation replicated at L2 and L3

**Measured result:** L2 and L3 each retained ALT state in 10 of 10 parents; zero target-state changes

**Evidence confidence:** high

**Claim scope:** cross-locus replication

**Limitations:** The tested W0 effect did not generalize across these two additional loci

**Candidate source:** `experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication/logs/cross_locus_W0_target_effect.log`

**Source resolution:** STRONG_CANDIDATE (score 198)

### A3_E01 — A3

**Lifecycle stages:** S1, S2, S3

**Evidence type:** experimental

**Asset:** F11 ALT-supporting nanopore reads

**Threat:** Target-mapped local raw-signal interpolation

**Mechanism:** Interpolation over W0, PM2, PM5, PM10 and PM20 signal windows

**Measured result:** 59 of 70 parent-condition observations changed target state

**Evidence confidence:** high

**Claim scope:** single-locus controlled case study

**Limitations:** Single individual, pathogenic locus, sequencing run, basecaller and model

**Candidate source:** `experiments/A3_clinical_consequence_mapping/findings/A3_F11_final_numerical_summary.tsv`

**Source resolution:** STRONG_CANDIDATE (score 219)

### A3_E02 — A3

**Lifecycle stages:** S3, S4

**Evidence type:** experimental

**Asset:** F11 pathogenic variant evidence

**Threat:** Target-overlapping local signal attack

**Mechanism:** PM2 interpolation over target base and two flanking bases

**Measured result:** All 14 clean-confirmed ALT parents lost ALT state under PM2

**Evidence confidence:** high

**Claim scope:** parent-level target-state analysis

**Limitations:** Controlled single-locus experiment

**Candidate source:** `experiments/A3_clinical_consequence_mapping/results/F11_candidate/controlled_signal_attacks/F11_attack_generation_summary.txt`

**Source resolution:** STRONG_CANDIDATE (score 192)

### A3_E03 — A3

**Lifecycle stages:** S4, S5

**Evidence type:** experimental

**Asset:** Pathogenic F11 heterozygous variant call

**Threat:** False-negative or missed-variant event

**Mechanism:** Controlled hybrid pileup and bcftools variant calling after targeted signal attack

**Measured result:** Clean 0/1 call with QUAL 222.201 was lost under PM2, PM5, PM10 and PM20

**Evidence confidence:** high

**Claim scope:** controlled variant-calling workflow

**Limitations:** Potential clinical interpretation risk only; no real clinical diagnosis or patient outcome was tested

**Candidate source:** `experiments/A3_clinical_consequence_mapping/results/F11_candidate/controlled_hybrid_variant_calling/F11_controlled_hybrid_variant_calling_summary.tsv`

**Source resolution:** STRONG_CANDIDATE (score 207)

### A3_E04 — A3

**Lifecycle stages:** S1, S2, S3, S4

**Evidence type:** experimental control

**Asset:** F11 pathogenic variant evidence

**Threat:** Non-target interpolation as confounding mechanism

**Mechanism:** PM2-sized off-target sham interpolation at least 5,000 signal samples from the F11 target

**Measured result:** Sham retained 14 of 14 ALT parents, genotype 0/1 and QUAL 222.202

**Evidence confidence:** high

**Claim scope:** target-specific causality control

**Limitations:** One off-target sham design within the same read cohort

**Candidate source:** `experiments/A3_clinical_consequence_mapping/results/F11_candidate/PM2_off_target_sham/F11_PM2_off_target_sham_report.txt`

**Source resolution:** STRONG_CANDIDATE (score 242)

### B1_E01 — B1

**Lifecycle stages:** S7, S8

**Evidence type:** simulation

**Asset:** Genomic-sharing population graph

**Threat:** Familial graph-amplified exposure

**Mechanism:** Population graph simulation and breach propagation

**Measured result:** Population graph contained 3,303 nodes, with 1,321 registered individuals and 786 baseline exposed

**Evidence confidence:** medium

**Claim scope:** graph simulation

**Limitations:** Synthetic or modelled graph rather than direct platform data

**Candidate source:** `experiments/B1_graph_amplification/results_log.txt`

**Source resolution:** STRONG_CANDIDATE (score 184)

### B1_E02 — B1

**Lifecycle stages:** S7, S8

**Evidence type:** calibrated simulation

**Asset:** Genomic-sharing population graph

**Threat:** Graph-amplified breach exposure

**Mechanism:** Calibration to a 493-fold target amplification scenario

**Measured result:** Model amplification reached 464.4-fold with 5.8% calibration error

**Evidence confidence:** medium

**Claim scope:** calibrated graph model

**Limitations:** Calibration target does not independently validate every graph assumption

**Candidate source:** `experiments/B1_graph_amplification/results_log.txt`

**Source resolution:** STRONG_CANDIDATE (score 232)

### B2_E01 — B2

**Lifecycle stages:** S6, S7

**Evidence type:** model-derived

**Asset:** Layered genomic vault

**Threat:** Reconstruction from disclosed semantic layers

**Mechanism:** Layered vault and unrecoverability model

**Measured result:** Adding the pathogenic-variant layer reduced unrecoverability to 0.044

**Evidence confidence:** medium

**Claim scope:** vault-model scenario

**Limitations:** Unrecoverability is produced by the project model and is not a formal cryptographic proof

**Candidate source:** `experiments/A2_adversarial_dna/basecalling/findings/master_A2_GPU/A2_GPU_master_findings.md`

**Source resolution:** WEAK_CANDIDATE (score 58)

### B2_E02 — B2

**Lifecycle stages:** S7, S9

**Evidence type:** simulation

**Asset:** Persistently disclosed genomic information

**Threat:** Time-dependent re-identification

**Mechanism:** Lifetime genomic-risk simulation

**Measured result:** Re-identification reached 50% by year 11 and 100% by year 20

**Evidence confidence:** medium

**Claim scope:** lifetime-risk simulation

**Limitations:** Long-term projections depend on model assumptions

**Candidate source:** `paper/figures/B2_lifetime_risk.png`

**Source resolution:** STRONG_CANDIDATE (score 136)

### B2_E03 — B2

**Lifecycle stages:** S8, S9

**Evidence type:** simulation

**Asset:** Familial genomic information

**Threat:** Persistent familial exposure

**Mechanism:** Lifetime familial-risk simulation

**Measured result:** Familial risk reached 100% by year 15

**Evidence confidence:** medium

**Claim scope:** lifetime-risk simulation

**Limitations:** Projection depends on the selected model parameters

**Candidate source:** `experiments/B2_vault_design/lifetime_risk.py`

**Source resolution:** STRONG_CANDIDATE (score 128)

### B3_E01 — B3

**Lifecycle stages:** S8, S10

**Evidence type:** simulation

**Asset:** Kinship graph exposure boundary

**Threat:** Graph-originating breach propagation

**Mechanism:** Graph-aware boundary-isolation simulation

**Measured result:** Exposure declined from 560 at k=5 to 6 at k=10; hub-origin containment required k=20

**Evidence confidence:** medium

**Claim scope:** containment simulation

**Limitations:** Containment performance depends on graph construction

**Candidate source:** `experiments/B3_authentication/containment_algorithm.py`

**Source resolution:** STRONG_CANDIDATE (score 128)

### B3_E02 — B3

**Lifecycle stages:** S6, S10

**Evidence type:** simulation or benchmark

**Asset:** Genomic-platform authentication layer

**Threat:** Unauthorized platform access

**Mechanism:** Behavioural authentication classifier

**Measured result:** At threshold 3.8, precision was 0.9737, recall 0.7400, F1 0.8409 and accuracy 0.9440

**Evidence confidence:** medium

**Claim scope:** authentication benchmark

**Limitations:** Classifier results require interpretation within the project's generated benchmark setting

**Candidate source:** `paper/figures/B3_containment_auth.png`

**Source resolution:** STRONG_CANDIDATE (score 116)

### B3_E03 — B3

**Lifecycle stages:** S6, S10

**Evidence type:** design decision

**Asset:** Genomic-platform authentication layer

**Threat:** Missed malicious access

**Mechanism:** Operational classifier-threshold selection

**Measured result:** Threshold 3.6 was selected operationally to favour recall

**Evidence confidence:** medium

**Claim scope:** project design decision

**Limitations:** Operational preference is a design choice rather than a universally optimal threshold

**Candidate source:** `experiments/B3_authentication/containment_algorithm.py`

**Source resolution:** STRONG_CANDIDATE (score 118)

