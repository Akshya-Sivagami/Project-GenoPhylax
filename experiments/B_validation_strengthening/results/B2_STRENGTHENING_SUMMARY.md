# B2 Validation Strengthening Summary

## Status

MODELLED / SENSITIVITY ANALYSIS

This analysis does not replace or modify the frozen historical B2 evidence.

## Frozen baseline reproduction

The original B2 lifetime equations were independently reproduced using
the frozen development assumptions.

Baseline outputs:
- re-identification reaches 100% at model year 13
- familial exposure reaches 100% at model year 15
- disease inference does not reach 100% within the 80-year horizon
- D5 at model year 50 = 9.3276, consistent with the frozen ~9.33 result

The pathogenic-variant unrecoverability calculation was also reproduced:
- pathogenic leakage assumption = 0.420
- exponential reconstruction coefficient = 3.5
- unrecoverability = 0.2299

## Lifetime parameter sensitivity

A total of 2187 model scenarios were evaluated.

The sensitivity grid varied:
- baseline re-identification risk
- baseline disease risk
- baseline familial risk
- database doubling time
- database saturation
- inference midpoint
- maximum inference factor

These are development sensitivity scenarios, not empirical confidence
intervals or real-world forecasts.

### Re-identification saturation

Among tested scenarios:
- earliest 100% horizon = model year 8
- median 100% horizon = model year 14.0
- latest 100% horizon = model year 26
- scenarios not reaching 100% = 0/2187

### Familial saturation

Among scenarios that reach 100%:
- earliest 100% horizon = model year 9
- median 100% horizon = model year 15.0
- latest 100% horizon = model year 26
- scenarios not reaching 100% = 243/2187

### Disease-inference saturation

Among scenarios that reach 100%:
- earliest 100% horizon = model year 16
- median 100% horizon = model year 26.0
- latest 100% horizon = model year 33
- scenarios not reaching 100% = 1458/2187

### D5 at model year 50

Across tested scenarios:
- minimum = 6.4967
- 5th percentile = 7.3300
- median = 8.6630
- 95th percentile = 10.0000
- maximum = 10.0000

The frozen ~9.33 value is therefore a baseline model output rather than a
universal persistence score.

## Pathogenic-variant unrecoverability sensitivity

A total of 247 combinations of pathogenic leakage and exponential
reconstruction coefficient were evaluated.

Across the full tested grid:
- minimum unrecoverability = 0.0388
- 5th percentile = 0.0681
- median = 0.2513
- 95th percentile = 0.5386
- maximum = 0.6703

The frozen 0.2299 value is therefore conditional on the selected leakage
and reconstruction assumptions.

A local +/-20% perturbation around those baseline assumptions produced
an unrecoverability range of 0.1204 to 0.3903.

## Structural model audit

The original lifetime implementation computes a technology-decay factor.

However, that factor is not used in the equations producing:
- re-identification risk
- disease-inference risk
- familial risk
- composite lifetime risk
- D5

Therefore the frozen lifetime outputs must not be described as being
numerically driven by technology-cost decay.

Technology decay is currently contextual/model scaffolding rather than an
active contributor to those reported risk trajectories.

## Defensible conclusion

B2 demonstrates how persistent genomic information can produce increasing
modeled privacy and familial exposure over long horizons under specified
database-growth and inference assumptions.

The exact year-13 re-identification horizon, year-15 familial horizon,
year-50 D5 of approximately 9.33, and pathogenic-variant unrecoverability
of 0.2299 are baseline MODEL OUTPUTS.

They are not observed real-world lifetimes, empirical probabilities, or
universal constants.

The strengthened evidence supports reporting ranges and scenario
sensitivity alongside the frozen baseline values.

## DEF CON framing

Safe claim:

"Under GenoPhylax's baseline lifetime model, re-identification saturates
at year 13 and familial exposure at year 15. Across 2,187 sensitivity
scenarios, the corresponding horizons shift substantially, demonstrating
that genomic persistence risk is durable but its exact timing is
assumption-dependent."

Avoid:

"Genomic data becomes fully re-identifiable after 13 years."

Also avoid:

"Pathogenic variants are 22.99% unrecoverable."

Prefer:

"Under the baseline reconstruction assumptions, the modeled
unrecoverability value is 0.2299; sensitivity analysis shows that this
quantity depends strongly on the leakage and reconstruction parameters."
