# Module C2.4 — Worked Scenarios and Validation Protocol

## Status

`PROTOCOL_LOCKED_BEFORE_HANDOFF_AND_GRI_IMPLEMENTATION`

## Purpose

This document defines the two principal lifecycle scenarios and the validation
requirements that the eventual Handoff Vector and GenoPhylax Risk Index must
satisfy.

The project does not claim clinical validation or universal risk calibration.

The intended validation is framework-level validation through traceability,
contrast cases, directionality, ablation and sensitivity analysis.

---

# Worked Scenario 1 — F11 Integrity Propagation

## Empirically observed arc

S1 Raw signal
-> S2 Basecalling
-> S3 Alignment evidence
-> S4 Variant calling
-> S5 Clinical annotation and interpretation

## Observed evidence

A target-overlapping nanopore raw-signal interpolation spanning the pathogenic
F11 target and two flanking bases on each side eliminated all ALT-supporting
parent states and suppressed the heterozygous pathogenic call in the controlled
bcftools workflow.

A same-sized off-target sham retained all 14 ALT parents, genotype 0/1 and
clean-like call quality.

## Modelled extension

S5 Clinical interpretation
-> S6 Storage and access control

The project may model the risk that an apparently negative or incomplete record
is stored or shared.

The project did not place the attacked result into a real clinical database and
did not observe a real patient outcome.

Any S5-to-S6 propagation record must therefore be labelled modelled or
illustrative rather than directly observed.

---

# Worked Scenario 2 — Graph-Amplified Privacy Breach

## Lifecycle arc

S6 Storage and access control
-> S7 Sharing and secondary use
-> S8 Familial and population amplification
-> S9 Long-term persistence and re-identification
-> S10 Containment, recovery and audit

## Evidence composition

The scenario combines:

- B1 calibrated graph-amplification results;
- B2 vault, lifetime and familial-risk modelling;
- B3 containment and authentication results.

It represents unauthorized genomic-platform access followed by graph-mediated
exposure, persistent downstream disclosure and containment response.

It must remain explicit which transitions are calibrated, simulated or
illustrative.

---

# Structural relationship between the two cases

Integrity arc:

S1 -> S2 -> S3 -> S4 -> S5 -> S6

Privacy arc:

S6 -> S7 -> S8 -> S9 -> S10

S6 is the lifecycle hinge connecting generation-time integrity risk to
storage-time privacy, propagation and containment risk.

---

# Validation Suite

## V1 — Schema and traceability validity

Every Handoff Vector and GRI claim must resolve to:

- one or more C2 evidence IDs;
- a defined C1 lifecycle stage;
- an authoritative repository source;
- an evidence tier;
- a stated limitation.

Any orphan claim fails validation.

## V2 — F11 target-versus-sham contrast

Inputs:

- clean F11 condition;
- PM2 on-target condition;
- PM2 off-target sham.

Pass condition:

The on-target PM2 scenario must rank strictly above clean and sham for D7
Pipeline Exposure Risk and relevant integrity and clinical modifiers.

The sham must remain in the same qualitative low-risk band as clean for
target-specific variant suppression.

## V3 — Amplifying versus non-amplifying disclosure

Inputs:

- isolated single-record disclosure without relative matching;
- B1 graph-amplified disclosure scenario.

Pass condition:

The graph-amplified scenario must score strictly higher for D3 Familial
Cascade Risk and D6 Amplification Risk.

## V4 — Confidence adjustment check

Inputs:

- an E2 controlled empirical case;
- an E4 uncalibrated model scenario.

Pass condition:

The framework must not present both as equally supported.

The weaker-evidence case must receive a lower evidence-adjusted score, wider
interval, lower confidence band or a documented combination.

## V5 — Directionality checks

All else equal:

- increased persistence must not reduce D5;
- increased graph amplification must not reduce D6;
- easier unauthorized access must not reduce D4;
- lower detectability must not reduce overall concern;
- lower recoverability must not reduce overall concern;
- stronger containment must not increase residual risk;
- lower evidence confidence must not increase evidentiary certainty.

All programmed assertions must pass.

## V6 — Ablation analysis

Privacy-case ablations:

- remove D5 persistence;
- remove D6 amplification;
- remove B3 containment.

Integrity-case ablations:

- remove clinical severity;
- remove detectability;
- remove evidence confidence.

Each ablation must alter the corresponding scenario in the expected direction.

## V7 — Weight sensitivity

Required weighting schemes:

- equal outcome-dimension weights;
- integrity-emphasized weights;
- privacy-emphasized weights;
- persistence-and-amplification-emphasized weights.

The following conclusions should remain stable across reasonable weight sets:

1. on-target F11 PM2 ranks above the sham for integrity-related risk;
2. graph-amplified disclosure ranks above isolated disclosure for D3 and D6;
3. stronger containment reduces residual privacy risk.

If these conclusions reverse under small weight changes, the GRI must be
reported as weight-sensitive.

## V8 — No-false-validation rule

Prohibited descriptions unless later evidence supports them:

- clinically validated;
- population validated;
- universally calibrated;
- predicts patient outcomes;
- proves real-world propagation.

Permitted descriptions include:

- framework-level validation;
- internally validated;
- contrast-tested;
- sensitivity-tested;
- calibrated simulation, where applicable;
- controlled single-locus case study.
