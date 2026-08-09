# C4.7 Base Case Dimension Profiles

## Purpose

C4.7 assembles the authoritative D1-D7 risk profile for each GenoPhylax worked
case.

This stage does not yet compute a final GenoPhylax Risk Index.

Its purpose is to freeze:

- which dimensions are numerically scored;
- which dimensions are context only;
- which dimensions lack a baseline severity anchor;
- which dimensions are not applicable;
- the M6 evidence support attached to every scored dimension.

---

# Status vocabulary

## SCORED

A defensible normalized baseline risk value exists.

## CONTEXT_ONLY

Relevant lifecycle information exists, but it must not contribute numerical
baseline severity.

## NO_BASELINE_SEVERITY

Direct mitigation or contextual evidence exists without a direct
risk-increasing severity anchor.

## NOT_APPLICABLE

The dimension is not part of the worked-case mechanism.

---

# F11 profile

The controlled F11 worked case numerically scores:

- D2 Clinical Interpretation Risk;
- D7 Pipeline Exposure Risk.

Both equal 1.0 under their respective locked normalizations.

D5 remains context only because S5 -> S6 storage propagation is modelled E5
propagation rather than directly observed persistence.

D1, D3, D4 and D6 are not applicable to the current F11 worked-case baseline.

---

# Privacy profile

The privacy case numerically scores:

- D1 Identity Risk;
- D3 Familial Cascade Risk;
- D5 Persistence Risk;
- D6 Amplification Risk.

D4 remains unscored because there is no direct risk-increasing baseline
severity anchor.

Its B2 disclosure context and B3 mitigation results remain contextual.

D2 is context only because disease-inference trajectories were reproduced but
were not part of the locked privacy severity evidence set.

D7 is not applicable to the privacy worked case.

---

# Evidence support

Each scored dimension carries its C4.6 M6 evidence class.

F11:

- D2 -> E2
- D7 -> E2

Privacy:

- D1 -> E4
- D3 -> E4
- D5 -> E4
- D6 -> E3

No numerical evidence multiplier is applied.

---

# Vector representation

For aggregation, each case receives a sparse D1-D7 vector.

Missing/non-scored values remain null.

They are not replaced with zero.

Therefore:

not applicable != zero risk

context only != zero risk

no baseline severity != zero risk

---

# No aggregation yet

C4.7 does not:

- choose dimension weights;
- average missing dimensions as zero;
- apply M1-M5 modifiers;
- apply evidence discounts;
- compute a final GRI.

Those decisions remain deferred to C4.8 and subsequent sensitivity validation.

---

# Correlation warning

Some scored dimensions share causal or numerical inputs.

Examples:

F11 D2 and D7 describe different consequences of the same controlled F11
integrity pathway.

Privacy D1, D3 and D5 are related through the same lifetime-risk model.

Therefore a later simple arithmetic average is a transparent baseline, not a
claim that dimensions are statistically independent.

This correlation must be tested by ablation and sensitivity analysis.
