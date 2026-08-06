# Module C2.3 — GenoPhylax Risk Architecture

## Status

`METHODOLOGY_LOCKED_BEFORE_GRI_IMPLEMENTATION`

## Purpose

This document reconciles the original seven GenoPhylax Risk Index dimensions
with the additional factors introduced during lifecycle-integration planning.

The two groups are not competing taxonomies.

The GRI uses a two-layer architecture:

1. outcome dimensions describing what kind of genomic risk exists;
2. handoff and evidence modifiers describing how strongly that risk manifests
   and how strongly the available evidence supports it.

No final weights or composite-risk formula are assigned at this stage.

---

## Layer A — Canonical GRI outcome dimensions

The original D1–D7 dimensions remain the paper-facing risk outcomes.

### D1 — Identity Risk

Likelihood that genomic information can be linked to an identifiable person.

### D2 — Disease Inference Risk

Ability to infer medical conditions, pathogenic variants, predispositions or
health-related traits.

### D3 — Familial Cascade Risk

Risk imposed on biological relatives who may not have directly contributed or
consented to the disclosed genomic information.

### D4 — Accessibility Risk

Ease with which an unauthorized actor can obtain or use genomic information.

### D5 — Persistence Risk

Difficulty of reversing, revoking or meaningfully mitigating genomic exposure.

### D6 — Amplification Risk

Increase in exposure created by relative matching, graph structure, dataset
replication or platform architecture.

### D7 — Pipeline Exposure Risk

Risk that a genomic record was corrupted, manipulated or otherwise compromised
during generation or computational processing.

---

## Layer B — Handoff and evidence modifiers

These fields do not become additional GRI outcome dimensions.

They modify lifecycle handoff records and interpretation of D1–D7 scores.

### M1 — Integrity Impact

Magnitude of the observed or modelled change to genomic information.

### M2 — Clinical Severity

Potential biological or clinical importance of the affected information.

Clinical severity does not establish that a real diagnosis or patient outcome
occurred.

### M3 — Detectability

Likelihood that ordinary quality-control, provenance or audit procedures would
detect the failure.

### M4 — Recoverability

Ability to restore a trustworthy record using retained source data and
provenance.

### M5 — Containment Difficulty

Difficulty of preventing further propagation after failure or disclosure.

### M6 — Evidence Confidence

Strength, scope and generalizability of evidence supporting a registry claim
or lifecycle handoff.

---

## Reconciliation of overlapping factors

| Proposed factor | Canonical representation |
| --- | --- |
| Privacy sensitivity | D1 Identity Risk and D2 Disease Inference Risk |
| Familial amplification | D3 Familial Cascade Risk and D6 Amplification Risk |
| Persistence | D5 Persistence Risk |

---

## Evidence tiers

Evidence tiers are assigned per evidence-registry row and per claim.

They must not be assigned once to an entire module.

A module may contain evidence records with different tiers.

### E1 — Replicated direct empirical evidence

Directly measured evidence with meaningful technical, seed, locus, sample or
other replication appropriate to the specific claim.

### E2 — Controlled direct empirical case study

Directly measured evidence with strong controls but limited biological,
technical or workflow generalizability.

### E3 — Calibrated simulation or model

A model calibrated against an external or independently defined target while
remaining dependent on simulation assumptions.

### E4 — Uncalibrated simulation, internal model or design benchmark

A project-derived model, simulation or benchmark without sufficient external
calibration for broad empirical claims.

### E5 — Illustrative or hypothetical lifecycle propagation

A conceptual handoff representing possible downstream consequences without
directly observing that propagation in a real deployment.

---

## Preliminary row-level tier guidance

| Evidence family | Likely tier |
| --- | --- |
| A1 measured fuzzing and ASAN findings | E1 or E2 depending on the row-level claim |
| A2 replicated Gaussian perturbation | E1 |
| A2 cross-locus no-effect result | E1 |
| A3 F11 target attack and sham control | E2 |
| A3 real-world downstream storage propagation | E5 unless directly demonstrated |
| B1 calibrated amplification model | E3 |
| B2 vault and lifetime-risk models | E4 unless stronger calibration is documented |
| B3 containment and authentication simulations | E3 or E4 depending on row-level validation |

---

## Required GRI output form

The final GRI must not provide only one falsely precise composite number.

At minimum, each scenario must report:

- observed or model-derived severity score;
- evidence-adjusted score or range;
- evidence tier;
- confidence band;
- generalization scope;
- dominant risk dimensions;
- key limitations.

---

## Required implementation rule

No GRI implementation may begin until:

1. C2 authoritative evidence sources are locked;
2. each evidence-registry row has an evidence tier;
3. the worked scenarios are concretely defined;
4. validation tests have explicit inputs and pass/fail criteria.
