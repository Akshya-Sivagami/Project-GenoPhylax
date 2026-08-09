# Module C — Lifecycle Integration and GenoPhylax Risk Index

## 1. Purpose

Module C integrates the generation-time security experiments in Modules A1-A3
with the storage-, sharing-, and containment-time models in Modules B1-B3.

The objective is not to claim that every stage of the genomic lifecycle was
experimentally observed in one continuous end-to-end attack.

Instead, Module C provides a provenance-aware lifecycle framework in which:

- directly observed experimental evidence;
- reproduced internal-model evidence;
- calibrated model evidence;
- contextual evidence; and
- explicitly modelled handoffs

remain distinguishable.

The resulting GenoPhylax Risk Index (GRI) is a lifecycle-aware severity
framework rather than a probability of compromise, clinical harm, or breach.

---

## 2. Canonical Lifecycle Schema

The final lifecycle uses ten stages:

- S1 — Generation
- S2 — Basecalling
- S3 — Alignment
- S4 — Variant Calling / Genotype Evidence
- S5 — Clinical Interpretation
- S6 — Storage
- S7 — Sharing / Release
- S8 — Reuse / Downstream Propagation
- S9 — Incident / Forensic Analysis
- S10 — Containment / Revocation

Modules A1-A3 primarily cover the generation-to-interpretation side of the
lifecycle.

Modules B1-B3 primarily cover storage, sharing, amplification, authentication,
and containment.

Module C connects these domains while preserving the evidence boundary between
directly observed and modelled stages.

---

## 3. Cross-Module Evidence Registry

The final C2 evidence registry contains:

- 20 total evidence records;
- 20 tier-assigned records;
- 0 SOURCE_PENDING records.

Final evidence-tier distribution:

- E1: 2
- E2: 10
- E3: 1
- E4: 7
- E5: 0

Evidence tiers are categorical provenance/evidence-strength descriptors.

They are not numerical confidence weights and are not multiplied directly into
the Base GRI.

### A1 provenance closure

Recovered A1 evidence is now source-locked.

A1_E01 through A1_E04 are assigned E2.

A1 remains:

`SOURCE_LOCKED_STANDALONE_NON_GRI`

A1 therefore contributes to the lifecycle threat model and paper narrative but
does not retroactively alter the already-validated F11 or Privacy GRI worked
cases.

---

## 4. A1 Software-Integrity Evidence

The canonical preserved BWA AddressSanitizer fuzzing campaign recorded:

- BWA version: 0.7.19-r1273
- 963,339 executions
- 23,120 seconds (~6.42 hours)
- 15.44% AFL bitmap coverage
- 521 saved crash artifacts

Crash-artifact counts are not interpreted as counts of unique vulnerabilities.

Two source-level ASAN-confirmed root causes were recovered:

1. `ksw_extend2`, `ksw.c:428`
   - heap-backed out-of-bounds READ
   - CWE-125

2. `mem_aln2sam`, `bwamem.c:906`
   - global/static-storage out-of-bounds READ
   - CWE-125

Exploitability, arbitrary code execution, memory-write corruption, patient
harm, and external CVE assignment were not established.

---

## 5. F11 Integrity Worked Case

The F11 worked case represents the generation-to-clinical-integrity path.

Reference variant:

- chromosome: chr4
- GRCh38 position: 186274193
- reference allele: G
- alternate allele: T
- ClinVar Variation ID: 11891
- interpretation: pathogenic nonsense variant in F11

Clean rebasecalling produced:

- 15 raw-signal parent reads
- 14 ALT-supporting clean parents
- 1 parent with no Dorado output

Under the PM2 targeted perturbation:

- all 14 clean ALT-supporting parents lost the ALT-supporting state;
- the attacked locus became a no-call;
- sham/off-target controls retained the ALT state in 14/14 parents.

This is treated as a controlled, truth-anchored worked case.

It is not evidence that the same outcome occurs across patients, loci,
basecallers, sequencing chemistries, or clinical laboratories.

No observed S5-to-S6 storage propagation occurred in this experiment.

Any lifecycle continuation beyond the directly observed experimental stages is
therefore explicitly modelled rather than presented as observed propagation.

---

## 6. Privacy Amplification Worked Case

The Privacy worked case integrates B1-B3.

### B1 — Kinship amplification

The authoritative B1 synthetic kinship graph contains:

- 4,144 nodes
- 1,657 registered individuals at 40% DTC registration

The calibrated amplification model produced approximately:

- 464.4x amplification

against the project reference target of approximately:

- 492.86x

with approximately 5.8% calibration error.

The calibration anchors the amplification mechanism but does not convert the
synthetic graph into direct population observation.

### B2 — Vault and lifetime exposure

Authoritative B2 outputs include:

- Pathogenic Variants unrecoverability: 0.2299
- cumulative all-six-tier unrecoverability: 0.0801
- re-identification reaches 50% at year 11
- re-identification reaches 100% at year 13
- familial risk reaches 100% at year 15

These are outputs of the project's configured internal models.

They are not formal cryptographic proofs or externally calibrated population
risk probabilities.

### B3 — Containment and authentication

For the principal containment simulation:

- baseline exposed nodes: 786
- k=5 exposed nodes: 560
- k=10 exposed nodes: 6
- k=10 exposure reduction: 99.2%

For the authentication benchmark:

- classifier threshold: 4.5
- precision: 1.0000
- recall: 0.9800
- F1: 0.9899
- accuracy: 0.9960

The authentication benchmark is generated internally and is not external
platform-validation evidence.

---

## 7. Handoff Vector Framework

C3 defines nine lifecycle handoffs:

- five F11 handoffs;
- four Privacy handoffs.

The handoff representation separates concepts including:

- likelihood;
- impact;
- detectability;
- persistence;
- reversibility;
- familial amplification;
- clinical severity;
- confidence.

A handoff therefore records how evidence crosses a lifecycle boundary without
pretending that all lifecycle transitions were observed experimentally.

---

## 8. GRI Outcome Dimensions

The final GRI framework uses seven dimensions:

- D1 — Identity Risk
- D2 — Disease Inference / Clinical Interpretation Risk
- D3 — Familial Cascade Risk
- D4 — Accessibility Risk
- D5 — Persistence Risk
- D6 — Amplification Risk
- D7 — Pipeline Exposure Risk

Dimensions may be:

- SCORED;
- CONTEXT_ONLY;
- NO_BASELINE_SEVERITY; or
- NOT_APPLICABLE.

Missing evidence is not treated as zero risk.

N/A is not interpreted as low risk.

---

## 9. F11 Base GRI

The F11 worked case has the following scored baseline dimensions:

- D2 = 1.0000000000
- D7 = 1.0000000000

Final Base GRI:

`1.0000000000`

This value means that the resolved dimensions in this deliberately narrow
worked case are at the maximum of their normalized severity scale.

It must not be interpreted as:

- a probability of patient harm;
- 100% probability of clinical misdiagnosis;
- externally validated clinical risk;
- population-level incidence;
- evidence of storage propagation.

The F11 worked case is classified as controlled direct empirical evidence with
explicit scope limitations.

---

## 10. Privacy Base GRI

The final scored Privacy dimensions are:

- D1 = 0.8886656512
- D3 = 0.8817416604
- D5 = 0.8852036558
- D6 = 0.9904301172

Final Base GRI:

`0.9115102712`

This score is model-dependent and contains mixed E3/E4 support.

It is not a probability that a breach will occur.

D1, D3, and D5 share the B2 lifetime-model provenance family and therefore are
not independent observations.

D6 is anchored to the calibrated B1 amplification model.

---

## 11. Modifier Architecture

Modifiers are maintained separately from Base GRI.

They are not multiplied into the validated Base GRI.

This prevents weak or contextual evidence from silently changing the primary
severity score.

### Privacy M3 correction

Privacy M3 (Detectability) is:

`UNMEASURED`

The project does not contain a direct empirical or calibrated measurement of
privacy-event detectability.

The B3 authentication benchmark remains valid:

- F1 = 0.9899
- residual performance complement = 1 - F1 = 0.0101

However, 0.0101 is retained only as:

`DIRECT_MITIGATION_ONLY / CONTEXT_ONLY`

It is not interpreted as Privacy M3.

Therefore the M3 semantic correction does not alter Privacy Base GRI.

---

## 12. Ablation Analysis

V6 evaluates whether individual dimensions or shared provenance families
dominate the Privacy score.

For Privacy:

- removing D1 gives GRI = 0.9191251445
- removing D3 gives GRI = 0.9214331414
- removing D5 gives GRI = 0.9202791429
- removing D6 gives GRI = 0.8852036558

The largest single-dimension effect is associated with D6.

Grouped provenance ablation is also required because D1, D3, and D5 originate
from the same B2 lifetime-model family.

This prevents correlated dimensions from being incorrectly interpreted as
independent replication.

---

## 13. Sensitivity Analysis

V7 evaluates deterministic sensitivity to modelling choices.

The final Privacy baseline remains:

`0.9115102712`

The tested analyses include:

- dimension/family weighting sensitivity;
- D6 reference-anchor sensitivity;
- temporal assumptions;
- M5 containment-origin scenarios.

Sensitivity ranges are deterministic scenario analyses.

They are not statistical confidence intervals.

M5 varies substantially across origin scenarios but remains a separate
modifier and does not change the primary Base GRI.

---

## 14. Evidence and Confidence Interpretation

The framework intentionally separates:

1. evidence provenance;
2. evidence tier;
3. normalized severity;
4. Base GRI;
5. contextual modifiers;
6. sensitivity analysis.

No evidence-tier multiplier is applied to Base GRI.

No missing value is silently converted to zero.

Model-generated values remain labelled as model-generated.

Controlled empirical case studies remain labelled as case studies.

This prevents the composite framework from expressing more certainty than its
underlying experiments support.

---

## 15. Primary Integrated Finding

The main scientific contribution of Module C is not simply a single numerical
GRI value.

The central result is that genomic cyber-biosecurity can be represented as a
single lifecycle threat model while preserving the distinction between:

- upstream software integrity;
- sequencing/basecalling manipulation;
- genotype evidence;
- clinical interpretation;
- storage and disclosure;
- familial amplification;
- authentication;
- containment.

The framework therefore connects generation-time integrity failures with
storage- and sharing-time privacy risk without claiming that every transition
was experimentally observed in one continuous attack chain.

---

## 16. Strongest Publication Claims

The project supports the following claims.

### Claim 1 — Lifecycle integration

Generation-time integrity attacks and downstream genomic privacy risks can be
represented within one provenance-aware lifecycle framework.

### Claim 2 — Evidence-aware synthesis

Observed experimental evidence, calibrated models, internal simulations and
modelled lifecycle handoffs can be combined without collapsing their evidence
strength into a single unsupported confidence number.

### Claim 3 — F11 worked-case severity

A controlled targeted raw-signal perturbation suppressed ALT-supporting
evidence at a pathogenic F11 variant in the tested HG002/Dorado configuration.

### Claim 4 — Privacy amplification

Kinship structure can amplify genomic exposure well beyond directly
compromised accounts in the calibrated B1 model.

### Claim 5 — Persistence and containment

The B2/B3 models demonstrate how long-lived genomic information and kinship
structure influence downstream persistence and containment difficulty.

### Claim 6 — GRI

GRI provides a reproducible normalized severity representation for the two
worked lifecycle cases while retaining evidence provenance and uncertainty
boundaries.

---

## 17. Claims That Must Not Be Made

The current project does not establish:

- real-world probability of a genomic cyberattack;
- probability of patient injury;
- universal clinical misdiagnosis rates;
- universal population-level privacy risk;
- externally validated performance of the B3 authentication classifier;
- real-world effectiveness of the containment model;
- full experimental S1-to-S10 propagation;
- independent replication of the F11 attack;
- clinical validation of the F11 result;
- exploitability or RCE for the A1 findings;
- assigned CVEs for A1;
- statistical confidence intervals for V7 sensitivity ranges.

---

## 18. Final Module C State

Module C is considered scientifically complete through:

- C1 lifecycle schema;
- C2 evidence registry;
- C2.13 A1 provenance closure;
- C3 handoff construction;
- C4 GRI architecture;
- C4.9 Privacy M3 construct-validity correction;
- V6 ablation;
- V7 sensitivity;
- V8 publication-claim audit.

The next project phase is publication packaging:

1. publication figures;
2. publication tables;
3. Methods;
4. Results;
5. Discussion and limitations;
6. final report;
7. conference/journal paper draft.

