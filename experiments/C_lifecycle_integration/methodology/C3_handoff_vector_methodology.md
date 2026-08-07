# C3 Handoff Vector Methodology

## Purpose

The C3 Handoff Vector represents how an observed or modelled cyber-biosecurity
effect propagates between adjacent lifecycle stages.

The vector is constructed from C2 evidence records but is not itself the final
GenoPhylax Risk Index.

## Lifecycle cases

### Case C3-F11 — Integrity propagation

Observed experimental chain:

S1 -> S2 -> S3 -> S4 -> S5

Modelled extension:

S5 -> S6

The storage handoff is intentionally labelled modelled because the project did
not place a corrupted clinical record into a real clinical database.

### Case C3-PRIV — Privacy amplification and containment

Modelled/simulated chain:

S6 -> S7 -> S8 -> S9 -> S10

This case integrates B1 graph amplification, B2 lifetime/privacy modelling and
B3 containment/authentication.

## Handoff classifications

### OBSERVED_EMPIRICAL

The handoff is supported by direct experimental observations from A2/A3.

### MODEL_SUPPORTED

The handoff is represented by a calibrated or internal simulation/model from
B1/B2/B3.

### MODELLED_PROPAGATION

The handoff is scientifically plausible within the lifecycle architecture but
was not directly observed or represented by a calibrated downstream system.

These handoffs receive E5 at the C3 handoff level.

## Handoff Vector fields

Each handoff carries:

- handoff_id
- case_id
- from_stage
- to_stage
- source_evidence_ids
- observation_class
- evidence_tier
- effect_summary
- integrity_impact
- clinical_severity
- detectability
- recoverability
- containment_difficulty
- confidence_basis
- limitations

The modifier fields are categorical at C3.

No numerical modifier weights are defined here.

## Important distinction

C2 evidence tiers classify source evidence.

C3 handoff tiers classify the evidentiary strength of the specific lifecycle
transition.

A modelled lifecycle transition may therefore be E5 even when an upstream C2
claim supporting the scenario is E2 or E3.

## Scoring rule

C3 must not calculate the final GenoPhylax Risk Index.

Numerical normalization, modifier mapping, weighting and sensitivity analysis
belong to C4.
