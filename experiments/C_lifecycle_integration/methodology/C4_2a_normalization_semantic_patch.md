# C4.2a Normalization Semantic Patch

## Purpose

This patch resolves two ambiguities identified during review of the C4.2
normalization registry.

No dimension scores, evidence weights, dimension weights, or GRI values are
introduced.

## 1. F11 D2 duplicate-measurement guardrail

The F11 D2 severity anchor has two related measurements:

- ALT-support loss fraction;
- pathogenic terminal call loss.

They derive from the same attacked experimental chain and must not be treated
as independent harms.

The roles are therefore locked as:

- ALT-support loss fraction:
  PRIMARY_SEVERITY_METRIC.

- pathogenic call loss:
  CORROBORATING_TERMINAL_ENDPOINT.

The terminal endpoint confirms downstream manifestation but is not added to or
averaged with the ALT-support loss fraction.

## 2. Lifetime probability versus temporal scalarization

The B2 re-identification, familial, and persistence evidence consists of
time-dependent modeled risk.

Each modeled probability is already bounded in [0,1] and therefore has a valid
risk-oriented probability normalization.

However, the choice of how a complete trajectory becomes one case-level scalar
is not equivalent to probability normalization.

C4.2 therefore does not select:

- year 10;
- year 20;
- the saturation year;
- the terminal modeled year;
- an arbitrary model-horizon denominator.

D1, D3 and D5 temporal scalarization is explicitly deferred to C4.3.

C4.3 must reconstruct the complete authoritative trajectories before candidate
temporal summaries are compared.

## Candidate for later evaluation

A time-average / trajectory-area summary may be evaluated because it can
incorporate both risk magnitude and onset time while remaining in [0,1].

It is not adopted by this patch.

## Final C4.2 state

Normalization families: defined.

Risk direction: defined.

Boundary behavior: tested.

Metric roles: defined.

F11 duplicate-severity counting: prohibited.

Lifetime temporal scalarization: deferred.

Dimension scores: not computed.

Dimension weights: not defined.

Evidence weights: not defined.

Final GRI: not computed.
