# Module C — Authoritative Lifecycle Integration Rebuild

This directory is the current authoritative Module C implementation for Project GenoPhylax.

It supersedes earlier generated Module C numerical outputs and correction layers under
`experiments/C_lifecycle_integration/`.

## Why this rebuild exists

The earlier Module C integration was constructed before the final authoritative Module B
source state was locked. Some downstream Module C artifacts therefore consumed superseded
B3 authentication and containment values.

The integration layer was rebuilt from authoritative upstream evidence rather than patched
in place.

## Authoritative build chain

C0 -> upstream source lock  
C1 -> validated S1-S10 lifecycle schema  
C2 -> authoritative evidence registry  
C3 -> evidence-backed lifecycle handoffs  
C4 -> GRI architecture, normalization, modifiers, sensitivity  
C5 -> integrated findings  
C6 -> publication figures  
C7 -> publication tables  
C8 -> claim-evidence map

## Scientific policies

- A1 is `STANDALONE_NON_GRI`.
- A2 is supporting evidence and is not forced into Base GRI.
- F11 is the controlled clinical-integrity case.
- B1 and B2 provide the primary privacy-risk evidence.
- B3 containment and authentication are mitigation context.
- Authentication F1 is not interpreted as privacy-event detectability.
- Missing, unmeasured and non-applicable dimensions are not converted to zero.
- Evidence tiers are not numerical GRI multipliers.
- Mitigation modifiers are not multiplied into Base GRI.
- Sensitivity analyses are robustness checks, not confidence intervals.
- No earlier Module C numerical output is consumed by the authoritative rebuild.

## Current Base GRI results

- F11 Base GRI: `1.0000000000`
- Privacy Base GRI: `0.9373875000`
- Privacy 50/50 B2-B1 provenance sensitivity: `0.9242583333`

The F11 value is a framework score for the demonstrated computational case, not a
patient-outcome probability.

The Privacy value is an integrated framework score using model-derived and calibrated
evidence, not an empirical population probability.

## B3 mitigation context

Final authoritative B3 authentication:

- threshold: `3.6`
- precision: `0.9070`
- recall: `0.7800`
- F1: `0.8387`
- accuracy: `0.9400`

Origin-specific M5 residual candidates at fixed `k=10`:

- peripheral: `0.008`
- mid-degree: `0.795`
- hub: `0.970`

These residuals are scenario-specific and are not incorporated into Base GRI.

## Reproducibility

Validation outputs are stored under:

`experiments/C_lifecycle_integration/authoritative_rebuild/validation/`

The final publication validation requires:

- stale-value hits: 0
- validation errors: 0
- STATUS: PASS

## Legacy Module C files

Files elsewhere under `experiments/C_lifecycle_integration/` pre-dating this rebuild remain
in Git for provenance and historical traceability.

They must not be treated as current numerical authority when they conflict with this
directory.

The authoritative source for current Module C results is:

`experiments/C_lifecycle_integration/authoritative_rebuild/`
